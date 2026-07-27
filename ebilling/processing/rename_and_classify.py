import datetime
from pathlib import Path
from azure.storage.blob import BlobServiceClient

# -----------------------------
# CONFIG
# -----------------------------
AZURE_STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=...AccountKey=..."
CONTAINER = "synapse"

BASE_PATH = "ebilling/invoice"
RAW_PATH = f"{BASE_PATH}/raw/"
PASSED_PATH = f"{BASE_PATH}/passed/"
IGNORED_PATH = f"{BASE_PATH}/ignored/"
FAILED_PATH = f"{BASE_PATH}/failed/"

# -----------------------------
# HELPERS
# -----------------------------
def today():
    return datetime.date.today().strftime("%Y-%m-%d")

def classify(delivery_mode):
    if delivery_mode in ("email", "print"):
        return "passed"
    if delivery_mode == "ignore":
        return "ignored"
    return "failed"

def upload_copy(blob_service, src_blob, dest_blob):
    src_client = blob_service.get_blob_client(CONTAINER, src_blob)
    dest_client = blob_service.get_blob_client(CONTAINER, dest_blob)
    dest_client.start_copy_from_url(src_client.url)

def delete_blob(blob_service, blob_path):
    blob_service.get_blob_client(CONTAINER, blob_path).delete_blob()

# -----------------------------
# MAIN LOGIC
# -----------------------------
def rename_and_classify(meta_df, ddp_df):
    """
    meta_df columns:
        invoice_number, billto_account, soldto_account

    ddp_df columns:
        account_number, doc_type, customer_control, delivery_mode
    """

    blob_service = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    container_client = blob_service.get_container_client(CONTAINER)

    # List raw PDFs
    raw_blobs = container_client.list_blobs(name_starts_with=RAW_PATH)

    for blob in raw_blobs:
        fname = Path(blob.name).name

        # Extract invoice number from filename: ABCINVOICE_2024050101.pdf
        invoice_number = Path(fname).stem.replace("ABCINVOICE_", "")

        # Lookup metadata
        meta_row = meta_df[meta_df["invoice_number"] == invoice_number]
        if meta_row.empty:
            # No metadata → failed
            dest = f"{FAILED_PATH}/{today()}/{fname}"
            upload_copy(blob_service, blob.name, dest)
            delete_blob(blob_service, blob.name)
            continue

        meta_row = meta_row.iloc[0]
        billto = meta_row["billto_account"]
        soldto = meta_row["soldto_account"]

        # Lookup DDP (customer control matrix)
        ddp_row = ddp_df[
            (ddp_df["account_number"] == billto) &
            (ddp_df["doc_type"] == "invoice")
        ]

        if ddp_row.empty:
            # No DDP → failed
            dest = f"{FAILED_PATH}/{today()}/{fname}"
            upload_copy(blob_service, blob.name, dest)
            delete_blob(blob_service, blob.name)
            continue

        ddp_row = ddp_row.iloc[0]
        control = ddp_row["customer_control"]      # Key / Sub / Both
        delivery = ddp_row["delivery_mode"]        # email / print / ignore / None
        classification = classify(delivery)

        # -----------------------------
        # RENAME LOGIC (ABC prefix)
        # -----------------------------
        new_files = []

        if control == "Key":
            new_files.append(f"ABCINV_{invoice_number}_{billto}.pdf")

        elif control == "Sub":
            new_files.append(f"ABCINV_{invoice_number}_{soldto}.pdf")

        elif control == "Both":
            new_files.append(f"ABCINV_{invoice_number}_{billto}.pdf")
            new_files.append(f"ABCINV_{invoice_number}_{soldto}.pdf")

        else:
            # Unknown control → failed
            dest = f"{FAILED_PATH}/{today()}/{fname}"
            upload_copy(blob_service, blob.name, dest)
            delete_blob(blob_service, blob.name)
            continue

        # -----------------------------
        # COPY TO CLASSIFICATION FOLDER
        # -----------------------------
        for new_name in new_files:
            dest = f"{BASE_PATH}/{classification}/{today()}/{new_name}"
            upload_copy(blob_service, blob.name, dest)

        # Delete raw file after processing
        delete_blob(blob_service, blob.name)

    print("PDF renaming + classification completed.")


import json
import datetime
from pathlib import Path

import pandas as pd
import pyodbc
from azure.storage.blob import BlobServiceClient

SETTINGS_PATH = "config/settings.json"

def load_settings():
    with open(SETTINGS_PATH) as f:
        return json.load(f)

def today():
    return datetime.date.today().strftime("%Y-%m-%d")

def classify(delivery_mode):
    if delivery_mode in ("email", "print"):
        return "passed"
    if delivery_mode == "ignore":
        return "ignored"
    return "failed"

def connect_blob(cfg):
    return BlobServiceClient.from_connection_string(cfg["azure_storage_connection_string"])

def connect_sql(cfg):
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={cfg['sql_server']};DATABASE={cfg['sql_db']};"
        f"UID={cfg['sql_user']};PWD={cfg['sql_password']};Encrypt=yes;TrustServerCertificate=no;"
    )
    return pyodbc.connect(conn_str)

def load_metadata_from_synapse(cfg):
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={cfg['synapse_server']};DATABASE={cfg['synapse_db']};"
        f"UID={cfg['sql_user']};PWD={cfg['sql_password']};Encrypt=yes;TrustServerCertificate=no;"
    )
    conn = pyodbc.connect(conn_str)

    sql = """
    SELECT
        h.EXTERNAL_REF_ID AS invoice_number,
        (SELECT TOP 1 c.EXTERNAL_CUST_ID
         FROM dbo.CUSTOMER c
         WHERE c.CUSTOMER_ID = h.CUSTOMER_ID) AS billto_account,
        (SELECT TOP 1 c.EXTERNAL_CUST_ID
         FROM dbo.CUSTOMER c
         WHERE c.CUSTOMER_ID = h.ALT2_CUSTOMER_ID) AS soldto_account
    FROM dbo.ORDER_HDR h;
    """
    df = pd.read_sql(sql, conn)
    conn.close()
    return df

def load_ddp(conn_sql):
    df = pd.read_sql("SELECT * FROM dbo.DDP;", conn_sql)
    return df

def rename_and_classify():
    cfg = load_settings()
    blob_service = connect_blob(cfg)
    conn_sql = connect_sql(cfg)

    meta_df = load_metadata_from_synapse(cfg)
    ddp_df = load_ddp(conn_sql)

    container = cfg["blob_container"]
    base = "ebilling/invoice"
    raw_prefix = f"{base}/raw/"
    passed_prefix = f"{base}/passed/{today()}/"
    ignored_prefix = f"{base}/ignored/{today()}/"
    failed_prefix = f"{base}/failed/{today()}/"

    container_client = blob_service.get_container_client(container)
    raw_blobs = container_client.list_blobs(name_starts_with=raw_prefix)

    for blob in raw_blobs:
        fname = Path(blob.name).name
        invoice_number = Path(fname).stem.replace("ABCINVOICE_", "")

        meta_row = meta_df[meta_df["invoice_number"] == invoice_number]
        if meta_row.empty:
            dest = failed_prefix + fname
            _copy_and_delete(blob_service, container, blob.name, dest)
            continue

        meta_row = meta_row.iloc[0]
        billto = meta_row["billto_account"]
        soldto = meta_row["soldto_account"]

        ddp_row = ddp_df[
            (ddp_df["account_number"] == billto) &
            (ddp_df["doc_type"] == "invoice")
        ]

        if ddp_row.empty:
            dest = failed_prefix + fname
            _copy_and_delete(blob_service, container, blob.name, dest)
            continue

        ddp_row = ddp_row.iloc[0]
        control = ddp_row["customer_control"]
        delivery = ddp_row["delivery_mode"]
        classification = classify(delivery)

        new_files = []
        if control == "Key":
            new_files.append(f"ABCINV_{invoice_number}_{billto}.pdf")
        elif control == "Sub":
            new_files.append(f"ABCINV_{invoice_number}_{soldto}.pdf")
        elif control == "Both":
            new_files.append(f"ABCINV_{invoice_number}_{billto}.pdf")
            new_files.append(f"ABCINV_{invoice_number}_{soldto}.pdf")
        else:
            dest = failed_prefix + fname
            _copy_and_delete(blob_service, container, blob.name, dest)
            continue

        for new_name in new_files:
            if classification == "passed":
                dest = passed_prefix + new_name
            elif classification == "ignored":
                dest = ignored_prefix + new_name
            else:
                dest = failed_prefix + new_name
            _copy(blob_service, container, blob.name, dest)

        blob_service.get_blob_client(container, blob.name).delete_blob()

    conn_sql.close()
    print("Rename + classification complete.")

def _copy(blob_service, container, src, dest):
    src_client = blob_service.get_blob_client(container, src)
    dest_client = blob_service.get_blob_client(container, dest)
    dest_client.start_copy_from_url(src_client.url)

def _copy_and_delete(blob_service, container, src, dest):
    _copy(blob_service, container, src, dest)
    blob_service.get_blob_client(container, src).delete_blob()

if __name__ == "__main__":
    rename_and_classify()

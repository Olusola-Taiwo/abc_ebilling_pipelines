import json
import paramiko
from azure.storage.blob import BlobServiceClient

SETTINGS_PATH = "config/settings.json"

def load_settings():
    with open(SETTINGS_PATH) as f:
        return json.load(f)

def ingest_raw():
    cfg = load_settings()

    # SFTP
    transport = paramiko.Transport((cfg["sftp_host"], cfg["sftp_port"]))
    transport.connect(username=cfg["sftp_user"], password=cfg["sftp_password"])
    sftp = paramiko.SFTPClient.from_transport(transport)

    # Blob
    blob_service = BlobServiceClient.from_connection_string(
        cfg["azure_storage_connection_string"]
    )
    container = cfg["blob_container"]
    raw_prefix = "ebilling/invoice/raw/"

    for fname in sftp.listdir("/outgoing/invoices"):
        if not fname.lower().endswith(".pdf"):
            continue

        remote_path = f"/outgoing/invoices/{fname}"
        with sftp.open(remote_path, "rb") as f:
            data = f.read()

        if len(data) == 0:
            continue

        blob_path = raw_prefix + fname
        blob_client = blob_service.get_blob_client(container=container, blob=blob_path)
        blob_client.upload_blob(data, overwrite=True)

        sftp.remove(remote_path)

    sftp.close()
    transport.close()
    print("Raw ingestion complete.")

if __name__ == "__main__":
    ingest_raw()


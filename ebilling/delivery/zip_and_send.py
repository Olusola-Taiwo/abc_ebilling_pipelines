import json
import io
import datetime
import zipfile

import paramiko
from azure.storage.blob import BlobServiceClient

SETTINGS_PATH = "config/settings.json"

def load_settings():
    with open(SETTINGS_PATH) as f:
        return json.load(f)

def create_zip_and_send():
    cfg = load_settings()
    blob_service = BlobServiceClient.from_connection_string(
        cfg["azure_storage_connection_string"]
    )
    container = cfg["blob_container"]

    base = "ebilling/invoice"
    passed_prefix = f"{base}/passed/{datetime.date.today().strftime('%Y-%m-%d')}/"
    zip_prefix = f"{base}/zipped/"

    blobs = list(
        blob_service.get_container_client(container).list_blobs(
            name_starts_with=passed_prefix
        )
    )

    if not blobs:
        print("No passed PDFs to zip.")
        return

    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for b in blobs:
            data = blob_service.get_blob_client(container, b.name).download_blob().readall()
            rel_name = b.name[len(passed_prefix):]
            zf.writestr(rel_name, data)

    mem_zip.seek(0)
    today = datetime.date.today().strftime("%Y%m%d")
    ts = datetime.datetime.now().strftime("%H%M%S")
    zip_name = f"ABCINV_{today}_{ts}_{len(blobs)}.zip"
    zip_blob_path = zip_prefix + zip_name

    blob_service.get_blob_client(container, zip_blob_path).upload_blob(mem_zip.read(), overwrite=True)

    # SFTP upload
    transport = paramiko.Transport((cfg["sftp_host"], cfg["sftp_port"]))
    transport.connect(username=cfg["sftp_user"], password=cfg["sftp_password"])
    sftp = paramiko.SFTPClient.from_transport(transport)

    remote_path = f"/incoming/invoices/{zip_name}"
    with sftp.open(remote_path, "wb") as f:
        f.write(mem_zip.getvalue())

    sftp.close()
    transport.close()
    print(f"ZIP {zip_name} sent to SFTP.")

if __name__ == "__main__":
    create_zip_and_send()


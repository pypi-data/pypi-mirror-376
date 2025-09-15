from google.cloud import storage
import os
from ..logging_utils import log

def upload_to_gcs(src_path: str, bucket: str, dest_blob: str, project: str | None = None):
    client = storage.Client(project=project)
    bkt = client.bucket(bucket)
    blob = bkt.blob(dest_blob)
    blob.chunk_size = 8 * 1024 * 1024  # 8MB resumable chunks
    blob.upload_from_filename(src_path)
    log("gcs_upload_ok", src=src_path, bucket=bucket, dest=dest_blob, bytes=os.path.getsize(src_path))

def download_from_gcs(bucket: str, blob_name: str, dst_path: str, project: str | None = None):
    client = storage.Client(project=project)
    bkt = client.bucket(bucket)
    blob = bkt.blob(blob_name)
    os.makedirs(os.path.dirname(dst_path) or ".", exist_ok=True)
    blob.download_to_filename(dst_path)
    log("gcs_download_ok", bucket=bucket, blob=blob_name, dst=dst_path, bytes=os.path.getsize(dst_path))

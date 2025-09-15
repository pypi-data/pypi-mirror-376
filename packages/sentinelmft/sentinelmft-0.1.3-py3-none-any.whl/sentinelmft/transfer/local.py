import shutil, os
from ..logging_utils import log

def copy_local(src: str, dst: str):
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    shutil.copy2(src, dst)
    log("local_copy_done", src=src, dst=dst, bytes=os.path.getsize(dst))

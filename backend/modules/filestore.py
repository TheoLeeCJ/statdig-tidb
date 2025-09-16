import os
import hashlib
from typing import Optional

FILESTORE_PATH = "filestore"

def ensure_filestore_exists():
    """Ensure the filestore directory exists"""
    os.makedirs(FILESTORE_PATH, exist_ok=True)

def get_file_md5(file_data: bytes) -> str:
    """Calculate MD5 hash of file data"""
    return hashlib.md5(file_data).hexdigest()

def store_file(file_data: bytes, original_filename: str) -> str:
    """
    Store file by its MD5 hash and return the MD5
    """
    ensure_filestore_exists()
    
    # Generate MD5 hash for the file
    file_md5 = get_file_md5(file_data)
    
    # Store using only the MD5 hash (no extension)
    filepath = os.path.join(FILESTORE_PATH, file_md5)
    
    with open(filepath, "wb") as f:
        f.write(file_data)
    
    return file_md5

def retrieve_file(file_md5: str) -> Optional[bytes]:
    """
    Retrieve file data by MD5 hash
    Returns None if file doesn't exist
    """
    filepath = os.path.join(FILESTORE_PATH, file_md5)
    
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, "rb") as f:
        return f.read()

import os
import uuid
import aiofiles
from fastapi import UploadFile


async def save_upload_file(upload_file: UploadFile, upload_dir: str) -> str:
    """Save an uploaded file and return the file path."""
    os.makedirs(upload_dir, exist_ok=True)
    ext = os.path.splitext(upload_file.filename or "paper.pdf")[1]
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(upload_dir, filename)

    async with aiofiles.open(file_path, "wb") as f:
        content = await upload_file.read()
        await f.write(content)

    return file_path


def get_file_size(file_path: str) -> int:
    """Get file size in bytes."""
    return os.path.getsize(file_path)


def delete_file(file_path: str) -> None:
    """Delete a file if it exists."""
    if os.path.exists(file_path):
        os.remove(file_path)

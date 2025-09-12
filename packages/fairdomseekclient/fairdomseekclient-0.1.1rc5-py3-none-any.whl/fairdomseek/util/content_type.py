import mimetypes
from pathlib import Path


def infer_content_type(file_path: Path) -> str:
    content_type, _ = mimetypes.guess_type(file_path)

    if content_type is None:
        content_type = "application/octet-stream"  # fallback

    return content_type

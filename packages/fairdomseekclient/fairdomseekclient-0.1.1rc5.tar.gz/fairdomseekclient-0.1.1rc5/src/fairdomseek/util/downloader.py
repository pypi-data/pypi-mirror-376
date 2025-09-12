import io
import mimetypes
from pathlib import Path
from typing import Optional


class BlobStream:
    def __init__(self, blob: bytes, content_type: Optional[str] = None):
        self.stream = io.BytesIO(blob)
        self.content_type = content_type.lower() if content_type else "application/octet-stream"

    @classmethod
    def from_http_response(cls, response):
        content_type = response.headers.get("Content-Type", "application/octet-stream")
        return cls(response.content, content_type)

    def get_extension_hint(self) -> str:
        ext = mimetypes.guess_extension(self.content_type)
        return ext or ".bin"

    def serialize_to_file(self, filepath: Path | str):
        """
        Save the blob to disk.
        """
        filepath = Path(filepath)
        self.stream.seek(0)
        with open(filepath, "wb") as f:
            f.write(self.stream.read())

    def __repr__(self):
        return f"<BlobStream content_type='{self.content_type}' size={self.size()} bytes>"

    def size(self):
        pos = self.stream.tell()
        self.stream.seek(0, io.SEEK_END)
        size = self.stream.tell()
        self.stream.seek(pos)
        return size

    def reset(self):
        self.stream.seek(0)
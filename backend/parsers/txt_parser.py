import chardet

from .document_parser import DocumentParser

class TxtParser(DocumentParser):
    """Parse plain text files.

    Handles UTF-8 and other encodings by detecting the most likely encoding using
    ``chardet``. Returns the content as a Unicode string. Raises ``ValueError`` if
    decoding fails.
    """

    def parse(self, file_bytes: bytes) -> str:
        # Detect encoding (fallback to utf-8)
        detection = chardet.detect(file_bytes)
        encoding = detection.get("encoding") or "utf-8"
        try:
            text = file_bytes.decode(encoding)
        except Exception as exc:
            raise ValueError(f"Failed to decode TXT file using encoding {encoding}: {exc}")
        return text.strip()

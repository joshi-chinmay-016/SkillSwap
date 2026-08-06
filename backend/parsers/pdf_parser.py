"""PDF Parser — text extraction from PDF files using PyMuPDF (fitz) or pypdf fallback."""
from __future__ import annotations

from .document_parser import DocumentParser


class PDFParser(DocumentParser):
    """Parse PDF files using PyMuPDF (or pypdf fallback).

    Extracts text page by page and joins with double newlines.
    Raises ValueError if document cannot be opened or contains no text.
    """

    def parse(self, file_bytes: bytes) -> str:
        # Try PyMuPDF (fitz) first
        try:
            import fitz

            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text_chunks = []
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                text = page.get_text("text")
                if text:
                    text_chunks.append(text.strip())
            doc.close()

            if not text_chunks:
                raise ValueError("No extractable text found in PDF document.")
            return "\n\n".join(text_chunks)
        except ImportError:
            # Fallback to pypdf if fitz is not installed
            try:
                import io
                import pypdf

                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                text_chunks = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_chunks.append(text.strip())

                if not text_chunks:
                    raise ValueError("No extractable text found in PDF document.")
                return "\n\n".join(text_chunks)
            except ImportError:
                raise ValueError(
                    "No PDF library available. Please install pymupdf or pypdf."
                )
            except Exception as exc:
                raise ValueError(f"Unable to open PDF file: {exc}")
        except Exception as exc:
            if isinstance(exc, ValueError):
                raise
            raise ValueError(f"Unable to open PDF file: {exc}")

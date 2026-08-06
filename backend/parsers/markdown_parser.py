import re
import markdown
from .document_parser import DocumentParser

class MarkdownParser(DocumentParser):
    """Parse Markdown files and return plain text.

    The parser converts markdown to HTML using the ``markdown`` library, then strips
    HTML tags to obtain clean plain‑text. This approach preserves line breaks and
    basic list structures while discarding formatting markup.
    """

    def _strip_html(self, html: str) -> str:
        # Very small HTML tag stripper – removes all <...> tags.
        # This is sufficient for simple markdown conversion.
        return re.sub(r"<[^>]+>", "", html)

    def parse(self, file_bytes: bytes) -> str:
        try:
            markdown_text = file_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Failed to decode markdown file as UTF‑8: {exc}")
        html = markdown.markdown(markdown_text)
        plain = self._strip_html(html)
        return plain.strip()

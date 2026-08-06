from .pdf_parser import PDFParser
from .txt_parser import TxtParser
from .markdown_parser import MarkdownParser
from .document_parser import DocumentParser

class UnsupportedFileTypeError(Exception):
    """Raised when no parser is available for a given file extension."""

class ParserFactory:
    """Factory that returns a concrete parser based on file extension.

    Supported extensions are mapped to their parser classes. New parsers can be
    added by extending the ``_parsers`` dictionary.
    """

    _parsers = {
        "pdf": PDFParser,
        "txt": TxtParser,
        "md": MarkdownParser,
        "markdown": MarkdownParser,
    }

    @classmethod
    def get_parser(cls, extension: str) -> DocumentParser:
        ext = extension.lower().lstrip(".")
        parser_cls = cls._parsers.get(ext)
        if not parser_cls:
            raise UnsupportedFileTypeError(f"No parser for extension '{extension}'")
        return parser_cls()

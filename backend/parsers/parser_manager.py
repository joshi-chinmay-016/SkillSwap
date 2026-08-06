from .parser_factory import ParserFactory, UnsupportedFileTypeError
from .document_parser import DocumentParser

class ParserManager:
    """High‑level manager used by services to parse a document.

    It hides the factory and provides a single entry point:
        parse_document(file_bytes: bytes, extension: str) -> str
    It also converts parsing errors into ``ValueError`` for the service layer.
    """

    @staticmethod
    def parse_document(file_bytes: bytes, extension: str) -> str:
        try:
            parser: DocumentParser = ParserFactory.get_parser(extension)
            return parser.parse(file_bytes)
        except UnsupportedFileTypeError as exc:
            raise ValueError(str(exc))
        except Exception as exc:
            # Wrap any unexpected errors for consistent handling.
            raise ValueError(f"Failed to parse {extension} document: {exc}")

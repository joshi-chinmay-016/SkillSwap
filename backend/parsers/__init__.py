"""parsers — document text extraction package."""
from .parser_manager import ParserManager
from .parser_factory import ParserFactory, UnsupportedFileTypeError

__all__ = ["ParserManager", "ParserFactory", "UnsupportedFileTypeError"]

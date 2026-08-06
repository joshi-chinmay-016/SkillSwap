import abc
from typing import Any

class DocumentParser(abc.ABC):
    """Abstract base class for all document parsers.

    Concrete parsers must implement the :meth:`parse` method, which receives the raw
    bytes of an uploaded file and returns a plain‑text string representation. The
    method should raise a :class:`ValueError` if parsing fails for any reason so the
    calling service can handle the error uniformly.
    """

    @abc.abstractmethod
    def parse(self, file_bytes: bytes) -> str:
        """Parse the supplied file bytes and return extracted plain text.

        Args:
            file_bytes: The binary content of the uploaded document.
        Returns:
            A string containing the extracted textual content.
        Raises:
            ValueError: If the file cannot be parsed or is of an unsupported format.
        """
        raise NotImplementedError

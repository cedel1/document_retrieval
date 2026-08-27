"""Abstract document page model."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional


class BaseDocumentPage(ABC):
    """Abstract representation of a single page within a document."""

    def __init__(self, identifier: str, page_url: str, index: int, output_dir: str = "output") -> None:
        """Initialize a page object for a single document page.

        Args:
            identifier: Unique identifier of the document page.
            page_url: URL used to fetch the page content.
            index: Zero-based position of the page within the document.
            output_dir: Directory used to store downloaded page artifacts.

        Returns:
            None: The page instance is created in memory.
        """
        self.identifier = identifier
        self.page_url = page_url
        self.index = index
        self.output_dir = Path(output_dir)

    @property
    def output_base(self) -> Path:
        """Return the filesystem base path used for the downloaded page output.

        Args:
            None: This property does not accept arguments.

        Returns:
            Path: The page-specific base output path.
        """
        return self.output_dir / f"page_{self.index:03d}_{self.identifier[:8]}"

    @property
    def image_properties_url(self) -> str:
        """Return the ImageProperties XML URL for the current page UUID.

        Args:
            None: This property does not accept arguments.

        Returns:
            str: URL of the image properties XML for the page.
        """
        return f"https://digitalnistudovna.army.cz/search/zoomify/uuid:{self.identifier}/ImageProperties.xml"

    @abstractmethod
    def download(self, dezoomify_path: str = "dezoomify-rs", dezoomify_args: Optional[List[str]] = None) -> bool:
        """Download the current page with the dezoomify tool.

        Args:
            dezoomify_path: Path or command name of the dezoomify executable.
            dezoomify_args: Optional additional command-line arguments.

        Returns:
            bool: True when the page download succeeds, otherwise False.
        """

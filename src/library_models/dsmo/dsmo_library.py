"""Abstract library model."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from typing import Sequence

from src.library_models.base.base_library import BaseLibrary
from src.library_models.dsmo.dsmo_document import DSMODocument
from src.library_models.dsmo.dsmo_document_factory import DSMODocumentFactory
from src.servers.base_server import BaseServerType
from src.servers.kramerius_5_server import Kramerius5ServerType


class DSMOLibrary(BaseLibrary):
    """Concrete DSMO library/server that a specific document is hosted on."""

    server_urls: list[str] = ["https://www.digitalniknihovna.cz/dsmo/", "https://digitalnistudovna.army.cz/"]
    server_type: BaseServerType = Kramerius5ServerType()  # NOSONAR  # subclass of BaseServerType
    page_detail_url: str = "https://digitalnistudovna.army.cz/"
    library_name = "Library_DSMO"

    def __init__(self, document_url: Optional[str] = None) -> None:
        """Initialize the DSMO library definition.

        Args:
            document_url: Base URL of the DSMO library.

        Returns:
            None: The library instance is created in memory.
        """
        if document_url is None:
            document_url = ""
        super().__init__(document_url)

    def preprocess_document_from_url(
        self,
        document_url: str,
        page_detail_url: str,
        output_dir: str = "output",
        page_uuids: Optional[Sequence[str]] = None,
    ) -> DSMODocument:
        """Preprocess a document before processing.

        Args:
            document_url: URL of the document to preprocess.
            page_detail_url: The base server URL for the document page.
            output_dir: Directory used to store generated document artifacts.
            page_uuids: Optional page identifiers to attach immediately.

        Returns:
            DSMODocument: The preprocessed document.

        Raises:
            ValueError: If the document URL does not belong to this library.
        """
        output_path = str(Path(output_dir + "/" + self.library_name))
        return DSMODocumentFactory.from_url(
            library=self,
            source_url=document_url,
            page_detail_url=page_detail_url,
            output_dir=output_path,
            page_uuids=page_uuids,
        )

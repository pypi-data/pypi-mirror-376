from prefect import get_run_logger
from nemo_library.adapter.genericodbc.flow import generic_odbc_extract_flow
from nemo_library.adapter.inforcom.inforcom_object_type import load_inforcom_enum
from nemo_library.adapter.utils.structures import ETLBaseObjectType
from nemo_library.core import NemoLibrary


class InforComExtract:
    """
    Adapter for InforCom API.
    """

    def __init__(self):

        nl = NemoLibrary()
        self.config = nl.config
        self.logger = get_run_logger()

        super().__init__()

    def extract(
        self,
        odbc_connstr: str,
        InforComObjectType: type[ETLBaseObjectType],
        timeout: int = 300,
    ) -> None:
        """
        Extracts data from the InforCom API for all entities.
        """

        for entity in InforComObjectType:
            self.logger.info(f"Starting extraction for entity: {entity.name}")

            generic_odbc_extract_flow(
                bextract=True,
                bload=True,
                odbc_connstr=odbc_connstr,
                query=f"SELECT * FROM {entity.label}",
                filename=f"INFORCOM_{entity.label}",
                chunksize=10000 if entity.big_data else None,
                gzip_enabled=True,
                timeout=timeout,
            )

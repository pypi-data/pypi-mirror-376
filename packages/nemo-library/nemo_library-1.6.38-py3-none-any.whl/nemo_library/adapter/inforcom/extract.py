from prefect import get_run_logger
from nemo_library.adapter.genericodbc.flow import generic_odbc_extract_flow
from nemo_library.core import NemoLibrary


class InforComExtract:
    """
    Adapter for InforCom API.
    """

    def __init__(self, cfg: dict) -> None:

        nl = NemoLibrary()
        self.config = nl.config
        self.logger = get_run_logger()
        self.cfg = cfg

        super().__init__()

    def extract(
        self, odbc_connstr: str, odbc_dsn: str, user: str, password: str
    ) -> None:
        """
        Extracts data from the InforCom API for all entities.
        """

        tables = self.cfg["extract"]["tables"]
        for table in tables:
            if not tables[table]["active"]:
                self.logger.info(f"Skipping inactive entity: {table}")
                continue
            
            self.logger.info(f"Starting extraction for entity: {table}")

            generic_odbc_extract_flow(
                bextract=True,
                bload=True,
                odbc_connstr=odbc_connstr,
                query=f"SELECT * FROM {self.cfg['extract']['table_prefix']}{table}",
                filename=f"INFORCOM_{table}",
                chunksize=10000 if tables[table]["big_data"] else None,
                gzip_enabled=True,
                timeout=self.cfg["extract"]["timeout"],
            )

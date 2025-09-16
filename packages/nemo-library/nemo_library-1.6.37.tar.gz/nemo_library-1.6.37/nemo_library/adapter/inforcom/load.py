from prefect import get_run_logger
from nemo_library.adapter.utils.file_handler import ETLFileHandler
from nemo_library.adapter.utils.structures import ETLBaseObjectType
from nemo_library.core import NemoLibrary


class InforComLoad:
    """
    Class to handle load of data for the InforCom adapter.
    """

    def __init__(self, cfg: dict) -> None:

        nl = NemoLibrary()
        self.config = nl.config
        self.logger = get_run_logger()
        self.cfg = cfg

        super().__init__()

    def load(self) -> None:
        """
        Load the extracted and transformed data into Nemo.
        """
        self.logger.info("Loading InforCom data into Nemo")


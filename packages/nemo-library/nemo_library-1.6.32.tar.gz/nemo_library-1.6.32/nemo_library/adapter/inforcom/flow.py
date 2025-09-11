from enum import Enum
from pathlib import Path
from prefect import flow, task, get_run_logger

from nemo_library.adapter.inforcom.extract import InforComExtract
from nemo_library.adapter.inforcom.inforcom_object_type import load_inforcom_enum
from nemo_library.adapter.inforcom.load import InforComLoad
from nemo_library.adapter.inforcom.transform import InforComTransform
from nemo_library.adapter.utils.structures import ETLBaseObjectType


@flow(name="InforCom ETL Flow", log_prints=True)
def inforcom_flow(
    bextract: bool = True,
    btransform: bool = True,
    bload: bool = True,
    odbc_connstr: str | None = None,
    timeout: int = 300,
):
    logger = get_run_logger()
    logger.info("Starting InforCom ETL Flow")

    # initialize config
    configpath = Path(__file__).parent / "config.json"
    
    if not configpath.exists():
        raise FileNotFoundError(f"Config file not found at {configpath}")
    
    InforComObjectType = load_inforcom_enum(configpath)
    if not InforComObjectType:
        raise ValueError("Failed to load InforComObjectType from config.json")

    if bextract:
        logger.info("Extracting objects from InforCom")
        extract(
            odbc_connstr=odbc_connstr,
            timeout=timeout,
            InforComObjectType=InforComObjectType,
        )

    if btransform:
        logger.info("Transforming InforCom objects")
        transform(InforComObjectType=InforComObjectType)

    if bload:
        logger.info("Loading InforCom objects")
        load(InforComObjectType=InforComObjectType)

    logger.info("InforCom ETL Flow finished")


@task(name="Extract All Objects from InforCom")
def extract(
    odbc_connstr: str,
    InforComObjectType: type[ETLBaseObjectType],
    timeout: int = 300,
):
    logger = get_run_logger()
    logger.info("Extracting all InforCom objects")

    extractor = InforComExtract()
    extractor.extract(
        odbc_connstr=odbc_connstr,
        timeout=timeout,
        InforComObjectType=InforComObjectType,
    )


@task(name="Transform Objects")
def transform(InforComObjectType: type[ETLBaseObjectType]):
    logger = get_run_logger()
    logger.info("Transforming InforCom objects")

    transformer = InforComTransform()


@task(name="Load Objects into Nemo")
def load(InforComObjectType: type[ETLBaseObjectType]):
    logger = get_run_logger()
    logger.info("Loading InforCom objects into Nemo")

    loader = InforComLoad()
    loader.load(InforComObjectType=InforComObjectType)

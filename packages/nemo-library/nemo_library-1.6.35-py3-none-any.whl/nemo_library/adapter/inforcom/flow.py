import json
from pathlib import Path
from prefect import flow, task, get_run_logger

from nemo_library.adapter.inforcom.config_io import load_config, to_primitive
from nemo_library.adapter.inforcom.extract import InforComExtract
from nemo_library.adapter.inforcom.load import InforComLoad
from nemo_library.adapter.inforcom.transform import InforComTransform


@flow(name="InforCom ETL Flow", log_prints=True)
def inforcom_flow(
    bextract: bool = True,
    btransform: bool = True,
    bload: bool = True,
    odbc_connstr: str | None = None,
    odbc_dsn: str | None = None,
    user: str | None = None,
    password: str | None = None,
):
    logger = get_run_logger()
    logger.info("Starting InforCom ETL Flow")

    # initialize config
    configpath = Path(__file__).parent / "config.json"
    if not configpath.exists():
        raise FileNotFoundError(f"Config file not found at {configpath}")
    cfg_model = load_config(configpath)
    cfg_dict = to_primitive(cfg_model)
    print(json.dumps(cfg_dict, indent=2))

    if bextract:
        logger.info("Extracting objects from InforCom")
        extract(
            odbc_connstr=odbc_connstr,
            odbc_dsn=odbc_dsn,
            user=user,
            password=password,
            cfg=cfg_dict,
        )

    if btransform:
        logger.info("Transforming InforCom objects")
        transform(cfg=cfg_dict)

    if bload:
        logger.info("Loading InforCom objects")
        load(cfg=cfg_dict)

    logger.info("InforCom ETL Flow finished")


@task(name="Extract All Objects from InforCom")
def extract(odbc_connstr: str, odbc_dsn: str, user: str, password: str, cfg: dict):
    logger = get_run_logger()
    logger.info("Extracting all InforCom objects")

    extractor = InforComExtract(cfg=cfg)
    extractor.extract(
        odbc_connstr=odbc_connstr,
        odbc_dsn=odbc_dsn,
        user=user,
        password=password,
    )


@task(name="Transform Objects")
def transform(cfg: dict):
    logger = get_run_logger()
    logger.info("Transforming InforCom objects")

    transformer = InforComTransform(cfg=cfg)
    transformer.join()


@task(name="Load Objects into Nemo")
def load(cfg: dict):
    logger = get_run_logger()
    logger.info("Loading InforCom objects into Nemo")

    loader = InforComLoad(cfg=cfg)
    loader.load()

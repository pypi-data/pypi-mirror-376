from prefect import get_run_logger
from nemo_library.adapter.inforcom.inforcom_object_type import InforComObjectType
from nemo_library.adapter.utils.file_handler import ETLFileHandler
from nemo_library.adapter.utils.structures import ETLAdapter, ETLBaseObjectType, ETLStep
from nemo_library.core import NemoLibrary
import pandas as pd


class InforComTransform:
    """
    Class to handle transformation of data for the InforCom adapter.
    """

    def __init__(self, cfg: dict) -> None:

        nl = NemoLibrary()
        self.config = nl.config
        self.logger = get_run_logger()
        self.cfg = cfg

        super().__init__()

    # --- helpers -------------------------------------------------------------

    def _load_table_as_df(
        self, filehandler: ETLFileHandler, table: str
    ) -> pd.DataFrame:
        """Load one extracted table as a pandas DataFrame."""
        data = filehandler.readJSON(
            adapter=ETLAdapter.INFORCOM,
            step=ETLStep.EXTRACT,
            entity=InforComObjectType.GENERIC,
            filename=f"INFORCOM_{table}",
        )
        df = pd.DataFrame(data)
        df.columns = [str(c) for c in df.columns]
        return df

    def _deduplicate(
        self, df: pd.DataFrame, subset, strategy: str = "first", sort_by=None
    ) -> pd.DataFrame:
        """Deduplicate right side before join to avoid fan-out."""
        tmp = df.copy()
        if sort_by:
            tmp = tmp.sort_values(sort_by)
        if strategy == "first":
            return tmp.drop_duplicates(subset=subset, keep="first")
        if strategy == "last":
            return tmp.drop_duplicates(subset=subset, keep="last")
        if strategy == "distinct":
            return tmp.drop_duplicates()
        raise ValueError(f"Unsupported dedup strategy: {strategy}")

    def _pandas_how(self, join_type: str) -> str:
        mapping = {
            "inner": "inner",
            "left": "left",
            "right": "right",
            "outer": "outer",
            "cross": "cross",
        }
        if join_type not in mapping:
            raise ValueError(f"Unsupported join_type: {join_type}")
        return mapping[join_type]

    def _run_single_join_plan_and_write(self, plan_name: str, plan_cfg: dict) -> None:
        """Run one join plan and write the result to TRANSFORM step."""
        base_table = plan_cfg["base_table"]
        sequence = plan_cfg.get("sequence", [])
        steps = plan_cfg.get("tables", {})
        rename = plan_cfg.get("rename", {})
        select_final = plan_cfg.get("select_final", [])

        # Load base
        self.logger.info(f"[{plan_name}] Loading base table: {base_table}")
        filehandler = ETLFileHandler()
        df = self._load_table_as_df(filehandler, base_table)

        # Execute steps
        for step_name in sequence:
            spec = steps[step_name]
            right_table = spec["right_table"]
            left_key = spec["left_key"]
            right_key = spec["right_key"]
            how = self._pandas_how(spec.get("join_type", "left"))

            self.logger.info(
                f"[{plan_name}] Step '{step_name}': {base_table} {how} -> {right_table} on {left_key}={right_key}"
            )

            right_df = self._load_table_as_df(filehandler, right_table)

            # Optional projection on right
            select_right = spec.get("select_right")
            if select_right:
                right_df = right_df[select_right]

            # Optional dedup on right
            dspec = spec.get("dedup_right")
            if dspec:
                right_df = self._deduplicate(
                    right_df,
                    subset=dspec["subset"],
                    strategy=dspec.get("strategy", "first"),
                    sort_by=dspec.get("sort_by"),
                )

            # Validate keys
            for lk in left_key:
                if lk not in df.columns:
                    raise KeyError(
                        f"[{plan_name}] Left key '{lk}' not in current frame columns"
                    )
            for rk in right_key:
                if rk not in right_df.columns:
                    raise KeyError(
                        f"[{plan_name}] Right key '{rk}' not in right table '{right_table}'"
                    )

            # Merge
            df = df.merge(
                right_df,
                how=how,
                left_on=left_key,
                right_on=right_key,
                suffixes=("", f"__{right_table}"),
            )

        # Final rename and projection
        if rename:
            df = df.rename(columns=rename)
        if select_final:
            cols = [c for c in select_final if c in df.columns]
            df = df[cols]

        # Write result to TRANSFORM
        self.logger.info(f"[{plan_name}] Writing result to TRANSFORM")
        filehandler.writeJSON(
            adapter=ETLAdapter.INFORCOM,
            step=ETLStep.TRANSFORM,
            entity=InforComObjectType.GENERIC,
            filename=f"INFORCOM_JOIN_{plan_name}",
            data=df.to_dict(orient="records"),
        )

    # --- public API ----------------------------------------------------------

    def join(self) -> None:
        """
        Run all join plans in cfg['join']['plans'].
        Reads from ETLStep.EXTRACT and writes to ETLStep.TRANSFORM.
        Returns nothing.
        """

        join_cfg = self.cfg.get("join", {})
        plans = join_cfg.get("plans")

        # Legacy fallback: single plan at top-level (base_table/sequence/tables)
        if not plans and {"base_table", "sequence", "tables"} <= set(join_cfg.keys()):
            plans = {"default": join_cfg}

        if not plans:
            self.logger.warning("No join plans found in cfg['join']. Nothing to do.")
            return

        for plan_name, plan_cfg in plans.items():
            self.logger.info(f"Running join plan: {plan_name}")
            self._run_single_join_plan_and_write(plan_name, plan_cfg)

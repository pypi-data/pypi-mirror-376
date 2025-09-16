# config_schema.py
from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional


# ----------------------------
# Extract configuration
# ----------------------------


class InforComTableConfig(BaseModel):
    big_data: bool = False
    description: Optional[str] = None
    active: bool = True


class InforComExtractConfig(BaseModel):
    """Configuration for InforCom extraction."""

    chunk_size: int = 5000
    timeout: int = 300
    tables: Dict[str, InforComTableConfig] = Field(default_factory=dict)


# ----------------------------
# JOIN configuration (with plans)
# ----------------------------

JoinType = Literal["inner", "left", "right", "outer", "cross"]


class DedupRightSpec(BaseModel):
    """
    Optional de-duplication for the RIGHT table before joining to avoid fan-out.
    - subset: columns that define uniqueness
    - strategy: 'first' | 'last' | 'distinct'
    - sort_by: columns to sort by before dropping duplicates (used with 'first'/'last')
    """

    subset: List[str]
    strategy: Literal["first", "last", "distinct"] = "first"
    sort_by: Optional[List[str]] = None


class InforComJoinTableConfig(BaseModel):
    """
    One join step in the pipeline:
    - left_table/right_table: logical table names (already extracted as files)
    - left_key/right_key: one or multiple columns to join on
    - join_type: pandas-like how ('left', 'inner', ...)
    - select_right: optional projection on the right table BEFORE joining
    - dedup_right: optional de-duplication spec for the right table
    """

    left_table: str
    right_table: str
    left_key: List[str]
    right_key: List[str]
    join_type: JoinType = "inner"
    select_right: Optional[List[str]] = None
    dedup_right: Optional[DedupRightSpec] = None


class InforComJoinPlan(BaseModel):
    """
    A single join plan:
    - base_table: the starting table for the pipeline
    - sequence: ordered list of join step names (keys into 'tables')
    - tables: mapping of step name -> InforComJoinTableConfig
    - rename: optional column rename mapping applied at the end
    - select_final: optional final projection/ordering of columns
    """

    base_table: str
    sequence: List[str] = Field(default_factory=list)
    tables: Dict[str, InforComJoinTableConfig] = Field(default_factory=dict)
    rename: Dict[str, str] = Field(default_factory=dict)
    select_final: List[str] = Field(default_factory=list)


class InforComJoinConfig(BaseModel):
    """
    Multiple join plans keyed by name.
    Example:
      {
        "plans": {
          "addresses_enriched": { ... },
          "orders_enriched": { ... }
        }
      }
    """

    plans: Dict[str, InforComJoinPlan] = Field(default_factory=dict)


class InforComETLConfig(BaseModel):
    extract: InforComExtractConfig
    join: InforComJoinConfig

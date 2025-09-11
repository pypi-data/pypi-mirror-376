import json
from dataclasses import dataclass, field
from typing import Any, Dict
from enum import Enum
from nemo_library.adapter.utils.structures import ETLBaseObjectType


# --- Dataclass for rich, extensible metadata per table -----------------------
@dataclass
class InforComMeta:
    """Extensible metadata for a single Infor COM table."""
    description: str = ""
    active: bool = True
    props: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize metadata including dynamic props."""
        return {"description": self.description, "active": self.active, **self.props}

    def __getattr__(self, key: str) -> Any:
        """
        Attribute-style access for dynamic props, e.g. meta.owner, meta.category.
        """
        if key in self.props:
            return self.props[key]
        raise AttributeError(f"{self.__class__.__name__} has no attribute '{key}'")


# --- Enum base that stays compatible with ETLBaseObjectType ------------------
class _InforComBase(ETLBaseObjectType):
    """
    Subclass of ETLBaseObjectType that adds a 'meta' attribute to each Enum member.
    Signature stays compatible with ETLBaseObjectType, we only extend with 'meta'.
    """
    def __init__(
        self,
        label: str,
        guid: str,
        sentiment_analysis_fields: list[str] | None = None,
        big_data: bool = False,
        meta: InforComMeta | None = None,
    ):
        # Keep parent initialization intact (compatibility!)
        super().__init__(label, guid, sentiment_analysis_fields, big_data)
        # Attach flexible metadata
        self.meta: InforComMeta = meta or InforComMeta()


# --- Factory to build the Enum class from config.json ------------------------
def load_inforcom_enum(config_path: str) -> type[ETLBaseObjectType]:
    """
    Build and return the Enum class 'InforComObjectType' based on a JSON config.

    JSON shape per table:
    {
      "RELAB": { "big_data": true, "description": "...", "active": true, "owner": "..." },
      ...
    }
    Any additional keys (e.g., 'owner', 'category', 'default_columns') flow into meta.props.
    """
    with open(config_path, "r", encoding="utf-8") as f:
        cfg: Dict[str, Dict[str, Any]] = json.load(f)

    # Build Enum member mapping: name -> (label, guid, sentiment_fields, big_data, meta)
    members: Dict[str, tuple] = {}

    # Order in JSON is preserved (Python 3.7+), so numbering is deterministic.
    for idx, (name, raw) in enumerate(cfg.items(), start=1):
        guid = f"{idx:04d}"

        big_data = bool(raw.get("big_data", False))
        description = str(raw.get("description", ""))
        active = bool(raw.get("active", True))

        # Everything except core keys goes into dynamic props
        dynamic_props = {k: v for k, v in raw.items() if k not in {"big_data", "description", "active"}}
        meta = InforComMeta(description=description, active=active, props=dynamic_props)

        # IMPORTANT: pass sentiment_analysis_fields=None to keep .sentiment_analysis == False
        members[name] = (name, guid, None, big_data, meta)

    # Create an Enum class named 'InforComObjectType' whose base is our _InforComBase
    InforComObjectType = Enum(
        "InforComObjectType",
        members,
        type=_InforComBase,   # ensures members are instances of our subclass (with .meta)
        module=__name__,
    )
    return InforComObjectType


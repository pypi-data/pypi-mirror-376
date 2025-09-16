# config_io.py
"""
Utilities to load, validate, merge and persist ETL configuration.

- Uses Pydantic v2 models (InforComETLConfig) for type-safe validation.
- Supports optional environment variable overrides (prefix-based).
- Supports overlay files (e.g., base + local).
- Returns primitive dicts when needed for cross-process/task boundaries.

Author: you :)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

from pydantic import ValidationError

from nemo_library.adapter.inforcom.config import InforComETLConfig


# -------------------------
# JSON helpers
# -------------------------


def _read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    return path.read_text(encoding="utf-8")


def _strip_json_comments(s: str) -> str:
    """
    Very small/naive JSONC support: strips // line and /* */ block comments.
    It does NOT handle edge cases (e.g. comments inside strings).
    Use with caution or replace with a proper JSON5 parser if needed.
    """
    import re

    # strip // comments
    s = re.sub(r"^\s*//.*?$", "", s, flags=re.MULTILINE)
    # strip /* ... */ comments
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.DOTALL)
    return s


def _load_json_file(path: Path, allow_jsonc: bool = True) -> Dict[str, Any]:
    raw = _read_text(path)
    if allow_jsonc:
        raw = _strip_json_comments(raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}") from e


# -------------------------
# Dict merge helpers
# -------------------------


def _deep_merge(base: Dict[str, Any], override: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Deeply merge override into base (immutably).
    - Dicts are merged recursively
    - Other types are replaced by override
    """
    result = dict(base)
    for k, v in override.items():
        if isinstance(v, Mapping) and isinstance(result.get(k), Mapping):
            result[k] = _deep_merge(result[k], v)  # type: ignore[arg-type]
        else:
            result[k] = v
    return result


# -------------------------
# Env override helpers
# -------------------------


def _parse_env_value(v: str) -> Any:
    """
    Attempt to parse env string as JSON; fall back to raw string.
    This lets you set lists/dicts/ints/bools via env cleanly, e.g.
      INFORCOM_EXTRACT__TABLES='["orders","items"]'
      INFORCOM_LOAD__CHUNK_SIZE=1000
    """
    try:
        return json.loads(v)
    except json.JSONDecodeError:
        # Try small convenience conversions
        lower = v.lower()
        if lower in {"true", "false"}:
            return lower == "true"
        if lower == "null" or lower == "none":
            return None
        # Try int/float
        try:
            if "." in v:
                return float(v)
            return int(v)
        except ValueError:
            return v


def _apply_env_overrides(
    data: Dict[str, Any], prefix: str = "INFORCOM_"
) -> Dict[str, Any]:
    """
    Override nested keys using env vars like:
      INFORCOM_EXTRACT__TABLES='["orders","items"]'
      INFORCOM_LOAD__IF_EXISTS="replace"
    Double underscore `__` denotes nesting.
    """
    out = dict(data)
    for key, val in os.environ.items():
        if not key.startswith(prefix):
            continue
        path = key[len(prefix) :]  # e.g. "EXTRACT__TABLES"
        parts = path.split("__")
        ref = out
        for p in parts[:-1]:
            p_norm = p.lower()
            if p_norm not in ref or not isinstance(ref[p_norm], dict):
                # allow case-insensitive insertions; normalize to lower-case
                ref[p_norm] = {}
            ref = ref[p_norm]
        last = parts[-1].lower()
        ref[last] = _parse_env_value(val)
    return out


def _lower_keys_recursive(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize all dict keys to lower-case (useful when mixing env overrides).
    """
    out: Dict[str, Any] = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out[k.lower()] = _lower_keys_recursive(v)
        else:
            out[k.lower()] = v
    return out


# -------------------------
# Public API
# -------------------------


def load_config(
    config_path: str | Path,
    *,
    overlay_path: Optional[str | Path] = None,
    env_prefix: str = "INFORCOM_",
    allow_jsonc: bool = True,
) -> InforComETLConfig:
    """
    Load configuration from one or two JSON files, apply env overrides, and validate.

    Args:
        config_path: path to the base JSON config file
        overlay_path: optional second JSON file that overrides the base (e.g., local/dev)
        env_prefix: prefix for environment overrides (default: INFORCOM_)
        allow_jsonc: allow comments in JSON (naive stripper)

    Returns:
        A validated InforComETLConfig instance.

    Raises:
        FileNotFoundError, ValueError, ValidationError
    """
    base = _load_json_file(Path(config_path), allow_jsonc=allow_jsonc)

    if overlay_path:
        overlay = _load_json_file(Path(overlay_path), allow_jsonc=allow_jsonc)
        merged = _deep_merge(base, overlay)
    else:
        merged = base

    # Normalize to lower-case keys to make env merging predictable
    merged = _lower_keys_recursive(merged)
    merged = _apply_env_overrides(merged, prefix=env_prefix)

    return InforComETLConfig.model_validate(merged)


def to_primitive(config: InforComETLConfig) -> Dict[str, Any]:
    """
    Convert a validated model to a plain, JSON-serializable dict.
    Useful for passing across task/process boundaries.
    """
    return config.model_dump()


def save_config(
    config: InforComETLConfig | Mapping[str, Any],
    path: str | Path,
    *,
    indent: int = 2,
) -> None:
    """
    Persist the config to disk as JSON (UTF-8).
    Accepts either a model or a raw mapping.
    """
    if isinstance(config, InforComETLConfig):
        data = config.model_dump()
    else:
        data = dict(config)
    Path(path).write_text(
        json.dumps(data, ensure_ascii=False, indent=indent), encoding="utf-8"
    )


"""JSON formatter for machine-readable CI/CD outputs."""

from __future__ import annotations

import json
from typing import Any
from pydantic import BaseModel
from dbanchor.output.redaction import sanitize_data_dict


def to_json(data: Any, indent: int = 2) -> str:
    """Convert arbitrary objects/models to sanitized JSON."""
    if isinstance(data, BaseModel):
        raw_dict = data.model_dump()
    elif isinstance(data, dict):
        raw_dict = data
    elif hasattr(data, "to_dict") and callable(data.to_dict):
        raw_dict = data.to_dict()
    elif hasattr(data, "__dict__"):
        raw_dict = vars(data)
    else:
        raw_dict = {"data": data}

    sanitized = sanitize_data_dict(raw_dict)
    return json.dumps(sanitized, indent=indent, default=str)

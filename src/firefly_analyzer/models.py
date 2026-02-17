"""
This module defines the core data structures used throughout the analyzer.
"""

from typing import Any, Dict, List, Optional
from enum import Enum


class State(str, Enum):
    MISSING = "Missing"
    MATCH = "Match"
    MODIFIED = "Modified"


class ChangeLogEntry:
    def __init__(self, key_name: str, cloud_value: Any, iac_value: Any):
        self.key_name = key_name
        self.cloud_value = cloud_value
        self.iac_value = iac_value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "KeyName": self.key_name,
            "CloudValue": self.cloud_value,
            "IacValue": self.iac_value,
        }


class AnalysisResult:
    def __init__(
        self,
        cloud_resource: Dict[str, Any],
        iac_resource: Optional[Dict[str, Any]],
        state: State,
        change_log: Optional[List[ChangeLogEntry]] = None,
    ):
        self.cloud_resource = cloud_resource
        self.iac_resource = iac_resource or {}
        self.state = state
        self.change_log = change_log or []

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "CloudResourceItem": self.cloud_resource,
            "IacResourceItem": self.iac_resource,
            "State": self.state.value,
            "ChangeLog": [entry.to_dict() for entry in self.change_log],
        }
        return result

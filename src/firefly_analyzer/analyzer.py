"""
This module implements the main logic for comparing cloud resources with IaC resources.
"""

import json
from typing import Any, Dict, List
from pathlib import Path

from .models import AnalysisResult, ChangeLogEntry, State
from .utils import deep_compare, find_matching_resource


class ResourceAnalyzer:

    def __init__(self, match_keys: List[str] = None):
        self.match_keys = match_keys or ["id"]

    def load_json(self, file_path: str) -> List[Dict[str, Any]]:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            raise ValueError(f"Invalid JSON format in {file_path}")

    def analyze_resource(
        self, cloud_resource: Dict[str, Any], iac_resources: List[Dict[str, Any]]
    ) -> AnalysisResult:

        iac_resource = find_matching_resource(
            cloud_resource, iac_resources, self.match_keys
        )

        if iac_resource is None:
            return AnalysisResult(
                cloud_resource=cloud_resource,
                iac_resource=None,
                state=State.MISSING,
                change_log=[],
            )

        are_equal, differences = deep_compare(cloud_resource, iac_resource)

        if are_equal:
            return AnalysisResult(
                cloud_resource=cloud_resource,
                iac_resource=iac_resource,
                state=State.MATCH,
                change_log=[],
            )

        change_log = [
            ChangeLogEntry(key_name=path, cloud_value=cloud_val, iac_value=iac_val)
            for path, cloud_val, iac_val in differences
        ]

        return AnalysisResult(
            cloud_resource=cloud_resource,
            iac_resource=iac_resource,
            state=State.MODIFIED,
            change_log=change_log,
        )

    def analyze(
        self, cloud_resources: List[Dict[str, Any]], iac_resources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        results = []

        for cloud_resource in cloud_resources:
            analysis_result = self.analyze_resource(cloud_resource, iac_resources)
            results.append(analysis_result.to_dict())

        return results

    def analyze_files(self, cloud_file: str, iac_file: str) -> List[Dict[str, Any]]:

        cloud_resources = self.load_json(cloud_file)
        iac_resources = self.load_json(iac_file)

        return self.analyze(cloud_resources, iac_resources)

    def save_results(
        self, results: List[Dict[str, Any]], output_file: str, pretty: bool = False
    ) -> None:

        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            if pretty:
                json.dump(results, f, indent=2, ensure_ascii=False)
            else:
                json.dump(results, f, ensure_ascii=False)

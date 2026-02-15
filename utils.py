"""
This module provides helper functions for deep comparison and change detection.
"""

from typing import Any, Dict, List, Tuple


def deep_compare(
    obj1: Any, obj2: Any, path: str = ""
) -> Tuple[bool, List[Tuple[str, Any, Any]]]:
    differences = []

    if obj1 is None and obj2 is None:
        return True, []
    if obj1 is None or obj2 is None:
        differences.append((path or "root", obj1, obj2))
        return False, differences

    if type(obj1) != type(obj2):
        differences.append((path or "root", obj1, obj2))
        return False, differences

    if isinstance(obj1, dict):
        all_keys = set(obj1.keys()) | set(obj2.keys())

        for key in all_keys:
            current_path = f"{path}.{key}" if path else key

            if key not in obj1:
                differences.append((current_path, None, obj2[key]))
            elif key not in obj2:
                differences.append((current_path, obj1[key], None))
            else:
                is_equal, nested_diffs = deep_compare(
                    obj1[key], obj2[key], current_path
                )
                differences.extend(nested_diffs)

        return len(differences) == 0, differences

    if isinstance(obj1, list):
        if len(obj1) != len(obj2):
            differences.append((path or "root", obj1, obj2))
            return False, differences

        for i, (item1, item2) in enumerate(zip(obj1, obj2)):
            current_path = f"{path}[{i}]" if path else f"[{i}]"
            is_equal, nested_diffs = deep_compare(item1, item2, current_path)
            differences.extend(nested_diffs)

        return len(differences) == 0, differences

    if obj1 != obj2:
        differences.append((path or "root", obj1, obj2))
        return False, differences

    return True, []


def find_matching_resource(
    cloud_resource: Dict[str, Any],
    iac_resources: List[Dict[str, Any]],
    match_keys: List[str] = None,
) -> Dict[str, Any] | None:
    if match_keys is None:
        match_keys = ["id"]

    for iac_resource in iac_resources:
        matches = True
        for key in match_keys:
            cloud_value = cloud_resource.get(key)
            iac_value = iac_resource.get(key)

            if cloud_value is None or iac_value is None or cloud_value != iac_value:
                matches = False
                break

        if matches:
            return iac_resource

    return None


def format_value(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, (dict, list)):
        return str(value)
    return repr(value)

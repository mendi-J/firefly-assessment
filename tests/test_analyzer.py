"""
Unit tests for the Firefly Asset Management solution.
"""

import json
import pytest
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from firefly_analyzer import (
    ResourceAnalyzer,
    State,
    deep_compare,
    find_matching_resource,
)


class TestDeepCompare:
    """Tests for the deep_compare utility function."""

    def test_equal_primitives(self):
        """Test comparison of equal primitive values."""
        are_equal, diffs = deep_compare("test", "test")
        assert are_equal is True
        assert len(diffs) == 0

    def test_different_primitives(self):
        """Test comparison of different primitive values."""
        are_equal, diffs = deep_compare("test1", "test2")
        assert are_equal is False
        assert len(diffs) == 1

    def test_equal_dicts(self):
        """Test comparison of equal dictionaries."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"a": 1, "b": 2}
        are_equal, diffs = deep_compare(dict1, dict2)
        assert are_equal is True
        assert len(diffs) == 0

    def test_different_dicts(self):
        """Test comparison of different dictionaries."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"a": 1, "b": 3}
        are_equal, diffs = deep_compare(dict1, dict2)
        assert are_equal is False
        assert len(diffs) == 1
        assert diffs[0][0] == "b"

    def test_nested_dicts(self):
        """Test comparison of nested dictionaries."""
        dict1 = {"a": {"b": {"c": 1}}}
        dict2 = {"a": {"b": {"c": 2}}}
        are_equal, diffs = deep_compare(dict1, dict2)
        assert are_equal is False
        assert len(diffs) == 1
        assert diffs[0][0] == "a.b.c"

    def test_lists(self):
        """Test comparison of lists."""
        list1 = [1, 2, 3]
        list2 = [1, 2, 4]
        are_equal, diffs = deep_compare(list1, list2)
        assert are_equal is False
        assert len(diffs) == 1


class TestFindMatchingResource:
    """Tests for the find_matching_resource utility function."""

    def test_find_by_id(self):
        """Test finding resource by ID."""
        cloud = {"id": "test-123", "name": "test"}
        iac_list = [
            {"id": "test-456", "name": "other"},
            {"id": "test-123", "name": "test"},
        ]
        result = find_matching_resource(cloud, iac_list)
        assert result is not None
        assert result["id"] == "test-123"

    def test_not_found(self):
        """Test when resource is not found."""
        cloud = {"id": "test-999", "name": "test"}
        iac_list = [
            {"id": "test-456", "name": "other"},
            {"id": "test-123", "name": "test"},
        ]
        result = find_matching_resource(cloud, iac_list)
        assert result is None

    def test_custom_match_keys(self):
        """Test finding resource with custom match keys."""
        cloud = {"name": "test", "region": "us-east-1"}
        iac_list = [
            {"name": "test", "region": "us-west-2"},
            {"name": "test", "region": "us-east-1"},
        ]
        result = find_matching_resource(cloud, iac_list, match_keys=["name", "region"])
        assert result is not None
        assert result["region"] == "us-east-1"


class TestResourceAnalyzer:
    """Tests for the ResourceAnalyzer class."""

    def test_analyze_missing_resource(self):
        """Test analysis when IaC resource is missing."""
        analyzer = ResourceAnalyzer()
        cloud = {"id": "test-1", "type": "instance"}
        iac_list = [{"id": "test-2", "type": "instance"}]

        result = analyzer.analyze_resource(cloud, iac_list)
        assert result.state == State.MISSING
        assert result.iac_resource == {}
        assert len(result.change_log) == 0

    def test_analyze_matching_resource(self):
        """Test analysis when resources match."""
        analyzer = ResourceAnalyzer()
        cloud = {"id": "test-1", "type": "instance", "size": 100}
        iac_list = [{"id": "test-1", "type": "instance", "size": 100}]

        result = analyzer.analyze_resource(cloud, iac_list)
        assert result.state == State.MATCH
        assert result.iac_resource["id"] == "test-1"
        assert len(result.change_log) == 0

    def test_analyze_modified_resource(self):
        """Test analysis when resources are modified."""
        analyzer = ResourceAnalyzer()
        cloud = {"id": "test-1", "type": "instance", "size": 100}
        iac_list = [{"id": "test-1", "type": "instance", "size": 200}]

        result = analyzer.analyze_resource(cloud, iac_list)
        assert result.state == State.MODIFIED
        assert len(result.change_log) == 1
        assert result.change_log[0].key_name == "size"
        assert result.change_log[0].cloud_value == 100
        assert result.change_log[0].iac_value == 200

    def test_analyze_nested_modification(self):
        """Test analysis of nested property modifications."""
        analyzer = ResourceAnalyzer()
        cloud = {"id": "test-1", "tags": {"totalAmount": "17kb"}}
        iac_list = [{"id": "test-1", "tags": {"totalAmount": "22kb"}}]

        result = analyzer.analyze_resource(cloud, iac_list)
        assert result.state == State.MODIFIED
        assert len(result.change_log) == 1
        assert result.change_log[0].key_name == "tags.totalAmount"
        assert result.change_log[0].cloud_value == "17kb"
        assert result.change_log[0].iac_value == "22kb"

    def test_analyze_multiple_resources(self):
        """Test analysis of multiple resources."""
        analyzer = ResourceAnalyzer()
        cloud_list = [
            {"id": "test-1", "size": 100},
            {"id": "test-2", "size": 200},
            {"id": "test-3", "size": 300},
        ]
        iac_list = [{"id": "test-1", "size": 100}, {"id": "test-2", "size": 250}]

        results = analyzer.analyze(cloud_list, iac_list)
        assert len(results) == 3
        assert results[0]["State"] == "Match"
        assert results[1]["State"] == "Modified"
        assert results[2]["State"] == "Missing"


class TestIntegration:
    """Integration tests using example files."""

    @pytest.fixture
    def analyzer(self):
        """Create an analyzer instance."""
        return ResourceAnalyzer()

    @pytest.fixture
    def example_dir(self):
        """Get the examples directory path."""
        return Path(__file__).parent.parent / "examples"

    def test_analyze_example_files(self, analyzer, example_dir):
        """Test analysis using the example files."""
        cloud_file = example_dir / "cloud_resources.json"
        iac_file = example_dir / "iac_resources.json"

        if not cloud_file.exists() or not iac_file.exists():
            pytest.skip("Example files not found")

        results = analyzer.analyze_files(str(cloud_file), str(iac_file))

        # Should have 4 cloud resources
        assert len(results) == 4

        # Check states
        states = [r["State"] for r in results]
        assert "Match" in states
        assert "Modified" in states
        assert "Missing" in states

        # Find the modified resource
        modified = [r for r in results if r["State"] == "Modified"]
        assert len(modified) >= 1

        # Check that modified resources have change logs
        for mod in modified:
            assert len(mod["ChangeLog"]) > 0

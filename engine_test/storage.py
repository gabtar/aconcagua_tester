"""Storage - handles persisting and loading test results."""

import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any

from .config import METADATA_DIR, METADATA_FILE
from .runner import TestResult


def ensure_directories():
    """Create necessary directories if they don't exist."""
    os.makedirs(METADATA_DIR, exist_ok=True)


def load_tests() -> List[Dict[str, Any]]:
    """Load all test results from storage."""
    ensure_directories()

    if not os.path.exists(METADATA_FILE):
        return []

    with open(METADATA_FILE, "r") as f:
        data = json.load(f)
        return data.get("tests", [])


def save_test(test: TestResult) -> None:
    """Save a test result to storage."""
    ensure_directories()

    tests = load_tests()
    tests.append(test.to_dict())

    with open(METADATA_FILE, "w") as f:
        json.dump({"tests": tests}, f, indent=2)


def get_tests_for_branch(branch: str) -> List[Dict[str, Any]]:
    """Get all tests for a specific branch."""
    all_tests = load_tests()
    return [t for t in all_tests if t.get("branch") == branch]


def get_test_by_id(test_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific test by its ID (partial match supported)."""
    all_tests = load_tests()
    for test in all_tests:
        if test.get("id", "").startswith(test_id):
            return test
    return None


def get_pending_tests() -> List[Dict[str, Any]]:
    """Get all pending tests that can be resumed."""
    all_tests = load_tests()
    return [t for t in all_tests if t.get("result") == "pending" and t.get("config_path")]


def get_latest_test() -> Optional[Dict[str, Any]]:
    """Get the most recent test result."""
    tests = load_tests()
    if not tests:
        return None
    return tests[-1]


def clear_results(branch: Optional[str] = None):
    """Clear test results. If branch is None, clear all results."""
    if branch:
        tests = [t for t in load_tests() if t.get("branch") != branch]
        with open(METADATA_FILE, "w") as f:
            json.dump({"tests": tests}, f, indent=2)
    else:
        if os.path.exists(METADATA_FILE):
            os.remove(METADATA_FILE)

    from .config import PGNS_DIR
    if os.path.exists(PGNS_DIR):
        import shutil
        shutil.rmtree(PGNS_DIR)
        os.makedirs(PGNS_DIR)
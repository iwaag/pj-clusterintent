#!/usr/bin/env python3
"""Emit the tracked test-suite measurements used by Test Strategy Phases 0 and 4.

Run from any directory. The default measures each component's ordinary collection; --runtime also
runs the maintained exact-local-source Nautobot gate and records its collected case count.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
COMPONENTS = {
    "nctl": ("nctl", "pytest"),
    "nintent": ("nintent", "unittest"),
    "nauto": ("nauto", "unittest"),
    "nodeutils": ("nodeutils", "pytest"),
    "ansible_agdev": ("ansible_agdev", "unittest"),
}


def run(*args: str, cwd: Path = ROOT) -> str:
    completed = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if completed.returncode:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(args)}\n{completed.stdout}\n{completed.stderr}")
    return completed.stdout + completed.stderr


def tracked_python_files(component: Path) -> list[Path]:
    names = run("git", "ls-files", "*.py", cwd=component).splitlines()
    return [component / name for name in names]


def is_test_file(path: Path) -> bool:
    return path.name.startswith("test")


def static_test_definitions(paths: list[Path]) -> int:
    total = 0
    for path in paths:
        if not is_test_file(path):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        total += sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test") for node in ast.walk(tree))
    return total


def line_count(paths: list[Path]) -> int:
    return sum(len(path.read_text(encoding="utf-8").splitlines()) for path in paths)


def collect(component: str, path: Path, runner: str) -> int:
    if runner == "pytest":
        output = run("uv", "run", "pytest", "--collect-only", "-q", cwd=path)
        match = re.search(r"(\d+) tests? collected", output)
        if not match:
            raise RuntimeError(f"could not parse pytest collection for {component}:\n{output}")
        return int(match.group(1))
    test_dir = "roles/nodeutils_pvesh_helper/tests" if component == "ansible_agdev" else "tests"
    if component == "nintent":
        test_dir = "nautobot_intent_catalog/tests"
    code = (
        "import unittest; "
        f"suite=unittest.defaultTestLoader.discover({test_dir!r}); "
        "print(suite.countTestCases())"
    )
    return int(run("python3", "-c", code, cwd=path).strip())


def component_measurement(name: str, relative: str, runner: str) -> dict[str, object]:
    path = ROOT / relative
    paths = tracked_python_files(path)
    test_paths = [item for item in paths if is_test_file(item)]
    test_lines = line_count(test_paths)
    non_test_lines = line_count(paths) - test_lines
    return {
        "component": name,
        "tracked_python_files": len(paths),
        "test_files": len(test_paths),
        "static_test_definitions": static_test_definitions(paths),
        "collected_cases": collect(name, path, runner),
        "test_lines": test_lines,
        "non_test_python_lines": non_test_lines,
        "source_to_test_ratio": round(test_lines / non_test_lines, 3) if non_test_lines else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", action="store_true", help="also run and measure the Nautobot runtime gate")
    args = parser.parse_args()
    measurements = [component_measurement(name, *spec) for name, spec in COMPONENTS.items()]
    result: dict[str, object] = {"components": measurements}
    if args.runtime:
        output = run(str(ROOT / "devtests/test_strategy/run_nautobot_runtime_gate.sh"), "--keepdb")
        match = re.search(r"Found (\d+) test\(s\)", output)
        if not match:
            raise RuntimeError(f"could not parse Nautobot runtime collection:\n{output}")
        result["nautobot_runtime_collected_cases"] = int(match.group(1))
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

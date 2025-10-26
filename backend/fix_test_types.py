#!/usr/bin/env python3
"""Script to add return type annotations to test functions."""

import re
from pathlib import Path


def fix_test_file(file_path: Path) -> None:
    """Add -> None to test functions missing return type annotations."""
    content = file_path.read_text()
    original_content = content

    # Pattern to match test functions without return type
    # Matches: def test_something(...) or async def test_something(...)
    # But not: def test_something(...) -> None
    patterns = [
        # async def without return type
        (r"(async def (?:test_|setup_|teardown_)\w+\([^)]*\)):", r"\1 -> None:"),
        # Regular def without return type
        (r"(def (?:test_|setup_|teardown_)\w+\([^)]*\)):", r"\1 -> None:"),
    ]

    for pattern, replacement in patterns:
        # Only replace if not already has -> in the signature
        lines = content.split("\n")
        new_lines = []
        for line in lines:
            # Check if this line matches and doesn't already have ->
            if re.search(pattern, line) and " -> " not in line:
                line = re.sub(pattern, replacement, line)
            new_lines.append(line)
        content = "\n".join(new_lines)

    # Fix specific patterns for fixture functions
    content = re.sub(
        r"(def \w+\([^)]*\)):\s*# type: ignore", r"\1 -> Any:  # type: ignore", content
    )

    # Add Any import if we added it and it's not there
    if (
        "-> Any:" in content
        and "from typing import" in content
        and "Any" not in content.split("from typing import")[1].split("\n")[0]
    ):
        content = content.replace("from typing import ", "from typing import Any, ", 1)
    elif "-> Any:" in content and "from typing import" not in content:
        # Add import at the top after other imports
        lines = content.split("\n")
        import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                import_idx = i
        lines.insert(import_idx + 1, "from typing import Any")
        content = "\n".join(lines)

    if content != original_content:
        file_path.write_text(content)
        print(f"Fixed {file_path}")


def main() -> None:
    """Fix all test files."""
    test_dir = Path("app/tests")
    test_files = list(test_dir.rglob("*.py"))

    for test_file in test_files:
        if test_file.name != "__init__.py":
            fix_test_file(test_file)

    print(f"\nProcessed {len(test_files)} files")


if __name__ == "__main__":
    main()

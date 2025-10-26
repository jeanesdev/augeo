#!/usr/bin/env python3
"""Fix all mypy strict mode issues in test files."""

import re
from pathlib import Path


def fix_test_function_return_types(content: str) -> str:
    """Add -> None to test functions missing return type annotations."""
    # Pattern for async test methods (class methods)
    pattern1 = r"(    )(async def (test_\w+|setup\w*|teardown\w*)\([^)]*\))(\s*:)"
    content = re.sub(pattern1, r"\1\2 -> None\4", content)

    # Pattern for sync test methods (class methods)
    pattern2 = r"(    )(def (test_\w+|setup\w*|teardown\w*)\([^)]*\))(\s*:)"
    content = re.sub(pattern2, r"\1\2 -> None\4", content)

    # Pattern for async test functions (module level)
    pattern3 = r"^(async def (test_\w+|setup\w*|teardown\w*)\([^)]*\))(\s*:)"
    content = re.sub(pattern3, r"\1 -> None\3", content, flags=re.MULTILINE)

    # Pattern for sync test functions (module level)
    pattern4 = r"^(def (test_\w+|setup\w*|teardown\w*)\([^)]*\))(\s*:)"
    content = re.sub(pattern4, r"\1 -> None\3", content, flags=re.MULTILINE)

    return content


def fix_file(file_path: Path) -> None:
    """Fix a single Python file."""
    content = file_path.read_text()
    original_content = content

    content = fix_test_function_return_types(content)

    if content != original_content:
        file_path.write_text(content)
        print(f"Fixed: {file_path}")


def main() -> None:
    """Process all test files."""
    tests_dir = Path("app/tests")

    for file_path in tests_dir.rglob("*.py"):
        if file_path.name != "__init__.py":
            fix_file(file_path)

    print("Done!")


if __name__ == "__main__":
    main()

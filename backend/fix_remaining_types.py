#!/usr/bin/env python3
"""Fix remaining type annotation issues in test files."""

import re
from pathlib import Path


def fix_file(file_path: Path) -> None:
    """Fix type annotations in a file."""
    content = file_path.read_text()
    original = content
    lines = content.split("\n")
    new_lines = []

    for i, line in enumerate(lines):
        # Skip if already has return type
        if " -> " in line:
            new_lines.append(line)
            continue

        # Match async def or def at start of line (considering indentation)
        if re.match(r"^\s*(async )?def ", line) and not line.strip().endswith("\\"):
            # Check if it's a test or fixture function
            if (
                "test_" in line
                or "setup" in line
                or "teardown" in line
                or "@pytest.fixture" in "\n".join(lines[max(0, i - 5) : i])
            ):
                # Find the closing paren
                if ")" in line and ":" in line:
                    # Single line function def
                    line = line.replace("):", ") -> None:")
                elif ")" not in line:
                    # Multi-line, need to find closing paren
                    j = i
                    while j < len(lines) and ")" not in lines[j]:
                        j += 1
                    if j < len(lines) and ")" in lines[j]:
                        lines[j] = lines[j].replace("):", ") -> None:")

        new_lines.append(line)

    content = "\n".join(new_lines)

    # Fix specific patterns
    content = re.sub(
        r"def (\w+)\(([^)]*)\):  # type: ignore$",
        r"def \1(\2) -> Any:  # type: ignore",
        content,
        flags=re.MULTILINE,
    )

    # Add Any import if needed and not present
    if "-> Any" in content and "from typing import" in content:
        if "Any" not in content.split("from typing import")[1].split("\n")[0]:
            content = content.replace("from typing import ", "from typing import Any, ", 1)

    if content != original:
        file_path.write_text(content)
        print(f"Fixed {file_path}")


def main() -> None:
    """Fix specific test files with remaining issues."""
    files = [
        Path("app/tests/integration/test_session_expiration.py"),
        Path("app/tests/integration/test_auth_flow.py"),
        Path("app/tests/integration/test_email_verification.py"),
        Path("app/tests/integration/test_role_assignment.py"),
        Path("app/tests/integration/test_audit_logging.py"),
        Path("app/tests/contract/test_users_role.py"),
        Path("app/tests/contract/test_email_verification.py"),
        Path("app/tests/unit/test_jwt_blacklist.py"),
    ]

    for file_path in files:
        if file_path.exists():
            fix_file(file_path)


if __name__ == "__main__":
    main()

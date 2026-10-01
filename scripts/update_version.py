"""This script updates the version in pyproject.toml."""

import re
import sys
from pathlib import Path

version = sys.argv[1]

pyproject = Path("pyproject.toml")
content = pyproject.read_text(encoding="utf-8")

content = re.sub(
    r'^version = ".*"$',
    f'version = "{version}"',
    content,
    flags=re.MULTILINE,
)

pyproject.write_text(content, encoding="utf-8")

"""Register local src in this project's venv without pip or network access."""

import sys
import sysconfig
from pathlib import Path


root = Path(__file__).resolve().parents[1]
expected = (root / ".venv").resolve()
if Path(sys.prefix).resolve() != expected or sys.prefix == sys.base_prefix:
    raise SystemExit("Run with this project's .venv/Scripts/python.exe")
target = Path(sysconfig.get_path("purelib")) / "affiliate_hub_local.pth"
target.write_text(str(root / "src") + "\n", encoding="utf-8")
print("Local src registered; no packages downloaded.")

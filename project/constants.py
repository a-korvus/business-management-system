"""The project constants file."""

from os import getenv
from pathlib import Path

DEV_MODE: bool = getenv("DEV_MODE", "0") == "1"
ROOT_DIR: Path = Path(__file__).resolve().parent.parent
LOG_DIR: Path = ROOT_DIR / "log"

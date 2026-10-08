"""Paths independent of the caller's working directory."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    home: Path

    @classmethod
    def load(cls, override: str | None = None) -> "Settings":
        value = override or os.environ.get("AFFILIATE_HUB_HOME")
        home = Path(value).expanduser() if value else Path(__file__).resolve().parents[2]
        if not home.is_absolute():
            raise ValueError("Runtime home must be an absolute path")
        return cls(home.resolve())

    @property
    def database(self) -> Path:
        return self.home / "data" / "affiliate_hub.sqlite3"

    @property
    def log(self) -> Path:
        return self.home / "logs" / "events.jsonl"

    def prepare(self) -> None:
        for name in ("data", "logs", "exports"):
            (self.home / name).mkdir(parents=True, exist_ok=True)

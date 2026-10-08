"""OS-released lock and structured, allow-listed job logging."""

import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from affiliate_hub.db import now


class BusyError(Exception):
    pass


@contextmanager
def exclusive_lock(path: Path) -> Iterator[None]:
    with path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise BusyError("Another command is running") from None
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def log_event(path: Path, **fields: object) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"time": now(), **fields}, ensure_ascii=False) + "\n")

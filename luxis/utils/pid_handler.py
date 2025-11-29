import os
from pathlib import Path

PID_PATH = Path("/tmp/luxis.pid")


async def write_pid():
    PID_PATH.write_text(str(os.getpid()))


async def read_pid() -> int | None:
    if PID_PATH.exists():
        return int(PID_PATH.read_text().strip())
    return None


async def remove_pid():
    if PID_PATH.exists():
        PID_PATH.unlink(missing_ok=True)

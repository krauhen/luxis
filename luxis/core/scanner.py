import fnmatch
import itertools

from pathlib import Path


async def scan_directories(base: Path, include: list[str], ignore: list[str]) -> list[Path]:
    matched = itertools.chain.from_iterable(base.rglob(pattern) for pattern in include)
    result = {Path(f) for f in matched if f.is_file()}
    for pattern in ignore:
        for path in list(result):
            if fnmatch.fnmatch(str(path), pattern):
                result.discard(path)
    return sorted(result)

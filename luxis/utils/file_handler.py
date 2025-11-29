import shutil

from pathlib import Path


async def ensure_dir_exists(path: Path, clean_index: bool = False) -> None:
    if path.exists() and clean_index:
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)

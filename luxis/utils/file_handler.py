from pathlib import Path


def ensure_dir_exists(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

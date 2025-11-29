from pathlib import Path
from typing import List

from pydantic import BaseModel


class Directories(BaseModel):
    path: Path = Path("./luxis")
    include: List[str] = ["**"]
    ignore: List[str] = [".venv/**", ".git/**", ".idea/**", "**/__pycache__/**", "**/.cache/**", "**/cache/**", "**/*cache*/**"]


class Config(BaseModel):
    embedding_dim: int = 1536
    top_k: int = 10
    directories: List[Directories] = [Directories()]

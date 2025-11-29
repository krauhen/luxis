import faiss

import numpy as np

from pathlib import Path


class VectorIndex:
    def __init__(self, path: str, dim: int):
        self.path = Path(path)
        self.dim = dim
        self.index = faiss.IndexIDMap(faiss.IndexFlatL2(dim))

        if self.path.exists():
            self.load()

    def upsert(self, id_: int, embedding: list[float]) -> None:
        vec = np.array([embedding], dtype=np.float32)
        ids = np.array([id_], dtype=np.int64)
        self.index.remove_ids(ids)
        self.index.add_with_ids(vec, ids)

    def query(self, embedding: list[float], k: int = 5):
        vec = np.array([embedding], dtype=np.float32)
        distances, ids = self.index.search(vec, k)
        return [int(i) for i in ids[0] if i != -1]

    def save(self) -> None:
        faiss.write_index(self.index, str(self.path))

    def load(self) -> None:
        self.index = faiss.read_index(str(self.path))

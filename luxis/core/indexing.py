import numpy as np

from pathlib import Path

from luxis.index.vector_index import VectorIndex
from luxis.index.meta_index import MetaIndex
from luxis.utils.settings import settings
from luxis.utils.logger import logger
from luxis.utils.file_handler import ensure_dir_exists


class IndexManager:
    def __init__(self, vector_index_path: str | None = None, meta_index_path: str | None = None, dim: int = 1536):
        vector_index_path = vector_index_path or settings.vector_index_path
        meta_index_path = meta_index_path or settings.meta_index_path
        ensure_dir_exists(Path(vector_index_path).parent)
        ensure_dir_exists(Path(meta_index_path).parent)
        self.vector = VectorIndex(vector_index_path, dim=dim)
        self.meta = MetaIndex(meta_index_path)
        logger.info(f"Vector index initialized at {vector_index_path} (dim={dim})")
        logger.info(f"Meta index initialized at {meta_index_path}")

    def update(self, entries: list[tuple[list[float], str, str]]) -> None:
        if not entries:
            logger.debug("No entries to update.")
            return
        for embedding, filepath, filehash in entries:
            id_ = self.meta.upsert(filepath=filepath, filehash=filehash)
            self.vector.upsert(id_, embedding)
            logger.debug(f"Updated entry ID={id_} → {filepath}")
        self.vector.save()
        logger.info(f"Index updated and saved ({len(entries)} entries).")

    def prune_missing(self, selected_files) -> None:
        session = self.meta.Session()
        all_entries = session.query(self.meta.FileEntry).all()
        removed_count = 0
        for entry in all_entries:
            if entry.filepath not in selected_files:
                logger.info(f"Removing missing file: {entry.filepath}")
                session.delete(entry)
                self.vector.index.remove_ids(np.array([entry.id], dtype=np.int64))
                removed_count += 1
        session.commit()
        session.close()
        if removed_count:
            self.vector.save()
            logger.info(f"Pruned {removed_count} missing file entries from index.")
        else:
            logger.info("No missing files to prune.")

import numpy as np

from pathlib import Path

from luxis.index.vector_index import VectorIndex
from luxis.index.meta_index import MetaIndex
from luxis.utils.logger import logger
from luxis.utils.file_handler import ensure_dir_exists


class IndexManager:
    def __init__(self, config):
        self.config = config
        self.vector_index_path = config.settings.vector_index_path
        self.meta_index_path = config.settings.meta_index_path

    async def setup(self, clean_index: bool = False):
        await ensure_dir_exists(Path(self.vector_index_path).parent, clean_index)
        await ensure_dir_exists(Path(self.meta_index_path).parent, clean_index)
        dim = self.config.ingest.embedding_dim
        self.vector = VectorIndex(self.vector_index_path, dim=dim)
        await self.vector.setup()
        self.meta = MetaIndex(self.meta_index_path)
        logger.info(f"Vector index initialized at {self.vector_index_path} (dim={dim})")
        logger.info(f"Meta index initialized at {self.meta_index_path}")

    async def update(self, entries: list[tuple[list[float], str, str]]) -> None:
        if not entries:
            logger.debug("No entries to update.")
            return
        for embedding, filepath, filehash in entries:
            id_ = await self.meta.upsert(filepath=filepath, filehash=filehash)
            await self.vector.upsert(id_, embedding)
            logger.debug(f"Updated entry ID={id_} → {filepath}")
        await self.vector.save()
        logger.info(f"Index updated and saved ({len(entries)} entries).")

    async def prune_missing(self, selected_files):
        session = self.meta.Session()
        all_entries = session.query(self.meta.FileEntry).all()
        removed_files = []
        for entry in all_entries:
            if entry.filepath not in selected_files:
                logger.info(f"Removing missing file: {entry.filepath}")
                session.delete(entry)
                self.vector.index.remove_ids(np.array([entry.id], dtype=np.int64))
                removed_files.append(entry.filepath)
        session.commit()
        session.close()
        if len(removed_files) > 0:
            await self.vector.save()
            logger.info(f"Pruned {len(removed_files)} missing file entries from index.")
        else:
            logger.info("No missing files to prune.")
        return removed_files

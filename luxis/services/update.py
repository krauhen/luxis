import asyncio
import time

from luxis.core.schemas import Config
from luxis.utils.logger import logger
from luxis.utils.settings import settings
from luxis.core.hashing import sha256sum
from luxis.core.embedding import extract_text, embed_texts
from luxis.core.scanner import scan_directories
from luxis.core.indexing import IndexManager


def run_index_update(config: Config) -> None:
    start = time.time()
    logger.info("Updating index...")
    idx = IndexManager(
        vector_index_path=settings.vector_index_path,
        meta_index_path=settings.meta_index_path,
        dim=config.embedding_dim,
    )

    entries = []
    all_files = []
    for directory_cfg in config.directories:
        base = directory_cfg.path
        include = directory_cfg.include
        ignore = directory_cfg.ignore
        files = scan_directories(base, include, ignore)
        logger.info(f"Scanning {base}, found {len(files)} files")
        all_files.append(files)
        for file_path in files:
            try:
                filehash = sha256sum(file_path)
                existing = idx.meta.get_by_filepath(str(file_path))
                if existing and existing.filehash == filehash:
                    logger.debug(f"Skipping unchanged file: {file_path}")
                    continue
                text = extract_text(file_path)
                if not text.strip():
                    continue
                loop = asyncio.get_event_loop()
                status, embeddings = loop.run_until_complete(embed_texts([text]))
                if not status:
                    logger.warning(f"Skipping {file_path}")
                    continue
                emb = embeddings[0]
                entries.append((emb, str(file_path), filehash))
                logger.info(f"Added {file_path} to index.")
            except Exception as e:
                logger.warning(f"Skipping {file_path}: {e}")

    if entries:
        idx.update(entries)
        logger.success(f"Index updated with {len(entries)} files.")
    else:
        logger.info("No valid files to index.")

    combined_files = [str(p) for sublist in all_files for p in sublist]
    idx.prune_missing(combined_files)

    logger.info(f"Index update complete.(Elapsed time: {time.time() - start}s)")

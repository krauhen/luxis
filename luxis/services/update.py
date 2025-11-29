import asyncio
import time

from luxis.utils.logger import logger
from luxis.core.hashing import sha256sum
from luxis.core.embedding import extract_text, embed_texts
from luxis.core.scanner import scan_directories
from luxis.core.indexing import IndexManager


def _collect_candidates(config, idx):
    candidates, all_files = [], []
    for directory_cfg in config.directories:
        base, include, ignore = directory_cfg.path, directory_cfg.include, directory_cfg.ignore
        files = scan_directories(base, include, ignore)
        logger.info(f"Scanning {base}, found {len(files)} files")
        all_files.append(files)
        for file_path in files:
            try:
                filehash = sha256sum(file_path)
                existing = idx.meta.get_by_filepath(str(file_path))
                if existing and existing.filehash == filehash:
                    logger.debug(f"Skipping unchanged: {file_path}")
                    continue
                text = extract_text(file_path)
                if text.strip():
                    candidates.append((text, str(file_path), filehash))
            except Exception as e:
                logger.warning(f"Skipping {file_path}: {e}")
    return candidates, all_files


def _process_embeddings(candidates, config):
    loop = asyncio.get_event_loop()
    texts = [text for text, _, _ in candidates]
    status, embeddings = loop.run_until_complete(embed_texts(texts, config))
    if status:
        logger.info("Batch embedding succeeded.")
        return [(emb, fp, fh) for (t, fp, fh), emb in zip(candidates, embeddings)]
    logger.info("Falling back to single embeddings.")
    entries = []
    for text, fp, fh in candidates:
        st, emb = loop.run_until_complete(embed_texts([text], config))
        if st:
            entries.append((emb[0], fp, fh))
    return entries


def run_index_update(config) -> None:
    start = time.time()
    idx = IndexManager(config)
    logger.info("Updating index...")
    candidates, all_files = _collect_candidates(config, idx)
    if not candidates:
        logger.info("No valid files to index.")
    else:
        entries = _process_embeddings(candidates, config)
        if entries:
            idx.update(entries)
            logger.success(f"Index updated with {len(entries)} files.")
    combined_files = [str(p) for sublist in all_files for p in sublist]
    idx.prune_missing(combined_files)
    logger.info(f"Index update complete. (Elapsed {time.time() - start:.2f}s)")

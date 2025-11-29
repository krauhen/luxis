import time

from luxis.utils.logger import logger
from luxis.core.hashing import sha256sum
from luxis.core.embedding import extract_text, embed_texts
from luxis.core.scanner import scan_directories
from luxis.core.indexing import IndexManager


async def _collect_candidates(config, idx):
    candidates, all_files = [], []
    for directory_cfg in config.directories:
        base, include, ignore = directory_cfg.path, directory_cfg.include, directory_cfg.ignore
        files = await scan_directories(base, include, ignore)
        logger.info(f"Scanning {base}, found {len(files)} files")
        all_files.append(files)
        for file_path in files:
            try:
                filehash = await sha256sum(file_path)
                existing = await idx.meta.get_by_filepath(str(file_path))
                if existing and existing.filehash == filehash:
                    logger.debug(f"Skipping unchanged: {file_path}")
                    continue
                text = await extract_text(file_path)
                if text.strip():
                    logger.info(f"Adding {file_path} with {len(text)} characters.")
                    candidates.append((text, str(file_path), filehash))
            except Exception as e:
                logger.warning(f"Skipping {file_path}: {e}")
    return candidates, all_files


async def _process_embeddings(candidates, config):
    texts = [text for text, _, _ in candidates]
    logger.info(f"Processing {len(texts)} files...")
    status, embeddings = await embed_texts(texts, config)
    if status:
        logger.info("Batch embedding succeeded.")
        return [(emb, fp, fh) for (t, fp, fh), emb in zip(candidates, embeddings)]
    logger.info("Falling back to single embeddings.")
    entries = []
    for text, fp, fh in candidates:
        logger.info(f"Processing {fp}...")
        st, emb = await embed_texts([text], config)
        if st:
            entries.append((emb[0], fp, fh))
    return entries


async def run_index_update(config, clean_index: bool):
    start = time.time()
    idx = IndexManager(config)
    await idx.setup(clean_index)
    logger.info("Updating index...")
    candidates, all_files = await _collect_candidates(config, idx)
    if not candidates:
        logger.info("No valid files to index.")
    else:
        entries = await _process_embeddings(candidates, config)
        if entries:
            await idx.update(entries)
            logger.success(f"Index updated with {len(entries)} files.")
    combined_files = [str(p) for sublist in all_files for p in sublist]
    response = {
        "removed_files": await idx.prune_missing(combined_files),
        "indexed_files": [files for files in all_files],
        "updated_files": [fp for t, fp, fh in candidates],
    }
    logger.info(f"Index update complete. (Elapsed {time.time() - start:.2f}s)")
    return response

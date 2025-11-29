from luxis.utils.logger import logger
from luxis.core.embedding import embed_texts
from luxis.core.indexing import IndexManager


async def run_query(text: str, config):
    logger.info("Running query...")
    idx = IndexManager(config)
    await idx.setup()
    if not text.strip():
        logger.warning("Query text is empty.")
        return []
    status, embeddings = await embed_texts([text], config)
    if not status:
        logger.warning("Skipping because query text is too big.")
        return []
    emb = embeddings[0]
    ids = await idx.vector.query(emb, k=config.query.top_k)
    if not ids:
        logger.info("No similar documents found.")
        return []
    logger.debug(f"Top {len(ids)} similar files:")
    entries = []
    for rank, id_ in enumerate(ids, start=1):
        entry = await idx.meta.get(id_)
        entries.append(entry.filepath)
        logger.debug(f"{rank:>2}. {entry.filepath}  (hash={entry.filehash})" if entry else f"{rank:>2}. <missing entry id={id_}>")
    logger.success("Query completed.")
    return entries

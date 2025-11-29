import asyncio

from luxis.utils.logger import logger
from luxis.core.embedding import embed_texts
from luxis.core.indexing import IndexManager


def run_query(text: str, config) -> None:
    logger.info("Running query...")
    idx = IndexManager(config)
    if not text.strip():
        logger.warning("Query text is empty.")
        return
    loop = asyncio.get_event_loop()
    status, embeddings = loop.run_until_complete(embed_texts([text], config))
    if not status:
        logger.warning("Skipping because query text is too big.")
        return
    emb = embeddings[0]
    ids = idx.vector.query(emb, k=config.query.top_k)
    if not ids:
        logger.info("No similar documents found.")
        return
    logger.info(f"Top {len(ids)} similar files:")
    for rank, id_ in enumerate(ids, start=1):
        entry = idx.meta.get(id_)
        logger.info(f"{rank:>2}. {entry.filepath}  (hash={entry.filehash})" if entry else f"{rank:>2}. <missing entry id={id_}>")
    logger.success("Query completed.")

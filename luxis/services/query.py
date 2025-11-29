import asyncio

from luxis.core.schemas import Config
from luxis.utils.logger import logger
from luxis.utils.settings import settings
from luxis.core.embedding import embed_texts
from luxis.core.indexing import IndexManager


def run_query(text: str, config: Config) -> None:
    logger.info("Running query...")
    idx = IndexManager(
        vector_index_path=settings.vector_index_path,
        meta_index_path=settings.meta_index_path,
        dim=config.embedding_dim,
    )

    if not text.strip():
        logger.warning("Query file contains no textual content.")
        return

    loop = asyncio.get_event_loop()
    status, embeddings = loop.run_until_complete(embed_texts([text]))
    if not status:
        logger.warning("Skipping because query text is to big.")
        return
    emb = embeddings[0]

    ids = idx.vector.query(emb, k=config.top_k)
    if not ids:
        logger.info("No similar documents found.")
        return

    logger.info(f"\nTop {len(ids)} similar files:")
    for rank, id_ in enumerate(ids, start=1):
        entry = idx.meta.get(id_)
        if entry:
            logger.info(f"{rank:>2}. {entry.filepath}  (hash={entry.filehash})")
        else:
            logger.info(f"{rank:>2}. <missing entry id={id_}>")

    logger.success("Query completed.")

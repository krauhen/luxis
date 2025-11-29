import traceback

from luxis.utils.logger import logger


async def log_exception(exc: Exception, context: str = "unknown") -> None:
    tb = traceback.extract_tb(exc.__traceback__)
    if not tb:
        logger.error(f"[{context}] {type(exc).__name__}: {exc}")
        return

    frame = None
    for f in reversed(tb):
        if "utils/exceptions.py" not in f.filename and "site-packages" not in f.filename:
            frame = f
            break
    frame = frame or tb[-1]

    file_path = frame.filename
    line_no = frame.lineno
    func = frame.name

    logger.error(f"[{context}] {type(exc).__name__}: {exc} at {file_path}:{line_no} in {func}()")

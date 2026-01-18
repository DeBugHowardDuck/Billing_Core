from __future__ import annotations

import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@contextmanager
def billing_transaction(name: str = "billing") -> None:
    logger.info("BEGIN %s", name)
    try:
        yield
    except Exception:
        logger.exception("ROLLBACK %s", name)
        raise
    else:
        logger.info("COMMIT %s", name)

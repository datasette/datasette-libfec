"""
RSS sync cron handler — replaces the old RssWatcher background loop.

Registered as a cron handler via cron_register_handlers hook.
Reads config from internal DB, runs sync, writes progress to internal DB.
"""

import asyncio
import logging
import time

from .internal_db import InternalDB

logger = logging.getLogger("datasette_libfec.rss")


class RssProgressWriter:
    """Duck-type compatible callback for libfec RPC client.

    The client sets attributes like exported_count, total_count, etc.
    This adapter buffers writes and flushes to the internal DB periodically.
    """

    def __init__(self, internal_db: InternalDB):
        self._db = internal_db
        self._state = {
            "phase": "syncing",
            "exported_count": 0,
            "total_count": 0,
            "current_filing_id": None,
            "error_message": None,
            "error_code": None,
            "feed_title": None,
            "feed_last_modified": None,
        }
        self._dirty = False
        self._last_flush = 0.0

    def __setattr__(self, name, value):
        if name.startswith("_"):
            super().__setattr__(name, value)
        elif name in self._state:
            self._state[name] = value
            self._dirty = True
        else:
            super().__setattr__(name, value)

    def __getattr__(self, name):
        if name in self.__dict__.get("_state", {}):
            return self._state[name]
        raise AttributeError(name)

    async def flush(self):
        if not self._dirty:
            return
        await self._db.update_rss_progress(**self._state)
        self._dirty = False
        self._last_flush = time.time()

    async def maybe_flush(self):
        if self._dirty and (time.time() - self._last_flush) > 2:
            await self.flush()


async def rss_sync_handler(datasette, config):
    """Cron handler for RSS sync. Reads config, runs sync, writes progress."""
    from .libfec_client import LibfecClient

    internal_db = InternalDB(datasette.get_internal_database())
    rss_config = await internal_db.get_rss_config()

    if not rss_config.database_name:
        logger.warning("RSS sync: no database_name configured")
        return

    db = datasette.databases.get(rss_config.database_name)
    if not db or not db.path:
        logger.warning("RSS sync: database %s not found or has no path", rss_config.database_name)
        return

    # Reset progress
    await internal_db.update_rss_progress(
        phase="syncing",
        exported_count=0,
        total_count=0,
        current_filing_id=None,
        error_message=None,
        error_code=None,
        sync_started_at=_now_iso(),
        sync_finished_at=None,
    )

    progress = RssProgressWriter(internal_db)
    client = LibfecClient()

    # Periodic flush task
    async def periodic_flush():
        while True:
            await asyncio.sleep(2)
            await progress.maybe_flush()

    flush_task = asyncio.create_task(periodic_flush())

    try:
        await client.rss_watch_with_progress(
            db.path,
            rss_config.state_filter,
            rss_config.cover_only,
            progress,
            since=rss_config.since_duration,
        )
        await progress.flush()
        await internal_db.update_rss_progress(
            phase="idle",
            sync_finished_at=_now_iso(),
        )
        logger.info("RSS sync complete: %d exported", progress._state["exported_count"])
    except Exception as e:
        await internal_db.update_rss_progress(
            phase="error",
            error_message=str(e),
            sync_finished_at=_now_iso(),
        )
        logger.error("RSS sync failed: %s", e)
        raise
    finally:
        flush_task.cancel()
        try:
            await flush_task
        except asyncio.CancelledError:
            pass


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()

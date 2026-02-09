"""
RSS Watcher - background sync based on plugin config.

If datasette-libfec plugin config has rss-sync-interval-seconds set,
syncs RSS feed at that interval. Always cover_only, no state filter.
"""

import asyncio
import time
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .libfec_rpc_client import LibfecRpcClient


class RssWatcher:
    """RSS watcher controlled by plugin config."""

    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._db_path: Optional[str] = None
        self._libfec_client = None
        self._interval_seconds: Optional[int] = None

        # Lazy initialization state (set by startup hook, started on first request)
        self._configured_interval: Optional[int] = None
        self._initialized: bool = False

        # Progress tracking for RPC callbacks
        self.phase: str = "idle"
        self.exported_count: int = 0
        self.total_count: int = 0
        self.current_filing_id: Optional[str] = None
        self.feed_title: Optional[str] = None
        self.feed_last_modified: Optional[str] = None
        self.error_message: Optional[str] = None
        self.error_code: Optional[int] = None
        self.error_data: Optional[str] = None
        self.sync_start_time: Optional[float] = None
        self.currently_syncing: bool = False
        self.rpc_client: Optional["LibfecRpcClient"] = None
        self._next_sync_time: Optional[float] = None

    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    def set_config(self, interval_seconds: int) -> None:
        """Store config from startup hook for later lazy initialization."""
        self._configured_interval = interval_seconds

    def ensure_started(self, db_path: str, libfec_client) -> None:
        """Lazy initialization - called on first request.

        Uses asyncio.get_running_loop().create_task() to ensure the task
        is created in the active event loop (not the startup phase).
        """
        if self._initialized or self.is_running():
            return

        if self._configured_interval is None:
            return

        self._initialized = True
        self._db_path = db_path
        self._libfec_client = libfec_client
        self._interval_seconds = self._configured_interval

        loop = asyncio.get_running_loop()
        self._task = loop.create_task(self._run_loop())

    def seconds_until_next_sync(self) -> Optional[int]:
        if self._next_sync_time is None:
            return None
        remaining = self._next_sync_time - time.time()
        return max(0, int(remaining))

    async def start(self, db_path: str, libfec_client, interval_seconds: int) -> None:
        """Start watcher with given interval."""
        if self.is_running():
            return

        self._db_path = db_path
        self._libfec_client = libfec_client
        self._interval_seconds = interval_seconds

        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        """Stop the watcher."""
        if self.rpc_client:
            try:
                await self.rpc_client.sync_cancel()
            except Exception:
                pass

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        self._reset()

    def _reset(self) -> None:
        self.phase = "idle"
        self.exported_count = 0
        self.total_count = 0
        self.current_filing_id = None
        self.error_message = None
        self.currently_syncing = False
        self._next_sync_time = None

    async def _run_loop(self) -> None:
        """Background sync loop."""
        interval = self._interval_seconds
        if not interval:
            return

        # Brief delay to let event loop stabilize
        await asyncio.sleep(1)

        while True:
            self.phase = "syncing"
            self.exported_count = 0
            self.total_count = 0
            self.error_message = None

            try:
                await self._libfec_client.rss_watch_with_progress(
                    self._db_path,
                    None,  # No state filter
                    True,  # cover_only
                    self,
                )
                self.phase = "idle"

            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.phase = "error"
                self.error_message = str(e)

            self._next_sync_time = time.time() + interval
            await asyncio.sleep(interval)


rss_watcher = RssWatcher()

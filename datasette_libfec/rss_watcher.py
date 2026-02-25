"""
RSS Watcher - background sync driven by internal DB config.

Reads config from datasette_libfec_rss_config each iteration.
If enabled=False, sleeps and re-checks. If enabled=True, runs sync.
"""

import asyncio
import time
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .libfec_rpc_client import LibfecRpcClient


class RssWatcher:
    """RSS watcher controlled by internal DB config."""

    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._datasette = None
        self._initialized: bool = False
        self._wake_event: Optional[asyncio.Event] = None

        # Current interval for status reporting
        self._current_interval: Optional[int] = None

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

    def set_datasette(self, datasette) -> None:
        """Store datasette reference for config access."""
        self._datasette = datasette

    def ensure_started(self) -> None:
        """Lazy initialization - called on first request.

        Uses asyncio.get_running_loop().create_task() to ensure the task
        is created in the active event loop (not the startup phase).
        """
        if self._initialized or self.is_running():
            return

        if self._datasette is None:
            return

        self._initialized = True
        self._wake_event = asyncio.Event()
        loop = asyncio.get_running_loop()
        self._task = loop.create_task(self._run_loop())

    def wake(self) -> None:
        """Signal the loop to wake up and re-check config immediately."""
        if self._wake_event is not None:
            self._wake_event.set()

    async def _interruptible_sleep(self, seconds: float) -> None:
        """Sleep that can be interrupted by wake()."""
        assert self._wake_event is not None
        self._wake_event.clear()
        try:
            await asyncio.wait_for(self._wake_event.wait(), timeout=seconds)
        except asyncio.TimeoutError:
            pass

    def seconds_until_next_sync(self) -> Optional[int]:
        if self._next_sync_time is None:
            return None
        remaining = self._next_sync_time - time.time()
        return max(0, int(remaining))

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
        """Background sync loop - reads config from internal DB each iteration."""
        from .internal_db import InternalDB
        from .libfec_client import LibfecClient

        # Brief delay to let event loop stabilize
        await asyncio.sleep(1)

        datasette = self._datasette
        assert datasette is not None

        internal = InternalDB(datasette.get_internal_database())
        client = LibfecClient()

        while True:
            config = await internal.get_rss_config()

            if not config.enabled:
                self._current_interval = None
                self._next_sync_time = None
                self.phase = "idle"
                await self._interruptible_sleep(10)
                continue

            if not config.database_name:
                self.phase = "idle"
                await self._interruptible_sleep(10)
                continue

            # Resolve database_name to file path
            db = datasette.databases.get(config.database_name)
            if not db or not db.path:
                self.phase = "error"
                self.error_message = (
                    f"Database '{config.database_name}' not found or has no path"
                )
                await self._interruptible_sleep(10)
                continue

            self._current_interval = config.interval_seconds

            self.phase = "syncing"
            self.exported_count = 0
            self.total_count = 0
            self.error_message = None

            try:
                await client.rss_watch_with_progress(
                    db.path,
                    config.state_filter,
                    config.cover_only,
                    self,
                    since=config.since_duration,
                )
                self.phase = "idle"

            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.phase = "error"
                self.error_message = str(e)

            interval = config.interval_seconds
            self._current_interval = interval
            self._next_sync_time = time.time() + interval
            self.phase = "waiting"
            await self._interruptible_sleep(interval)


rss_watcher = RssWatcher()

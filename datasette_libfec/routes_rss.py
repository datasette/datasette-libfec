"""RSS watcher API routes."""

from pydantic import BaseModel
from datasette import Response
from typing import Optional

from .database import get_libfec_database
from .router import router, check_permission
from .rss_watcher import rss_watcher


class RssStatusResponse(BaseModel):
    enabled: bool
    running: bool
    phase: str
    interval_seconds: Optional[int] = None
    seconds_until_next_sync: Optional[int] = None
    exported_count: int = 0
    total_count: int = 0
    error_message: Optional[str] = None


class RssSyncRecord(BaseModel):
    sync_id: int
    sync_uuid: str
    created_at: str
    completed_at: Optional[str] = None
    status: str
    exported_count: int
    total_feed_items: Optional[int] = None
    error_message: Optional[str] = None


@router.GET("/-/api/libfec/rss/status")
@check_permission()
async def rss_status(datasette, request):
    from .state import libfec_client

    # Lazy initialization - start watcher if configured but not running
    db = get_libfec_database(datasette)
    if db.path:
        rss_watcher.ensure_started(db.path, libfec_client)

    running = rss_watcher.is_running()
    interval = rss_watcher._interval_seconds

    return Response.json(
        RssStatusResponse(
            enabled=running,
            running=running,
            phase=rss_watcher.phase,
            interval_seconds=interval,
            seconds_until_next_sync=rss_watcher.seconds_until_next_sync(),
            exported_count=rss_watcher.exported_count,
            total_count=rss_watcher.total_count,
            error_message=rss_watcher.error_message,
        ).model_dump()
    )


@router.GET("/-/api/libfec/rss/syncs")
@check_permission()
async def rss_syncs(datasette, request):
    """List recent sync attempts from libfec_rss_syncs table."""
    db = get_libfec_database(datasette)

    # Check if table exists
    tables = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='libfec_rss_syncs'"
    )
    if not tables.first():
        return Response.json({"syncs": []})

    result = await db.execute("""
        SELECT sync_id, sync_uuid, created_at, completed_at, status,
               exported_count, total_feed_items, error_message
        FROM libfec_rss_syncs
        ORDER BY created_at DESC
        LIMIT 20
    """)

    syncs = []
    for row in result.rows:
        syncs.append(
            RssSyncRecord(
                sync_id=row[0],
                sync_uuid=row[1],
                created_at=row[2],
                completed_at=row[3],
                status=row[4],
                exported_count=row[5] or 0,
                total_feed_items=row[6],
                error_message=row[7],
            ).model_dump()
        )

    return Response.json({"syncs": syncs})

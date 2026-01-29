from pydantic import BaseModel
from datasette import Response
from datasette_plugin_router import Body
from typing import Optional
import asyncio

from .router import router
from .state import libfec_client, rss_watcher_state


class RssStartParams(BaseModel):
    state: Optional[str] = None
    cover_only: bool = True
    interval: int = 60


class RssResponse(BaseModel):
    status: str
    message: str
    running: bool
    config: Optional[dict] = None


async def rss_watch_loop(
    output_db: str,
    state: Optional[str],
    cover_only: bool,
    interval: int
):
    """Background task that runs RSS watch periodically"""
    import time
    while rss_watcher_state.running:
        try:
            # Reset progress state before each sync
            rss_watcher_state.phase = "idle"
            rss_watcher_state.exported_count = 0
            rss_watcher_state.total_count = 0
            rss_watcher_state.current_filing_id = None
            rss_watcher_state.error_message = None
            rss_watcher_state.error_code = None
            rss_watcher_state.error_data = None

            print(f"Running RSS watch: state={state}, cover_only={cover_only}, db={output_db}")
            # Use RPC-based method with progress tracking
            await libfec_client.rss_watch_with_progress(
                output_db, state, cover_only, rss_watcher_state
            )
            print(f"RSS watch completed, sleeping {interval} seconds")
        except Exception as e:
            print(f"RSS watch error: {e}")
            rss_watcher_state.phase = "error"
            rss_watcher_state.error_message = str(e)
        finally:
            rss_watcher_state.next_sync_time = time.time() + interval
        await asyncio.sleep(interval)


@router.POST("/-/api/libfec/rss/start", output=RssResponse)
async def rss_start(datasette, params: Body[RssStartParams]):
    if rss_watcher_state.running:
        return Response.json({
            "status": "error",
            "message": "RSS watcher is already running",
            "running": True
        }, status=400)

    # Get output database
    output_db = None
    for name, db in datasette.databases.items():
        if not db.is_memory:
            output_db = db
            break
    if output_db is None:
        return Response.json({
            "status": "error",
            "message": "No writable database found.",
            "running": False
        }, status=500)

    # Validate interval
    if params.interval < 1:
        return Response.json({
            "status": "error",
            "message": "Interval must be at least 1 second",
            "running": False
        }, status=400)

    # Start the background task
    import time
    rss_watcher_state.running = True
    rss_watcher_state.state = params.state
    rss_watcher_state.cover_only = params.cover_only
    rss_watcher_state.interval = params.interval
    rss_watcher_state.output_db = output_db.path
    rss_watcher_state.next_sync_time = time.time()
    rss_watcher_state.currently_syncing = False
    rss_watcher_state.task = asyncio.create_task(
        rss_watch_loop(
            output_db.path,
            None if params.state == "" else params.state,
            params.cover_only,
            params.interval
        )
    )

    return Response.json(
        RssResponse(
            status="success",
            message="RSS watcher started",
            running=True,
            config={
                "state": params.state,
                "cover_only": params.cover_only,
                "interval": params.interval
            }
        ).model_dump()
    )


@router.POST("/-/api/libfec/rss/stop", output=RssResponse)
async def rss_stop(datasette):
    if not rss_watcher_state.running:
        return Response.json({
            "status": "error",
            "message": "RSS watcher is not running",
            "running": False
        }, status=400)

    # Cancel RPC sync if in progress
    if rss_watcher_state.rpc_client:
        try:
            await rss_watcher_state.rpc_client.sync_cancel()
        except Exception as e:
            print(f"Error canceling RPC sync: {e}")

    # Stop the background task
    rss_watcher_state.running = False
    if rss_watcher_state.task:
        rss_watcher_state.task.cancel()
        try:
            await rss_watcher_state.task
        except asyncio.CancelledError:
            pass
        rss_watcher_state.task = None

    return Response.json(
        RssResponse(
            status="success",
            message="RSS watcher stopped",
            running=False
        ).model_dump()
    )


@router.GET("/-/api/libfec/rss/status", output=RssResponse)
async def rss_status(datasette):
    config = None
    if rss_watcher_state.running:
        config = {
            "state": rss_watcher_state.state,
            "cover_only": rss_watcher_state.cover_only,
            "interval": rss_watcher_state.interval,
            "output_db": rss_watcher_state.output_db,
            "next_sync_time": rss_watcher_state.next_sync_time,
            "currently_syncing": rss_watcher_state.currently_syncing,
            # Progress tracking fields
            "phase": rss_watcher_state.phase,
            "exported_count": rss_watcher_state.exported_count,
            "total_count": rss_watcher_state.total_count,
            "current_filing_id": rss_watcher_state.current_filing_id,
            "feed_title": rss_watcher_state.feed_title,
            "feed_last_modified": rss_watcher_state.feed_last_modified,
            "error_message": rss_watcher_state.error_message,
            "error_code": rss_watcher_state.error_code,
            "error_data": rss_watcher_state.error_data,
            "sync_start_time": rss_watcher_state.sync_start_time
        }

    return Response.json(
        RssResponse(
            status="success",
            message="RSS watcher status",
            running=rss_watcher_state.running,
            config=config
        ).model_dump()
    )

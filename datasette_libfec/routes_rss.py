from pydantic import BaseModel
from datasette import Response
from datasette_plugin_router import Body
from typing import Optional, List, Literal
import asyncio

from .router import router
from .state import libfec_client, rss_watcher_state


class RssSyncRecord(BaseModel):
    sync_id: int
    sync_uuid: str
    created_at: str
    completed_at: Optional[str] = None
    since_filter: Optional[str] = None
    preset_filter: Optional[str] = None
    form_type_filter: Optional[str] = None
    committee_filter: Optional[str] = None
    state_filter: Optional[str] = None
    party_filter: Optional[str] = None
    total_feed_items: Optional[int] = None
    filtered_items: Optional[int] = None
    new_filings_count: int
    exported_count: int
    cover_only: bool
    status: str
    error_message: Optional[str] = None


class RssSyncFilingRecord(BaseModel):
    filing_id: str
    rss_pub_date: Optional[str] = None
    rss_title: Optional[str] = None
    committee_id: Optional[str] = None
    form_type: Optional[str] = None
    coverage_from: Optional[str] = None
    coverage_through: Optional[str] = None
    report_type: Optional[str] = None
    export_success: bool
    export_message: Optional[str] = None


class ApiRssSyncsListResponse(BaseModel):
    status: Literal['success']
    syncs: List[RssSyncRecord]
    message: Optional[str] = None


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


@router.GET("/-/api/libfec/rss/syncs$", output=ApiRssSyncsListResponse)
async def list_rss_syncs(datasette):
    """List all RSS sync operations from the metadata tables"""
    db = datasette.get_database()

    # Check if the table exists
    try:
        tables = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='libfec_rss_syncs'")
        if not tables.first():
            return Response.json({
                "status": "success",
                "syncs": [],
                "message": "No RSS syncs yet"
            })
    except Exception as e:
        return Response.json({
            "status": "error",
            "message": f"Database error: {str(e)}"
        }, status=500)

    try:
        syncs_result = await db.execute("""
            SELECT
                sync_id,
                sync_uuid,
                created_at,
                completed_at,
                since_filter,
                preset_filter,
                form_type_filter,
                committee_filter,
                state_filter,
                party_filter,
                total_feed_items,
                filtered_items,
                new_filings_count,
                exported_count,
                cover_only,
                status,
                error_message
            FROM libfec_rss_syncs
            ORDER BY created_at DESC
            LIMIT 50
        """)

        syncs = []
        for row in syncs_result.rows:
            syncs.append({
                "sync_id": row[0],
                "sync_uuid": row[1],
                "created_at": row[2],
                "completed_at": row[3],
                "since_filter": row[4],
                "preset_filter": row[5],
                "form_type_filter": row[6],
                "committee_filter": row[7],
                "state_filter": row[8],
                "party_filter": row[9],
                "total_feed_items": row[10],
                "filtered_items": row[11],
                "new_filings_count": row[12],
                "exported_count": row[13],
                "cover_only": bool(row[14]),
                "status": row[15],
                "error_message": row[16]
            })
        return Response.json(ApiRssSyncsListResponse(
            status="success",
            syncs=syncs
        ).model_dump_json())

    except Exception as e:
        return Response.json({
            "status": "error",
            "message": f"Failed to fetch RSS syncs: {str(e)}"
        }, status=500)


@router.GET("/-/api/libfec/rss/syncs/(?P<sync_id>\\d+)")
async def get_rss_sync_detail(datasette, sync_id: str):
    """Get detailed information about a specific RSS sync"""
    db = datasette.get_database()
    sync_id_int = int(sync_id)

    try:
        # Get sync record
        sync_result = await db.execute("""
            SELECT
                sync_id,
                sync_uuid,
                created_at,
                completed_at,
                since_filter,
                preset_filter,
                form_type_filter,
                committee_filter,
                state_filter,
                party_filter,
                total_feed_items,
                filtered_items,
                new_filings_count,
                exported_count,
                cover_only,
                status,
                error_message
            FROM libfec_rss_syncs
            WHERE sync_id = ?
        """, [sync_id_int])

        sync_row = sync_result.first()
        if not sync_row:
            return Response.json({
                "status": "error",
                "message": "RSS sync not found"
            }, status=404)

        sync = {
            "sync_id": sync_row[0],
            "sync_uuid": sync_row[1],
            "created_at": sync_row[2],
            "completed_at": sync_row[3],
            "since_filter": sync_row[4],
            "preset_filter": sync_row[5],
            "form_type_filter": sync_row[6],
            "committee_filter": sync_row[7],
            "state_filter": sync_row[8],
            "party_filter": sync_row[9],
            "total_feed_items": sync_row[10],
            "filtered_items": sync_row[11],
            "new_filings_count": sync_row[12],
            "exported_count": sync_row[13],
            "cover_only": bool(sync_row[14]),
            "status": sync_row[15],
            "error_message": sync_row[16]
        }

        # Get filings for this sync
        filings = []
        try:
            filings_result = await db.execute("""
                SELECT
                    filing_id,
                    rss_pub_date,
                    rss_title,
                    committee_id,
                    form_type,
                    coverage_from,
                    coverage_through,
                    report_type,
                    export_success,
                    export_message
                FROM libfec_rss_filings
                WHERE sync_id = ?
                ORDER BY rss_pub_date DESC
            """, [sync_id_int])

            for row in filings_result.rows:
                filings.append({
                    "filing_id": row[0],
                    "rss_pub_date": row[1],
                    "rss_title": row[2],
                    "committee_id": row[3],
                    "form_type": row[4],
                    "coverage_from": row[5],
                    "coverage_through": row[6],
                    "report_type": row[7],
                    "export_success": bool(row[8]),
                    "export_message": row[9]
                })
        except Exception:
            # Table might not exist
            pass

        return Response.json({
            "status": "success",
            "sync": sync,
            "filings": filings
        })

    except Exception as e:
        return Response.json({
            "status": "error",
            "message": f"Failed to fetch RSS sync detail: {str(e)}"
        }, status=500)

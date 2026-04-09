"""RSS watcher API routes — reads progress from internal DB, controls cron task."""

from pydantic import BaseModel
from datasette import Response
from datasette_plugin_router import Body
from typing import Optional

from .router import router, check_permission, check_write_permission
from .internal_db import InternalDB


class RssStatusResponse(BaseModel):
    enabled: bool
    running: bool
    phase: str
    interval_seconds: int = 60
    seconds_until_next_sync: Optional[int] = None
    exported_count: int = 0
    total_count: int = 0
    error_message: Optional[str] = None


class RssConfigResponse(BaseModel):
    enabled: bool
    interval_seconds: int = 60
    cover_only: bool = True
    state_filter: Optional[str] = None
    since_duration: str = "1 day"
    database_name: Optional[str] = None
    updated_at: Optional[str] = None


class RssConfigUpdateParams(BaseModel):
    enabled: Optional[bool] = None
    interval_seconds: Optional[int] = None
    cover_only: Optional[bool] = None
    state_filter: Optional[str] = None
    since_duration: Optional[str] = None
    database_name: Optional[str] = None


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
    new_filings_count: int = 0
    exported_count: int = 0
    cover_only: bool = False
    status: str = "started"
    error_message: Optional[str] = None


class RssFilingRecord(BaseModel):
    filing_id: str
    rss_pub_date: Optional[str] = None
    rss_title: Optional[str] = None
    committee_id: Optional[str] = None
    form_type: Optional[str] = None
    coverage_from: Optional[str] = None
    coverage_through: Optional[str] = None
    report_type: Optional[str] = None
    export_success: bool = True
    export_message: Optional[str] = None


def _seconds_until(next_run_at: str | None) -> int | None:
    if not next_run_at:
        return None
    from datetime import datetime, timezone

    try:
        nxt = datetime.fromisoformat(next_run_at)
        if nxt.tzinfo is None:
            nxt = nxt.replace(tzinfo=timezone.utc)
        remaining = (nxt - datetime.now(timezone.utc)).total_seconds()
        return max(0, int(remaining))
    except Exception:
        return None


@router.GET("/(?P<database>[^/]+)/-/api/libfec/rss/status$", output=RssStatusResponse)
@check_permission()
async def rss_status(datasette, request, database: str):
    internal = InternalDB(datasette.get_internal_database())
    config = await internal.get_rss_config()
    progress = await internal.get_rss_progress()

    # Get cron task state for next_run_at
    next_run_at = None
    task_enabled = config.enabled
    try:
        scheduler = datasette._cron_scheduler
        task = await scheduler.internal_db.get_task("libfec:rss-sync")
        if task:
            next_run_at = task.next_run_at
            task_enabled = bool(task.enabled)
    except Exception:
        pass

    return Response.json(
        RssStatusResponse(
            enabled=task_enabled,
            running=progress.get("phase") == "syncing",
            phase=progress.get("phase", "idle"),
            interval_seconds=config.interval_seconds,
            seconds_until_next_sync=_seconds_until(next_run_at),
            exported_count=progress.get("exported_count", 0),
            total_count=progress.get("total_count", 0),
            error_message=progress.get("error_message"),
        ).model_dump()
    )


@router.GET("/(?P<database>[^/]+)/-/api/libfec/rss/config$", output=RssConfigResponse)
@check_permission()
async def rss_config_get(datasette, request, database: str):
    internal = InternalDB(datasette.get_internal_database())
    config = await internal.get_rss_config()
    return Response.json(config.model_dump())


@router.POST(
    "/(?P<database>[^/]+)/-/api/libfec/rss/config/update$",
    output=RssConfigResponse,
)
@check_write_permission()
async def rss_config_update(
    datasette, request, database: str, params: Body[RssConfigUpdateParams]
):
    updates = params.model_dump(exclude_none=True)

    # If enabling and no database_name set, auto-set to current database
    if updates.get("enabled") and "database_name" not in updates:
        updates["database_name"] = database

    internal = InternalDB(datasette.get_internal_database())
    config = await internal.update_rss_config(**updates)

    # Sync cron task with new config
    try:
        scheduler = datasette._cron_scheduler
        if config.enabled:
            await scheduler.add_task(
                name="libfec:rss-sync",
                handler="libfec:rss-sync",
                schedule={"interval": config.interval_seconds},
                config={},
                overlap="skip",
            )
            await scheduler.enable_task("libfec:rss-sync")
            await scheduler.trigger_task("libfec:rss-sync")
        else:
            await scheduler.disable_task("libfec:rss-sync")
    except Exception:
        pass

    return Response.json(config.model_dump())


@router.GET("/(?P<database>[^/]+)/-/api/libfec/rss/syncs$")
@check_permission()
async def rss_syncs(datasette, request, database: str):
    """List recent sync attempts from libfec_rss_syncs table."""
    db = datasette.databases[database]

    tables = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='libfec_rss_syncs'"
    )
    if not tables.first():
        return Response.json({"syncs": []})

    result = await db.execute("""
        SELECT sync_id, sync_uuid, created_at, completed_at,
               since_filter, preset_filter, form_type_filter,
               committee_filter, state_filter, party_filter,
               total_feed_items, filtered_items, new_filings_count,
               exported_count, cover_only, status, error_message
        FROM libfec_rss_syncs
        ORDER BY created_at DESC
        LIMIT 20
    """)

    syncs = [_parse_sync_row(row) for row in result.rows]
    return Response.json({"syncs": syncs})


def _parse_sync_row(row) -> dict:
    return RssSyncRecord(
        sync_id=row[0],
        sync_uuid=row[1],
        created_at=row[2],
        completed_at=row[3],
        since_filter=row[4],
        preset_filter=row[5],
        form_type_filter=row[6],
        committee_filter=row[7],
        state_filter=row[8],
        party_filter=row[9],
        total_feed_items=row[10],
        filtered_items=row[11],
        new_filings_count=row[12] or 0,
        exported_count=row[13] or 0,
        cover_only=bool(row[14]),
        status=row[15] or "started",
        error_message=row[16],
    ).model_dump()


@router.GET("/(?P<database>[^/]+)/-/api/libfec/rss/syncs/(?P<sync_id>[0-9]+)$")
@check_permission()
async def rss_sync_detail(datasette, request, database: str, sync_id: str):
    """Get detail for a single sync including its filings."""
    db = datasette.databases[database]

    sync_result = await db.execute(
        """
        SELECT sync_id, sync_uuid, created_at, completed_at,
               since_filter, preset_filter, form_type_filter,
               committee_filter, state_filter, party_filter,
               total_feed_items, filtered_items, new_filings_count,
               exported_count, cover_only, status, error_message
        FROM libfec_rss_syncs
        WHERE sync_id = ?
    """,
        [sync_id],
    )

    row = sync_result.first()
    if not row:
        return Response.json(
            {"status": "error", "message": "Sync not found"}, status=404
        )

    filings_result = await db.execute(
        """
        SELECT filing_id, rss_pub_date, rss_title, committee_id,
               form_type, coverage_from, coverage_through, report_type,
               export_success, export_message
        FROM libfec_rss_filings
        WHERE sync_id = ?
        ORDER BY rss_pub_date DESC
    """,
        [sync_id],
    )

    filings = [
        RssFilingRecord(
            filing_id=f[0],
            rss_pub_date=f[1],
            rss_title=f[2],
            committee_id=f[3],
            form_type=f[4],
            coverage_from=f[5],
            coverage_through=f[6],
            report_type=f[7],
            export_success=bool(f[8]),
            export_message=f[9],
        ).model_dump()
        for f in filings_result.rows
    ]

    return Response.json(
        {
            "status": "success",
            "sync": _parse_sync_row(row),
            "filings": filings,
        }
    )

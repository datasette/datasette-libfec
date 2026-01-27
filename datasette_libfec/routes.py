from pydantic import BaseModel
from datasette import Response
from datasette_plugin_router import Router, Body
from typing import Literal, Optional
import asyncio
from .libfec_client import LibfecClient, RssWatcherState

libfec_client = LibfecClient()
rss_watcher_state = RssWatcherState()
router = Router()


@router.GET("/-/libfec")
async def libfec_page(datasette):
    return Response.html(
        await datasette.render_template(
            "libfec.html",
        )
    )


class ImportParams(BaseModel):
    kind: Literal['committee'] | Literal['candidate'] | Literal['contest']
    id: str
    cycle: int = 2026

class ImportResponse(BaseModel):
    status: str
    message: str

# RSS Watcher models and endpoints (defined before general import endpoint)
async def rss_watch_loop(output_db: str, state: Optional[str], cover_only: bool, interval: int):
    """Background task that runs RSS watch periodically"""
    while rss_watcher_state.running:
        try:
            print(f"Running RSS watch: state={state}, cover_only={cover_only}, db={output_db}")
            await libfec_client.rss_watch(output_db, state, cover_only)
            print(f"RSS watch completed, sleeping {interval} seconds")
        except Exception as e:
            print(f"RSS watch error: {e}")
        await asyncio.sleep(interval)


class RssStartParams(BaseModel):
    state: Optional[str] = None
    cover_only: bool = True
    interval: int = 60


class RssResponse(BaseModel):
    status: str
    message: str
    running: bool
    config: Optional[dict] = None


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
    rss_watcher_state.running = True
    rss_watcher_state.state = params.state
    rss_watcher_state.cover_only = params.cover_only
    rss_watcher_state.interval = params.interval
    rss_watcher_state.output_db = output_db.path
    rss_watcher_state.task = asyncio.create_task(
        rss_watch_loop(output_db.path, params.state, params.cover_only, params.interval)
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
            "output_db": rss_watcher_state.output_db
        }

    return Response.json(
        RssResponse(
            status="success",
            message="RSS watcher status",
            running=rss_watcher_state.running,
            config=config
        ).model_dump()
    )


# General import endpoint (defined after RSS endpoints to avoid route conflicts)
@router.POST("/-/api/libfec", output=ImportResponse)
async def libfec_import(datasette, params: Body[ImportParams]):
    output_db = None
    for name, db in datasette.databases.items():
        if not db.is_memory:
            output_db = db
            break
    if output_db is None:
        return Response.json({
            "status": "error",
            "message": "No writable database found."
        }, status=500)
    # validate cycle: expected even cycles between 2022 and 2026 inclusive
    if not (2022 <= params.cycle <= 2026) or (params.cycle % 2 != 0):
        return Response.json({
            "status": "error",
            "message": "Invalid cycle: must be an even year between 2022 and 2026."
        }, status=400)

    await libfec_client.export(
        committee_id=params.id,
        cycle=params.cycle,
        output_db=output_db.path)
    return Response.json(
        ImportResponse(
            status="success",
            message=f"Data for {params.kind} {params.id} imported successfully."
        ).model_dump_json()
    )

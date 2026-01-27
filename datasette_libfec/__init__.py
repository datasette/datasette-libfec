from pydantic import BaseModel
from datasette import hookimpl, Response
from datasette_plugin_router import Router, Body
from pathlib import Path
from textwrap import dedent
from typing import Literal, Optional
import sys
import subprocess
import json
import os
import asyncio




class LibfecClient:
    def __init__(self):
        bin_path = os.environ.get("DATASETTE_LIBFEC_BIN_PATH")
        if bin_path:
            self.libfec_path = Path(bin_path)
        else:
            self.libfec_path = Path(sys.executable).parent / 'libfec'

    def _run_libfec_command(self, args):
        """Synchronous command execution"""
        print(args)
        result = subprocess.run([str(self.libfec_path)] + args, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"libfec error: {result.stderr}")
        return result.stdout

    async def _run_libfec_command_async(self, args):
        """Async command execution - doesn't block event loop"""
        print(f"Running async: {args}")
        process = await asyncio.create_subprocess_exec(
            str(self.libfec_path),
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"libfec error: {stderr.decode()}")
        return stdout.decode()

    async def export(self, committee_id: str, cycle: int, output_db: str) -> str:
        """Export FEC data (async - won't block event loop)"""
        return await self._run_libfec_command_async([
            'export', committee_id,
            '--election', str(cycle),
            '--form-type', 'F3',
            #'--form-type', 'F1',
            '-o', output_db
          ])

    async def rss_watch(self, output_db: str, state: Optional[str] = None, cover_only: bool = True):
        """Run single RSS watch command (async - won't block event loop)"""
        args = ['rss', '--since', '1 day']
        if cover_only:
            args.append('--cover-only')
        args.extend(['-x', output_db])
        if state:
            args.extend(['--state', state])
        return await self._run_libfec_command_async(args)


# RSS watcher state
class RssWatcherState:
    def __init__(self):
        self.task: Optional[asyncio.Task] = None
        self.running = False
        self.interval = 60
        self.state: Optional[str] = None
        self.cover_only = True
        self.output_db: Optional[str] = None

rss_watcher_state = RssWatcherState()

libfec_client = LibfecClient()
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

# https://vite.dev/guide/backend-integration.html
class ManifestChunk(BaseModel):
    """Vite manifest chunk."""
    src: Optional[str] = None
    file: str  # The output file name of this chunk / asset
    css: Optional[list[str]] = None  # The list of CSS files imported by this chunk (JS chunks only)
    assets: Optional[list[str]] = None  # The list of asset files imported by this chunk, excluding CSS (JS chunks only)
    isEntry: Optional[bool] = None  # Whether this chunk or asset is an entry point
    name: Optional[str] = None  # The name of this chunk / asset if known
    isDynamicEntry: Optional[bool] = None  # Whether this chunk is a dynamic entry point (JS chunks only)
    imports: Optional[list[str]] = None  # The list of statically imported chunks (JS chunks only)
    dynamicImports: Optional[list[str]] = None  # The list of dynamically imported chunks (JS chunks only)

@hookimpl
def register_routes():
    return router.routes()

@hookimpl
def extra_template_vars(datasette):
    vite_path = os.environ.get("DATASETTE_LIBFEC_VITE_PATH")
    if vite_path:
        pass
    else:
        manifest_path = Path(__file__).parent / "manifest.json"
        if not manifest_path.exists():
            # Fallback if manifest doesn't exist yet
            manifest = {}
        else:
            manifest_raw = json.loads(manifest_path.read_text())
            manifest: dict[str, ManifestChunk] = {
                k: ManifestChunk(**v) for k, v in manifest_raw.items()
            }

    async def datasette_libfec_vite_entry(entrypoint):
        # https://vite.dev/guide/backend-integration.html

        if vite_path:
          return dedent(f"""

          <script type="module" src="{vite_path}@vite/client"></script>
          <script type="module" src="{vite_path}{entrypoint}"></script>

          """
          )
        else:
            chunk  = manifest.get(entrypoint)
            if not chunk:
                raise ValueError(f"Entrypoint {entrypoint} not found in manifest")
            parts = []

            # part 1, css files
            for css in chunk.css or []:
                file = str(Path(css).relative_to("static"))
                href = datasette.urls.static_plugins("datasette_libfec", file)
                parts.append(f'<link rel="stylesheet" href="{href}">')

            # part 2, import lists's chunks css files
            # TODO

            # part 3, entry point script
            # pop first path part which is always "static/"
            file = str(Path(chunk.file).relative_to("static"))
            src = datasette.urls.static_plugins("datasette_libfec", file)
            parts.append(f'<script type="module" src="{src}"></script>')

            # skip part 4
            return "\n".join(parts)


    return {"datasette_libfec_vite_entry": datasette_libfec_vite_entry}
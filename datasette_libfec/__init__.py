from pydantic import BaseModel
from datasette import hookimpl
from datasette.permissions import Action
from pathlib import Path
from textwrap import dedent
from typing import Optional
import json
import os

# Import route modules to trigger route registration on the shared router
# pylint: disable=unused-import
from . import routes_rss, routes_export, routes_search, routes_exports, routes_pages
from .router import router, LIBFEC_ACCESS_NAME, LIBFEC_WRITE_NAME

_ = routes_rss, routes_export, routes_search, routes_exports, routes_pages


# https://vite.dev/guide/backend-integration.html
class ManifestChunk(BaseModel):
    """Vite manifest chunk."""

    src: Optional[str] = None
    file: str  # The output file name of this chunk / asset
    css: Optional[list[str]] = (
        None  # The list of CSS files imported by this chunk (JS chunks only)
    )
    assets: Optional[list[str]] = (
        None  # The list of asset files imported by this chunk, excluding CSS (JS chunks only)
    )
    isEntry: Optional[bool] = None  # Whether this chunk or asset is an entry point
    name: Optional[str] = None  # The name of this chunk / asset if known
    isDynamicEntry: Optional[bool] = (
        None  # Whether this chunk is a dynamic entry point (JS chunks only)
    )
    imports: Optional[list[str]] = (
        None  # The list of statically imported chunks (JS chunks only)
    )
    dynamicImports: Optional[list[str]] = (
        None  # The list of dynamically imported chunks (JS chunks only)
    )


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

          """)
        else:
            chunk = manifest.get(entrypoint)
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


@hookimpl
def register_actions(datasette):
    return [
        Action(
            name=LIBFEC_ACCESS_NAME,
            description="Can access libfec pages (read-only)",
        ),
        Action(
            name=LIBFEC_WRITE_NAME,
            description="Can import FEC data and manage RSS watcher",
        ),
    ]


@hookimpl
def database_actions(datasette, actor, database):
    async def inner():
        if actor and (await datasette.allowed(action=LIBFEC_ACCESS_NAME, actor=actor)):
            return [
                {
                    "href": datasette.urls.path(f"/{database}/-/libfec/"),
                    "label": "FEC Data",
                }
            ]
        return []

    return inner


@hookimpl
def startup(datasette):
    """Store RSS config for lazy initialization (started on first request)."""

    async def inner():
        from .rss_watcher import rss_watcher

        # Check plugin config for rss-sync-interval-seconds
        config = datasette.plugin_config("datasette-libfec") or {}
        interval = config.get("rss-sync-interval-seconds")

        if not interval:
            return

        # Store config for lazy init - task will start on first API request
        rss_watcher.set_config(interval)

    return inner


@hookimpl
def shutdown(datasette):
    """Stop RSS watcher on shutdown."""

    async def inner():
        from .rss_watcher import rss_watcher

        if rss_watcher.is_running():
            await rss_watcher.stop()

    return inner

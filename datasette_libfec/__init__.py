from pydantic import BaseModel
from datasette import hookimpl
from pathlib import Path
from textwrap import dedent
from typing import Optional
import json
import os

from .routes import router

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
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




class LibfecClient:
    def __init__(self):
        bin_path = os.environ.get("DATASETTE_LIBFEC_BIN_PATH")
        if bin_path:
            self.libfec_path = Path(bin_path)
        else:
            self.libfec_path = Path(sys.executable).parent / 'libfec'

    def _run_libfec_command(self, args):
        print(args)
        result = subprocess.run([str(self.libfec_path)] + args, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"libfec error: {result.stderr}")
        return result.stdout
    
    async def export(self, committee_id: str, cycle: int, output_db: str) -> str:
        return self._run_libfec_command([
            'export', committee_id,
            '--election', str(cycle),
            '--form-type', 'F3',
            #'--form-type', 'F1',
            '-o', output_db
          ])

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
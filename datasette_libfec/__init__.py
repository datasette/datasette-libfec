from pydantic import BaseModel
from datasette import hookimpl, Response
from datasette_plugin_router import Router, Body
from pathlib import Path
import sys
import subprocess
from typing import Literal




class LibfecClient:
    def __init__(self):
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

@hookimpl
def register_routes():
    return router.routes()
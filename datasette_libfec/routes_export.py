from pydantic import BaseModel
from datasette import Response
from datasette_plugin_router import Body
from typing import Optional, List
import asyncio
import uuid

from .database import get_libfec_database
from .router import router, check_permission, check_write_permission
from .state import libfec_client, export_state


class ExportStartParams(BaseModel):
    filings: Optional[List[str]] = None
    cycle: Optional[int] = None
    cover_only: bool = False
    clobber: bool = False


class ExportResponse(BaseModel):
    status: str
    message: str
    export_id: Optional[str] = None
    phase: Optional[str] = None


@router.POST("/-/api/libfec/export/start", output=ExportResponse)
@check_write_permission()
async def export_start(datasette, request, params: Body[ExportStartParams]):
    if export_state.running:
        return Response.json(
            {
                "status": "error",
                "message": "Export already in progress",
                "phase": export_state.phase,
            },
            status=400,
        )

    # Get output database
    output_db = get_libfec_database(datasette)

    # Start export in background task
    async def run_export():
        await libfec_client.export_with_progress(
            output_db=output_db.path,
            filings=params.filings,
            cycle=params.cycle,
            cover_only=params.cover_only,
            clobber=params.clobber,
            export_state=export_state,
        )

    export_state.export_id = f"export-{uuid.uuid4()}"
    asyncio.create_task(run_export())

    # Give it a moment to start
    await asyncio.sleep(0.1)

    return Response.json(
        ExportResponse(
            status="success",
            message="Export started",
            export_id=export_state.export_id,
            phase=export_state.phase,
        ).model_dump()
    )


@router.GET("/-/api/libfec/export/status", output=ExportResponse)
@check_permission()
async def export_status(datasette, request):
    response_data = {
        "status": "success",
        "message": "Export status",
        "export_id": export_state.export_id,
        "phase": export_state.phase,
    }

    # Add additional fields based on phase
    if export_state.phase in ("sourcing", "downloading_bulk", "exporting"):
        response_data["completed"] = export_state.completed
        response_data["total"] = export_state.total

        if export_state.phase == "downloading_bulk" and export_state.current:
            response_data["current"] = export_state.current
        elif export_state.phase == "exporting" and export_state.current_filing_id:
            response_data["current_filing_id"] = export_state.current_filing_id

    elif export_state.phase == "complete":
        response_data["total_exported"] = export_state.total_exported
        response_data["warnings"] = export_state.warnings

        # Get the database export_id for redirect
        try:
            db = get_libfec_database(datasette)
            result = await db.execute(
                "SELECT export_id FROM libfec_exports ORDER BY export_id DESC LIMIT 1"
            )
            row = result.first()
            if row:
                response_data["db_export_id"] = row[0]
        except Exception:
            pass

    elif export_state.phase == "error":
        response_data["error_message"] = export_state.error_message

    return Response.json(response_data)


@router.POST("/-/api/libfec/export/cancel", output=ExportResponse)
@check_write_permission()
async def export_cancel(datasette, request):
    if not export_state.running:
        return Response.json(
            {"status": "error", "message": "No export in progress"}, status=400
        )

    # Cancel RPC export if in progress
    if export_state.rpc_client:
        try:
            await export_state.rpc_client.export_cancel()
        except Exception as e:
            print(f"Error canceling RPC export: {e}")

    return Response.json(
        ExportResponse(
            status="success",
            message="Export canceled",
            export_id=export_state.export_id,
            phase="canceled",
        ).model_dump()
    )

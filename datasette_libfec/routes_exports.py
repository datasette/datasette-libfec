from pydantic import BaseModel
from datasette import Response
from typing import Optional, List, Literal

from .router import router, check_permission


class ExportRecord(BaseModel):
    export_id: int
    export_uuid: str
    created_at: str
    filings_count: int
    cover_only: bool
    status: str
    error_message: Optional[str] = None


class ExportFilingRecord(BaseModel):
    filing_id: str
    success: bool
    message: Optional[str] = None


class ExportInputRecord(BaseModel):
    id: int
    input_type: str
    input_value: str
    cycle: Optional[int] = None
    office: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    filing_ids: List[str] = []


class ExportDetailResponse(BaseModel):
    export: ExportRecord
    inputs: List[ExportInputRecord]
    filings: List[ExportFilingRecord]


class ApiExportsListResponse(BaseModel):
    status: Literal["success"]
    exports: List[ExportRecord]
    message: Optional[str] = None


@router.GET("/(?P<database>[^/]+)/-/api/libfec/exports$", output=ApiExportsListResponse)
@check_permission()
async def list_exports(datasette, request, database: str):
    """List all export operations from the metadata tables"""
    db = datasette.databases[database]

    # Check if the table exists
    try:
        tables = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='libfec_exports'"
        )
        if not tables.first():
            return Response.json(
                {"status": "success", "exports": [], "message": "No exports yet"}
            )
    except Exception as e:
        return Response.json(
            {"status": "error", "message": f"Database error: {str(e)}"}, status=500
        )

    try:
        exports_result = await db.execute("""
            SELECT
                export_id,
                export_uuid,
                created_at,
                filings_count,
                cover_only,
                status,
                error_message
            FROM libfec_exports
            ORDER BY created_at DESC
            LIMIT 50
        """)

        exports = []
        for row in exports_result.rows:
            exports.append(
                {
                    "export_id": row[0],
                    "export_uuid": row[1],
                    "created_at": row[2],
                    "filings_count": row[3],
                    "cover_only": bool(row[4]),
                    "status": row[5],
                    "error_message": row[6],
                }
            )
        return Response.json(
            ApiExportsListResponse(status="success", exports=exports).model_dump()
        )

    except Exception as e:
        return Response.json(
            {"status": "error", "message": f"Failed to fetch exports: {str(e)}"},
            status=500,
        )


@router.GET("/(?P<database>[^/]+)/-/api/libfec/exports/(?P<export_id>\\d+)")
@check_permission()
async def get_export_detail(datasette, request, database: str, export_id: str):
    """Get detailed information about a specific export"""
    db = datasette.databases[database]
    export_id_int = int(export_id)

    try:
        # Get export record
        export_result = await db.execute(
            """
            SELECT
                export_id,
                export_uuid,
                created_at,
                filings_count,
                cover_only,
                status,
                error_message
            FROM libfec_exports
            WHERE export_id = ?
        """,
            [export_id_int],
        )

        export_row = export_result.first()
        if not export_row:
            return Response.json(
                {"status": "error", "message": "Export not found"}, status=404
            )

        export = {
            "export_id": export_row[0],
            "export_uuid": export_row[1],
            "created_at": export_row[2],
            "filings_count": export_row[3],
            "cover_only": bool(export_row[4]),
            "status": export_row[5],
            "error_message": export_row[6],
        }

        # Get inputs with their resolved filing IDs
        inputs = []
        try:
            inputs_result = await db.execute(
                """
                SELECT
                    i.id,
                    i.input_type,
                    i.input_value,
                    i.cycle,
                    i.office,
                    i.state,
                    i.district
                FROM libfec_export_inputs i
                WHERE i.export_id = ?
                ORDER BY i.id
            """,
                [export_id_int],
            )

            for row in inputs_result.rows:
                input_record = {
                    "id": row[0],
                    "input_type": row[1],
                    "input_value": row[2],
                    "cycle": row[3],
                    "office": row[4],
                    "state": row[5],
                    "district": row[6],
                    "filing_ids": [],
                }

                # Get filing IDs for this input
                filings_for_input = await db.execute(
                    """
                    SELECT filing_id
                    FROM libfec_export_input_filings
                    WHERE input_id = ?
                """,
                    [row[0]],
                )

                input_record["filing_ids"] = [f[0] for f in filings_for_input.rows]
                inputs.append(input_record)

        except Exception:
            # Table might not exist
            pass

        # Get filings with their success/failure status
        filings = []
        try:
            filings_result = await db.execute(
                """
                SELECT
                    filing_id,
                    success,
                    message
                FROM libfec_export_filings
                WHERE export_id = ?
                ORDER BY filing_id
            """,
                [export_id_int],
            )

            for row in filings_result.rows:
                filings.append(
                    {"filing_id": row[0], "success": bool(row[1]), "message": row[2]}
                )
        except Exception:
            # Table might not exist
            pass

        return Response.json(
            {
                "status": "success",
                "export": export,
                "inputs": inputs,
                "filings": filings,
            }
        )

    except Exception as e:
        return Response.json(
            {"status": "error", "message": f"Failed to fetch export detail: {str(e)}"},
            status=500,
        )

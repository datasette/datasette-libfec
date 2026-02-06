"""
Routes for contest, candidate, and committee pages.
"""
from datasette import Response

from .router import router, check_permission, check_write_permission, LIBFEC_WRITE_NAME
from .page_data import (
    Candidate,
    CandidatePageData,
    Committee,
    CommitteePageData,
    ContestPageData,
    ExportFilingInfo,
    ExportInputInfo,
    ExportPageData,
    Filing,
    FilingDetailPageData,
    IndexPageData,
    ImportPageData,
    RssPageData,
)


@router.GET("/-/libfec$")
@check_permission()
async def libfec_page(datasette, request):
    db = datasette.get_database()
    can_write = await datasette.allowed(
        action=LIBFEC_WRITE_NAME, actor=request.actor
    )
    page_data = IndexPageData(database_name=db.name, can_write=can_write)
    return Response.html(
        await datasette.render_template(
            "libfec_base.html",
            {
                "page_title": "FEC Import",
                "entrypoint": "src/index_view.ts",
                "page_data": page_data.model_dump(),
            }
        )
    )


@router.GET("/-/libfec/import$")
@check_write_permission()
async def import_page(datasette, request):
    db = datasette.get_database()
    page_data = ImportPageData(database_name=db.name)
    return Response.html(
        await datasette.render_template(
            "libfec_base.html",
            {
                "page_title": "Import FEC Data",
                "entrypoint": "src/import_view.ts",
                "page_data": page_data.model_dump(),
            }
        )
    )


@router.GET("/-/libfec/rss$")
@check_write_permission()
async def rss_page(datasette, request):
    db = datasette.get_database()
    page_data = RssPageData(database_name=db.name)
    return Response.html(
        await datasette.render_template(
            "libfec_base.html",
            {
                "page_title": "RSS Watcher",
                "entrypoint": "src/rss_view.ts",
                "page_data": page_data.model_dump(),
            }
        )
    )


@router.GET("/-/libfec/filing/(?P<filing_id>[^/]+)")
@check_permission()
async def filing_detail_page(datasette, request, filing_id: str):
    db = datasette.get_database()
    filing = None
    form_data = None
    error = None

    try:
        filing_row = await db.execute(
            "SELECT * FROM libfec_filings WHERE filing_id = ?", [filing_id]
        )
        filing_result = filing_row.first()

        if not filing_result:
            return Response.html("<h1>Filing not found</h1>", status=404)

        filing = Filing(**dict(filing_result))

        # Fetch form-specific data based on cover_record_form
        form_type = filing.cover_record_form
        form_table_map = {
            "F1": "libfec_F1",
            "F1S": "libfec_F1S",
            "F2": "libfec_F2",
            "F3": "libfec_F3",
            "F3P": "libfec_F3P",
            "F3S": "libfec_F3S",
            "F3X": "libfec_F3X",
            "F24": "libfec_F24",
            "F6": "libfec_F6",
            "F99": "libfec_F99",
        }

        table_name = form_table_map.get(form_type) if form_type else None
        if table_name:
            try:
                form_row = await db.execute(
                    f"SELECT * FROM {table_name} WHERE filing_id = ?", [filing_id]
                )
                form_result = form_row.first()
                if form_result:
                    form_data = dict(form_result)
            except Exception as e:
                error = f"Error fetching form data: {e}"

    except Exception as e:
        error = str(e)

    page_data = FilingDetailPageData(
        filing_id=filing_id,
        filing=filing,
        form_data=form_data,
        database_name=db.name,
        error=error,
    )
    return Response.html(
        await datasette.render_template(
            "libfec_base.html",
            {
                "page_title": f"Filing {filing_id}",
                "entrypoint": "src/filing_detail_view.ts",
                "page_data": page_data.model_dump(),
            }
        )
    )


@router.GET("/-/libfec/contest$")
@check_permission()
async def contest_page(datasette, request):
    """
    Contest page showing candidates for a specific race.

    Query params:
    - state: Two-letter state code (e.g., "CA")
    - office: Office type - "H" (House), "S" (Senate), or "P" (President)
    - district: District number for House races (optional for S/P)
    - cycle: Election cycle year (default: 2026)
    """
    state = request.args.get("state")
    office = request.args.get("office")
    district = request.args.get("district")
    cycle = int(request.args.get("cycle", 2026))

    if not state or not office:
        return Response.html("<h1>Missing required parameters: state and office</h1>", status=400)

    candidates = []
    error = None

    try:
        db = datasette.get_database()

        if office == "H" and district:
            candidates_result = await db.execute(
                """
                SELECT * FROM libfec_candidates
                WHERE state = ? AND office = ? AND district = ? AND cycle = ?
                GROUP BY candidate_id
                ORDER BY name
                """,
                [state, office, district, cycle]
            )
        else:
            candidates_result = await db.execute(
                """
                SELECT * FROM libfec_candidates
                WHERE state = ? AND office = ? AND cycle = ?
                GROUP BY candidate_id
                ORDER BY name
                """,
                [state, office, cycle]
            )

        candidates = [Candidate(**dict(row)) for row in candidates_result.rows]

    except Exception as e:
        error = str(e)

    # Build contest description
    office_names = {"H": "House", "S": "Senate", "P": "President"}
    office_name = office_names.get(office, office)
    contest_description = f"{state} {office_name}"
    if office == "H" and district:
        contest_description = f"{state} Congressional District {district}"
    elif office == "S":
        contest_description = f"{state} Senate"

    page_data = ContestPageData(
        state=state,
        office=office,
        district=district,
        cycle=cycle,
        contest_description=contest_description,
        candidates=candidates,
        error=error,
    )
    return Response.html(
        await datasette.render_template(
            "libfec_base.html",
            {
                "page_title": f"{contest_description} - {cycle}",
                "entrypoint": "src/contest_view.ts",
                "page_data": page_data.model_dump(),
            }
        )
    )


@router.GET("/-/libfec/candidate/(?P<candidate_id>[^/]+)$")
@check_permission()
async def candidate_page(datasette, request, candidate_id: str):
    """
    Candidate detail page.

    Shows candidate information and their principal committee.
    """
    cycle = int(request.args.get("cycle", 2026))
    candidate = None
    committee = None
    filings = []
    error = None
    principal_committee_id = None

    try:
        db = datasette.get_database()

        # Fetch candidate from database
        candidate_result = await db.execute(
            """
            SELECT * FROM libfec_candidates
            WHERE candidate_id = ? AND cycle = ?
            """,
            [candidate_id, cycle]
        )
        candidate_row = candidate_result.first()
        if candidate_row:
            candidate = Candidate(**dict(candidate_row))
            principal_committee_id = candidate.principal_campaign_committee

        # Get principal committee if available
        if principal_committee_id:
            committee_result = await db.execute(
                """
                SELECT * FROM libfec_committees
                WHERE committee_id = ? AND cycle = ?
                """,
                [principal_committee_id, cycle]
            )
            committee_row = committee_result.first()
            if committee_row:
                committee = Committee(**dict(committee_row))

            # Fetch filings for this committee
            filings_result = await db.execute(
                """
                SELECT * FROM libfec_filings
                WHERE filer_id = ?
                ORDER BY filing_id DESC
                LIMIT 50
                """,
                [principal_committee_id]
            )
            filings = [Filing(**dict(row)) for row in filings_result.rows]

    except Exception as e:
        error = str(e)

    page_data = CandidatePageData(
        candidate_id=candidate_id,
        cycle=cycle,
        candidate=candidate,
        committee=committee,
        filings=filings,
        error=error,
    )
    candidate_name = candidate.name if candidate else candidate_id
    return Response.html(
        await datasette.render_template(
            "libfec_base.html",
            {
                "page_title": f"{candidate_name} - Candidate",
                "entrypoint": "src/candidate_view.ts",
                "page_data": page_data.model_dump(),
            }
        )
    )


@router.GET("/-/libfec/exports/(?P<export_id>\\d+)$")
@check_permission()
async def export_detail_page(datasette, request, export_id: str):
    """
    Export detail page showing all filings from an export.
    """
    db = datasette.get_database()
    export_id_int = int(export_id)

    export_uuid = None
    created_at = None
    status = None
    filings_count = 0
    cover_only = False
    error_message = None
    inputs = []
    filings = []
    error = None

    try:
        # Get export record
        export_result = await db.execute("""
            SELECT export_uuid, created_at, status, filings_count, cover_only, error_message
            FROM libfec_exports
            WHERE export_id = ?
        """, [export_id_int])
        export_row = export_result.first()

        if not export_row:
            return Response.html("<h1>Export not found</h1>", status=404)

        export_uuid = export_row[0]
        created_at = export_row[1]
        status = export_row[2]
        filings_count = export_row[3] or 0
        cover_only = bool(export_row[4])
        error_message = export_row[5]

        # Get inputs
        try:
            inputs_result = await db.execute("""
                SELECT id, input_type, input_value, cycle
                FROM libfec_export_inputs
                WHERE export_id = ?
                ORDER BY id
            """, [export_id_int])

            for row in inputs_result.rows:
                input_record = ExportInputInfo(
                    id=row[0],
                    input_type=row[1],
                    input_value=row[2],
                    cycle=row[3],
                    filing_ids=[]
                )
                # Get filing IDs for this input
                filings_for_input = await db.execute("""
                    SELECT filing_id
                    FROM libfec_export_input_filings
                    WHERE input_id = ?
                """, [row[0]])
                input_record.filing_ids = [f[0] for f in filings_for_input.rows]
                inputs.append(input_record)
        except Exception:
            pass

        # Get filings with metadata from libfec_filings
        try:
            filings_result = await db.execute("""
                SELECT
                    ef.filing_id,
                    ef.success,
                    ef.message,
                    f.cover_record_form,
                    f.filer_id,
                    f.filer_name,
                    f.coverage_from_date,
                    f.coverage_through_date
                FROM libfec_export_filings ef
                LEFT JOIN libfec_filings f ON ef.filing_id = f.filing_id
                WHERE ef.export_id = ?
                ORDER BY ef.filing_id DESC
            """, [export_id_int])

            for row in filings_result.rows:
                filings.append(ExportFilingInfo(
                    filing_id=row[0],
                    success=bool(row[1]),
                    message=row[2],
                    cover_record_form=row[3],
                    filer_id=row[4],
                    filer_name=row[5],
                    coverage_from_date=row[6],
                    coverage_through_date=row[7],
                ))
        except Exception:
            pass

    except Exception as e:
        error = str(e)

    page_data = ExportPageData(
        export_id=export_id_int,
        export_uuid=export_uuid,
        created_at=created_at,
        status=status,
        filings_count=filings_count,
        cover_only=cover_only,
        error_message=error_message,
        inputs=inputs,
        filings=filings,
        database_name=db.name,
        error=error,
    )
    return Response.html(
        await datasette.render_template(
            "libfec_base.html",
            {
                "page_title": f"Export {export_id}",
                "entrypoint": "src/export_view.ts",
                "page_data": page_data.model_dump(),
            }
        )
    )


@router.GET("/-/libfec/committee/(?P<committee_id>[^/]+)$")
@check_permission()
async def committee_page(datasette, request, committee_id: str):
    """
    Committee detail page.

    Shows committee information and recent filings.
    """
    cycle = int(request.args.get("cycle", 2026))
    committee = None
    candidate = None
    filings = []
    error = None
    candidate_id = None

    try:
        db = datasette.get_database()

        # Fetch committee from database
        committee_result = await db.execute(
            """
            SELECT * FROM libfec_committees
            WHERE committee_id = ? AND cycle = ?
            """,
            [committee_id, cycle]
        )
        committee_row = committee_result.first()
        if committee_row:
            committee = Committee(**dict(committee_row))
            candidate_id = committee.candidate_id

        # If this committee has a candidate_id, fetch the candidate
        if candidate_id:
            candidate_result = await db.execute(
                """
                SELECT * FROM libfec_candidates
                WHERE candidate_id = ? AND cycle = ?
                """,
                [candidate_id, cycle]
            )
            candidate_row = candidate_result.first()
            if candidate_row:
                candidate = Candidate(**dict(candidate_row))

        # Fetch filings for this committee
        filings_result = await db.execute(
            """
            SELECT * FROM libfec_filings
            WHERE filer_id = ?
            ORDER BY filing_id DESC
            LIMIT 50
            """,
            [committee_id]
        )
        filings = [Filing(**dict(row)) for row in filings_result.rows]

    except Exception as e:
        error = str(e)

    page_data = CommitteePageData(
        committee_id=committee_id,
        cycle=cycle,
        committee=committee,
        candidate=candidate,
        filings=filings,
        error=error,
    )
    committee_name = committee.name if committee else committee_id
    return Response.html(
        await datasette.render_template(
            "libfec_base.html",
            {
                "page_title": f"{committee_name} - Committee",
                "entrypoint": "src/committee_view.ts",
                "page_data": page_data.model_dump(),
            }
        )
    )

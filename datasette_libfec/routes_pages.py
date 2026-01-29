"""
Routes for contest, candidate, and committee pages.
"""
from datasette import Response

from .router import router
from .page_data import (
    Candidate,
    CandidatePageData,
    Committee,
    CommitteePageData,
    ContestPageData,
    Filing, FilingDetailPageData, IndexPageData
)


@router.GET("/-/libfec$")
async def libfec_page(datasette):
    db = datasette.get_database()
    page_data = IndexPageData(database_name=db.name)
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


@router.GET("/-/libfec/filing/(?P<filing_id>[^/]+)")
async def filing_detail_page(datasette, filing_id: str):
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


@router.GET("/-/libfec/committee/(?P<committee_id>[^/]+)$")
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

"""
API routes for creating FEC alerts via datasette-alerts custom alert types.
"""

from typing import Annotated

from pydantic import BaseModel
from datasette import Response
from datasette_plugin_router import Body

from .router import router, check_permission
from .page_data import (
    ContributorCriteria,
    FecContributorAlertConfig,
    FecFilingAlertConfig,
    RaceSpec,
)


class CreateFecAlertBody(BaseModel):
    name: str = ""
    alert_type: str  # "fec-filing" | "fec-contributor"
    frequency: str = "+1 second"
    destination_id: str
    # Filing config
    committee_ids: list[str] = []
    races: list[RaceSpec] = []
    state_filter: str = ""
    # Contributor config
    contributors: list[ContributorCriteria] = []


@router.POST("/(?P<database>[^/]+)/-/api/libfec/alerts/new")
@check_permission()
async def api_create_fec_alert(
    datasette,
    request,
    database: str,
    body: Annotated[CreateFecAlertBody, Body()],
):
    # Ensure queue table + trigger exist
    from .alert_types import ensure_queue_table

    db = datasette.databases.get(database)
    if db:
        await ensure_queue_table(db)

    # Build custom_config from the request
    custom_config = {}
    if body.alert_type == "fec-filing":
        config = FecFilingAlertConfig(
            committee_ids=body.committee_ids,
            races=body.races,
            state_filter=body.state_filter,
        )
        custom_config = config.model_dump(exclude_defaults=True)
    elif body.alert_type == "fec-contributor":
        config = FecContributorAlertConfig(
            contributors=body.contributors,
        )
        custom_config = config.model_dump(exclude_defaults=True)
    else:
        return Response.json(
            {"ok": False, "error": f"Unknown alert type: {body.alert_type}"},
            status=400,
        )

    # Create the alert via datasette-alerts internal API
    try:
        from datasette_alerts.internal_db import (
            InternalDB,
            NewAlertRouteParameters,
            NewSubscription,
        )
        from datasette_alerts import _register_cron_task_for_alert
    except ImportError:
        return Response.json(
            {"ok": False, "error": "datasette-alerts is not installed"},
            status=400,
        )

    internal_db = InternalDB(datasette.get_internal_database())
    params = NewAlertRouteParameters(
        database_name=database,
        alert_type=f"custom:{body.alert_type}",
        frequency=body.frequency,
        custom_config=custom_config,
        subscriptions=[
            NewSubscription(
                destination_id=body.destination_id,
                meta={"aggregate": True},
            )
        ],
    )

    alert_id = await internal_db.new_alert(params)

    # Register the cron task
    from types import SimpleNamespace

    alert_obj = SimpleNamespace(
        id=alert_id,
        alert_type=f"custom:{body.alert_type}",
        frequency=body.frequency,
    )
    await _register_cron_task_for_alert(datasette, alert_obj)

    return Response.json({"ok": True, "alert_id": alert_id})


@router.POST("/(?P<database>[^/]+)/-/api/libfec/alerts/(?P<alert_id>[^/]+)/delete")
@check_permission()
async def api_delete_fec_alert(datasette, request, database: str, alert_id: str):
    try:
        from datasette_alerts.internal_db import InternalDB
    except ImportError:
        return Response.json(
            {"ok": False, "error": "datasette-alerts is not installed"},
            status=400,
        )

    internal_db = InternalDB(datasette.get_internal_database())
    await internal_db.delete_alert(alert_id)

    # Remove cron task
    try:
        scheduler = datasette._cron_scheduler
        for prefix in ["alerts:cursor:", "alerts:custom:"]:
            try:
                await scheduler.remove_task(f"{prefix}{alert_id}")
            except Exception:
                pass
    except Exception:
        pass

    return Response.json({"ok": True})

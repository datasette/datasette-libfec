"""Tests for FEC custom alert types via datasette-alerts (trigger+queue based)."""

import json
import sqlite3
import pytest
import pytest_asyncio
from datasette.app import Datasette


@pytest_asyncio.fixture
async def datasette_with_fec_db(tmp_path):
    db_path = tmp_path / "fec.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        CREATE TABLE libfec_filings (
            filing_id TEXT PRIMARY KEY,
            filer_id TEXT,
            filer_name TEXT,
            cover_record_form TEXT
        );
        CREATE TABLE libfec_committees (
            committee_id TEXT PRIMARY KEY,
            name TEXT,
            candidate_id TEXT
        );
        CREATE TABLE libfec_candidates (
            candidate_id TEXT PRIMARY KEY,
            office TEXT,
            state TEXT,
            district TEXT,
            cycle INTEGER
        );
        CREATE TABLE libfec_schedule_a (
            filing_id TEXT,
            contributor_first_name TEXT,
            contributor_last_name TEXT,
            contributor_city TEXT,
            contributor_state TEXT,
            contribution_amount REAL
        );

        INSERT INTO libfec_committees VALUES ('C00123456', 'Test PAC', 'P001');
        INSERT INTO libfec_committees VALUES ('C00789012', 'Other PAC', 'P002');
        INSERT INTO libfec_candidates VALUES ('P001', 'H', 'CA', '12', 2026);
    """)
    conn.close()

    ds = Datasette(
        [str(db_path)],
        config={
            "permissions": {
                "datasette-alerts-access": True,
                "datasette_libfec_access": True,
                "datasette_libfec_write": True,
            },
        },
    )
    await ds.invoke_startup()
    return ds


# --- Queue + trigger ---


@pytest.mark.asyncio
async def test_queue_table_and_trigger_created(datasette_with_fec_db):
    db = datasette_with_fec_db.get_database("fec")
    result = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='libfec_alert_queue'"
    )
    assert len(result.rows) == 1
    result = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='trigger' AND name='libfec_filings_alert_trigger'"
    )
    assert len(result.rows) == 1


@pytest.mark.asyncio
async def test_insert_filing_populates_queue(datasette_with_fec_db):
    db = datasette_with_fec_db.get_database("fec")
    await db.execute_write(
        "INSERT INTO libfec_filings VALUES ('9001', 'C00123456', 'Test PAC', 'F3')"
    )

    result = await db.execute("SELECT filing_id, status FROM libfec_alert_queue")
    assert len(result.rows) == 1
    assert result.rows[0][0] == "9001"
    assert result.rows[0][1] == "pending"


# --- Filing alert ---


@pytest.mark.asyncio
async def test_filing_check_drains_queue(datasette_with_fec_db):
    from datasette_libfec.alert_types import FecFilingAlertType

    ds = datasette_with_fec_db
    db = ds.get_database("fec")

    await db.execute_write(
        "INSERT INTO libfec_filings VALUES ('9001', 'C001', 'PAC A', 'F3')"
    )
    await db.execute_write(
        "INSERT INTO libfec_filings VALUES ('9002', 'C002', 'PAC B', 'F3X')"
    )

    at = FecFilingAlertType()
    messages = await at.check(ds, {}, "fec", None)
    assert len(messages) == 2
    assert "FEC-9001" in messages[0].text
    assert "FEC-9002" in messages[1].text

    # All done
    result = await db.execute("SELECT status FROM libfec_alert_queue")
    for row in result.rows:
        assert row[0] == "done"

    # Second check: nothing pending
    messages = await at.check(ds, {}, "fec", None)
    assert len(messages) == 0


@pytest.mark.asyncio
async def test_filing_check_empty_queue(datasette_with_fec_db):
    from datasette_libfec.alert_types import FecFilingAlertType

    messages = await FecFilingAlertType().check(datasette_with_fec_db, {}, "fec", None)
    assert len(messages) == 0


# --- Contributor alert ---


@pytest.mark.asyncio
async def test_contributor_check_drains_and_matches(datasette_with_fec_db):
    from datasette_libfec.alert_types import FecContributorAlertType

    ds = datasette_with_fec_db
    db = ds.get_database("fec")

    await db.execute_write(
        "INSERT INTO libfec_filings VALUES ('9001', 'C001', 'Test PAC', 'F3')"
    )
    await db.execute_write(
        "INSERT INTO libfec_schedule_a VALUES ('9001', 'John', 'Smith', 'Los Angeles', 'CA', 5000.00)"
    )

    at = FecContributorAlertType()
    messages = await at.check(
        ds, {"contributors": [{"last_name": "Smith"}]}, "fec", None
    )
    assert len(messages) == 1
    assert "Smith" in messages[0].text
    assert "$5,000.00" in messages[0].text

    # Queue drained
    result = await db.execute("SELECT status FROM libfec_alert_queue")
    assert result.rows[0][0] == "done"

    # Second check: nothing pending
    messages = await at.check(
        ds, {"contributors": [{"last_name": "Smith"}]}, "fec", None
    )
    assert len(messages) == 0


@pytest.mark.asyncio
async def test_contributor_check_no_match_still_drains(datasette_with_fec_db):
    from datasette_libfec.alert_types import FecContributorAlertType

    ds = datasette_with_fec_db
    db = ds.get_database("fec")

    await db.execute_write(
        "INSERT INTO libfec_filings VALUES ('9001', 'C001', 'Test PAC', 'F3')"
    )
    await db.execute_write(
        "INSERT INTO libfec_schedule_a VALUES ('9001', 'John', 'Smith', 'LA', 'CA', 5000.00)"
    )

    at = FecContributorAlertType()
    messages = await at.check(
        ds, {"contributors": [{"last_name": "Nobody"}]}, "fec", None
    )
    assert len(messages) == 0

    # Queue still drained even though no match
    result = await db.execute("SELECT status FROM libfec_alert_queue")
    assert result.rows[0][0] == "done"


@pytest.mark.asyncio
async def test_contributor_check_multiple_matches(datasette_with_fec_db):
    from datasette_libfec.alert_types import FecContributorAlertType

    ds = datasette_with_fec_db
    db = ds.get_database("fec")

    await db.execute_write(
        "INSERT INTO libfec_filings VALUES ('9001', 'C001', 'Test PAC', 'F3')"
    )
    await db.execute_write(
        "INSERT INTO libfec_schedule_a VALUES ('9001', 'John', 'Smith', 'LA', 'CA', 5000.00)"
    )
    await db.execute_write(
        "INSERT INTO libfec_schedule_a VALUES ('9001', 'Jane', 'Doe', 'NY', 'NY', 2500.00)"
    )

    at = FecContributorAlertType()
    messages = await at.check(
        ds,
        {"contributors": [{"last_name": "Smith"}, {"last_name": "Doe"}]},
        "fec",
        None,
    )
    assert len(messages) == 1
    assert "2 contributor matches" in messages[0].text


@pytest.mark.asyncio
async def test_contributor_check_empty_contributors(datasette_with_fec_db):
    from datasette_libfec.alert_types import FecContributorAlertType

    messages = await FecContributorAlertType().check(
        datasette_with_fec_db, {"contributors": []}, "fec", None
    )
    assert len(messages) == 0


# --- API ---


@pytest.mark.asyncio
async def test_create_fec_filing_alert(datasette_with_fec_db):
    ds = datasette_with_fec_db
    from datasette_alerts.internal_db import InternalDB, NewDestination

    internal_db = InternalDB(ds.get_internal_database())
    dest_id = await internal_db.create_destination(
        NewDestination(notifier="test", label="Test Dest", config={})
    )

    response = await ds.client.post(
        "/fec/-/api/libfec/alerts/new",
        json={"alert_type": "fec-filing", "destination_id": dest_id},
    )
    assert response.status_code == 200
    alert = await internal_db.get_alert_for_check(response.json()["alert_id"])
    assert alert is not None
    assert alert.alert_type == "custom:fec-filing"


@pytest.mark.asyncio
async def test_create_fec_contributor_alert(datasette_with_fec_db):
    ds = datasette_with_fec_db
    from datasette_alerts.internal_db import InternalDB, NewDestination

    internal_db = InternalDB(ds.get_internal_database())
    dest_id = await internal_db.create_destination(
        NewDestination(notifier="test", label="Test Dest", config={})
    )

    response = await ds.client.post(
        "/fec/-/api/libfec/alerts/new",
        json={
            "alert_type": "fec-contributor",
            "destination_id": dest_id,
            "contributors": [{"last_name": "Smith", "state": "CA"}],
        },
    )
    assert response.status_code == 200
    alert = await internal_db.get_alert_for_check(response.json()["alert_id"])
    assert alert is not None
    assert alert.alert_type == "custom:fec-contributor"
    custom_config = json.loads(alert.custom_config)
    assert custom_config["contributors"][0]["last_name"] == "Smith"


@pytest.mark.asyncio
async def test_delete_fec_alert(datasette_with_fec_db):
    ds = datasette_with_fec_db
    from datasette_alerts.internal_db import InternalDB, NewDestination

    internal_db = InternalDB(ds.get_internal_database())
    dest_id = await internal_db.create_destination(
        NewDestination(notifier="test", label="Test Dest", config={})
    )

    response = await ds.client.post(
        "/fec/-/api/libfec/alerts/new",
        json={"alert_type": "fec-filing", "destination_id": dest_id},
    )
    alert_id = response.json()["alert_id"]
    response = await ds.client.post(f"/fec/-/api/libfec/alerts/{alert_id}/delete")
    assert response.status_code == 200

    assert await internal_db.get_alert_for_check(alert_id) is None


@pytest.mark.asyncio
async def test_invalid_alert_type_returns_400(datasette_with_fec_db):
    ds = datasette_with_fec_db
    from datasette_alerts.internal_db import InternalDB, NewDestination

    internal_db = InternalDB(ds.get_internal_database())
    dest_id = await internal_db.create_destination(
        NewDestination(notifier="test", label="Test Dest", config={})
    )

    response = await ds.client.post(
        "/fec/-/api/libfec/alerts/new",
        json={"alert_type": "invalid", "destination_id": dest_id},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_alerts_page_shows_created_alerts(datasette_with_fec_db):
    ds = datasette_with_fec_db
    from datasette_alerts.internal_db import InternalDB, NewDestination

    internal_db = InternalDB(ds.get_internal_database())
    dest_id = await internal_db.create_destination(
        NewDestination(notifier="test", label="Test Dest", config={})
    )

    response = await ds.client.post(
        "/fec/-/api/libfec/alerts/new",
        json={"alert_type": "fec-filing", "destination_id": dest_id},
    )
    alert_id = response.json()["alert_id"]

    response = await ds.client.get("/fec/-/libfec/alerts")
    assert response.status_code == 200
    assert alert_id in response.text


# --- Full end-to-end handler execution ---


@pytest.mark.asyncio
async def test_full_filing_handler_execution(datasette_with_fec_db):
    from datasette_alerts.internal_db import InternalDB, NewDestination
    from datasette_alerts.handlers import custom_alert_handler

    ds = datasette_with_fec_db
    db = ds.get_database("fec")

    internal_db = InternalDB(ds.get_internal_database())
    dest_id = await internal_db.create_destination(
        NewDestination(notifier="test", label="Test Dest", config={})
    )

    resp = await ds.client.post(
        "/fec/-/api/libfec/alerts/new",
        json={"alert_type": "fec-filing", "destination_id": dest_id},
    )
    alert_id = resp.json()["alert_id"]

    await db.execute_write(
        "INSERT INTO libfec_filings VALUES ('8001', 'C001', 'PAC A', 'F3')"
    )
    await db.execute_write(
        "INSERT INTO libfec_filings VALUES ('8002', 'C002', 'PAC B', 'F3X')"
    )

    # Pending
    result = await db.execute(
        "SELECT count(*) FROM libfec_alert_queue WHERE status='pending'"
    )
    assert result.rows[0][0] == 2

    await custom_alert_handler(ds, {"alert_id": alert_id, "type_slug": "fec-filing"})

    # Drained
    result = await db.execute(
        "SELECT count(*) FROM libfec_alert_queue WHERE status='pending'"
    )
    assert result.rows[0][0] == 0
    result = await db.execute(
        "SELECT count(*) FROM libfec_alert_queue WHERE status='done'"
    )
    assert result.rows[0][0] == 2


@pytest.mark.asyncio
async def test_full_contributor_handler_execution(datasette_with_fec_db):
    from datasette_alerts.internal_db import InternalDB, NewDestination
    from datasette_alerts.handlers import custom_alert_handler

    ds = datasette_with_fec_db
    db = ds.get_database("fec")

    internal_db = InternalDB(ds.get_internal_database())
    dest_id = await internal_db.create_destination(
        NewDestination(notifier="test", label="Test Dest", config={})
    )

    resp = await ds.client.post(
        "/fec/-/api/libfec/alerts/new",
        json={
            "alert_type": "fec-contributor",
            "destination_id": dest_id,
            "contributors": [{"last_name": "Smith"}],
        },
    )
    alert_id = resp.json()["alert_id"]

    await db.execute_write(
        "INSERT INTO libfec_filings VALUES ('8001', 'C001', 'PAC A', 'F3')"
    )
    await db.execute_write(
        "INSERT INTO libfec_schedule_a VALUES ('8001', 'John', 'Smith', 'LA', 'CA', 5000.00)"
    )

    await custom_alert_handler(
        ds, {"alert_id": alert_id, "type_slug": "fec-contributor"}
    )

    # Queue drained
    result = await db.execute(
        "SELECT count(*) FROM libfec_alert_queue WHERE status='pending'"
    )
    assert result.rows[0][0] == 0


# --- Regression tests ---


@pytest.mark.asyncio
async def test_trigger_created_on_alert_creation(datasette_with_fec_db):
    ds = datasette_with_fec_db
    db = ds.get_database("fec")

    await db.execute_write("DROP TRIGGER IF EXISTS libfec_filings_alert_trigger")
    result = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='trigger' AND name='libfec_filings_alert_trigger'"
    )
    assert len(result.rows) == 0

    from datasette_alerts.internal_db import InternalDB, NewDestination

    internal_db = InternalDB(ds.get_internal_database())
    dest_id = await internal_db.create_destination(
        NewDestination(notifier="test", label="Test Dest", config={})
    )
    await ds.client.post(
        "/fec/-/api/libfec/alerts/new",
        json={"alert_type": "fec-filing", "destination_id": dest_id},
    )

    result = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='trigger' AND name='libfec_filings_alert_trigger'"
    )
    assert len(result.rows) == 1


@pytest.mark.asyncio
async def test_alert_frequency_is_one_second(datasette_with_fec_db):
    ds = datasette_with_fec_db
    from datasette_alerts.internal_db import InternalDB, NewDestination

    internal_db = InternalDB(ds.get_internal_database())
    dest_id = await internal_db.create_destination(
        NewDestination(notifier="test", label="Test Dest", config={})
    )

    response = await ds.client.post(
        "/fec/-/api/libfec/alerts/new",
        json={"alert_type": "fec-filing", "destination_id": dest_id},
    )
    alert = await internal_db.get_alert_for_check(response.json()["alert_id"])
    assert alert is not None
    assert alert.frequency == "+1 second"


@pytest.mark.asyncio
async def test_cron_schedule_is_one_second(datasette_with_fec_db):
    ds = datasette_with_fec_db
    from datasette_alerts.internal_db import InternalDB, NewDestination

    internal_db = InternalDB(ds.get_internal_database())
    dest_id = await internal_db.create_destination(
        NewDestination(notifier="test", label="Test Dest", config={})
    )

    response = await ds.client.post(
        "/fec/-/api/libfec/alerts/new",
        json={"alert_type": "fec-filing", "destination_id": dest_id},
    )
    alert_id = response.json()["alert_id"]

    result = await ds.get_internal_database().execute(
        "SELECT schedule_config FROM datasette_cron_tasks WHERE name = ?",
        [f"alerts:custom:{alert_id}"],
    )
    assert json.loads(result.rows[0][0])["seconds"] == 1


@pytest.mark.asyncio
async def test_five_filings_all_queued_and_drained(datasette_with_fec_db):
    from datasette_libfec.alert_types import FecFilingAlertType

    ds = datasette_with_fec_db
    db = ds.get_database("fec")

    for i in range(5):
        await db.execute_write(
            f"INSERT INTO libfec_filings VALUES ('F{i}', 'C{i}', 'PAC {i}', 'F3')"
        )

    result = await db.execute(
        "SELECT count(*) FROM libfec_alert_queue WHERE status='pending'"
    )
    assert result.rows[0][0] == 5

    messages = await FecFilingAlertType().check(ds, {}, "fec", None)
    assert len(messages) == 5

    result = await db.execute(
        "SELECT count(*) FROM libfec_alert_queue WHERE status='pending'"
    )
    assert result.rows[0][0] == 0

    messages = await FecFilingAlertType().check(ds, {}, "fec", None)
    assert len(messages) == 0


# --- Custom config shapes ---


@pytest.mark.asyncio
async def test_create_filing_with_committees_stores_config(datasette_with_fec_db):
    ds = datasette_with_fec_db
    from datasette_alerts.internal_db import InternalDB, NewDestination

    internal_db = InternalDB(ds.get_internal_database())
    dest_id = await internal_db.create_destination(
        NewDestination(notifier="test", label="Test", config={})
    )

    response = await ds.client.post(
        "/fec/-/api/libfec/alerts/new",
        json={
            "alert_type": "fec-filing",
            "destination_id": dest_id,
            "committee_ids": ["C00123456", "C00789012"],
            "state_filter": "CA",
        },
    )
    assert response.status_code == 200
    alert = await internal_db.get_alert_for_check(response.json()["alert_id"])
    assert alert is not None
    config = json.loads(alert.custom_config)
    assert config["committee_ids"] == ["C00123456", "C00789012"]
    assert config["state_filter"] == "CA"


@pytest.mark.asyncio
async def test_create_filing_with_races_stores_config(datasette_with_fec_db):
    ds = datasette_with_fec_db
    from datasette_alerts.internal_db import InternalDB, NewDestination

    internal_db = InternalDB(ds.get_internal_database())
    dest_id = await internal_db.create_destination(
        NewDestination(notifier="test", label="Test", config={})
    )

    response = await ds.client.post(
        "/fec/-/api/libfec/alerts/new",
        json={
            "alert_type": "fec-filing",
            "destination_id": dest_id,
            "races": [{"office": "H", "state": "CA", "district": "12", "cycle": 2026}],
        },
    )
    assert response.status_code == 200
    alert = await internal_db.get_alert_for_check(response.json()["alert_id"])
    assert alert is not None
    config = json.loads(alert.custom_config)
    assert len(config["races"]) == 1
    assert config["races"][0]["office"] == "H"
    assert config["races"][0]["state"] == "CA"


@pytest.mark.asyncio
async def test_create_contributor_stores_config(datasette_with_fec_db):
    ds = datasette_with_fec_db
    from datasette_alerts.internal_db import InternalDB, NewDestination

    internal_db = InternalDB(ds.get_internal_database())
    dest_id = await internal_db.create_destination(
        NewDestination(notifier="test", label="Test", config={})
    )

    response = await ds.client.post(
        "/fec/-/api/libfec/alerts/new",
        json={
            "alert_type": "fec-contributor",
            "destination_id": dest_id,
            "contributors": [
                {"first_name": "ELON", "last_name": "MUSK", "city": "", "state": ""},
            ],
        },
    )
    assert response.status_code == 200
    alert = await internal_db.get_alert_for_check(response.json()["alert_id"])
    assert alert is not None
    config = json.loads(alert.custom_config)
    assert config["contributors"][0]["last_name"] == "MUSK"


@pytest.mark.asyncio
async def test_create_empty_filing_stores_empty_config(datasette_with_fec_db):
    """All-filings mode: no committees, races, or state_filter."""
    ds = datasette_with_fec_db
    from datasette_alerts.internal_db import InternalDB, NewDestination

    internal_db = InternalDB(ds.get_internal_database())
    dest_id = await internal_db.create_destination(
        NewDestination(notifier="test", label="Test", config={})
    )

    response = await ds.client.post(
        "/fec/-/api/libfec/alerts/new",
        json={"alert_type": "fec-filing", "destination_id": dest_id},
    )
    assert response.status_code == 200
    alert = await internal_db.get_alert_for_check(response.json()["alert_id"])
    assert alert is not None
    config = json.loads(alert.custom_config)
    assert config == {}


# --- Alert types registered ---


@pytest.mark.asyncio
async def test_alert_types_registered(datasette_with_fec_db):
    from datasette_alerts.handlers import _get_alert_types

    types = _get_alert_types(datasette_with_fec_db)
    assert "fec-filing" in types
    assert "fec-contributor" in types
    assert types["fec-filing"].name == "FEC Filing Alert"
    assert types["fec-contributor"].name == "FEC Contributor Alert"


# --- Detail page ---


@pytest.mark.asyncio
async def test_alert_detail_page_loads(datasette_with_fec_db):
    ds = datasette_with_fec_db
    from datasette_alerts.internal_db import InternalDB, NewDestination

    internal_db = InternalDB(ds.get_internal_database())
    dest_id = await internal_db.create_destination(
        NewDestination(notifier="test", label="Test Dest", config={})
    )

    response = await ds.client.post(
        "/fec/-/api/libfec/alerts/new",
        json={
            "alert_type": "fec-contributor",
            "destination_id": dest_id,
            "contributors": [{"first_name": "ELON", "last_name": "MUSK"}],
        },
    )
    alert_id = response.json()["alert_id"]

    response = await ds.client.get(f"/fec/-/libfec/alerts/{alert_id}")
    assert response.status_code == 200
    assert "Contributor Alert" in response.text
    assert "MUSK" in response.text
    assert alert_id in response.text


@pytest.mark.asyncio
async def test_alert_detail_page_404_for_missing(datasette_with_fec_db):
    response = await datasette_with_fec_db.client.get(
        "/fec/-/libfec/alerts/nonexistent-id"
    )
    assert response.status_code == 404


# --- Pydantic models ---


def test_race_spec_model():
    from datasette_libfec.page_data import RaceSpec

    r = RaceSpec(office="H", state="CA", district="12", cycle=2026)
    assert r.office == "H"
    assert r.cycle == 2026


def test_contributor_criteria_model():
    from datasette_libfec.page_data import ContributorCriteria

    c = ContributorCriteria(last_name="MUSK")
    assert c.last_name == "MUSK"
    assert c.first_name == ""
    assert c.state == ""


def test_filing_alert_config_excludes_defaults():
    from datasette_libfec.page_data import FecFilingAlertConfig

    config = FecFilingAlertConfig(committee_ids=["C001"])
    dumped = config.model_dump(exclude_defaults=True)
    assert dumped == {"committee_ids": ["C001"]}
    assert "races" not in dumped
    assert "state_filter" not in dumped


def test_contributor_alert_config():
    from datasette_libfec.page_data import FecContributorAlertConfig, ContributorCriteria

    config = FecContributorAlertConfig(
        contributors=[ContributorCriteria(first_name="ELON", last_name="MUSK")]
    )
    assert len(config.contributors) == 1
    assert config.contributors[0].last_name == "MUSK"

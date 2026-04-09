"""
Custom AlertType implementations for datasette-alerts.

Trigger+queue pattern. SQLite trigger on libfec_filings INSERT pushes
to libfec_alert_queue. check() drains pending items, marks them done.
"""

import logging

from datasette_alerts.alert_type import AlertType  # type: ignore[import-not-found]
from datasette_alerts.notifier import Message  # type: ignore[import-not-found]

from .page_data import FecContributorAlertConfig, FecFilingAlertConfig

logger = logging.getLogger("datasette_libfec.alerts")


async def ensure_queue_table(db):
    """Apply user DB migrations and ensure trigger exists."""
    from sqlite_utils import Database as SqliteUtilsDatabase

    from .user_migrations import user_migrations

    def migrate(connection):
        sdb = SqliteUtilsDatabase(connection)
        user_migrations.apply(sdb)
        # Always ensure trigger exists (may have been dropped manually)
        connection.executescript(
            """
            CREATE TRIGGER IF NOT EXISTS libfec_filings_alert_trigger
            AFTER INSERT ON libfec_filings
            BEGIN
                INSERT INTO libfec_alert_queue (filing_id, filer_id, filer_name, form_type)
                VALUES (NEW.filing_id, NEW.filer_id, NEW.filer_name, NEW.cover_record_form);
            END;
            """
        )

    await db.execute_write_fn(migrate)


async def _claim_pending(db):
    """Get pending queue items and mark them done. Returns the rows."""
    result = await db.execute(
        "SELECT id, filing_id, filer_id, filer_name, form_type "
        "FROM libfec_alert_queue WHERE status = 'pending' ORDER BY id LIMIT 200"
    )
    if not result.rows:
        return []

    ids = [row[0] for row in result.rows]
    placeholders = ",".join("?" for _ in ids)
    await db.execute_write(
        f"UPDATE libfec_alert_queue SET status = 'done' WHERE id IN ({placeholders})",
        ids,
    )
    return result.rows


class FecFilingAlertType(AlertType):
    slug = "fec-filing"
    name = "FEC Filing Alert"
    description = "Fires when new FEC filings are imported."

    async def check(self, datasette, alert_config, database_name, last_check_at):
        FecFilingAlertConfig(**alert_config)  # validate config
        db = datasette.get_database(database_name)
        await ensure_queue_table(db)

        rows = await _claim_pending(db)
        if not rows:
            return []

        messages = []
        for row in rows:
            _, filing_id, filer_id, filer_name, form_type = row
            messages.append(
                Message(f"New filing FEC-{filing_id} ({form_type}) from {filer_name}")
            )

        logger.info("Drained %d filings from queue", len(messages))
        return messages


class FecContributorAlertType(AlertType):
    slug = "fec-contributor"
    name = "FEC Contributor Alert"
    description = "Fires when watched contributors appear in new FEC filings."

    async def check(self, datasette, alert_config, database_name, last_check_at):
        config = FecContributorAlertConfig(**alert_config)
        db = datasette.get_database(database_name)
        await ensure_queue_table(db)

        if not config.contributors:
            return []

        rows = await _claim_pending(db)
        if not rows:
            return []

        logger.info(
            "Checking %d filings against %d contributor criteria",
            len(rows),
            len(config.contributors),
        )

        messages = []
        for row in rows:
            _, filing_id, filer_id, filer_name, form_type = row

            try:
                sa_result = await db.execute(
                    "SELECT contributor_first_name, contributor_last_name, "
                    "contributor_city, contributor_state, contribution_amount "
                    "FROM libfec_schedule_a WHERE filing_id = ?",
                    [filing_id],
                )
            except Exception:
                continue

            if not sa_result.rows:
                continue

            matches = []
            for sa_row in sa_result.rows:
                sa_first = (sa_row[0] or "").upper()
                sa_last = (sa_row[1] or "").upper()
                sa_city = (sa_row[2] or "").upper()
                sa_state = (sa_row[3] or "").upper()
                sa_amount = sa_row[4]

                for criteria in config.contributors:
                    c_first = criteria.first_name.upper()
                    c_last = criteria.last_name.upper()
                    c_city = criteria.city.upper()
                    c_state = criteria.state.upper()

                    if c_last and c_last not in sa_last:
                        continue
                    if c_first and c_first not in sa_first:
                        continue
                    if c_state and c_state != sa_state:
                        continue
                    if c_city and c_city not in sa_city:
                        continue

                    amount_str = f" (${sa_amount:,.2f})" if sa_amount else ""
                    matches.append(
                        f"{sa_row[0] or ''} {sa_row[1] or ''} from "
                        f"{sa_row[2] or ''}, {sa_row[3] or ''}{amount_str}"
                    )
                    break

            if not matches:
                continue

            if len(matches) == 1:
                messages.append(
                    Message(
                        f"Contributor match in FEC-{filing_id} ({filer_name}): {matches[0]}"
                    )
                )
            else:
                messages.append(
                    Message(
                        f"{len(matches)} contributor matches in FEC-{filing_id} ({filer_name}): "
                        + "; ".join(matches[:5])
                    )
                )

        logger.info("Found %d contributor alerts", len(messages))
        return messages

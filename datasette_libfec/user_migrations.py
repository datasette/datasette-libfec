from sqlite_utils import Database
from sqlite_migrate import Migrations

user_migrations = Migrations("datasette-libfec.user")


@user_migrations()
def m001_alert_queue(db: Database):
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS libfec_alert_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filing_id TEXT NOT NULL,
            filer_id TEXT NOT NULL,
            filer_name TEXT NOT NULL,
            form_type TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TRIGGER IF NOT EXISTS libfec_filings_alert_trigger
        AFTER INSERT ON libfec_filings
        BEGIN
            INSERT INTO libfec_alert_queue (filing_id, filer_id, filer_name, form_type)
            VALUES (NEW.filing_id, NEW.filer_id, NEW.filer_name, NEW.cover_record_form);
        END;
        """
    )

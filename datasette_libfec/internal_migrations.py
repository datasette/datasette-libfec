from sqlite_utils import Database
from sqlite_migrate import Migrations

internal_migrations = Migrations("datasette-libfec.internal")


@internal_migrations()
def m001_rss_config(db: Database):
    db.executescript("""
        CREATE TABLE datasette_libfec_rss_config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            enabled INTEGER NOT NULL DEFAULT 0,
            interval_seconds INTEGER NOT NULL DEFAULT 60,
            cover_only INTEGER NOT NULL DEFAULT 1,
            state_filter TEXT,
            since_duration TEXT NOT NULL DEFAULT '1 day',
            database_name TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        INSERT INTO datasette_libfec_rss_config (id) VALUES (1);
    """)


@internal_migrations()
def m002_rss_progress(db: Database):
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS datasette_libfec_rss_progress (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            phase TEXT NOT NULL DEFAULT 'idle',
            exported_count INTEGER NOT NULL DEFAULT 0,
            total_count INTEGER NOT NULL DEFAULT 0,
            current_filing_id TEXT,
            feed_title TEXT,
            feed_last_modified TEXT,
            error_message TEXT,
            error_code TEXT,
            sync_started_at TEXT,
            sync_finished_at TEXT,
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now'))
        );

        INSERT OR IGNORE INTO datasette_libfec_rss_progress (id) VALUES (1);
        """
    )

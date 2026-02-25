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

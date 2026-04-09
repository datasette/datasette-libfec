from pydantic import BaseModel
from typing import Optional


class RssConfig(BaseModel):
    enabled: bool = False
    interval_seconds: int = 60
    cover_only: bool = True
    state_filter: Optional[str] = None
    since_duration: str = "1 day"
    database_name: Optional[str] = None
    updated_at: Optional[str] = None


class InternalDB:
    def __init__(self, internal_db):
        self.db = internal_db

    async def get_rss_config(self) -> RssConfig:
        def read(conn):
            with conn:
                row = conn.execute(
                    "SELECT enabled, interval_seconds, cover_only, state_filter, "
                    "since_duration, database_name, updated_at "
                    "FROM datasette_libfec_rss_config WHERE id = 1"
                ).fetchone()
                if row is None:
                    return RssConfig()
                return RssConfig(
                    enabled=bool(row[0]),
                    interval_seconds=row[1],
                    cover_only=bool(row[2]),
                    state_filter=row[3],
                    since_duration=row[4],
                    database_name=row[5],
                    updated_at=row[6],
                )

        return await self.db.execute_write_fn(read)

    async def update_rss_config(self, **kwargs) -> RssConfig:
        def write(conn):
            with conn:
                # Build SET clause from provided kwargs
                allowed = {
                    "enabled",
                    "interval_seconds",
                    "cover_only",
                    "state_filter",
                    "since_duration",
                    "database_name",
                }
                updates = {k: v for k, v in kwargs.items() if k in allowed}
                if not updates:
                    return

                # Convert bools to ints for SQLite
                for k, v in updates.items():
                    if isinstance(v, bool):
                        updates[k] = int(v)

                set_parts = [f"{k} = ?" for k in updates]
                set_parts.append("updated_at = CURRENT_TIMESTAMP")
                values = list(updates.values())

                conn.execute(
                    f"UPDATE datasette_libfec_rss_config SET {', '.join(set_parts)} WHERE id = 1",
                    values,
                )

        await self.db.execute_write_fn(write)
        return await self.get_rss_config()

    async def get_rss_progress(self) -> dict:
        def read(conn):
            row = conn.execute(
                "SELECT phase, exported_count, total_count, current_filing_id, "
                "feed_title, feed_last_modified, error_message, error_code, "
                "sync_started_at, sync_finished_at "
                "FROM datasette_libfec_rss_progress WHERE id = 1"
            ).fetchone()
            if row is None:
                return {"phase": "idle"}
            return {
                "phase": row[0],
                "exported_count": row[1],
                "total_count": row[2],
                "current_filing_id": row[3],
                "feed_title": row[4],
                "feed_last_modified": row[5],
                "error_message": row[6],
                "error_code": row[7],
                "sync_started_at": row[8],
                "sync_finished_at": row[9],
            }

        return await self.db.execute_write_fn(read)

    async def update_rss_progress(self, **kwargs) -> None:
        def write(conn):
            allowed = {
                "phase", "exported_count", "total_count", "current_filing_id",
                "feed_title", "feed_last_modified", "error_message", "error_code",
                "sync_started_at", "sync_finished_at",
            }
            updates = {k: v for k, v in kwargs.items() if k in allowed}
            if not updates:
                return
            set_parts = [f"{k} = ?" for k in updates]
            set_parts.append("updated_at = strftime('%Y-%m-%dT%H:%M:%f', 'now')")
            conn.execute(
                f"UPDATE datasette_libfec_rss_progress SET {', '.join(set_parts)} WHERE id = 1",
                list(updates.values()),
            )

        await self.db.execute_write_fn(write)

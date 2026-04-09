from datasette import hookimpl
from datasette.permissions import Action
from datasette_vite import vite_entry
import os

# Import route modules to trigger route registration on the shared router
# pylint: disable=unused-import
from . import (
    routes_rss,
    routes_export,
    routes_search,
    routes_exports,
    routes_pages,
    routes_alerts,
)
from .router import router, LIBFEC_ACCESS_NAME, LIBFEC_WRITE_NAME

_ = (
    routes_rss,
    routes_export,
    routes_search,
    routes_exports,
    routes_pages,
    routes_alerts,
)


@hookimpl
def register_routes():
    return router.routes()


@hookimpl
def extra_template_vars(datasette):
    entry = vite_entry(
        datasette=datasette,
        plugin_package="datasette_libfec",
        vite_dev_path=os.environ.get("DATASETTE_LIBFEC_VITE_PATH"),
    )
    return {"datasette_libfec_vite_entry": entry}


@hookimpl
def register_actions(datasette):
    return [
        Action(
            name=LIBFEC_ACCESS_NAME,
            description="Can access libfec pages (read-only)",
        ),
        Action(
            name=LIBFEC_WRITE_NAME,
            description="Can import FEC data and manage RSS watcher",
        ),
    ]


@hookimpl
def database_actions(datasette, actor, database):
    async def inner():
        if await datasette.allowed(action=LIBFEC_ACCESS_NAME, actor=actor):
            return [
                {
                    "href": datasette.urls.path(f"/{database}/-/libfec/"),
                    "label": "FEC Data",
                }
            ]
        return []

    return inner


@hookimpl
def startup(datasette):
    """Apply internal migrations and initialize RSS watcher."""

    async def inner():
        from sqlite_utils import Database as SqliteUtilsDatabase
        from .internal_migrations import internal_migrations
        from .rss_watcher import rss_watcher

        # Apply internal database migrations
        def migrate(connection):
            db = SqliteUtilsDatabase(connection)
            internal_migrations.apply(db)

        await datasette.get_internal_database().execute_write_fn(migrate)

        rss_watcher.set_datasette(datasette)

        # Ensure alert queue table + trigger exist in DBs that have libfec_filings
        from .alert_types import ensure_queue_table

        for db_name, db in datasette.databases.items():
            if db_name.startswith("_") or not db.is_mutable:
                continue
            try:
                result = await db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='libfec_filings'"
                )
                if result.rows:
                    await ensure_queue_table(db)
            except Exception:
                pass

    return inner


@hookimpl
def datasette_alerts_register_alert_types(datasette):
    """Register FEC alert types with datasette-alerts."""
    from .alert_types import FecFilingAlertType, FecContributorAlertType

    return [FecFilingAlertType(), FecContributorAlertType()]


@hookimpl
def shutdown(datasette):
    """Stop RSS watcher on shutdown."""

    async def inner():
        from .rss_watcher import rss_watcher

        if rss_watcher.is_running():
            await rss_watcher.stop()

    return inner


try:
    from datasette_sidebar.hookspecs import SidebarApp  # type: ignore[import-not-found]  # ty: ignore[unresolved-import]

    @hookimpl
    def datasette_sidebar_apps(datasette):
        return [
            SidebarApp(
                label="FEC Data",
                description="Work with federal campaign finance data via libfec",
                href=lambda db: f"/{db}/-/libfec" if db else "/",
                icon='<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-piggy-bank-fill" viewBox="0 0 16 16"><path d="M7.964 1.527c-2.977 0-5.571 1.704-6.32 4.125h-.55A1 1 0 0 0 .11 6.824l.254 1.46a1.5 1.5 0 0 0 1.478 1.243h.263c.3.513.688.978 1.145 1.382l-.729 2.477a.5.5 0 0 0 .48.641h2a.5.5 0 0 0 .471-.332l.482-1.351c.635.173 1.31.267 2.011.267.707 0 1.388-.095 2.028-.272l.543 1.372a.5.5 0 0 0 .465.316h2a.5.5 0 0 0 .478-.645l-.761-2.506C13.81 9.895 14.5 8.559 14.5 7.069q0-.218-.02-.431c.261-.11.508-.266.705-.444.315.306.815.306.815-.417 0 .223-.5.223-.461-.026a1 1 0 0 0 .09-.255.7.7 0 0 0-.202-.645.58.58 0 0 0-.707-.098.74.74 0 0 0-.375.562c-.024.243.082.48.32.654a2 2 0 0 1-.259.153c-.534-2.664-3.284-4.595-6.442-4.595m7.173 3.876a.6.6 0 0 1-.098.21l-.044-.025c-.146-.09-.157-.175-.152-.223a.24.24 0 0 1 .117-.173c.049-.027.08-.021.113.012a.2.2 0 0 1 .064.199m-8.999-.65a.5.5 0 1 1-.276-.96A7.6 7.6 0 0 1 7.964 3.5c.763 0 1.497.11 2.18.315a.5.5 0 1 1-.287.958A6.6 6.6 0 0 0 7.964 4.5c-.64 0-1.255.09-1.826.254ZM5 6.25a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0"/></svg>',
                color="green",
            ),
        ]

except ImportError:
    pass

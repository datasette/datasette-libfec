from datasette import hookimpl
from datasette.permissions import Action
from datasette_vite import vite_entry
import os

# Import route modules to trigger route registration on the shared router
# pylint: disable=unused-import
from . import routes_rss, routes_export, routes_search, routes_exports, routes_pages
from .router import router, LIBFEC_ACCESS_NAME, LIBFEC_WRITE_NAME

_ = routes_rss, routes_export, routes_search, routes_exports, routes_pages


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

        # Give the watcher a reference to datasette for config access
        rss_watcher.set_datasette(datasette)

    return inner


@hookimpl
def shutdown(datasette):
    """Stop RSS watcher on shutdown."""

    async def inner():
        from .rss_watcher import rss_watcher

        if rss_watcher.is_running():
            await rss_watcher.stop()

    return inner

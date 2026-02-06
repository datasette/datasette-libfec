"""Database utility for libfec plugin."""


def get_libfec_database(datasette):
    """
    Get the database to use for libfec data.

    Checks plugin config for 'libfec_database_name' setting.
    If set, returns that database. Otherwise falls back to datasette.get_database()
    (first writable database).

    Config example (in datasette.yaml):
        plugins:
          datasette-libfec:
            libfec_database_name: fec
    """
    config = datasette.plugin_config("datasette-libfec") or {}
    db_name = config.get("libfec_database_name")

    if db_name:
        return datasette.databases[db_name]

    return datasette.get_database()

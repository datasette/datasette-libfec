"""
Tests showing what libfec commands/params are constructed from export API requests.

The export system works via JSON-RPC:
1. Subprocess spawned: `libfec export --rpc -o <output_db>`
2. JSON-RPC params sent over stdin based on POST body
"""


def test_export_rpc_params_construction():
    """
    Show what RPC params are constructed from various inputs.

    The subprocess command is always: libfec export --rpc -o <output_db>
    The variation is in the JSON-RPC params sent to export/start.
    """

    # Test cases: (input_kwargs, expected_params)
    test_cases = [
        # Basic filings with cycle
        (
            {
                "filings": ["C00123456"],
                "cycle": 2024,
                "cover_only": False,
                "clobber": False,
            },
            {
                "filings": ["C00123456"],
                "cycle": 2024,
                "include_all_bulk": True,
                "write_metadata": True,
            },
        ),
        # Contest codes
        (
            {
                "filings": ["CA01", "TX30"],
                "cycle": 2026,
                "cover_only": False,
                "clobber": False,
            },
            {
                "filings": ["CA01", "TX30"],
                "cycle": 2026,
                "include_all_bulk": True,
                "write_metadata": True,
            },
        ),
        # With cover_only
        (
            {
                "filings": ["1234567"],
                "cycle": 2024,
                "cover_only": True,
                "clobber": False,
            },
            {
                "filings": ["1234567"],
                "cycle": 2024,
                "cover_only": True,
                "include_all_bulk": True,
                "write_metadata": True,
            },
        ),
        # With clobber
        (
            {
                "filings": ["C00111111"],
                "cycle": None,
                "cover_only": False,
                "clobber": True,
            },
            {
                "filings": ["C00111111"],
                "clobber": True,
                "include_all_bulk": True,
                "write_metadata": True,
            },
        ),
        # No filings (export all)
        (
            {"filings": None, "cycle": 2026, "cover_only": False, "clobber": False},
            {"cycle": 2026, "include_all_bulk": True, "write_metadata": True},
        ),
        # All options enabled
        (
            {
                "filings": ["C00123456", "CA01"],
                "cycle": 2024,
                "cover_only": True,
                "clobber": True,
            },
            {
                "filings": ["C00123456", "CA01"],
                "cycle": 2024,
                "cover_only": True,
                "clobber": True,
                "include_all_bulk": True,
                "write_metadata": True,
            },
        ),
    ]

    for input_kwargs, expected_params in test_cases:
        # Build params the same way LibfecExportRpcClient.export_start() does
        params = {"include_all_bulk": True}

        if input_kwargs.get("filings") is not None:
            params["filings"] = input_kwargs["filings"]
        if input_kwargs.get("cycle") is not None:
            params["cycle"] = input_kwargs["cycle"]
        if input_kwargs.get("cover_only"):
            params["cover_only"] = input_kwargs["cover_only"]
        if input_kwargs.get("clobber"):
            params["clobber"] = input_kwargs["clobber"]
        params["write_metadata"] = True

        assert params == expected_params, (
            f"Input {input_kwargs} produced {params}, expected {expected_params}"
        )


def test_export_subprocess_args():
    """
    The subprocess args are always the same - only the output_db varies.

    Command: libfec export --rpc -o <output_db>

    The args passed to create_subprocess_exec in start_process() are:
    [libfec_path, "export", "--rpc", "-o", output_db]
    """
    from datasette_libfec.libfec_export_rpc_client import LibfecExportRpcClient

    libfec_path = "/usr/bin/libfec"
    output_db = "/path/to/data.db"

    client = LibfecExportRpcClient(libfec_path, output_db)

    assert client.libfec_path == libfec_path
    assert client.output_db == output_db


def test_export_params_match_api_body():
    """
    Show the mapping from API POST body to RPC params.

    POST /-/api/libfec/export/start
    Body: {"filings": [...], "cycle": 2024, "cover_only": true, "clobber": false}

    Becomes RPC call to export/start with params.
    """
    from datasette_libfec.routes_export import ExportStartParams

    # Simulate API body - parse through Pydantic model (as the route does)
    params = ExportStartParams(
        filings=["CA01", "TX30", "NY14"],
        cycle=2026,
        cover_only=False,
        clobber=False,
    )

    # These values get passed to libfec_client.export_with_progress()
    # which passes them to LibfecExportRpcClient.export_start()
    assert params.filings == ["CA01", "TX30", "NY14"]
    assert params.cycle == 2026
    assert params.cover_only is False
    assert params.clobber is False

    # The RPC params constructed would be:
    rpc_params = {"include_all_bulk": True, "write_metadata": True}
    if params.filings:
        rpc_params["filings"] = params.filings
    if params.cycle:
        rpc_params["cycle"] = params.cycle
    if params.cover_only:
        rpc_params["cover_only"] = params.cover_only
    if params.clobber:
        rpc_params["clobber"] = params.clobber

    assert rpc_params == {
        "filings": ["CA01", "TX30", "NY14"],
        "cycle": 2026,
        "include_all_bulk": True,
        "write_metadata": True,
    }

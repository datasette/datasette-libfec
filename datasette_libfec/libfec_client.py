from __future__ import annotations

import os
import shutil
import sys
import asyncio
import time
from pathlib import Path
from typing import Optional, TYPE_CHECKING, List

if TYPE_CHECKING:
    from .libfec_rpc_client import LibfecRpcClient
    from .libfec_export_rpc_client import LibfecExportRpcClient


class LibfecClient:
    def __init__(self):
        bin_path = os.environ.get("DATASETTE_LIBFEC_BIN_PATH")
        if bin_path:
            self.libfec_path = Path(bin_path)
        else:
            # Try the Python executable's directory first, then fall back to PATH
            candidate = Path(sys.executable).parent / "libfec"
            if candidate.exists():
                self.libfec_path = candidate
            else:
                found = shutil.which("libfec")
                if found:
                    self.libfec_path = Path(found)
                else:
                    self.libfec_path = candidate

    async def _run_libfec_command_async(self, args):
        """Async command execution - doesn't block event loop"""
        print(f"Running async: {args}")
        process = await asyncio.create_subprocess_exec(
            str(self.libfec_path),
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"libfec error: {stderr.decode()}")
        return stdout.decode()

    async def export(self, committee_id: str, cycle: int, output_db: str) -> str:
        """Export FEC data (async - won't block event loop)"""
        return await self._run_libfec_command_async(
            ["export", committee_id, "--election", str(cycle), "-o", output_db]
        )

    async def rss_watch(
        self, output_db: str, state: Optional[str] = None, cover_only: bool = True
    ):
        """Run single RSS watch command (async - won't block event loop)"""
        args = ["rss", "--since", "1 day"]
        if cover_only:
            args.append("--cover-only")
        args.extend(["-x", output_db])
        if state:
            args.extend(["--state", state])
        return await self._run_libfec_command_async(args)

    async def rss_watch_with_progress(
        self,
        output_db: str,
        state: Optional[str],
        cover_only: bool,
        watcher_state,  # RssRuntimeState or similar with same attributes
        since: str = "1 day",
    ) -> None:
        """
        Run RSS watch using RPC mode with real-time progress tracking.

        Updates watcher_state with progress information from RPC notifications.
        """
        from .libfec_rpc_client import LibfecRpcClient, RpcError

        # Reset progress state
        watcher_state.phase = "idle"
        watcher_state.exported_count = 0
        watcher_state.total_count = 0
        watcher_state.current_filing_id = None
        watcher_state.feed_title = None
        watcher_state.feed_last_modified = None
        watcher_state.error_message = None
        watcher_state.error_code = None
        watcher_state.error_data = None
        watcher_state.sync_start_time = time.time()

        # Use RPC mode
        rpc_client = LibfecRpcClient(str(self.libfec_path))
        watcher_state.rpc_client = rpc_client

        def on_progress(notification: dict) -> None:
            """Progress callback - updates watcher_state from RPC notifications"""
            method = notification.get("method")
            params = notification.get("params", {})

            if method == "sync/progress":
                watcher_state.phase = params.get("phase", "idle")
                watcher_state.exported_count = params.get("exported_count", 0)
                watcher_state.total_count = params.get("total_count", 0)
                watcher_state.current_filing_id = params.get("current_filing_id")
                watcher_state.feed_title = params.get("feed_title")
                watcher_state.feed_last_modified = params.get("feed_last_modified")

                # Update currently_syncing based on phase
                watcher_state.currently_syncing = watcher_state.phase in (
                    "fetching",
                    "exporting",
                )

        try:
            watcher_state.currently_syncing = True
            await rpc_client.start_process()

            result = await rpc_client.sync_start(
                since=since,
                state=state,
                cover_only=cover_only,
                output_path=output_db,
                progress_callback=on_progress,
                write_metadata=True,
            )

            # Mark as complete
            watcher_state.phase = "complete"
            print(f"RSS sync complete: {result}")

        except RpcError as e:
            watcher_state.phase = "error"
            watcher_state.error_message = e.message
            watcher_state.error_code = e.code
            watcher_state.error_data = str(e.data) if e.data else None
            print(f"RPC error: {e}, data: {e.data}")

        except asyncio.TimeoutError:
            watcher_state.phase = "error"
            watcher_state.error_message = "Sync timed out after 5 minutes"
            print("RSS sync timeout")

        except Exception as e:
            watcher_state.phase = "error"
            watcher_state.error_message = str(e)
            print(f"RSS sync error: {e}")

        finally:
            watcher_state.currently_syncing = False
            try:
                await rpc_client.shutdown()
            except Exception as e:
                print(f"Error shutting down RPC client: {e}")
                try:
                    await rpc_client.terminate()
                except Exception:
                    pass
            watcher_state.rpc_client = None

    async def export_with_progress(
        self,
        output_db: str,
        filings: Optional[List[str]],
        cycle: Optional[int],
        cover_only: bool,
        clobber: bool,
        export_state: ExportState,
    ) -> None:
        """
        Run export using RPC mode with real-time progress tracking.

        Updates export_state with progress information from RPC notifications.
        """
        from .libfec_export_rpc_client import LibfecExportRpcClient, RpcError

        # Reset progress state
        export_state.phase = "idle"
        export_state.completed = 0
        export_state.total = 0
        export_state.current_filing_id = None
        export_state.current = None
        export_state.total_exported = None
        export_state.warnings = []
        export_state.error_message = None
        export_state.export_start_time = time.time()

        # Use RPC mode
        rpc_client = LibfecExportRpcClient(str(self.libfec_path), output_db)
        export_state.rpc_client = rpc_client

        def on_progress(notification: dict) -> None:
            """Progress callback - updates export_state from RPC notifications"""
            method = notification.get("method")
            params = notification.get("params", {})

            if method == "export/progress":
                export_state.phase = params.get("phase", "idle")
                export_state.completed = params.get("completed", 0)
                export_state.total = params.get("total", 0)
                export_state.current_filing_id = params.get("current_filing_id")
                export_state.current = params.get("current")
                export_state.total_exported = params.get("total_exported")
                export_state.warnings = params.get("warnings", [])
                if params.get("error_message"):
                    export_state.error_message = params["error_message"]

        try:
            export_state.running = True
            await rpc_client.start_process()

            result = await rpc_client.export_start(
                filings=filings,
                cycle=cycle,
                cover_only=cover_only,
                clobber=clobber,
                progress_callback=on_progress,
            )

            # Mark as complete
            export_state.phase = "complete"
            print(f"Export complete: {result}")

        except RpcError as e:
            export_state.phase = "error"
            export_state.error_message = str(e.data) if e.data else e.message
            print(f"RPC error: {e}")

        except asyncio.TimeoutError:
            export_state.phase = "error"
            export_state.error_message = "Export timed out after 5 minutes"
            print("Export timeout")

        except Exception as e:
            export_state.phase = "error"
            export_state.error_message = str(e)
            print(f"Export error: {e}")

        finally:
            export_state.running = False
            try:
                await rpc_client.shutdown()
            except Exception as e:
                print(f"Error shutting down RPC client: {e}")
                try:
                    await rpc_client.terminate()
                except Exception:
                    pass
            export_state.rpc_client = None


# RSS watcher state
class RssWatcherState:
    def __init__(self):
        self.task: Optional[asyncio.Task] = None
        self.running = False
        self.interval = 60
        self.state: Optional[str] = None
        self.cover_only = True
        self.output_db: Optional[str] = None
        self.next_sync_time: Optional[float] = None
        self.currently_syncing = False

        # Progress tracking fields for RPC mode
        self.phase: str = "idle"  # idle|fetching|exporting|complete|canceled|error
        self.exported_count: int = 0
        self.total_count: int = 0
        self.current_filing_id: Optional[str] = None
        self.feed_title: Optional[str] = None
        self.feed_last_modified: Optional[str] = None
        self.error_message: Optional[str] = None
        self.error_code: Optional[int] = None
        self.error_data: Optional[str] = None
        self.sync_start_time: Optional[float] = None
        self.rpc_client: Optional["LibfecRpcClient"] = None


# Export state
class ExportState:
    def __init__(self):
        self.export_id: Optional[str] = None
        self.running = False

        # Progress tracking fields for export RPC mode
        self.phase: str = (
            "idle"  # idle|sourcing|downloading_bulk|exporting|complete|canceled|error
        )
        self.completed: int = 0
        self.total: int = 0
        self.current_filing_id: Optional[str] = None
        self.current: Optional[str] = None  # For bulk download phase
        self.total_exported: Optional[int] = None
        self.warnings: List[str] = []
        self.error_message: Optional[str] = None
        self.export_start_time: Optional[float] = None
        self.rpc_client: Optional["LibfecExportRpcClient"] = None

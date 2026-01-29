"""
JSON-RPC 2.0 client for libfec export --rpc mode.

Manages libfec export subprocess lifecycle using JSONL protocol over stdin/stdout.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Optional, List

logger = logging.getLogger(__name__)


class RpcError(Exception):
    """JSON-RPC error response"""
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"RPC Error {code}: {message}")


class LibfecExportRpcClient:
    """
    Manages libfec export --rpc process lifecycle.

    Uses JSON-RPC 2.0 over JSONL protocol:
    - Requests/responses: JSON objects with id field
    - Notifications: JSON objects without id field
    """

    def __init__(self, libfec_path: str, output_db: str):
        self.libfec_path = libfec_path
        self.output_db = output_db
        self.process: Optional[asyncio.subprocess.Process] = None
        self.request_id = 0
        self.pending_requests: dict[int, asyncio.Future] = {}
        self.listen_task: Optional[asyncio.Task] = None
        self.progress_callback: Optional[Callable] = None
        self.completion_future: Optional[asyncio.Future] = None
        self.ready_future: Optional[asyncio.Future] = None

    async def start_process(self) -> None:
        """Spawn libfec export --rpc subprocess"""
        if self.process is not None:
            raise RuntimeError("Process already started")

        logger.info(f"Starting libfec export --rpc: {self.libfec_path} -o {self.output_db}")

        # Create ready future to wait for ready notification
        self.ready_future = asyncio.Future()

        self.process = await asyncio.create_subprocess_exec(
            self.libfec_path,
            "export",
            "--rpc",
            "-o",
            self.output_db,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Start listening for messages
        self.listen_task = asyncio.create_task(self._listen_for_messages())

        # Wait for ready notification with timeout
        try:
            await asyncio.wait_for(self.ready_future, timeout=5.0)
            logger.info("RPC server ready")
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for ready notification")
            await self.terminate()
            raise RuntimeError("libfec process did not send ready notification")

    async def _listen_for_messages(self) -> None:
        """
        Read stdout line-by-line (JSONL protocol).
        Route responses to waiting futures by request ID.
        Route notifications to progress_callback.
        """
        if not self.process or not self.process.stdout:
            return

        try:
            while True:
                line = await self.process.stdout.readline()
                if not line:
                    # EOF - process died
                    logger.error("libfec process stdout EOF (process crashed?)")
                    # Cancel all pending requests
                    for future in self.pending_requests.values():
                        if not future.done():
                            future.set_exception(
                                RuntimeError("libfec process terminated unexpectedly")
                            )
                    # Cancel completion future if waiting
                    if self.completion_future and not self.completion_future.done():
                        self.completion_future.set_exception(
                            RuntimeError("libfec process terminated before export completed")
                        )
                    break

                try:
                    msg = json.loads(line.decode())
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from libfec: {line!r} - {e}")
                    continue

                # Check if response or notification
                if "id" in msg:
                    # Response - match to pending request
                    request_id = msg["id"]
                    future = self.pending_requests.get(request_id)

                    if future and not future.done():
                        if "error" in msg:
                            err = msg["error"]
                            future.set_exception(
                                RpcError(
                                    err.get("code", -1),
                                    err.get("message", "Unknown error"),
                                    err.get("data")
                                )
                            )
                        elif "result" in msg:
                            future.set_result(msg["result"])
                        else:
                            future.set_exception(
                                RuntimeError(f"Invalid RPC response: {msg}")
                            )
                else:
                    # Notification - deliver to callback
                    if "method" in msg:
                        # Check if this is a ready notification
                        if msg.get("method") == "ready":
                            if self.ready_future and not self.ready_future.done():
                                self.ready_future.set_result(msg.get("params", {}))

                        # Check if this is a completion notification
                        elif msg.get("method") == "export/progress":
                            params = msg.get("params", {})
                            phase = params.get("phase")

                            # Resolve completion future on terminal phases
                            if phase in ("complete", "canceled", "error"):
                                if self.completion_future and not self.completion_future.done():
                                    self.completion_future.set_result(params)

                        # Deliver to callback
                        if self.progress_callback:
                            try:
                                self.progress_callback(msg)
                            except Exception as e:
                                logger.error(f"Progress callback error: {e}", exc_info=True)

        except asyncio.CancelledError:
            logger.debug("Message listener cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in message listener: {e}", exc_info=True)

    async def send_request(
        self,
        method: str,
        params: Optional[dict] = None,
        timeout: float = 5.0
    ) -> Any:
        """
        Send JSON-RPC request via stdin, wait for response.

        Args:
            method: RPC method name
            params: Method parameters
            timeout: Response timeout in seconds

        Returns:
            Result from response

        Raises:
            RpcError: On JSON-RPC error response
            TimeoutError: On timeout
            RuntimeError: On process errors
        """
        if not self.process or not self.process.stdin:
            raise RuntimeError("Process not started")

        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
        }
        if params is not None:
            request["params"] = params

        # Create future for response
        future: asyncio.Future = asyncio.Future()
        self.pending_requests[self.request_id] = future

        try:
            # Send request
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json.encode())
            await self.process.stdin.drain()

            logger.debug(f"Sent RPC request: {method} (id={self.request_id})")

            # Wait for response with timeout
            result = await asyncio.wait_for(future, timeout=timeout)
            return result

        except asyncio.TimeoutError:
            logger.error(f"RPC request timeout: {method}")
            raise TimeoutError(f"RPC request timed out: {method}")
        finally:
            # Clean up pending request
            self.pending_requests.pop(self.request_id, None)

    async def export_start(
        self,
        filings: Optional[List[str]],
        cycle: Optional[int],
        cover_only: bool,
        clobber: bool,
        progress_callback: Callable,
        write_metadata: bool = True,
    ) -> dict:
        """
        Start export operation with progress tracking.

        Args:
            filings: Filing IDs, committee IDs, or candidate IDs to export
            cycle: Election cycle year (e.g., 2024)
            cover_only: Only export cover pages
            clobber: Overwrite existing database content
            progress_callback: Called with export/progress notifications
            write_metadata: Whether to write metadata tables in output database

        Returns:
            Final export result

        Raises:
            RpcError: On export errors
            TimeoutError: On export timeout (300s)
        """
        self.progress_callback = progress_callback

        params = {}
        if filings is not None:
            params["filings"] = filings
        if cycle is not None:
            params["cycle"] = cycle
        if cover_only:
            params["cover_only"] = cover_only
        if clobber:
            params["clobber"] = clobber
        if write_metadata:
            params["write_metadata"] = write_metadata
        
        # Create completion future to wait for final notification
        self.completion_future = asyncio.Future()

        # Send export/start request (just starts the export)
        logger.info(f"Sending export/start with params: {params}")
        start_result = await self.send_request("export/start", params, timeout=30.0)
        logger.info(f"Export started: {start_result}")

        # Keep sending export/status requests to keep the RPC server processing exports
        async def poll_status():
            while self.completion_future and not self.completion_future.done():
                try:
                    await asyncio.sleep(0.5)  # Poll every 500ms
                    if self.completion_future and not self.completion_future.done():
                        await self.send_request("export/status", timeout=5.0)
                except Exception as e:
                    logger.debug(f"Status poll error (expected on completion): {e}")
                    break

        # Start status polling task
        poll_task = asyncio.create_task(poll_status())

        # Wait for completion notification with 300s timeout
        try:
            completion_result = await asyncio.wait_for(self.completion_future, timeout=300.0)

            # Check if export completed with error
            if completion_result.get("phase") == "error":
                error_msg = completion_result.get("error_message", "Unknown error")
                error_code = completion_result.get("error_code", -1)
                error_data = completion_result.get("error_data")
                raise RpcError(error_code, error_msg, error_data)

            return completion_result
        except asyncio.TimeoutError:
            logger.error("Export did not complete within 300 seconds")
            raise TimeoutError("Export timed out after 5 minutes")
        finally:
            # Cancel polling task
            poll_task.cancel()
            try:
                await poll_task
            except asyncio.CancelledError:
                pass

    async def export_cancel(self) -> dict:
        """Cancel in-progress export"""
        return await self.send_request("export/cancel", timeout=5.0)

    async def shutdown(self) -> None:
        """Gracefully shutdown RPC process"""
        if not self.process:
            return

        try:
            await self.send_request("shutdown", timeout=2.0)
        except Exception as e:
            logger.warning(f"Shutdown request failed: {e}")

        # Wait for process to exit
        try:
            await asyncio.wait_for(self.process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Process did not exit after shutdown, terminating")
            await self.terminate()

        # Cancel listener task
        if self.listen_task and not self.listen_task.done():
            self.listen_task.cancel()
            try:
                await self.listen_task
            except asyncio.CancelledError:
                pass

        self.process = None

    async def terminate(self) -> None:
        """Force kill the process (for cleanup)"""
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                logger.warning("Process did not terminate, killing")
                self.process.kill()
                await self.process.wait()
            except Exception as e:
                logger.error(f"Error terminating process: {e}")

        if self.listen_task and not self.listen_task.done():
            self.listen_task.cancel()
            try:
                await self.listen_task
            except asyncio.CancelledError:
                pass

        self.process = None

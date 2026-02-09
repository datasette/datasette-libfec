"""
JSON-RPC 2.0 client for libfec search --rpc mode.

Manages libfec search subprocess lifecycle using JSONL protocol over stdin/stdout.
"""

import asyncio
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RpcError(Exception):
    """JSON-RPC error response"""

    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"RPC Error {code}: {message}")


class LibfecSearchRpcClient:
    """
    Manages libfec search --rpc process lifecycle.

    Uses JSON-RPC 2.0 over JSONL protocol:
    - Requests/responses: JSON objects with id field
    - Notifications: JSON objects without id field
    """

    def __init__(self, libfec_path: str, cycle: int = 2026):
        self.libfec_path = libfec_path
        self.cycle = cycle
        self.process: Optional[asyncio.subprocess.Process] = None
        self.request_id = 0
        self.pending_requests: dict[int, asyncio.Future] = {}
        self.listen_task: Optional[asyncio.Task] = None
        self.ready_future: Optional[asyncio.Future] = None

    async def start_process(self) -> None:
        """Spawn libfec search --rpc subprocess"""
        if self.process is not None:
            raise RuntimeError("Process already started")

        logger.info(
            f"Starting libfec search --rpc: {self.libfec_path} --cycle {self.cycle}"
        )

        # Create ready future to wait for ready notification
        self.ready_future = asyncio.Future()

        self.process = await asyncio.create_subprocess_exec(
            self.libfec_path,
            "search",
            "--rpc",
            "--cycle",
            str(self.cycle),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Start listening for messages
        self.listen_task = asyncio.create_task(self._listen_for_messages())

        # Wait for ready notification with timeout
        try:
            await asyncio.wait_for(self.ready_future, timeout=5.0)
            logger.info("Search RPC server ready")
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for ready notification")
            await self.terminate()
            raise RuntimeError("libfec search process did not send ready notification")

    async def _listen_for_messages(self) -> None:
        """
        Read stdout line-by-line (JSONL protocol).
        Route responses to waiting futures by request ID.
        """
        if not self.process or not self.process.stdout:
            return

        try:
            while True:
                line = await self.process.stdout.readline()
                if not line:
                    # EOF - process died
                    logger.error("libfec search process stdout EOF (process crashed?)")
                    # Cancel all pending requests
                    for future in self.pending_requests.values():
                        if not future.done():
                            future.set_exception(
                                RuntimeError(
                                    "libfec search process terminated unexpectedly"
                                )
                            )
                    break

                try:
                    msg = json.loads(line.decode())
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from libfec search: {line!r} - {e}")
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
                                    err.get("data"),
                                )
                            )
                        elif "result" in msg:
                            future.set_result(msg["result"])
                        else:
                            future.set_exception(
                                RuntimeError(f"Invalid RPC response: {msg}")
                            )
                else:
                    # Notification
                    if "method" in msg:
                        # Check if this is a ready notification
                        if msg.get("method") == "ready":
                            if self.ready_future and not self.ready_future.done():
                                self.ready_future.set_result(msg.get("params", {}))

        except asyncio.CancelledError:
            logger.debug("Message listener cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in message listener: {e}", exc_info=True)

    async def send_request(
        self, method: str, params: Optional[dict] = None, timeout: float = 10.0
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

            logger.debug(f"Sent search RPC request: {method} (id={self.request_id})")

            # Wait for response with timeout
            result = await asyncio.wait_for(future, timeout=timeout)
            return result

        except asyncio.TimeoutError:
            logger.error(f"Search RPC request timeout: {method}")
            raise TimeoutError(f"Search RPC request timed out: {method}")
        finally:
            # Clean up pending request
            self.pending_requests.pop(self.request_id, None)

    async def search_query(
        self, query: str, cycle: Optional[int] = None, limit: int = 100
    ) -> dict:
        """
        Search for candidates and committees.

        Args:
            query: Search query string
            cycle: Election cycle year (uses default if omitted)
            limit: Max results per category

        Returns:
            Search results with candidates and committees
        """
        params = {"query": query, "limit": limit}
        if cycle is not None:
            params["cycle"] = cycle

        return await self.send_request("search/query", params)

    async def get_candidate(
        self, candidate_id: str, cycle: Optional[int] = None
    ) -> dict:
        """
        Get detailed candidate information.

        Args:
            candidate_id: FEC candidate ID
            cycle: Election cycle year

        Returns:
            Candidate details
        """
        params = {"candidate_id": candidate_id}
        if cycle is not None:
            params["cycle"] = cycle

        return await self.send_request("search/candidate", params)

    async def get_committee(
        self, committee_id: str, cycle: Optional[int] = None
    ) -> dict:
        """
        Get detailed committee information.

        Args:
            committee_id: FEC committee ID
            cycle: Election cycle year

        Returns:
            Committee details
        """
        params = {"committee_id": committee_id}
        if cycle is not None:
            params["cycle"] = cycle

        return await self.send_request("search/committee", params)

    async def shutdown(self) -> None:
        """Gracefully shutdown search RPC process"""
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

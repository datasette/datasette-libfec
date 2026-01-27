import os
import sys
import asyncio
import subprocess
from pathlib import Path
from typing import Optional


class LibfecClient:
    def __init__(self):
        bin_path = os.environ.get("DATASETTE_LIBFEC_BIN_PATH")
        if bin_path:
            self.libfec_path = Path(bin_path)
        else:
            self.libfec_path = Path(sys.executable).parent / 'libfec'

    def _run_libfec_command(self, args):
        """Synchronous command execution"""
        print(args)
        result = subprocess.run([str(self.libfec_path)] + args, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"libfec error: {result.stderr}")
        return result.stdout

    async def _run_libfec_command_async(self, args):
        """Async command execution - doesn't block event loop"""
        print(f"Running async: {args}")
        process = await asyncio.create_subprocess_exec(
            str(self.libfec_path),
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"libfec error: {stderr.decode()}")
        return stdout.decode()

    async def export(self, committee_id: str, cycle: int, output_db: str) -> str:
        """Export FEC data (async - won't block event loop)"""
        return await self._run_libfec_command_async([
            'export', committee_id,
            '--election', str(cycle),
            '--form-type', 'F3',
            #'--form-type', 'F1',
            '-o', output_db
          ])

    async def rss_watch(self, output_db: str, state: Optional[str] = None, cover_only: bool = True):
        """Run single RSS watch command (async - won't block event loop)"""
        args = ['rss', '--since', '1 day']
        if cover_only:
            args.append('--cover-only')
        args.extend(['-x', output_db])
        if state:
            args.extend(['--state', state])
        return await self._run_libfec_command_async(args)


# RSS watcher state
class RssWatcherState:
    def __init__(self):
        self.task: Optional[asyncio.Task] = None
        self.running = False
        self.interval = 60
        self.state: Optional[str] = None
        self.cover_only = True
        self.output_db: Optional[str] = None

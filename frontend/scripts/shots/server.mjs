// Boot/teardown of the throwaway datasette the shots drive.
//
// The data comes from a pre-built FEC fixture .db, copied to a mutable /tmp copy
// so datasette opens it writable (the plugin's startup hook adds its alert-queue
// table) without touching the committed fixture. The instance permission gates
// every libfec page checks are opened globally.
import { mkdir, copyFile, access } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { APP, BASE, SECRET, FIXTURE_DB, DATA_DIR, DATA_DB, PORT } from './config.mjs';

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Is something already answering on our port? (status < 500 = "alive").
export async function reachable() {
  try {
    const ac = new AbortController();
    const t = setTimeout(() => ac.abort(), 500);
    const r = await fetch(APP, { redirect: 'manual', signal: ac.signal });
    clearTimeout(t);
    return r.status < 500;
  } catch {
    return false;
  }
}

// Fresh mutable copy of the fixture db.
async function setupDataDb() {
  try {
    await access(FIXTURE_DB);
  } catch {
    throw new Error(`fixture db missing: ${FIXTURE_DB}\nRun \`just shots-fixture\` first.`);
  }
  await mkdir(DATA_DIR, { recursive: true });
  await copyFile(FIXTURE_DB, DATA_DB);
}

export async function startServer() {
  await setupDataDb();
  // Refuse to start over an already-listening server rather than screenshot
  // whatever is there — the poll can't tell a stale server from ours.
  if (await reachable()) {
    throw new Error(
      `something is already serving on ${BASE}. Stop it (or set SHOTS_PORT) and retry.`
    );
  }
  // `detached: true` puts datasette in its own process group. datasette is a
  // grandchild of `uv run`, so we kill the whole group in stopServer.
  const child = spawn(
    'uv',
    [
      'run',
      'datasette',
      DATA_DB,
      '--secret',
      SECRET,
      // Open every gate the UI checks so all features render: read access, the
      // write gate (import + RSS pages and their index cards), and alerts access
      // (datasette-alerts is a dependency, so the Alerts page resolves).
      '-s',
      'permissions.datasette_libfec_access',
      'true',
      '-s',
      'permissions.datasette_libfec_write',
      'true',
      '-s',
      'permissions.datasette-alerts-access',
      'true',
      '-p',
      String(PORT),
    ],
    {
      stdio: ['ignore', 'pipe', 'pipe'],
      detached: true,
      // PYTHONHASHSEED=0 → any hash-derived ordering/colours stay stable.
      env: { ...process.env, PYTHONHASHSEED: '0' },
    }
  );
  let log = '';
  child.stdout.on('data', (d) => (log += d));
  child.stderr.on('data', (d) => (log += d));

  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) {
      throw new Error(`datasette exited early (code ${child.exitCode}):\n${log}`);
    }
    if (await reachable()) return child;
    await sleep(250);
  }
  stopServer(child);
  throw new Error(`datasette never came up on ${BASE}:\n${log}`);
}

// Kill the server's whole process group (datasette is uv's child). Idempotent.
export function stopServer(child) {
  if (!child || child.exitCode !== null) return;
  try {
    process.kill(-child.pid, 'SIGKILL');
  } catch {
    try {
      child.kill('SIGKILL');
    } catch {
      // already gone
    }
  }
}

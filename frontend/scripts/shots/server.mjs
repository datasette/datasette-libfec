// Boot/teardown of the throwaway datasette the shots drive.
//
// The data comes from a pre-built FEC fixture .db, copied to a mutable /tmp copy
// so datasette opens it writable (the plugin's startup hook adds its alert-queue
// table) without touching the committed fixture. The instance permission gates
// every libfec page checks are opened globally.
//
// The `paper` shot additionally boots with datasette-paper (`--extra paper`,
// from PyPI) + its permission gates + the actor-name plugin — only when that
// shot is in the run set, so the other shots stay lightweight.
import { mkdir, copyFile, access, rm } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import {
  APP,
  BASE,
  SECRET,
  FIXTURE_DB,
  DATA_DIR,
  DATA_DB,
  INTERNAL_DB,
  PLUGINS_DIR,
  PORT,
} from './config.mjs';

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

// Fresh mutable copy of the fixture db. `needsPaper` also wipes the internal DB
// so the seeded paper doc's id stays deterministic across runs.
async function setupDataDb(needsPaper) {
  try {
    await access(FIXTURE_DB);
  } catch {
    throw new Error(`fixture db missing: ${FIXTURE_DB}\nRun \`just shots-fixture\` first.`);
  }
  await mkdir(DATA_DIR, { recursive: true });
  await copyFile(FIXTURE_DB, DATA_DB);
  if (needsPaper) await rm(INTERNAL_DB, { force: true });
}

// Extra `uv run` / datasette args that pull in datasette-paper + open its gates.
// `--extra paper` resolves it from PyPI; the `>=0.0.2a3` specifier is an alpha,
// so `--prerelease=allow` lets uv pick it (and any prerelease transitive deps).
// The plugin dir adds a friendly display name for the doc author.
function paperArgs() {
  return {
    uv: ['--prerelease=allow', '--extra', 'paper'],
    ds: [
      '--internal',
      INTERNAL_DB,
      '--plugins-dir',
      PLUGINS_DIR,
      '-s',
      'permissions.datasette-paper-create',
      'true',
      '-s',
      'permissions.paper-view',
      'true',
    ],
  };
}

export async function startServer(needsPaper) {
  await setupDataDb(needsPaper);
  // Refuse to start over an already-listening server rather than screenshot
  // whatever is there — the poll can't tell a stale server from ours.
  if (await reachable()) {
    throw new Error(
      `something is already serving on ${BASE}. Stop it (or set SHOTS_PORT) and retry.`
    );
  }
  const paper = needsPaper ? paperArgs() : { uv: [], ds: [] };
  // `detached: true` puts datasette in its own process group. datasette is a
  // grandchild of `uv run`, so we kill the whole group in stopServer.
  const child = spawn(
    'uv',
    [
      'run',
      ...paper.uv,
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
      ...paper.ds,
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

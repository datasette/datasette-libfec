// Programmatic doc screenshots of datasette-libfec → docs/screenshots/*.png.
//
// SELF-CONTAINED: boots its own throwaway datasette on a fixed port, pointed at
// a small pre-built FEC database (frontend/scripts/build-fixture.sh), drives
// Playwright through the plugin's pages, then tears the server down. One command,
// reproducible — so the committed PNGs only change when the UI actually changes.
//
// Output is committed; the README embeds these, so re-run + commit when the UI
// look changes:  `just shots`  (or a subset, e.g. `just shots index contest`).
//
// libfec's own pages are plain read-only views gated by a single instance
// permission, so they need no signed actor cookies or ACL grants — just open the
// access gate and browse; the "seed" is the fixture .db, not a startup plugin.
// The one exception is the `paper` shot: it boots the server with `--extra
// paper` (datasette-paper, from PyPI) and seeds a paper document that embeds FEC
// candidates as cards, viewed as a signed-in owner (see seedPaperDoc + PAPER_*).
import { chromium } from '@playwright/test';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { mkdir, copyFile, access } from 'node:fs/promises';
import { rmSync } from 'node:fs';
import { spawn, execFileSync } from 'node:child_process';

// Free high port unique to this plugin (others: paper 8486, sheets 8487,
// town 8489, screenshot-skill default 8490).
const PORT = Number(process.env.SHOTS_PORT || 8491);
const BASE = `http://localhost:${PORT}`;
// datasette database name == the data-db filename stem.
const DB_NAME = 'data';
const APP = `${BASE}/${DB_NAME}/-/libfec`;
const SECRET = 'screenshots-secret-not-for-prod';

const HERE = dirname(fileURLToPath(import.meta.url));
// Pre-built demo database (run `just shots-fixture` to (re)generate).
const FIXTURE_DB = resolve(HERE, 'shot-data/libfec.db');
const DATA_DIR = '/tmp/datasette-libfec-shots-data'; // dir name is irrelevant; file stem == DB_NAME
const DATA_DB = `${DATA_DIR}/${DB_NAME}.db`;
// datasette-paper stores docs in the internal DB; a throwaway one, wiped each
// run, keeps the seeded doc's id deterministic. Only used for the `paper` shot.
const INTERNAL_DB = `${DATA_DIR}/internal.db`;
const OUT = resolve(HERE, '../../docs/screenshots');

const VIEWPORT = { width: 1200, height: 900 };
// Cropped to fit the paper editor chrome + heading + the two stacked embed
// cards, with a little breathing room below.
const VIEWPORT_TALL = { width: 1200, height: 800 };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// --- Concrete demo entities (from the fixture: 2024 Ohio Senate + big PACs) ---
const SHERROD_BROWN = 'S6OH00163'; // candidate id
const BERNIE_MORENO = 'S4OH00192'; // candidate id (his 2024 Senate opponent)
const FAIRSHAKE = 'C00835959'; // crypto super PAC committee id
const BROWN_YE_FILING = '1870297'; // Friends of Sherrod Brown, F3 year-end 2024

// --- Paper embed demo (only when the `paper` shot runs) ---------------------
// datasette-paper isn't a hard dependency (it owns the paper_embed_provider
// spec, so our hookimpl is a no-op without it). The `paper` shot boots the
// server with `--extra paper` so a doc can embed live FEC-candidate cards; refs
// use the plugin's namespace, `/-/libfec/candidate/{db}/{candidate_id}` (see
// datasette_libfec/paper.py + frontend/src/paper_embed.ts).
const PAPER = `${BASE}/-/paper`;
const PAPER_ACTOR = 'alice'; // doc owner — create seeds an owner acl grant to it
const PAPER_EMBED_CANDIDATES = [SHERROD_BROWN, BERNIE_MORENO]; // the 2024 matchup

// ---------------------------------------------------------------------------
async function reachable() {
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

// Copy the pre-built fixture to a throwaway mutable db so datasette opens it
// writable (the plugin's startup hook adds its alert-queue table) without ever
// touching the committed-ish fixture. `needsPaper` also wipes the internal DB
// so the seeded paper doc's id is deterministic across runs.
async function setupDataDb(needsPaper) {
  try {
    await access(FIXTURE_DB);
  } catch {
    throw new Error(`fixture db missing: ${FIXTURE_DB}\nRun \`just shots-fixture\` first.`);
  }
  await mkdir(DATA_DIR, { recursive: true });
  await copyFile(FIXTURE_DB, DATA_DB);
  if (needsPaper) rmSync(INTERNAL_DB, { force: true });
}

// Extra `uv run` / datasette args that pull in datasette-paper + open its gates.
// `--extra paper` resolves it from PyPI; the `>=0.0.2a3` specifier is an alpha,
// so `--prerelease=allow` lets uv pick it (and any prerelease transitive deps).
function paperServerArgs() {
  return {
    // Go right after `run`, before `datasette`.
    uv: ['--prerelease=allow', '--extra', 'paper'],
    // datasette flags: persist docs in a throwaway internal DB, and let alice
    // create + everyone view docs (per-doc edit/manage still derive from the
    // owner grant the create endpoint seeds).
    ds: [
      '--internal',
      INTERNAL_DB,
      '-s',
      'permissions.datasette-paper-create',
      'true',
      '-s',
      'permissions.paper-view',
      'true',
    ],
  };
}

async function startServer(needsPaper) {
  await setupDataDb(needsPaper);
  if (await reachable()) {
    throw new Error(
      `something is already serving on ${BASE}. Stop it (or set SHOTS_PORT) and retry.`
    );
  }
  const paper = needsPaper ? paperServerArgs() : { uv: [], ds: [] };
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

// Mint a signed `ds_actor` cookie for the paper doc owner. There's no Node port
// of itsdangerous, so shell out to the same URLSafeSerializer(salt="actor")
// datasette signs with. One actor, so a single cached value.
let _paperCookie;
function paperCookie() {
  if (_paperCookie) return _paperCookie;
  _paperCookie = execFileSync(
    'uv',
    [
      'run',
      '--prerelease=allow',
      'python',
      '-c',
      'import sys, json; from itsdangerous import URLSafeSerializer; ' +
        'print(URLSafeSerializer(sys.argv[1]).dumps(json.loads(sys.argv[2]), salt="actor"))',
      SECRET,
      JSON.stringify({ a: { id: PAPER_ACTOR } }),
    ],
    { encoding: 'utf8' }
  ).trim();
  return _paperCookie;
}

// Create a paper doc that embeds the demo FEC candidates as block cards, over
// paper's real create API. A block embed is a fenced ```paper-embed code block
// whose body is {config, mode, ref}; paper renders it via the provider that owns
// the ref's prefix (libfec, here). Returns the new doc id.
async function seedPaperDoc() {
  const blocks = PAPER_EMBED_CANDIDATES.map(
    (cid) =>
      '```paper-embed\n' +
      JSON.stringify({
        config: {},
        mode: 'block',
        ref: `/-/libfec/candidate/${DB_NAME}/${cid}`,
      }) +
      '\n```'
  ).join('\n\n');
  const content =
    '# 2024 Ohio Senate\n\n' +
    'The two campaigns in the race, embedded as live FEC-candidate cards:\n\n' +
    blocks +
    '\n';
  const resp = await fetch(`${PAPER}/api/docs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Cookie: `ds_actor=${paperCookie()}`,
    },
    body: JSON.stringify({ name: '2024 Ohio Senate', content }),
  });
  if (!resp.ok) {
    throw new Error(`create paper doc → ${resp.status}: ${await resp.text()}`);
  }
  const { id } = await resp.json();
  return id;
}

// Kill the server's whole process group (datasette is uv's child). Idempotent.
function stopServer(child) {
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

// ---------------------------------------------------------------------------
// Per-page stabilization: kill carets / transitions and hide dev-only widgets so
// a re-run with no UI change produces no binary diff.
const STABILITY_CSS = `*, *::before, *::after {
  caret-color: transparent !important;
  transition: none !important;
  animation: none !important;
}
#datasette-debug-bar { display: none !important; }`;

async function freezeVolatile(page) {
  await page.evaluate(() => {
    document.getElementById('datasette-debug-bar')?.remove();
  });
}

async function makeContext(browser, viewport = VIEWPORT, cookieActor = null) {
  const ctx = await browser.newContext({ viewport, deviceScaleFactor: 2 });
  // The paper shot views a doc owned by `alice`; the rest browse anonymously.
  if (cookieActor) {
    await ctx.addCookies([{ name: 'ds_actor', value: paperCookie(), url: BASE }]);
  }
  await ctx.addInitScript((css) => {
    const inject = () => {
      if (document.getElementById('__shots_stability')) return;
      const s = document.createElement('style');
      s.id = '__shots_stability';
      s.textContent = css;
      (document.head || document.documentElement).appendChild(s);
    };
    inject();
    document.addEventListener('DOMContentLoaded', inject);
  }, STABILITY_CSS);
  return ctx;
}

// ---------------------------------------------------------------------------
// Per-plugin shot map. Each entry opens a context, navigates, WAITS ON A REAL
// READINESS SELECTOR (not sleep), then screenshots.
function buildShots(browser, { paperDocId } = {}) {
  const out = (n) => resolve(OUT, `${n}.png`);

  async function shotPage(name, url, readySelector, viewport = VIEWPORT) {
    const ctx = await makeContext(browser, viewport);
    const page = await ctx.newPage();
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.locator(readySelector).first().waitFor({ timeout: 15_000 });
    await freezeVolatile(page);
    await page.screenshot({ path: out(name) });
    await ctx.close();
  }

  // A datasette-paper document embedding FEC-candidate cards. Unlike the plain
  // pages, this loads paper's editor (a live collab connection that never goes
  // network-idle), so wait on domcontentloaded + explicit readiness: the editor
  // surface, then both embed cards resolved (each card's `mount()` swaps its
  // "Loading candidate…" placeholder for a card carrying a "Candidate ID" row).
  async function shotPaperDoc(name) {
    if (!paperDocId) throw new Error('paper doc was not seeded');
    const ctx = await makeContext(browser, VIEWPORT_TALL, PAPER_ACTOR);
    const page = await ctx.newPage();
    await page.goto(`${PAPER}/doc/${paperDocId}`, {
      waitUntil: 'domcontentloaded',
    });
    await page.locator('.ProseMirror').first().waitFor({ timeout: 15_000 });
    await page.waitForFunction(
      (n) =>
        [...document.querySelectorAll('span')].filter((s) => s.textContent === 'Candidate ID')
          .length >= n,
      PAPER_EMBED_CANDIDATES.length,
      { timeout: 15_000 }
    );
    await freezeVolatile(page);
    await sleep(300); // let the cards' final layout settle before capture
    await page.screenshot({ path: out(name) });
    await ctx.close();
  }

  return {
    // Landing page: nav cards + "Most Recent Filings" table.
    index: () => shotPage('index', APP, '.recent-filings table tbody tr'),

    // A race: 2024 Ohio Senate (Brown vs Moreno + field).
    contest: () =>
      shotPage(
        'contest',
        `${APP}/contest?state=OH&office=S&cycle=2024`,
        '.candidates-table tbody tr'
      ),

    // A candidate: Sherrod Brown.
    candidate: () =>
      shotPage(
        'candidate',
        `${APP}/candidate/${SHERROD_BROWN}?cycle=2024`,
        '.candidate-page .filings-table'
      ),

    // A committee: Fairshake super PAC.
    committee: () =>
      shotPage(
        'committee',
        `${APP}/committee/${FAIRSHAKE}?cycle=2024`,
        '.committee-page .filings-table'
      ),

    // A single filing's cover detail.
    filing: () =>
      shotPage('filing', `${APP}/filing/${BROWN_YE_FILING}`, '.filing-detail .info-section'),

    // Filing Day: compare F3 reports across a field for one reporting period.
    'filing-day': () =>
      shotPage(
        'filing-day',
        `${APP}/filing-day?report=Q3&year=2024&office=S`,
        '.reports-table tbody tr'
      ),

    // Import form: pull FEC filings for a committee/candidate/contest.
    import: () => shotPage('import', `${APP}/import`, '.import-section form'),

    // RSS watcher: auto-import new filings from the FEC RSS feed.
    rss: () => shotPage('rss', `${APP}/rss`, '.rss-section .status-card'),

    // Alerts: build watchlists that notify on new filings / contributors.
    alerts: () => shotPage('alerts', `${APP}/alerts`, '.create-section form'),

    // Paper: an FEC candidate embedded as a live card inside a paper document
    // (the datasette-paper embed provider). Needs `--extra paper` + a seeded doc.
    paper: () => shotPaperDoc('paper'),
  };
}

// The full shot set, in capture order. Kept as a static list (not derived from
// buildShots) so we can resolve the requested subset — and thus whether the
// server needs datasette-paper — before booting. buildShots() is asserted to
// cover exactly these below.
const SHOT_NAMES = [
  'index',
  'contest',
  'candidate',
  'committee',
  'filing',
  'filing-day',
  'import',
  'rss',
  'alerts',
  'paper',
];

// ---------------------------------------------------------------------------
async function main() {
  const requested = new Set(process.argv.slice(2));
  const unknown = [...requested].filter((n) => !SHOT_NAMES.includes(n));
  if (unknown.length) {
    throw new Error(`unknown shot(s): ${unknown.join(', ')} (have: ${SHOT_NAMES.join(', ')})`);
  }
  const todo = requested.size ? SHOT_NAMES.filter((n) => requested.has(n)) : SHOT_NAMES;
  const needsPaper = todo.includes('paper');

  await mkdir(OUT, { recursive: true });
  console.log(`booting datasette on ${BASE}${needsPaper ? ' (with paper)' : ''} …`);
  const server = await startServer(needsPaper);
  const onSignal = () => {
    stopServer(server);
    process.exit(130);
  };
  process.once('SIGINT', onSignal);
  process.once('SIGTERM', onSignal);

  const paperDocId = needsPaper ? await seedPaperDoc() : null;

  const browser = await chromium.launch();
  try {
    const shotsByName = buildShots(browser, { paperDocId });
    const missing = SHOT_NAMES.filter((n) => !shotsByName[n]);
    if (missing.length) {
      throw new Error(`buildShots missing: ${missing.join(', ')}`);
    }

    for (const name of todo) {
      await shotsByName[name]();
      console.log(`✓ ${name} → ${resolve(OUT, name + '.png')}`);
    }
  } finally {
    await browser.close();
    stopServer(server);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

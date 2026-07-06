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
// Unlike the other plugins in this screenshot family, libfec's pages are plain
// read-only views gated by a single instance permission, so there are no signed
// actor cookies or per-resource ACL grants here — just open the access gate and
// browse. The "seed" is the fixture .db, not a startup plugin.
import { chromium } from "@playwright/test";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { mkdir, copyFile, access } from "node:fs/promises";
import { spawn, execFileSync } from "node:child_process";

// Free high port unique to this plugin (others: paper 8486, sheets 8487,
// town 8489, screenshot-skill default 8490).
const PORT = Number(process.env.SHOTS_PORT || 8491);
const BASE = `http://localhost:${PORT}`;
// datasette database name == the data-db filename stem.
const DB_NAME = "data";
const APP = `${BASE}/${DB_NAME}/-/libfec`;
const SECRET = "screenshots-secret-not-for-prod";

const HERE = dirname(fileURLToPath(import.meta.url));
// Pre-built demo database (run `just shots-fixture` to (re)generate).
const FIXTURE_DB = resolve(HERE, "shot-data/libfec.db");
const DATA_DIR = "/tmp/datasette-libfec-shots-data"; // dir name is irrelevant; file stem == DB_NAME
const DATA_DB = `${DATA_DIR}/${DB_NAME}.db`;
const OUT = resolve(HERE, "../../docs/screenshots");

const VIEWPORT = { width: 1200, height: 900 };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// --- Concrete demo entities (from the fixture: 2024 Ohio Senate + big PACs) ---
const SHERROD_BROWN = "S6OH00163"; // candidate id
const FAIRSHAKE = "C00835959"; // crypto super PAC committee id
const BROWN_YE_FILING = "1870297"; // Friends of Sherrod Brown, F3 year-end 2024

// ---------------------------------------------------------------------------
async function reachable() {
  try {
    const ac = new AbortController();
    const t = setTimeout(() => ac.abort(), 500);
    const r = await fetch(APP, { redirect: "manual", signal: ac.signal });
    clearTimeout(t);
    return r.status < 500;
  } catch {
    return false;
  }
}

// Copy the pre-built fixture to a throwaway mutable db so datasette opens it
// writable (the plugin's startup hook adds its alert-queue table) without ever
// touching the committed-ish fixture.
async function setupDataDb() {
  try {
    await access(FIXTURE_DB);
  } catch {
    throw new Error(
      `fixture db missing: ${FIXTURE_DB}\nRun \`just shots-fixture\` first.`,
    );
  }
  await mkdir(DATA_DIR, { recursive: true });
  await copyFile(FIXTURE_DB, DATA_DB);
}

async function startServer() {
  await setupDataDb();
  if (await reachable()) {
    throw new Error(
      `something is already serving on ${BASE}. Stop it (or set SHOTS_PORT) and retry.`,
    );
  }
  // `detached: true` puts datasette in its own process group. datasette is a
  // grandchild of `uv run`, so we kill the whole group in stopServer.
  const child = spawn(
    "uv",
    [
      "run",
      "datasette",
      DATA_DB,
      "--secret",
      SECRET,
      // Open every gate the UI checks so all features render: read access, the
      // write gate (import + RSS pages and their index cards), and alerts access
      // (datasette-alerts is a dependency, so the Alerts page resolves).
      "-s",
      "permissions.datasette_libfec_access",
      "true",
      "-s",
      "permissions.datasette_libfec_write",
      "true",
      "-s",
      "permissions.datasette-alerts-access",
      "true",
      "-p",
      String(PORT),
    ],
    {
      stdio: ["ignore", "pipe", "pipe"],
      detached: true,
      env: { ...process.env, PYTHONHASHSEED: "0" },
    },
  );
  let log = "";
  child.stdout.on("data", (d) => (log += d));
  child.stderr.on("data", (d) => (log += d));

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
function stopServer(child) {
  if (!child || child.exitCode !== null) return;
  try {
    process.kill(-child.pid, "SIGKILL");
  } catch {
    try {
      child.kill("SIGKILL");
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
    document.getElementById("datasette-debug-bar")?.remove();
  });
}

async function makeContext(browser, viewport = VIEWPORT) {
  const ctx = await browser.newContext({ viewport, deviceScaleFactor: 2 });
  await ctx.addInitScript((css) => {
    const inject = () => {
      if (document.getElementById("__shots_stability")) return;
      const s = document.createElement("style");
      s.id = "__shots_stability";
      s.textContent = css;
      (document.head || document.documentElement).appendChild(s);
    };
    inject();
    document.addEventListener("DOMContentLoaded", inject);
  }, STABILITY_CSS);
  return ctx;
}

// ---------------------------------------------------------------------------
// Per-plugin shot map. Each entry opens a context, navigates, WAITS ON A REAL
// READINESS SELECTOR (not sleep), then screenshots.
function buildShots(browser) {
  const out = (n) => resolve(OUT, `${n}.png`);

  async function shotPage(name, url, readySelector, viewport = VIEWPORT) {
    const ctx = await makeContext(browser, viewport);
    const page = await ctx.newPage();
    await page.goto(url, { waitUntil: "networkidle" });
    await page.locator(readySelector).first().waitFor({ timeout: 15_000 });
    await freezeVolatile(page);
    await page.screenshot({ path: out(name) });
    await ctx.close();
  }

  return {
    // Landing page: nav cards + "Most Recent Filings" table.
    index: () => shotPage("index", APP, ".recent-filings table tbody tr"),

    // A race: 2024 Ohio Senate (Brown vs Moreno + field).
    contest: () =>
      shotPage(
        "contest",
        `${APP}/contest?state=OH&office=S&cycle=2024`,
        ".candidates-table tbody tr",
      ),

    // A candidate: Sherrod Brown.
    candidate: () =>
      shotPage(
        "candidate",
        `${APP}/candidate/${SHERROD_BROWN}?cycle=2024`,
        ".candidate-page .filings-table",
      ),

    // A committee: Fairshake super PAC.
    committee: () =>
      shotPage(
        "committee",
        `${APP}/committee/${FAIRSHAKE}?cycle=2024`,
        ".committee-page .filings-table",
      ),

    // A single filing's cover detail.
    filing: () =>
      shotPage(
        "filing",
        `${APP}/filing/${BROWN_YE_FILING}`,
        ".filing-detail .info-section",
      ),

    // Filing Day: compare F3 reports across a field for one reporting period.
    "filing-day": () =>
      shotPage(
        "filing-day",
        `${APP}/filing-day?report=Q3&year=2024&office=S`,
        ".reports-table tbody tr",
      ),

    // Import form: pull FEC filings for a committee/candidate/contest.
    import: () =>
      shotPage("import", `${APP}/import`, ".import-section form"),

    // RSS watcher: auto-import new filings from the FEC RSS feed.
    rss: () => shotPage("rss", `${APP}/rss`, ".rss-section .status-card"),

    // Alerts: build watchlists that notify on new filings / contributors.
    alerts: () =>
      shotPage("alerts", `${APP}/alerts`, ".create-section form"),
  };
}

// ---------------------------------------------------------------------------
async function main() {
  const requested = new Set(process.argv.slice(2));

  await mkdir(OUT, { recursive: true });
  console.log(`booting datasette on ${BASE} …`);
  const server = await startServer();
  const onSignal = () => {
    stopServer(server);
    process.exit(130);
  };
  process.once("SIGINT", onSignal);
  process.once("SIGTERM", onSignal);

  const browser = await chromium.launch();
  try {
    const shotsByName = buildShots(browser);
    const names = Object.keys(shotsByName);
    const unknown = [...requested].filter((n) => !names.includes(n));
    if (unknown.length) {
      throw new Error(`unknown shot(s): ${unknown.join(", ")} (have: ${names.join(", ")})`);
    }
    const todo = requested.size ? names.filter((n) => requested.has(n)) : names;

    for (const name of todo) {
      await shotsByName[name]();
      console.log(`✓ ${name} → ${resolve(OUT, name + ".png")}`);
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

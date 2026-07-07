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
// This file is a THIN RUNNER. The harness lives in shots/ (matching the
// datasette-paper / datasette-places convention):
//   * shots/config.mjs     — constants + out(name)
//   * shots/server.mjs     — boot/teardown of the throwaway datasette
//   * shots/cookie.mjs     — signed ds_actor cookie (itsdangerous via uv)
//   * shots/seed.mjs       — seed() the paper-embed doc (paper shot only)
//   * shots/helpers.mjs    — STABILITY_CSS / freezeVolatile / makeContext
//   * shots/defineShot.mjs — per-shot context → goto → wait → freeze → capture
//   * shots/defs/<name>.mjs — ONE FILE PER SHOT, auto-discovered below.
//
// libfec specifics: its own pages are anonymous, read-only views over the
// fixture db (no cookies/seed). The one exception is the `paper` shot, which
// boots the server with datasette-paper and seeds a document embedding FEC
// candidates as cards, viewed as a signed-in owner — see shots/seed.mjs.
import { chromium } from '@playwright/test';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { mkdir, readdir } from 'node:fs/promises';
import { BASE, OUT, out } from './shots/config.mjs';
import { startServer, stopServer } from './shots/server.mjs';
import { seed } from './shots/seed.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));

// Auto-discover the shots: every shots/defs/<name>.mjs default-exports a
// defineShot() descriptor. The file name IS the shot id — asserted below so a
// typo can't silently mis-name an output PNG. No central registry to edit.
async function discoverShots() {
  const dir = resolve(HERE, 'shots/defs');
  const files = (await readdir(dir)).filter((f) => f.endsWith('.mjs'));
  const shots = [];
  for (const f of files) {
    const name = f.replace(/\.mjs$/, '');
    const mod = await import(resolve(dir, f));
    const run = mod.default;
    if (typeof run !== 'function') {
      throw new Error(`shots/defs/${f} must default-export a defineShot() descriptor`);
    }
    if (run.shotName !== name) {
      throw new Error(`shots/defs/${f}: declared name "${run.shotName}" != file name "${name}"`);
    }
    shots.push({ name, run, order: run.order ?? 0 });
  }
  shots.sort((a, b) => a.order - b.order || a.name.localeCompare(b.name));
  return shots;
}

async function main() {
  const requested = new Set(process.argv.slice(2));

  const shots = await discoverShots();
  const names = shots.map((s) => s.name);
  const unknown = [...requested].filter((n) => !names.includes(n));
  if (unknown.length) {
    throw new Error(`unknown shot(s): ${unknown.join(', ')} (have: ${names.join(', ')})`);
  }
  const todo = requested.size ? shots.filter((s) => requested.has(s.name)) : shots;
  // Only the paper shot needs datasette-paper booted + a seeded doc.
  const needsPaper = todo.some((s) => s.name === 'paper');

  await mkdir(OUT, { recursive: true });
  console.log(`booting datasette on ${BASE}${needsPaper ? ' (with paper)' : ''} …`);
  const server = await startServer(needsPaper);
  const onSignal = () => {
    stopServer(server);
    process.exit(130);
  };
  process.once('SIGINT', onSignal);
  process.once('SIGTERM', onSignal);

  const browser = await chromium.launch();
  try {
    const ids = await seed(needsPaper);
    for (const { name, run } of todo) {
      await run(browser, ids);
      console.log(`✓ ${name} → ${out(name)}`);
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

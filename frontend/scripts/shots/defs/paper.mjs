import { defineShot } from '../defineShot.mjs';
import { PAPER, PAPER_ACTOR, PAPER_EMBED_CANDIDATES, VIEWPORT_TALL } from '../config.mjs';

// An FEC candidate embedded as a live card inside a datasette-paper document
// (the paper embed provider — datasette_libfec/paper.py + src/paper_embed.ts).
// Needs `--extra paper` + the doc seeded by shots/seed.mjs.
//
// The editor holds a live SSE connection that never goes network-idle, so wait
// on domcontentloaded + explicit readiness: the editor surface, then both cards
// resolved (each card's mount() swaps its "Loading candidate…" placeholder for
// a card carrying a "Candidate ID" row).
export default defineShot({
  name: 'paper',
  order: 10,
  actor: PAPER_ACTOR,
  viewport: VIEWPORT_TALL,
  waitUntil: 'domcontentloaded',
  url: (ids) => `${PAPER}/doc/${ids.paperDocId}`,
  prepare: async (page) => {
    await page.locator('.ProseMirror').first().waitFor({ timeout: 15_000 });
    await page.waitForFunction(
      (n) =>
        [...document.querySelectorAll('span')].filter((s) => s.textContent === 'Candidate ID')
          .length >= n,
      PAPER_EMBED_CANDIDATES.length,
      { timeout: 15_000 }
    );
    // Let the cards' final layout settle before capture.
    await new Promise((r) => setTimeout(r, 300));
  },
});

// defineShot turns a declarative descriptor into the `async (browser, ids) =>
// {…}` the runner calls, owning the per-shot boilerplate: open a fresh context
// (with the right actor + viewport) → navigate → wait for readiness → interact →
// freeze → capture → close.
//
// Descriptor fields:
//   name      (required) — output PNG base name; MUST equal the shot's file name
//                          (asserted by the runner).
//   order     — run sequence (ascending, then by name). libfec shots are
//               independent, so this just fixes a stable order.
//   url       (required) — (ids) => string, the page to screenshot.
//   actor     — actor id to sign a ds_actor cookie for (default null = anon).
//   viewport  — context viewport (default VIEWPORT).
//   waitUntil — page.goto wait condition (default "networkidle"; the paper shot
//               uses "domcontentloaded", as its editor holds a live SSE
//               connection that never goes idle).
//   ready     — a selector waited on after navigation (the common case).
//   prepare   — async (page, {ids}) for custom waits / interaction.
//   capture   — async (page, file, {ids}); default = full-page screenshot.
//   freeze    — default true; runs freezeVolatile before capture.
import { makeContext, freezeVolatile } from './helpers.mjs';
import { VIEWPORT, out } from './config.mjs';

export function defineShot(desc) {
  const {
    name,
    order = 0,
    url,
    actor = null,
    viewport = VIEWPORT,
    waitUntil = 'networkidle',
    ready,
    prepare,
    capture,
    freeze = true,
  } = desc;
  if (!name) throw new Error('defineShot: missing `name`');
  if (typeof url !== 'function') {
    throw new Error(`defineShot(${name}): \`url\` must be a function`);
  }

  const run = async (browser, ids) => {
    const ctx = await makeContext(browser, { actor, viewport });
    try {
      const page = await ctx.newPage();
      await page.goto(url(ids), { waitUntil });
      if (ready) await page.locator(ready).first().waitFor({ timeout: 15_000 });
      if (prepare) await prepare(page, { ids });
      if (freeze) await freezeVolatile(page);
      if (capture) await capture(page, out(name), { ids });
      else await page.screenshot({ path: out(name) });
    } finally {
      await ctx.close();
    }
  };
  run.shotName = name;
  run.order = order;
  return run;
}

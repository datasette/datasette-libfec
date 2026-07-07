// Page-stabilization + capture helpers shared by every shot.
import { BASE, VIEWPORT } from './config.mjs';
import { signActorCookie } from './cookie.mjs';

// Injected on the context (survives navigation) so re-runs produce no binary
// diff: kill the caret, transitions and animations, and hide the debug bar.
export const STABILITY_CSS = `*, *::before, *::after {
  caret-color: transparent !important;
  transition: none !important;
  animation: none !important;
}
#datasette-debug-bar { display: none !important; }`;

// Rewrite the moving text to fixed strings just before each capture. libfec's
// own pages carry none, but the paper editor header shows a relative "edited …"
// time — pin it so the paper shot doesn't diff on the clock.
export async function freezeVolatile(page) {
  await page.evaluate(() => {
    document.getElementById('datasette-debug-bar')?.remove();
    document.querySelectorAll('.updated-at').forEach((el) => (el.textContent = 'edited just now'));
  });
}

// New context: viewport + retina, the stability stylesheet on every navigation,
// and (for the paper shot) a signed owner cookie. libfec's own pages browse
// anonymously — only `actor` shots get a cookie.
export async function makeContext(browser, { actor = null, viewport = VIEWPORT } = {}) {
  const ctx = await browser.newContext({ viewport, deviceScaleFactor: 2 });
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
  if (actor) {
    await ctx.addCookies([{ name: 'ds_actor', value: signActorCookie(actor), url: BASE }]);
  }
  return ctx;
}

// Page-stabilization + capture helpers shared by every shot.
import { VIEWPORT } from './config.mjs';

// Injected on the context (survives navigation) so re-runs produce no binary
// diff: kill the caret, transitions and animations, and hide the debug bar.
export const STABILITY_CSS = `*, *::before, *::after {
  caret-color: transparent !important;
  transition: none !important;
  animation: none !important;
}
#datasette-debug-bar { display: none !important; }`;

// Rewrite any moving text to fixed strings just before each capture. libfec's
// pages carry none, so this only removes the dev debug bar if present.
export async function freezeVolatile(page) {
  await page.evaluate(() => {
    document.getElementById('datasette-debug-bar')?.remove();
  });
}

// New context: viewport + retina, with the stability stylesheet injected on
// every navigation.
export async function makeContext(browser, { viewport = VIEWPORT } = {}) {
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
  return ctx;
}

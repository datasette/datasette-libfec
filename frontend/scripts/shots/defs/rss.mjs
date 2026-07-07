import { defineShot } from '../defineShot.mjs';
import { APP } from '../config.mjs';

// RSS watcher: auto-import new filings from the FEC RSS feed.
export default defineShot({
  name: 'rss',
  order: 8,
  url: () => `${APP}/rss`,
  ready: '.rss-section .status-card',
});

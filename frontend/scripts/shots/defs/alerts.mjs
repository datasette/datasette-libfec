import { defineShot } from '../defineShot.mjs';
import { APP } from '../config.mjs';

// Alerts: build watchlists that notify on new filings / contributors.
export default defineShot({
  name: 'alerts',
  order: 9,
  url: () => `${APP}/alerts`,
  ready: '.create-section form',
});

import { defineShot } from '../defineShot.mjs';
import { APP, SHERROD_BROWN } from '../config.mjs';

// A candidate: Sherrod Brown.
export default defineShot({
  name: 'candidate',
  order: 3,
  url: () => `${APP}/candidate/${SHERROD_BROWN}?cycle=2024`,
  ready: '.candidate-page .filings-table',
});

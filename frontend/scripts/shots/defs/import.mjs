import { defineShot } from '../defineShot.mjs';
import { APP } from '../config.mjs';

// Import form: pull FEC filings for a committee/candidate/contest.
export default defineShot({
  name: 'import',
  order: 7,
  url: () => `${APP}/import`,
  ready: '.import-section form',
});

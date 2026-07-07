import { defineShot } from '../defineShot.mjs';
import { APP, FAIRSHAKE } from '../config.mjs';

// A committee: Fairshake super PAC.
export default defineShot({
  name: 'committee',
  order: 4,
  url: () => `${APP}/committee/${FAIRSHAKE}?cycle=2024`,
  ready: '.committee-page .filings-table',
});

import { defineShot } from '../defineShot.mjs';
import { APP } from '../config.mjs';

// Landing page: nav cards + "Most Recent Filings" table.
export default defineShot({
  name: 'index',
  order: 1,
  url: () => APP,
  ready: '.recent-filings table tbody tr',
});

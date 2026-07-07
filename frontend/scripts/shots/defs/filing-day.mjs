import { defineShot } from '../defineShot.mjs';
import { APP } from '../config.mjs';

// Filing Day: compare F3 reports across a field for one reporting period.
export default defineShot({
  name: 'filing-day',
  order: 6,
  url: () => `${APP}/filing-day?report=Q3&year=2024&office=S`,
  ready: '.reports-table tbody tr',
});

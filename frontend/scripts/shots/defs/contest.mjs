import { defineShot } from '../defineShot.mjs';
import { APP } from '../config.mjs';

// A race: 2024 Ohio Senate (Brown vs Moreno + field).
export default defineShot({
  name: 'contest',
  order: 2,
  url: () => `${APP}/contest?state=OH&office=S&cycle=2024`,
  ready: '.candidates-table tbody tr',
});

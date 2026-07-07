import { defineShot } from '../defineShot.mjs';
import { APP, BROWN_YE_FILING } from '../config.mjs';

// A single filing's cover detail.
export default defineShot({
  name: 'filing',
  order: 5,
  url: () => `${APP}/filing/${BROWN_YE_FILING}`,
  ready: '.filing-detail .info-section',
});

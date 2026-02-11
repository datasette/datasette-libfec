import { mount } from 'svelte';
import FilingDay from './filing-day/FilingDay.svelte';

const app = mount(FilingDay, {
  target: document.getElementById('app-root')!,
});

export default app;

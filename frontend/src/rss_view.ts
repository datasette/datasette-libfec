import { mount } from 'svelte';
import Rss from './Rss.svelte';

const app = mount(Rss, {
  target: document.getElementById('app-root')!,
});

export default app;

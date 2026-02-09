import { mount } from 'svelte';
import Committee from './Committee.svelte';

const app = mount(Committee, {
  target: document.getElementById('app-root')!,
});

export default app;

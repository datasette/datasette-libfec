import { mount } from 'svelte';
import LibfecIndex from './LibfecIndex.svelte';

const app = mount(LibfecIndex, {
  target: document.getElementById('app-root')!,
});

export default app;

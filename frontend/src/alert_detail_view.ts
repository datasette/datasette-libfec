import { mount } from 'svelte';
import AlertDetail from './AlertDetail.svelte';

const app = mount(AlertDetail, {
  target: document.getElementById('app-root')!,
});

export default app;

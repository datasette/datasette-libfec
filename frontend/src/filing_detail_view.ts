import { mount } from 'svelte';
import FilingDetail from './FilingDetail.svelte';

const app = mount(FilingDetail, {
  target: document.getElementById('app-root')!,
});

export default app;

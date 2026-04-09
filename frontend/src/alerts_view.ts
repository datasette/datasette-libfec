import { mount } from 'svelte';
import Alerts from './Alerts.svelte';

const app = mount(Alerts, {
  target: document.getElementById('app-root')!,
});

export default app;

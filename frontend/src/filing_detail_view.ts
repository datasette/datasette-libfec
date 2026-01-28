import { mount } from 'svelte'
import FilingDetail from "./FilingDetail.svelte";

const app = mount(FilingDetail, {
  target: document.getElementById('filing-detail-root')!,
})

export default app;

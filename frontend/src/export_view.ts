import { mount } from 'svelte'
import Export from "./Export.svelte";

const app = mount(Export, {
  target: document.getElementById('app-root')!,
})

export default app

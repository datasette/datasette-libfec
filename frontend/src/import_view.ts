import { mount } from 'svelte'
import Import from './Import.svelte'

const app = mount(Import, {
  target: document.getElementById('app-root')!,
})

export default app

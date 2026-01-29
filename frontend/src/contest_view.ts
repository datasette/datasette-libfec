import { mount } from 'svelte'
import Contest from './Contest.svelte'

const app = mount(Contest, {
  target: document.getElementById('app-root')!,
})

export default app

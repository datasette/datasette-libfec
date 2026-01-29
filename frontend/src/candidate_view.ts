import { mount } from 'svelte'
import Candidate from './Candidate.svelte'

const app = mount(Candidate, {
  target: document.getElementById('app-root')!,
})

export default app

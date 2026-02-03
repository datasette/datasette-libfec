<script lang="ts">
	import { F3Sankey } from './F3Sankey';
	import type { InputRow } from './F3Sankey';
	import { onMount } from 'svelte';
	interface Props {
		items: InputRow[];
	}
	let data: Props = $props();
	let container: HTMLDivElement;
	let toggledCoh = $state(true);
  const WIDTH  = 700;

	onMount(() => {
		container.appendChild(F3Sankey(data.items, { width: WIDTH, showCoh: toggledCoh }) );
	});

	$effect(() => {
		toggledCoh;
		if (container && container.firstChild) {
			container.innerHTML = '';
			container.appendChild(F3Sankey(data.items, { width: WIDTH, showCoh: toggledCoh }) );
		}
	});
</script>

<div class="w-full">
  <div class="flex justify-center" bind:this={container}></div>
  <div class="mt-4 flex float-right gap-2">
    <input type="checkbox" id="toggle" bind:checked={toggledCoh}/>
    <label for="toggle">Show Cash on Hand</label>
  </div>
</div>

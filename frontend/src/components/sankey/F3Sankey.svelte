<script lang="ts">
  import { F3Sankey } from './F3Sankey';
  import type { F3Node, InputRow } from './F3Sankey';
  import { onMount } from 'svelte';
  interface Props {
    items: InputRow[];
  }
  let data: Props = $props();
  let container: HTMLDivElement;
  let toggledCoh = $state(true);
  const WIDTH = 700;

  onMount(() => {
    container.appendChild(F3Sankey(data.items, { width: WIDTH, showCoh: toggledCoh }));
  });

  $effect(() => {
    toggledCoh;
    if (container && container.firstChild) {
      container.innerHTML = '';
      function onClick(node: F3Node) {
        console.log(node);
        if (node.schedule === 'A' && node.line_number === '11AI') {
          window.open(
            '/ye2/libfec_schedule_a?_sort=rowid&filing_id__exact=1941312&form_type__exact=SA11AI'
          );
        }
      }
      container.appendChild(F3Sankey(data.items, { width: WIDTH, showCoh: toggledCoh, onClick }));
    }
  });
</script>

<div class="wrapper">
  <div class="container" bind:this={container}></div>
  <div class="toggle-row">
    <input type="checkbox" id="toggle" bind:checked={toggledCoh} />
    <label for="toggle">Show Cash on Hand</label>
  </div>
</div>

<style>
  .wrapper {
    width: 100%;
  }
  .container {
    display: flex;
    justify-content: center;
  }
  .toggle-row {
    margin-top: 1rem;
    display: flex;
    float: right;
    gap: 0.5rem;
  }
</style>

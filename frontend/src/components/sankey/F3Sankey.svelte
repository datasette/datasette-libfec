<script lang="ts">
  import { F3Sankey } from './F3Sankey';
  import type { F3Node, InputRow } from './F3Sankey';
  import { onMount } from 'svelte';

  interface Props {
    items: InputRow[];
    databaseName: string;
    filingId: string;
  }

  let { items, databaseName, filingId }: Props = $props();
  let container: HTMLDivElement;
  let toggledCoh = $state(true);
  const WIDTH = 700;

  function buildScheduleUrl(node: F3Node): string | null {
    if (!node.schedule || !node.line_number) return null;

    const tableName = `libfec_schedule_${node.schedule.toLowerCase()}`;
    const formType = `S${node.schedule}${node.line_number}`;
    const params = new URLSearchParams({
      _sort: 'rowid',
      filing_id__exact: filingId,
      form_type__exact: formType,
    });
    return `/${databaseName}/${tableName}?${params}`;
  }

  function handleNodeClick(node: F3Node) {
    const url = buildScheduleUrl(node);
    if (url) {
      window.open(url);
    }
  }

  onMount(() => {
    container.appendChild(
      F3Sankey(items, { width: WIDTH, showCoh: toggledCoh, onClick: handleNodeClick })
    );
  });

  $effect(() => {
    toggledCoh;
    if (container && container.firstChild) {
      container.innerHTML = '';
      container.appendChild(
        F3Sankey(items, { width: WIDTH, showCoh: toggledCoh, onClick: handleNodeClick })
      );
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

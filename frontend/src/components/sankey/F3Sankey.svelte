<script lang="ts">
  import { F3Sankey } from './F3Sankey';
  import type { F3Node, InputRow } from './F3Sankey';
  import { onMount } from 'svelte';

  interface Props {
    items: InputRow[];
    databaseName: string;
    filingIds: string[];
  }

  let { items, databaseName, filingIds }: Props = $props();
  let wrapper: HTMLDivElement;
  let container: HTMLDivElement;
  let toggledCoh = $state(true);
  let width = $state(700);

  function filingIdParams(): Record<string, string> {
    if (filingIds.length === 1) return { filing_id__exact: filingIds[0]! };
    return { filing_id__in: filingIds.join(',') };
  }

  function buildScheduleUrl(node: F3Node): string | null {
    if (!node.schedule || !node.line_number) return null;

    const tableName = `libfec_schedule_${node.schedule.toLowerCase()}`;
    const formType = `S${node.schedule}${node.line_number}`;
    const params = new URLSearchParams({
      _sort: 'rowid',
      ...filingIdParams(),
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

  function render() {
    if (!container) return;
    container.innerHTML = '';
    container.appendChild(
      F3Sankey(items, { width, showCoh: toggledCoh, onClick: handleNodeClick })
    );
  }

  onMount(() => {
    width = wrapper.clientWidth;
    render();

    const ro = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect.width;
      if (w != null && Math.abs(w - width) > 1) {
        width = w;
      }
    });
    ro.observe(wrapper);
    return () => ro.disconnect();
  });

  $effect(() => {
    // Track reactive deps
    toggledCoh;
    width;
    render();
  });
</script>

<div class="wrapper" bind:this={wrapper}>
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

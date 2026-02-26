<script lang="ts">
  import { F3XSankey } from './F3XSankey';
  import type { F3XNode, F3XInputRow } from './F3XSankey';
  import { onMount } from 'svelte';

  interface Props {
    items: F3XInputRow[];
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

  function buildScheduleUrl(node: F3XNode): string | null {
    if (!node.schedule || !node.line_number) return null;

    const scheduleMap: Record<string, string> = {
      A: 'libfec_schedule_a',
      B: 'libfec_schedule_b',
      D: 'libfec_schedule_d',
      E: 'libfec_schedule_e',
      H3: 'libfec_schedule_h3',
      H4: 'libfec_schedule_h4',
      H6: 'libfec_schedule_h6',
    };

    const tableName = scheduleMap[node.schedule];
    if (!tableName) return null;

    // Schedule E links by filing_id only (no form_type filter)
    if (node.schedule === 'E') {
      const params = new URLSearchParams({
        _sort: 'rowid',
        ...filingIdParams(),
      });
      return `/${databaseName}/${tableName}?${params}`;
    }

    const formType = `S${node.schedule}${node.line_number}`;
    const params = new URLSearchParams({
      _sort: 'rowid',
      ...filingIdParams(),
      form_type__exact: formType,
    });
    return `/${databaseName}/${tableName}?${params}`;
  }

  function handleNodeClick(node: F3XNode) {
    const url = buildScheduleUrl(node);
    if (url) {
      window.open(url);
    }
  }

  function render() {
    if (!container) return;
    container.innerHTML = '';
    container.appendChild(
      F3XSankey(items, { width, showCoh: toggledCoh, onClick: handleNodeClick })
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
    toggledCoh;
    width;
    render();
  });
</script>

<div class="wrapper" bind:this={wrapper}>
  <div class="container" bind:this={container}></div>
  <div class="toggle-row">
    <input type="checkbox" id="toggle-f3x" bind:checked={toggledCoh} />
    <label for="toggle-f3x">Show Cash on Hand</label>
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

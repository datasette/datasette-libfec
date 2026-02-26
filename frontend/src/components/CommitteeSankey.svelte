<script lang="ts">
  import { query } from '../api';
  import { useQuery } from '../useQuery.svelte';
  import type { InputRow } from './sankey/F3Sankey';
  import type { F3XInputRow } from './sankey/F3XSankey';
  import F3SankeyComponent from './sankey/F3Sankey.svelte';
  import F3XSankeyComponent from './sankey/F3XSankey.svelte';

  interface Props {
    committeeId: string;
    committeeType: string;
    databaseName: string;
    selectedCycle: number;
  }

  let { committeeId, committeeType, databaseName, selectedCycle }: Props = $props();

  // H/S/P committee types use F3, everything else uses F3X
  const isF3 = ['H', 'S', 'P'].includes(committeeType);
  const formTable = isF3 ? 'libfec_F3' : 'libfec_F3X';
  const formType = isF3 ? 'F3' : 'F3X';

  async function fetchData() {
    const sql = `
WITH matching_filings AS (
  SELECT fil.filing_id, fil.coverage_from_date, fil.coverage_through_date
  FROM libfec_filings fil
  WHERE fil.filer_id = :committee_id
    AND fil.cover_record_form = :form_type
    AND strftime('%Y', fil.coverage_through_date) IN (:year1, :year2)
),
final AS (
  SELECT f.*, mf.coverage_from_date, mf.coverage_through_date
  FROM matching_filings mf
  JOIN ${formTable} f ON mf.filing_id = f.filing_id
  ORDER BY mf.coverage_from_date
)
SELECT * FROM final`;

    const year1 = String(selectedCycle - 1);
    const year2 = String(selectedCycle);
    return await query(databaseName, sql, {
      committee_id: committeeId,
      form_type: formType,
      year1,
      year2,
    });
  }

  const result = useQuery(fetchData);

  $effect(() => {
    selectedCycle;
    result.refetch?.();
  });

  const dateRange = $derived.by(() => {
    const rows = result.data as any[] | undefined;
    if (!rows || rows.length === 0) return null;
    const dates = rows
      .flatMap((r) => [r.coverage_from_date, r.coverage_through_date])
      .filter(Boolean)
      .sort();
    if (dates.length === 0) return null;
    return { from: dates[0], through: dates[dates.length - 1] };
  });

  const filingIds = $derived.by(() => {
    const rows = result.data as any[] | undefined;
    if (!rows || rows.length === 0) return [];
    return [...new Set(rows.map((r) => String(r.filing_id)))];
  });
</script>

{#if result.isLoading}
  <section class="sankey-section">
    <h2>Financial Summary</h2>
    <p>Loading financial summary...</p>
  </section>
{:else if result.error}
  <section class="sankey-section">
    <h2>Financial Summary</h2>
    <p class="error">Error loading financial data: {result.error}</p>
  </section>
{:else if result.data && result.data.length > 0}
  <section class="sankey-section">
    <h2>
      Financial Summary
      {#if dateRange}
        <span class="date-range">{dateRange.from} to {dateRange.through}</span>
      {/if}
    </h2>

    {#if isF3}
      <F3SankeyComponent items={result.data as InputRow[]} {databaseName} {filingIds} />
    {:else}
      <F3XSankeyComponent items={result.data as F3XInputRow[]} {databaseName} {filingIds} />
    {/if}
  </section>
{:else}
  <section class="sankey-section">
    <h2>Financial Summary</h2>
    <p class="no-data">No financial data available for the {selectedCycle} cycle.</p>
  </section>
{/if}

<style>
  .sankey-section {
    margin-bottom: 2rem;
  }

  .sankey-section h2 {
    font-size: 1.25rem;
    margin: 0 0 1rem 0;
  }

  .date-range {
    font-size: 0.85rem;
    font-weight: normal;
    color: #666;
    margin-left: 0.5rem;
  }

  .error {
    color: #900;
  }

  .no-data {
    color: #666;
    font-style: italic;
  }
</style>

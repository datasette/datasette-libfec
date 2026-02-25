<script lang="ts">
  import { get } from 'svelte/store';
  import { databaseName, basePath } from '../stores';
  import { query } from '../api';
  import { useQuery } from '../useQuery.svelte';
  import { getReportLabel } from '../utils/reportCodes';

  interface Props {
    filerId: string;
    coverageFromDate: string;
    formType: 'F3' | 'F3X';
  }

  let { filerId, coverageFromDate, formType }: Props = $props();

  const dbName = get(databaseName);
  const base = get(basePath);

  interface AdjacentFiling {
    filing_id: string;
    coverage_from_date: string;
    coverage_through_date: string;
    report_code: string;
  }

  const prevResult = useQuery<AdjacentFiling[]>(async () => {
    const table = formType === 'F3' ? 'libfec_F3' : 'libfec_F3X';
    return await query(
      dbName,
      `WITH final AS (
        SELECT f.filing_id, f.coverage_from_date, f.coverage_through_date, f.report_code
        FROM ${table} f
        JOIN libfec_filings fil ON f.filing_id = fil.filing_id
        WHERE fil.filer_id = :filer_id
          AND f.coverage_from_date < :coverage_from_date
        ORDER BY f.coverage_from_date DESC
        LIMIT 1
      )
      SELECT * FROM final`,
      { filer_id: filerId, coverage_from_date: coverageFromDate }
    );
  });

  const nextResult = useQuery<AdjacentFiling[]>(async () => {
    const table = formType === 'F3' ? 'libfec_F3' : 'libfec_F3X';
    return await query(
      dbName,
      `WITH final AS (
        SELECT f.filing_id, f.coverage_from_date, f.coverage_through_date, f.report_code
        FROM ${table} f
        JOIN libfec_filings fil ON f.filing_id = fil.filing_id
        WHERE fil.filer_id = :filer_id
          AND f.coverage_from_date > :coverage_from_date
        ORDER BY f.coverage_from_date ASC
        LIMIT 1
      )
      SELECT * FROM final`,
      { filer_id: filerId, coverage_from_date: coverageFromDate }
    );
  });

  const prev = $derived(prevResult.data?.[0] ?? null);
  const next = $derived(nextResult.data?.[0] ?? null);

  function label(f: AdjacentFiling): string {
    const year = f.coverage_from_date?.substring(0, 4);
    const report = getReportLabel(f.report_code);
    return `${year} ${report}`;
  }
</script>

{#if prev || next}
  <nav class="filing-nav">
    <div class="nav-prev">
      {#if prev}
        <a href="{base}/filing/{prev.filing_id}">
          <span class="arrow">&larr;</span> Previous report
          <span class="filing-id">FEC-{prev.filing_id}</span><br />
          <span class="nav-detail">{label(prev)}</span>
        </a>
      {/if}
    </div>
    <div class="nav-next">
      {#if next}
        <a href="{base}/filing/{next.filing_id}">
          Next report
          <span class="filing-id">FEC-{next.filing_id}</span>
          <span class="arrow">&rarr;</span><br />
          <span class="nav-detail">{label(next)}</span>
        </a>
      {/if}
    </div>
  </nav>
{/if}

<style>
  .filing-nav {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    margin-top: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid #e0e0e0;
  }

  .nav-prev,
  .nav-next {
    flex: 1;
  }

  .nav-next {
    text-align: right;
  }

  .filing-nav a {
    color: #0066cc;
    text-decoration: none;
    font-size: 0.95rem;
    line-height: 1.4;
  }

  .filing-nav a:hover {
    text-decoration: underline;
  }

  .arrow {
    font-weight: 600;
  }

  .filing-id {
    color: #999;
    font-size: 0.85rem;
  }

  .nav-detail {
    font-size: 0.85rem;
    color: #666;
  }
</style>

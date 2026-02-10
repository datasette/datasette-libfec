<script lang="ts">
  import { get } from 'svelte/store';
  import { databaseName } from '../../stores';
  import { query } from '../../api';
  import { useQuery } from '../../useQuery.svelte';
  import { getStateName } from '../../utils/stateNames';

  interface StateContribution {
    contributor_state: string;
    total_contributions: number;
  }

  interface Props {
    filingId: string;
    homeState: string | null;
  }

  let { filingId, homeState }: Props = $props();

  const dbName = get(databaseName);

  async function fetchStateContributions(): Promise<StateContribution[]> {
    if (!filingId) return [];

    const sql = `
      SELECT
        contributor_state,
        SUM(contribution_amount) as total_contributions
      FROM libfec_schedule_a
      WHERE filing_id = :filing_id
        AND contributor_state IS NOT NULL
        AND contributor_state != ''
        AND memo_code != 'X'
      GROUP BY contributor_state
      ORDER BY total_contributions DESC
    `;
    return query(dbName, sql, { filing_id: filingId });
  }

  const contributions = useQuery(fetchStateContributions);

  function usd(value: number | null | undefined, round = false): string {
    if (value == null) return '$0';
    const v = round ? Math.round(value) : value;
    return '$' + v.toLocaleString();
  }

  function stateUrl(stateCode: string): string {
    const params = new URLSearchParams({
      _sort: 'rowid',
      contributor_state__exact: stateCode,
      filing_id__exact: filingId,
      form_type__exact: 'SA11AI',
      memo_code__not: 'X',
    });
    return `/${dbName}/libfec_schedule_a?${params}`;
  }

  const total = $derived(
    (contributions.data ?? []).reduce((sum, row) => sum + (row.total_contributions || 0), 0)
  );
  const N = 10;
  const topN = $derived((contributions.data ?? []).slice(0, N));
  const other = $derived(
    (contributions.data ?? [])
      .slice(N)
      .reduce((sum, row) => sum + (row.total_contributions || 0), 0)
  );
</script>

{#if contributions.isLoading}
  <div class="section-box">
    <h4>Individual Contributions by State</h4>
    <div class="loading">Loading...</div>
  </div>
{:else if contributions.data && contributions.data.length > 0}
  <div class="section-box">
    <h4>Individual Contributions by State</h4>
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th class="text-left">State</th>
            <th class="text-right">Amount</th>
            <th class="text-right">% of Total</th>
          </tr>
        </thead>
        <tbody>
          {#each topN as row}
            <tr>
              <td>
                <a href={stateUrl(row.contributor_state)}>{getStateName(row.contributor_state)}</a>
                {#if row.contributor_state === homeState}
                  <span class="home-badge">Home</span>
                {/if}
              </td>
              <td class="text-right">{usd(row.total_contributions, true)}</td>
              <td class="text-right muted">
                {(((row.total_contributions || 0) / total) * 100).toFixed(1)}%
              </td>
            </tr>
          {/each}
          {#if other > 0}
            <tr class="other-row">
              <td class="muted italic">Other ({(contributions.data?.length ?? 0) - 5} states)</td>
              <td class="text-right muted">{usd(other, true)}</td>
              <td class="text-right muted">
                {((other / total) * 100).toFixed(1)}%
              </td>
            </tr>
          {/if}
          <tr class="total-row">
            <td>Total</td>
            <td class="text-right">{usd(total)}</td>
            <td class="text-right">100.0%</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p class="info-note">Only includes individuals who have given $200 or more this cycle.</p>
  </div>
{/if}

<style>
  .section-box {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1.5rem;
  }

  .section-box h4 {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #2563eb;
  }

  .table-container {
    overflow-x: auto;
  }

  .data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
  }

  .data-table th,
  .data-table td {
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid #e5e5e5;
  }

  .data-table th {
    font-weight: 600;
    color: #374151;
    border-bottom: 2px solid #d1d5db;
  }

  .data-table tbody tr:hover {
    background: #f9fafb;
  }

  .text-left {
    text-align: left;
  }

  .text-right {
    text-align: right;
  }

  .muted {
    color: #6b7280;
  }

  .italic {
    font-style: italic;
  }

  .home-badge {
    display: inline-block;
    margin-left: 0.5rem;
    padding: 0.1rem 0.4rem;
    background: #dbeafe;
    color: #1e40af;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 3px;
  }

  .other-row td {
    border-bottom: 1px solid #e5e5e5;
  }

  .total-row {
    font-weight: 700;
    border-top: 2px solid #9ca3af;
  }

  .total-row td {
    padding-top: 0.75rem;
  }

  .loading {
    text-align: center;
    color: #6b7280;
    padding: 1rem;
  }

  .info-note {
    margin-top: 0.75rem;
    font-size: 0.8rem;
    color: #6b7280;
    font-style: italic;
  }
</style>

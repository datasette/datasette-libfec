<script lang="ts">
  import { get } from 'svelte/store';
  import { databaseName } from '../../stores';
  import { useQuery } from '../../useQuery.svelte';
  import { getStateName } from '../../utils/stateNames';
  import type { FilingScope } from '../../utils/filingScope';
  import { fetchFilingIds } from '../../utils/filingScope';
  import { query } from '../../api';
  import {
    fetchStateContributions,
    fetchScopeMetadata,
    buildStateUrl,
  } from './stateContributorsFetcher';

  interface Props {
    scope: FilingScope;
    homeState?: string | null;
    formTypeFilter?: string;
  }

  let { scope, homeState = null, formTypeFilter }: Props = $props();

  const dbName = get(databaseName);

  const contributions = useQuery(() => fetchStateContributions(dbName, scope));
  const metadata = useQuery(() => fetchScopeMetadata(dbName, scope));
  const filingIdsResult = useQuery(() => fetchFilingIds(dbName, scope, query));

  $effect(() => {
    scope;
    contributions.refetch?.();
    metadata.refetch?.();
    filingIdsResult.refetch?.();
  });

  const monthAbbrs = [
    'Jan.',
    'Feb.',
    'Mar.',
    'Apr.',
    'May',
    'Jun.',
    'Jul.',
    'Aug.',
    'Sep.',
    'Oct.',
    'Nov.',
    'Dec.',
  ];

  function formatDate(dateStr: string): string {
    const d = new Date(dateStr + 'T00:00:00');
    return `${monthAbbrs[d.getMonth()]} ${d.getDate()} ${d.getFullYear()}`;
  }

  function usd(value: number | null | undefined, round = false): string {
    if (value == null) return '$0';
    const v = round ? Math.round(value) : value;
    return '$' + v.toLocaleString();
  }

  function stateUrl(stateCode: string): string {
    return buildStateUrl(dbName, scope, stateCode, formTypeFilter, filingIdsResult.data);
  }

  const total = $derived(
    (contributions.data ?? []).reduce((sum, row) => sum + (row.total_contributions || 0), 0)
  );
  const subtitle = $derived(() => {
    const m = metadata.data;
    if (!m?.committee_name) return null;
    const parts = [`Top individual contributions to ${m.committee_name}`];
    if (m.coverage_from_date && m.coverage_through_date) {
      parts[0] += ` between ${formatDate(m.coverage_from_date)} and ${formatDate(m.coverage_through_date)}`;
    }
    return parts[0];
  });

  const sourceNote = $derived(() => {
    const formType = metadata.data?.form_type;
    if (!formType) return null;
    if (formTypeFilter === 'SA11AI') {
      return `Source: ${formType}, Schedule A, Line 11(a)(i)`;
    }
    return `Source: ${formType}, Schedule A`;
  });

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
    {#if subtitle()}
      <p class="subtitle">{subtitle()}</p>
    {/if}
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
                {#if homeState && row.contributor_state === homeState}
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
              <td class="muted italic">Other ({(contributions.data?.length ?? 0) - N} states)</td>
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
    {#if sourceNote()}
      <p class="info-note">{sourceNote()}</p>
    {/if}
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
    margin-bottom: 0.25rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #2563eb;
  }

  .subtitle {
    font-size: 0.85rem;
    color: #6b7280;
    margin-top: 0.5rem;
    margin-bottom: 1rem;
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

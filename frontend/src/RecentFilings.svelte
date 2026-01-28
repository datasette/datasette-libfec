<script lang="ts">
  import { query } from './api';
  import { useQuery } from './useQuery.svelte';

  interface Filing {
    filing_id: string;
    filer_name: string;
    report_code: string;
    cover_record_form: string;
    coverage_from_date: string;
    coverage_through_date: string;
    state: string;
  }

  const queryResp = useQuery<Filing[]>(() =>
    query("tmp", `
      SELECT
        *
      FROM
        libfec_filings
      ORDER BY
        filing_id DESC
      LIMIT 100
    `)
  );

  const filings = $derived(queryResp.data);
  const error = $derived(queryResp.error);
  const isLoading = $derived(queryResp.isLoading);
  const refetch = queryResp.refetch!;

  function formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }
</script>

<section class="recent-filings">
  <h2>Most Recent Filings</h2>

  {#if isLoading}
    <div class="loading">
      <p>Loading recent filings...</p>
    </div>
  {:else if error}
    <div class="error">
      <p>Error: {error}</p>
      <button onclick={refetch}>Retry</button>
    </div>
  {:else if !filings || filings.length === 0}
    <div class="empty">
      <p>No recent filings found.</p>
    </div>
  {:else}
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>Filing ID</th>
            <th>Committee Name</th>
            <th>Report Type</th>
            <th>Report Code</th>
            <th>Coverage From</th>
            <th>Coverage Through</th>
          </tr>
        </thead>
        <tbody>
          {#each filings as filing}
            <tr>
              <td class="filing-id">{filing.filing_id}</td>
              <td>{filing.filer_name}</td>
              <td>{filing.report_code}</td>
              <td class="form-type">{filing.cover_record_form}</td>
              <td>{formatDate(filing.coverage_from_date)}</td>
              <td>{formatDate(filing.coverage_through_date)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</section>

<style>
  .recent-filings {
    margin: 2em 0;
    padding-top: 2em;
    border-top: 2px solid #ddd;
  }

  .recent-filings h2 {
    margin-bottom: 1em;
  }

  .loading,
  .error,
  .empty {
    padding: 2em;
    text-align: center;
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 4px;
  }

  .error {
    background: #f8d7da;
    border-color: #f5c6cb;
    color: #721c24;
  }

  .error button {
    margin-top: 1em;
    padding: 0.5em 1em;
    background: #721c24;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .error button:hover {
    background: #5a161d;
  }

  .empty {
    color: #666;
  }

  .table-container {
    overflow-x: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    border: 1px solid #dee2e6;
    border-radius: 4px;
  }

  thead {
    background: #f8f9fa;
  }

  th {
    padding: 0.75em;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #dee2e6;
    white-space: nowrap;
  }

  td {
    padding: 0.75em;
    border-bottom: 1px solid #dee2e6;
  }

  tbody tr:last-child td {
    border-bottom: none;
  }

  tbody tr:hover {
    background: #f8f9fa;
  }

  .filing-id {
    font-family: monospace;
    color: #0066cc;
    font-weight: 500;
  }

  .form-type {
    font-family: monospace;
    font-weight: 600;
  }

  .state {
    font-family: monospace;
    text-transform: uppercase;
    font-weight: 500;
  }
</style>

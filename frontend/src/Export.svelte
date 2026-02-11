<script lang="ts">
  import { loadPageData } from './page_data/load.ts';
  import Breadcrumb from './components/Breadcrumb.svelte';

  interface ExportFilingInfo {
    filing_id: string;
    success: boolean;
    message: string | null;
    cover_record_form: string | null;
    filer_id: string | null;
    filer_name: string | null;
    coverage_from_date: string | null;
    coverage_through_date: string | null;
  }

  interface ExportInputInfo {
    id: number;
    input_type: string;
    input_value: string;
    cycle: number | null;
    filing_ids: string[];
  }

  interface ExportPageData {
    export_id: number;
    export_uuid: string | null;
    created_at: string | null;
    status: string | null;
    filings_count: number;
    cover_only: boolean;
    error_message: string | null;
    inputs: ExportInputInfo[];
    filings: ExportFilingInfo[];
    database_name: string;
    error: string | null;
  }

  const pageData = loadPageData<ExportPageData>();

  function formatDate(dateStr: string | null): string {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString();
  }

  function getStatusClass(status: string | null): string {
    switch (status) {
      case 'complete':
        return 'status-complete';
      case 'error':
        return 'status-error';
      case 'canceled':
        return 'status-canceled';
      case 'started':
        return 'status-running';
      default:
        return '';
    }
  }

  function getInputTypeLabel(type: string): string {
    switch (type) {
      case 'committee':
        return 'Committee';
      case 'committee_cycle':
        return 'Committee + Cycle';
      case 'committee_filing':
        return 'Filing';
      case 'candidate':
        return 'Candidate';
      default:
        return type;
    }
  }

  function getInputLink(input: ExportInputInfo): string | null {
    switch (input.input_type) {
      case 'committee':
      case 'committee_cycle':
        return `/-/libfec/committee/${input.input_value}`;
      case 'committee_filing':
        return `/-/libfec/filing/${input.input_value}`;
      case 'candidate':
        return `/-/libfec/candidate/${input.input_value}`;
      default:
        return null;
    }
  }
</script>

<div class="export-detail">
  <Breadcrumb
    items={[{ label: 'FEC Data', href: '/-/libfec' }, { label: `Export #${pageData.export_id}` }]}
  />

  <header>
    <h1>Export #{pageData.export_id}</h1>
    {#if pageData.status}
      <span class="status-badge {getStatusClass(pageData.status)}">
        {pageData.status}
      </span>
    {/if}
  </header>

  {#if pageData.error}
    <div class="error-box">{pageData.error}</div>
  {/if}

  <section class="info-section">
    <h2>Export Info</h2>
    <dl class="info-grid">
      <dt>Created</dt>
      <dd>{formatDate(pageData.created_at)}</dd>

      <dt>UUID</dt>
      <dd><code>{pageData.export_uuid ?? '-'}</code></dd>

      <dt>Filings Count</dt>
      <dd>{pageData.filings_count}</dd>

      <dt>Cover Only</dt>
      <dd>{pageData.cover_only ? 'Yes' : 'No'}</dd>

      {#if pageData.error_message}
        <dt>Error</dt>
        <dd class="error-text">{pageData.error_message}</dd>
      {/if}
    </dl>
  </section>

  {#if pageData.inputs.length > 0}
    <section class="info-section">
      <h2>Inputs ({pageData.inputs.length})</h2>
      <ul class="inputs-list">
        {#each pageData.inputs as input}
          <li>
            <span class="input-type">{getInputTypeLabel(input.input_type)}</span>
            {#if getInputLink(input)}
              <a href={getInputLink(input)} class="input-value">{input.input_value}</a>
            {:else}
              <code class="input-value">{input.input_value}</code>
            {/if}
            {#if input.cycle}
              <span class="input-cycle">({input.cycle})</span>
            {/if}
            {#if input.filing_ids.length > 0}
              <span class="resolved-count">
                &rarr; {input.filing_ids.length} filing{input.filing_ids.length !== 1 ? 's' : ''}
              </span>
            {/if}
          </li>
        {/each}
      </ul>
    </section>
  {/if}

  {#if pageData.filings.length > 0}
    <section class="info-section">
      <h2>Filings ({pageData.filings.length})</h2>
      <div class="filings-table-container">
        <table class="filings-table">
          <thead>
            <tr>
              <th>Filing ID</th>
              <th>Form</th>
              <th>Filer</th>
              <th>Coverage Period</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {#each pageData.filings as filing}
              <tr class:success={filing.success} class:failure={!filing.success}>
                <td>
                  <a href="/-/libfec/filing/{filing.filing_id}">
                    {filing.filing_id}
                  </a>
                </td>
                <td>{filing.cover_record_form ?? '-'}</td>
                <td>
                  {#if filing.filer_id}
                    <a href="/-/libfec/committee/{filing.filer_id}">
                      {filing.filer_name ?? filing.filer_id}
                    </a>
                  {:else}
                    {filing.filer_name ?? '-'}
                  {/if}
                </td>
                <td>
                  {#if filing.coverage_from_date && filing.coverage_through_date}
                    {filing.coverage_from_date} - {filing.coverage_through_date}
                  {:else}
                    -
                  {/if}
                </td>
                <td>
                  {#if filing.success}
                    <span class="badge badge-success">OK</span>
                  {:else}
                    <span class="badge badge-error" title={filing.message ?? ''}>Failed</span>
                  {/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </section>
  {:else if pageData.status === 'complete'}
    <section class="info-section">
      <p class="empty-message">No filings in this export.</p>
    </section>
  {/if}
</div>

<style>
  .export-detail {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1em;
  }

  header {
    display: flex;
    align-items: center;
    gap: 1em;
    margin-bottom: 1.5em;
  }

  h1 {
    margin: 0;
  }

  .status-badge {
    padding: 0.25em 0.75em;
    border-radius: 4px;
    font-weight: 600;
    font-size: 0.9em;
    text-transform: capitalize;
  }

  .status-complete {
    background: #d4edda;
    color: #155724;
  }

  .status-error {
    background: #f8d7da;
    color: #721c24;
  }

  .status-canceled {
    background: #fff3cd;
    color: #856404;
  }

  .status-running {
    background: #cce5ff;
    color: #004085;
  }

  .error-box {
    padding: 1em;
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
    border-radius: 4px;
    margin-bottom: 1.5em;
  }

  .info-section {
    margin-bottom: 2em;
  }

  .info-section h2 {
    font-size: 1.2em;
    border-bottom: 1px solid #dee2e6;
    padding-bottom: 0.5em;
    margin-bottom: 1em;
  }

  .info-grid {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 0.5em 1.5em;
    margin: 0;
    font-size: 0.95em;
  }

  dt {
    font-weight: 500;
    color: #666;
  }

  dd {
    margin: 0;
  }

  dd code {
    background: #f8f9fa;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
  }

  .error-text {
    color: #721c24;
  }

  .inputs-list {
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .inputs-list li {
    padding: 0.75em;
    background: #f8f9fa;
    border-radius: 4px;
    margin-bottom: 0.5em;
    display: flex;
    align-items: center;
    gap: 0.75em;
    flex-wrap: wrap;
  }

  .input-type {
    display: inline-block;
    padding: 0.2em 0.5em;
    background: #6c757d;
    color: white;
    font-size: 0.8em;
    border-radius: 3px;
    text-transform: uppercase;
  }

  .input-value {
    font-family: 'Courier New', monospace;
    color: #0066cc;
    text-decoration: none;
  }

  a.input-value:hover {
    text-decoration: underline;
  }

  code.input-value {
    background: white;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    color: inherit;
  }

  .input-cycle {
    color: #666;
    font-size: 0.9em;
  }

  .resolved-count {
    color: #28a745;
    font-size: 0.85em;
  }

  .filings-table-container {
    overflow-x: auto;
  }

  .filings-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9em;
  }

  .filings-table th,
  .filings-table td {
    padding: 0.75em;
    text-align: left;
    border-bottom: 1px solid #dee2e6;
  }

  .filings-table th {
    background: #f8f9fa;
    font-weight: 600;
  }

  .filings-table tr:hover {
    background: #f8f9fa;
  }

  .filings-table tr.success {
    background: #f8fff8;
  }

  .filings-table tr.failure {
    background: #fff8f8;
  }

  .filings-table a {
    color: #0066cc;
    text-decoration: none;
  }

  .filings-table a:hover {
    text-decoration: underline;
  }

  .badge {
    display: inline-block;
    padding: 0.2em 0.5em;
    font-size: 0.85em;
    font-weight: 500;
    border-radius: 3px;
  }

  .badge-success {
    background: #d4edda;
    color: #155724;
  }

  .badge-error {
    background: #f8d7da;
    color: #721c24;
    cursor: help;
  }

  .empty-message {
    color: #666;
    font-style: italic;
  }
</style>

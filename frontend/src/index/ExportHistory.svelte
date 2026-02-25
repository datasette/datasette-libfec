<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import createClient from 'openapi-fetch';
  import type { paths } from '../../api.d.ts';
  import { databaseName as databaseNameStore, basePath as basePathStore } from '../stores';

  interface ExportRecord {
    export_id: number;
    export_uuid: string;
    created_at: string;
    filings_count: number;
    cover_only: boolean;
    status: string;
    error_message: string | null;
  }

  interface ExportInput {
    id: number;
    input_type: string;
    input_value: string;
    cycle: number | null;
    filing_ids: string[];
  }

  interface ExportFiling {
    filing_id: string;
    success: boolean;
    message: string | null;
  }

  interface ExportDetail {
    status: string;
    export: ExportRecord;
    inputs: ExportInput[];
    filings: ExportFiling[];
  }

  interface ExportsListResponse {
    status: string;
    exports: ExportRecord[];
    message?: string;
  }

  const basePath = get(basePathStore);
  const dbName = get(databaseNameStore);
  const client = createClient<paths>({ baseUrl: '/' });

  let exports = $state<ExportRecord[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let selectedExport = $state<ExportDetail | null>(null);
  let loadingDetail = $state(false);

  onMount(() => {
    loadExports();
  });

  async function loadExports() {
    loading = true;
    error = null;
    try {
      const { data, error: fetchError } = await client.GET('/{database}/-/api/libfec/exports', {
        params: { path: { database: dbName } },
      });
      if (fetchError) {
        error = 'Failed to load exports';
      } else if (data) {
        exports = (data as unknown as ExportsListResponse).exports || [];
      }
    } catch (e) {
      error = `Failed to load exports: ${e}`;
    } finally {
      loading = false;
    }
  }

  async function loadExportDetail(exportId: number) {
    loadingDetail = true;
    try {
      const { data } = await client.GET('/{database}/-/api/libfec/exports/{export_id}', {
        params: { path: { database: dbName, export_id: exportId.toString() } },
      });
      if (data) {
        const response = data as unknown as ExportDetail;
        if (response.status === 'success' && response.export) {
          selectedExport = response;
        } else {
          console.error('Invalid export detail response:', data);
          selectedExport = null;
        }
      } else {
        selectedExport = null;
      }
    } catch (e) {
      console.error('Failed to load export detail:', e);
      selectedExport = null;
    } finally {
      loadingDetail = false;
    }
  }

  function formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleString();
  }

  function getStatusClass(status: string): string {
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

  function closeDetail() {
    selectedExport = null;
  }
</script>

<section class="export-history">
  <div class="header">
    <h2>Export History</h2>
    <button type="button" class="refresh-btn" onclick={loadExports} disabled={loading}>
      {loading ? 'Loading...' : 'Refresh'}
    </button>
  </div>

  {#if error}
    <div class="error-message">{error}</div>
  {:else if loading}
    <div class="loading">Loading export history...</div>
  {:else if exports.length === 0}
    <div class="empty">No exports yet. Use the Import Data form above to start an export.</div>
  {:else}
    <div class="exports-table-container">
      <table class="exports-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Status</th>
            <th>Filings</th>
            <th>Cover Only</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {#each exports as exp}
            <tr
              class:selected={selectedExport &&
                selectedExport.export &&
                selectedExport.export.export_id === exp.export_id}
            >
              <td class="date-cell">{formatDate(exp.created_at)}</td>
              <td>
                <span class="status-badge {getStatusClass(exp.status)}">
                  {exp.status}
                </span>
              </td>
              <td class="count-cell">{exp.filings_count}</td>
              <td class="bool-cell">{exp.cover_only ? 'Yes' : 'No'}</td>
              <td class="action-cell">
                <button
                  type="button"
                  class="detail-btn"
                  onclick={() => loadExportDetail(exp.export_id)}
                  disabled={loadingDetail}
                >
                  Details
                </button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}

  {#if selectedExport && selectedExport.export}
    <div class="detail-panel">
      <div class="detail-header">
        <h3>Export Details</h3>
        <button type="button" class="close-btn" onclick={closeDetail}>Close</button>
      </div>

      <div class="detail-content">
        <div class="detail-section">
          <h4>Export Info</h4>
          <dl>
            <dt>Export ID</dt>
            <dd><code>{selectedExport.export.export_uuid}</code></dd>
            <dt>Created</dt>
            <dd>{formatDate(selectedExport.export.created_at)}</dd>
            <dt>Status</dt>
            <dd>
              <span class="status-badge {getStatusClass(selectedExport.export.status)}">
                {selectedExport.export.status}
              </span>
            </dd>
            <dt>Filings Count</dt>
            <dd>{selectedExport.export.filings_count}</dd>
            <dt>Cover Only</dt>
            <dd>{selectedExport.export.cover_only ? 'Yes' : 'No'}</dd>
            {#if selectedExport.export.error_message}
              <dt>Error</dt>
              <dd class="error-text">{selectedExport.export.error_message}</dd>
            {/if}
          </dl>
        </div>

        {#if selectedExport.inputs && selectedExport.inputs.length > 0}
          <div class="detail-section">
            <h4>Inputs ({selectedExport.inputs.length})</h4>
            <ul class="inputs-list">
              {#each selectedExport.inputs as input}
                <li>
                  <span class="input-type">{input.input_type}</span>
                  <code class="input-value">
                    {#if input.input_type === 'committee'}
                      <a href={`${basePath}/committee/${input.input_value}`}>{input.input_value}</a>
                    {:else if input.input_type === 'committee_cycle'}
                      <a href={`${basePath}/committee/${input.input_value}`}>{input.input_value}</a>
                    {:else if input.input_type === 'committee_filing'}
                      <a href={`${basePath}/filing/${input.input_value}`}>{input.input_value}</a>
                    {:else}
                      {input.input_value}
                    {/if}
                  </code>
                  {#if input.cycle}
                    <span class="input-cycle">({input.cycle})</span>
                  {/if}
                  {#if input.filing_ids.length > 0}
                    <span class="resolved-count">
                      → {input.filing_ids.length} filing{input.filing_ids.length !== 1 ? 's' : ''}
                    </span>
                  {/if}
                </li>
              {/each}
            </ul>
          </div>
        {/if}

        {#if selectedExport.filings && selectedExport.filings.length > 0}
          <div class="detail-section">
            <h4>Filings ({selectedExport.filings.length})</h4>
            <div class="filings-list-container">
              <ul class="filings-list">
                {#each selectedExport.filings as filing}
                  <li class:success={filing.success} class:failure={!filing.success}>
                    <a href="{basePath}/filing/{filing.filing_id}" target="_blank">
                      {filing.filing_id}
                    </a>
                    {#if filing.message}
                      <span class="filing-message">- {filing.message}</span>
                    {/if}
                  </li>
                {/each}
              </ul>
            </div>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</section>

<style>
  .export-history {
    margin-top: 2em;
    border-top: 1px solid #dee2e6;
    padding-top: 1.5em;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1em;
  }

  h2 {
    margin: 0;
  }

  .refresh-btn {
    padding: 0.5em 1em;
    font-size: 0.9em;
    background: #6c757d;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .refresh-btn:hover:not(:disabled) {
    background: #5a6268;
  }

  .refresh-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .loading,
  .empty {
    padding: 2em;
    text-align: center;
    color: #6c757d;
    background: #f8f9fa;
    border-radius: 4px;
  }

  .error-message {
    padding: 1em;
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
    border-radius: 4px;
  }

  .exports-table-container {
    overflow-x: auto;
  }

  .exports-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9em;
  }

  .exports-table th,
  .exports-table td {
    padding: 0.75em;
    text-align: left;
    border-bottom: 1px solid #dee2e6;
  }

  .exports-table th {
    background: #f8f9fa;
    font-weight: 600;
  }

  .exports-table tr:hover {
    background: #f8f9fa;
  }

  .exports-table tr.selected {
    background: #e7f3ff;
  }

  .date-cell {
    white-space: nowrap;
  }

  .count-cell,
  .bool-cell {
    text-align: center;
  }

  .action-cell {
    text-align: right;
  }

  .status-badge {
    display: inline-block;
    padding: 0.25em 0.5em;
    font-size: 0.85em;
    font-weight: 500;
    border-radius: 3px;
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

  .detail-btn {
    padding: 0.35em 0.75em;
    font-size: 0.85em;
    background: #0066cc;
    color: white;
    border: none;
    border-radius: 3px;
    cursor: pointer;
  }

  .detail-btn:hover:not(:disabled) {
    background: #0052a3;
  }

  .detail-panel {
    margin-top: 1.5em;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    background: white;
  }

  .detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1em;
    background: #f8f9fa;
    border-bottom: 1px solid #dee2e6;
  }

  .detail-header h3 {
    margin: 0;
  }

  .close-btn {
    padding: 0.35em 0.75em;
    font-size: 0.85em;
    background: #6c757d;
    color: white;
    border: none;
    border-radius: 3px;
    cursor: pointer;
  }

  .close-btn:hover {
    background: #5a6268;
  }

  .detail-content {
    padding: 1em;
  }

  .detail-section {
    margin-bottom: 1.5em;
  }

  .detail-section:last-child {
    margin-bottom: 0;
  }

  .detail-section h4 {
    margin: 0 0 0.75em 0;
    font-size: 1em;
    color: #495057;
    border-bottom: 1px solid #e9ecef;
    padding-bottom: 0.5em;
  }

  dl {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 0.5em 1em;
    margin: 0;
    font-size: 0.9em;
  }

  dt {
    font-weight: 500;
    color: #6c757d;
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
    padding: 0.5em;
    background: #f8f9fa;
    border-radius: 3px;
    margin-bottom: 0.5em;
    font-size: 0.9em;
  }

  .input-type {
    display: inline-block;
    padding: 0.15em 0.4em;
    background: #6c757d;
    color: white;
    font-size: 0.8em;
    border-radius: 3px;
    text-transform: uppercase;
    margin-right: 0.5em;
  }

  .input-value {
    background: white;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
  }

  .input-cycle {
    color: #6c757d;
    font-size: 0.9em;
  }

  .resolved-count {
    color: #28a745;
    font-size: 0.85em;
    margin-left: 0.5em;
  }

  .filings-list-container {
    max-height: 300px;
    overflow-y: auto;
    border: 1px solid #e9ecef;
    border-radius: 4px;
  }

  .filings-list {
    margin: 0;
    padding: 0.5em;
    list-style: none;
    font-size: 0.85em;
  }

  .filings-list li {
    padding: 0.35em 0.5em;
    border-radius: 3px;
  }

  .filings-list li.success {
    background: #d4edda;
  }

  .filings-list li.failure {
    background: #f8d7da;
  }

  .filings-list a {
    font-family: 'Courier New', monospace;
    color: #0066cc;
    text-decoration: none;
  }

  .filings-list a:hover {
    text-decoration: underline;
  }

  .filing-message {
    color: #6c757d;
    font-size: 0.9em;
  }
</style>

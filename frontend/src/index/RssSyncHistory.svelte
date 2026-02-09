<script lang="ts">
  import { onMount } from 'svelte';

  interface RssSyncRecord {
    sync_id: number;
    sync_uuid: string;
    created_at: string;
    completed_at: string | null;
    since_filter: string | null;
    preset_filter: string | null;
    form_type_filter: string | null;
    committee_filter: string | null;
    state_filter: string | null;
    party_filter: string | null;
    total_feed_items: number | null;
    filtered_items: number | null;
    new_filings_count: number;
    exported_count: number;
    cover_only: boolean;
    status: string;
    error_message: string | null;
  }

  interface RssFilingRecord {
    filing_id: string;
    rss_pub_date: string | null;
    rss_title: string | null;
    committee_id: string | null;
    form_type: string | null;
    coverage_from: string | null;
    coverage_through: string | null;
    report_type: string | null;
    export_success: boolean;
    export_message: string | null;
  }

  interface RssSyncDetail {
    status: string;
    sync: RssSyncRecord;
    filings: RssFilingRecord[];
  }

  interface RssSyncsListResponse {
    status: string;
    syncs: RssSyncRecord[];
    message?: string;
  }

  let syncs = $state<RssSyncRecord[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let selectedSync = $state<RssSyncDetail | null>(null);
  let loadingDetail = $state(false);

  onMount(() => {
    loadSyncs();
  });

  async function loadSyncs() {
    loading = true;
    error = null;
    try {
      const response = await fetch('/-/api/libfec/rss/syncs');
      const data = await response.json();
      if (typeof data === 'string') {
        const parsed = JSON.parse(data) as RssSyncsListResponse;
        syncs = parsed.syncs || [];
      } else {
        syncs = (data as RssSyncsListResponse).syncs || [];
      }
    } catch (e) {
      error = `Failed to load RSS syncs: ${e}`;
    } finally {
      loading = false;
    }
  }

  async function loadSyncDetail(syncId: number) {
    loadingDetail = true;
    try {
      const response = await fetch(`/-/api/libfec/rss/syncs/${syncId}`);
      const data = (await response.json()) as RssSyncDetail;
      if (data.status === 'success' && data.sync) {
        selectedSync = data;
      } else {
        console.error('Invalid sync detail response:', data);
        selectedSync = null;
      }
    } catch (e) {
      console.error('Failed to load sync detail:', e);
      selectedSync = null;
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
    selectedSync = null;
  }

  function getActiveFilters(sync: RssSyncRecord): string[] {
    const filters: string[] = [];
    if (sync.since_filter) filters.push(`Since: ${sync.since_filter}`);
    if (sync.preset_filter) filters.push(`Preset: ${sync.preset_filter}`);
    if (sync.form_type_filter) filters.push(`Form: ${sync.form_type_filter}`);
    if (sync.committee_filter) filters.push(`Committee: ${sync.committee_filter}`);
    if (sync.state_filter) filters.push(`State: ${sync.state_filter}`);
    if (sync.party_filter) filters.push(`Party: ${sync.party_filter}`);
    return filters;
  }
</script>

<section class="rss-sync-history">
  <div class="header">
    <h2>RSS Sync History</h2>
    <button type="button" class="refresh-btn" onclick={loadSyncs} disabled={loading}>
      {loading ? 'Loading...' : 'Refresh'}
    </button>
  </div>

  {#if error}
    <div class="error-message">{error}</div>
  {:else if loading}
    <div class="loading">Loading RSS sync history...</div>
  {:else if syncs.length === 0}
    <div class="empty">No RSS syncs yet. Start the RSS watcher above to begin syncing filings.</div>
  {:else}
    <div class="syncs-table-container">
      <table class="syncs-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Status</th>
            <th>New</th>
            <th>Exported</th>
            <th>Filters</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {#each syncs as sync}
            <tr
              class:selected={selectedSync &&
                selectedSync.sync &&
                selectedSync.sync.sync_id === sync.sync_id}
            >
              <td class="date-cell">{formatDate(sync.created_at)}</td>
              <td>
                <span class="status-badge {getStatusClass(sync.status)}">
                  {sync.status}
                </span>
              </td>
              <td class="count-cell">{sync.new_filings_count}</td>
              <td class="count-cell">{sync.exported_count}</td>
              <td class="filters-cell">
                {#if getActiveFilters(sync).length > 0}
                  <span class="filters-preview">{getActiveFilters(sync).join(', ')}</span>
                {:else}
                  <span class="no-filters">None</span>
                {/if}
              </td>
              <td class="action-cell">
                <button
                  type="button"
                  class="detail-btn"
                  onclick={() => loadSyncDetail(sync.sync_id)}
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

  {#if selectedSync && selectedSync.sync}
    <div class="detail-panel">
      <div class="detail-header">
        <h3>Sync Details</h3>
        <button type="button" class="close-btn" onclick={closeDetail}>Close</button>
      </div>

      <div class="detail-content">
        <div class="detail-section">
          <h4>Sync Info</h4>
          <dl>
            <dt>Sync ID</dt>
            <dd><code>{selectedSync.sync.sync_uuid}</code></dd>
            <dt>Started</dt>
            <dd>{formatDate(selectedSync.sync.created_at)}</dd>
            {#if selectedSync.sync.completed_at}
              <dt>Completed</dt>
              <dd>{formatDate(selectedSync.sync.completed_at)}</dd>
            {/if}
            <dt>Status</dt>
            <dd>
              <span class="status-badge {getStatusClass(selectedSync.sync.status)}">
                {selectedSync.sync.status}
              </span>
            </dd>
            <dt>Total Feed Items</dt>
            <dd>{selectedSync.sync.total_feed_items ?? 'N/A'}</dd>
            <dt>Filtered Items</dt>
            <dd>{selectedSync.sync.filtered_items ?? 'N/A'}</dd>
            <dt>New Filings</dt>
            <dd>{selectedSync.sync.new_filings_count}</dd>
            <dt>Exported</dt>
            <dd>{selectedSync.sync.exported_count}</dd>
            <dt>Cover Only</dt>
            <dd>{selectedSync.sync.cover_only ? 'Yes' : 'No'}</dd>
            {#if selectedSync.sync.error_message}
              <dt>Error</dt>
              <dd class="error-text">{selectedSync.sync.error_message}</dd>
            {/if}
          </dl>
        </div>

        {#if getActiveFilters(selectedSync.sync).length > 0}
          <div class="detail-section">
            <h4>Filters</h4>
            <ul class="filters-list">
              {#each getActiveFilters(selectedSync.sync) as filter}
                <li>{filter}</li>
              {/each}
            </ul>
          </div>
        {/if}

        {#if selectedSync.filings && selectedSync.filings.length > 0}
          <div class="detail-section">
            <h4>Filings ({selectedSync.filings.length})</h4>
            <div class="filings-list-container">
              <table class="filings-table">
                <thead>
                  <tr>
                    <th>Filing ID</th>
                    <th>Committee</th>
                    <th>Form</th>
                    <th>Title</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {#each selectedSync.filings as filing}
                    <tr
                      class:success={filing.export_success}
                      class:failure={!filing.export_success}
                    >
                      <td>
                        <a href="/-/libfec/filing/{filing.filing_id}" target="_blank">
                          {filing.filing_id}
                        </a>
                      </td>
                      <td>
                        {#if filing.committee_id}
                          <a href="/-/libfec/committee/{filing.committee_id}" target="_blank">
                            {filing.committee_id}
                          </a>
                        {:else}
                          -
                        {/if}
                      </td>
                      <td>{filing.form_type || '-'}</td>
                      <td class="title-cell">{filing.rss_title || '-'}</td>
                      <td>
                        {#if filing.export_success}
                          <span class="success-icon">✓</span>
                        {:else}
                          <span class="failure-icon" title={filing.export_message || ''}>✗</span>
                        {/if}
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</section>

<style>
  .rss-sync-history {
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

  .syncs-table-container {
    overflow-x: auto;
  }

  .syncs-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9em;
  }

  .syncs-table th,
  .syncs-table td {
    padding: 0.75em;
    text-align: left;
    border-bottom: 1px solid #dee2e6;
  }

  .syncs-table th {
    background: #f8f9fa;
    font-weight: 600;
  }

  .syncs-table tr:hover {
    background: #f8f9fa;
  }

  .syncs-table tr.selected {
    background: #e7f3ff;
  }

  .date-cell {
    white-space: nowrap;
  }

  .count-cell {
    text-align: center;
  }

  .filters-cell {
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .filters-preview {
    font-size: 0.85em;
    color: #495057;
  }

  .no-filters {
    color: #adb5bd;
    font-style: italic;
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

  .filters-list {
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .filters-list li {
    padding: 0.5em;
    background: #f8f9fa;
    border-radius: 3px;
    margin-bottom: 0.5em;
    font-size: 0.9em;
  }

  .filings-list-container {
    max-height: 400px;
    overflow-y: auto;
    border: 1px solid #e9ecef;
    border-radius: 4px;
  }

  .filings-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85em;
  }

  .filings-table th,
  .filings-table td {
    padding: 0.5em 0.75em;
    text-align: left;
    border-bottom: 1px solid #e9ecef;
  }

  .filings-table th {
    background: #f8f9fa;
    font-weight: 600;
    position: sticky;
    top: 0;
  }

  .filings-table tr.success {
    background: #d4edda;
  }

  .filings-table tr.failure {
    background: #f8d7da;
  }

  .filings-table a {
    font-family: 'Courier New', monospace;
    color: #0066cc;
    text-decoration: none;
  }

  .filings-table a:hover {
    text-decoration: underline;
  }

  .title-cell {
    max-width: 250px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .success-icon {
    color: #155724;
    font-weight: bold;
  }

  .failure-icon {
    color: #721c24;
    font-weight: bold;
    cursor: help;
  }
</style>

<script lang="ts">
  import { onMount } from 'svelte';
  import createClient from 'openapi-fetch';
  import type { paths } from '../../api.d.ts';
  import SearchMultiSelect, { type SelectedItem } from '../components/SearchMultiSelect.svelte';

  const client = createClient<paths>({ baseUrl: '/' });

  interface ExportStatus {
    export_id?: string;
    phase?: string;
    completed?: number;
    total?: number;
    current?: string;
    current_filing_id?: string;
    total_exported?: number;
    warnings?: string[];
    error_message?: string;
    db_export_id?: number;
  }

  type ImportMode = 'search' | 'contests';

  let isLoading = $state(false);
  let cycle = $state(2026);
  let selectedSearchItems = $state<SelectedItem[]>([]);
  let exportStatus = $state<ExportStatus | null>(null);
  let exportRunning = $state(false);
  let importMode = $state<ImportMode>('search');
  let contestsInput = $state('');
  let contestsValidationError = $state<string | null>(null);
  let waitingForExport = $state(false); // Track if we started an export and are waiting

  // Regex for contest codes: 2-letter state + 2-digit district (e.g., CA01, TX30)
  const CONTEST_REGEX = /^[A-Z]{2}\d{2}$/;

  function parseContests(input: string): string[] {
    return input
      .toUpperCase()
      .split(/[\s,]+/)
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
  }

  function validateContests(input: string): { valid: boolean; codes: string[]; errors: string[] } {
    const codes = parseContests(input);
    const errors: string[] = [];
    const validCodes: string[] = [];

    for (const code of codes) {
      if (CONTEST_REGEX.test(code)) {
        validCodes.push(code);
      } else {
        errors.push(`"${code}" is not a valid contest code (expected format: CA01, TX30, etc.)`);
      }
    }

    return { valid: errors.length === 0, codes: validCodes, errors };
  }

  function handleContestsInput() {
    if (contestsInput.trim() === '') {
      contestsValidationError = null;
      return;
    }
    const { valid, errors } = validateContests(contestsInput);
    contestsValidationError = valid ? null : errors.join('; ');
  }

  function isActivelyExporting(): boolean {
    console.log(exportStatus?.phase);
    return (
      exportStatus != null &&
      (exportStatus.phase === 'sourcing' ||
        exportStatus.phase === 'downloading_bulk' ||
        exportStatus.phase === 'exporting')
    );
  }

  onMount(() => {
    loadExportStatus();
    // Poll for status updates while an export might be running
    const statusInterval = setInterval(loadExportStatus, 1000);

    return () => {
      clearInterval(statusInterval);
    };
  });

  async function loadExportStatus() {
    try {
      const { data, error } = await client.GET('/-/api/libfec/export/status');
      if (data && !error) {
        const status = data as unknown as ExportStatus;
        exportStatus = status;
        exportRunning = isActivelyExporting();

        // If an export is actively running, track it so we redirect when complete
        if (exportRunning) {
          waitingForExport = true;
        }

        // Redirect to export detail page when our export completes
        if (waitingForExport && status.phase === 'complete' && status.db_export_id) {
          waitingForExport = false;
          window.location.href = `/-/libfec/exports/${status.db_export_id}`;
        }
      }
    } catch (error) {
      console.error('Error loading export status:', error);
    }
  }

  function formatProgress(): string {
    if (!exportStatus) return 'Idle';

    const phase = exportStatus.phase || 'idle';

    switch (phase) {
      case 'idle':
        return 'Idle';
      case 'sourcing':
        if (exportStatus.total && exportStatus.total > 0) {
          const count = exportStatus.completed || 0;
          const total = exportStatus.total;
          return `Finding filings: ${count}/${total}`;
        }
        return 'Finding filings...';
      case 'downloading_bulk':
        if (exportStatus.total && exportStatus.total > 0) {
          const count = exportStatus.completed || 0;
          const total = exportStatus.total;
          const percent = Math.round((count / total) * 100);
          return `Downloading: ${count}/${total} (${percent}%)`;
        }
        return 'Downloading bulk data...';
      case 'exporting':
        if (exportStatus.total && exportStatus.total > 0) {
          const count = exportStatus.completed || 0;
          const total = exportStatus.total;
          const percent = Math.round((count / total) * 100);
          return `Exporting: ${count}/${total} filings (${percent}%)`;
        }
        return 'Exporting filings...';
      case 'complete':
        return `Complete: ${exportStatus.total_exported || 0} filings exported`;
      case 'canceled':
        return 'Export canceled';
      case 'error':
        return 'Error';
      default:
        return phase;
    }
  }

  function handleSearchSelection(items: SelectedItem[]) {
    selectedSearchItems = items;
  }

  async function onSubmit(e: SubmitEvent) {
    e.preventDefault();

    let filingIds: string[];

    if (importMode === 'search') {
      if (selectedSearchItems.length === 0) {
        alert('Please select a candidate or committee to import.');
        return;
      }
      filingIds = selectedSearchItems.map((item) => item.id);
    } else {
      // Contests mode
      if (contestsInput.trim() === '') {
        alert('Please enter at least one contest code.');
        return;
      }
      const { valid, codes, errors } = validateContests(contestsInput);
      if (!valid) {
        alert(`Invalid contest codes:\n${errors.join('\n')}`);
        return;
      }
      filingIds = codes;
    }

    isLoading = true;
    try {
      const { error } = await client.POST('/-/api/libfec/export/start', {
        body: {
          filings: filingIds,
          cycle: cycle,
        },
      });
      if (error) {
        alert(`Error starting import: ${JSON.stringify(error)}`);
        return;
      }
      // Mark that we're waiting for this export to complete
      waitingForExport = true;
      // Clear inputs after starting import
      if (importMode === 'search') {
        selectedSearchItems = [];
      } else {
        contestsInput = '';
        contestsValidationError = null;
      }
      // Immediately load status
      await loadExportStatus();
    } finally {
      isLoading = false;
    }
  }

  async function cancelExport() {
    isLoading = true;
    try {
      const { error } = await client.POST('/-/api/libfec/export/cancel', {});
      if (error) {
        alert(`Error canceling export: ${JSON.stringify(error)}`);
        return;
      }
      await loadExportStatus();
    } finally {
      isLoading = false;
    }
  }
</script>

<section class="import-section">
  <h2>Import Data</h2>

  {#if exportRunning && exportStatus}
    <div class="export-status running">
      <strong>Export in Progress</strong>

      <div class="progress-section">
        <div class="progress-status">
          Status: <strong>{formatProgress()}</strong>
        </div>

        {#if exportStatus.total && exportStatus.total > 0}
          <div class="progress-bar">
            <div
              class="progress-fill"
              style="width: {((exportStatus.completed || 0) / exportStatus.total) * 100}%"
            ></div>
          </div>
        {/if}

        {#if exportStatus.phase === 'downloading_bulk' && exportStatus.current}
          <div class="current-item">
            Downloading: <code>{exportStatus.current}</code>
          </div>
        {/if}

        {#if exportStatus.phase === 'exporting' && exportStatus.current_filing_id}
          <div class="current-item">
            Processing: <code>{exportStatus.current_filing_id}</code>
          </div>
        {/if}

        {#if exportStatus.phase === 'error' && exportStatus.error_message}
          <div class="error-message">
            <strong>Error:</strong>
            {exportStatus.error_message}
          </div>
        {/if}
      </div>

      <button type="button" class="button-danger" disabled={isLoading} onclick={cancelExport}>
        {isLoading ? 'Canceling...' : 'Cancel Export'}
      </button>
    </div>
  {:else}
    {#if exportStatus && exportStatus.phase === 'complete'}
      <div class="export-status complete">
        <strong>Last Export Complete</strong>
        <div class="complete-info">
          Exported {exportStatus.total_exported || 0} filings
          {#if exportStatus.warnings && exportStatus.warnings.length > 0}
            <div class="warnings">
              <strong>Warnings ({exportStatus.warnings.length}):</strong>
              <ul>
                {#each exportStatus.warnings as warning}
                  <li>{warning}</li>
                {/each}
              </ul>
            </div>
          {/if}
        </div>
      </div>
    {/if}

    {#if exportStatus && exportStatus.phase === 'error'}
      <div class="export-status error">
        <strong>Last Export Failed</strong>
        <div class="error-message">
          {exportStatus.error_message || 'Unknown error'}
        </div>
      </div>
    {/if}

    <form onsubmit={onSubmit}>
      <!-- Mode Toggle -->
      <div class="form-group">
        <div class="mode-toggle">
          <button
            type="button"
            class="mode-btn"
            class:active={importMode === 'search'}
            onclick={() => (importMode = 'search')}
          >
            Candidates / Committees
          </button>
          <button
            type="button"
            class="mode-btn"
            class:active={importMode === 'contests'}
            onclick={() => (importMode = 'contests')}
          >
            Contests
          </button>
        </div>
      </div>

      {#if importMode === 'search'}
        <!-- Search Component -->
        <div class="form-group">
          <div style="font-weight: bold; margin-bottom: 0.5em;">
            Search for Candidate or Committee
          </div>
          <SearchMultiSelect
            bind:selected={selectedSearchItems}
            {cycle}
            placeholder="Search for candidate or committee..."
            onselect={handleSearchSelection}
          />
          <small>Search by name and select a candidate or committee to import</small>
        </div>
      {:else}
        <!-- Contests Input -->
        <div class="form-group">
          <label for="contests"> Contest Codes </label>
          <input
            type="text"
            id="contests"
            name="contests"
            bind:value={contestsInput}
            oninput={handleContestsInput}
            placeholder="CA01, TX30, NY14..."
            class:invalid={contestsValidationError !== null}
          />
          <small>Enter contest codes separated by commas or spaces (e.g., CA01, TX30, NY14)</small>
          {#if contestsValidationError}
            <div class="validation-error">{contestsValidationError}</div>
          {/if}
        </div>
      {/if}

      <!-- Cycle Input -->
      <div class="form-group">
        <label for="cycle"> Election Cycle </label>
        <select id="cycle" name="cycle" bind:value={cycle}>
          <option value={2026}>2026</option>
          <option value={2024}>2024</option>
          <option value={2022}>2022</option>
        </select>
      </div>

      <!-- Submit Button -->
      <button
        type="submit"
        disabled={isLoading ||
          (importMode === 'search'
            ? selectedSearchItems.length === 0
            : contestsInput.trim() === '' || contestsValidationError !== null)}
      >
        {isLoading ? 'Starting...' : 'Import Data'}
      </button>
    </form>
  {/if}
</section>

<style>
  .import-section {
    flex: 1;
  }

  .form-group {
    margin-bottom: 1.5em;
  }

  .form-group label {
    display: block;
    font-weight: bold;
    margin-bottom: 0.5em;
  }

  .form-group select,
  .form-group input[type='text'] {
    max-width: 400px;
    padding: 0.5em;
    font-size: 1em;
    border: 1px solid #ccc;
    border-radius: 4px;
    width: 100%;
    box-sizing: border-box;
  }

  .form-group input[type='text'].invalid {
    border-color: #dc3545;
  }

  .mode-toggle {
    display: flex;
    gap: 0;
    border: 1px solid #ccc;
    border-radius: 4px;
    overflow: hidden;
    max-width: 400px;
  }

  .mode-btn {
    flex: 1;
    padding: 0.5em 1em;
    font-size: 0.9em;
    background: #f8f9fa;
    color: #495057;
    border: none;
    border-right: 1px solid #ccc;
    cursor: pointer;
    transition:
      background 0.2s,
      color 0.2s;
  }

  .mode-btn:last-child {
    border-right: none;
  }

  .mode-btn:hover:not(.active) {
    background: #e9ecef;
  }

  .mode-btn.active {
    background: #0066cc;
    color: white;
  }

  .validation-error {
    color: #dc3545;
    font-size: 0.85em;
    margin-top: 0.5em;
  }

  small {
    display: block;
    color: #666;
    font-size: 0.85em;
    margin-top: 0.5em;
  }

  button {
    padding: 0.75em 1.5em;
    font-size: 1em;
    background: #0066cc;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  button:hover:not(:disabled) {
    background: #0052a3;
  }

  button:disabled {
    background: #999;
    cursor: not-allowed;
  }

  .button-danger {
    background: #dc3545;
  }

  .button-danger:hover:not(:disabled) {
    background: #c82333;
  }

  .export-status {
    padding: 1.5em;
    border-radius: 4px;
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    margin-bottom: 1.5em;
  }

  .export-status.running {
    background: #cce5ff;
    border-color: #b8daff;
  }

  .export-status.complete {
    background: #d4edda;
    border-color: #c3e6cb;
  }

  .export-status.error {
    background: #f8d7da;
    border-color: #f5c6cb;
  }

  .export-status strong {
    display: block;
    margin-bottom: 1em;
    font-size: 1.1em;
  }

  .progress-section {
    margin: 1em 0;
    padding: 1em;
    background: white;
    border-radius: 4px;
  }

  .progress-status {
    font-size: 0.95em;
    margin-bottom: 0.75em;
  }

  .progress-bar {
    height: 24px;
    background: #e9ecef;
    border-radius: 12px;
    overflow: hidden;
    margin: 0.75em 0;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #0066cc, #0052a3);
    transition: width 0.3s ease;
  }

  .current-item {
    margin-top: 0.75em;
    font-size: 0.9em;
    color: #495057;
  }

  .current-item code {
    background: #f8f9fa;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
  }

  .complete-info {
    padding: 0.5em 0;
  }

  .warnings {
    margin-top: 1em;
    padding: 0.75em;
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 4px;
    font-size: 0.9em;
  }

  .warnings ul {
    margin: 0.5em 0 0 1.5em;
    padding: 0;
  }

  .warnings li {
    margin: 0.25em 0;
  }

  .error-message {
    margin-top: 0.75em;
    padding: 0.75em;
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
    border-radius: 4px;
    font-size: 0.9em;
  }
</style>

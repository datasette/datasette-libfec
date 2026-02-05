<script lang="ts">
  import { onMount } from 'svelte';
  import createClient from "openapi-fetch";
  import type { paths } from "../../api.d.ts";

  const client = createClient<paths>({ baseUrl: "/" });

  interface RssStatus {
    enabled: boolean;
    running: boolean;
    phase: string;
    interval_seconds: number | null;
    seconds_until_next_sync: number | null;
    exported_count: number;
    total_count: number;
    error_message: string | null;
  }

  interface SyncRecord {
    sync_id: number;
    sync_uuid: string;
    created_at: string;
    completed_at: string | null;
    status: string;
    exported_count: number;
    total_feed_items: number | null;
    error_message: string | null;
  }

  let status = $state<RssStatus | null>(null);
  let syncs = $state<SyncRecord[]>([]);

  // Client-side countdown tracking
  let nextSyncTimestamp = $state<Date | null>(null);
  let secondsRemaining = $state<number | null>(null);

  function isActivelySyncing(): boolean {
    return status != null &&
           (status.phase === 'fetching' || status.phase === 'exporting' || status.phase === 'syncing');
  }

  onMount(() => {
    loadStatus();
    loadSyncs();

    // Update countdown every second
    const countdownInterval = setInterval(() => {
      if (nextSyncTimestamp && status?.running && !isActivelySyncing()) {
        const now = Date.now();
        const remaining = Math.floor((nextSyncTimestamp.getTime() - now) / 1000);
        secondsRemaining = Math.max(0, remaining);
      }
    }, 1000);

    // Poll server for status updates
    const statusInterval = setInterval(() => {
      loadStatus();
      if (isActivelySyncing()) {
        loadSyncs();
      }
    }, isActivelySyncing() ? 2000 : 10000);

    // Refresh sync history periodically
    const syncsInterval = setInterval(() => {
      loadSyncs();
    }, 30000);

    return () => {
      clearInterval(countdownInterval);
      clearInterval(statusInterval);
      clearInterval(syncsInterval);
    };
  });

  async function loadStatus() {
    try {
      const { data, error } = await client.GET("/-/api/libfec/rss/status");
      if (data && !error) {
        status = data as unknown as RssStatus;

        if (status.seconds_until_next_sync !== null && status.seconds_until_next_sync !== undefined) {
          nextSyncTimestamp = new Date(Date.now() + status.seconds_until_next_sync * 1000);
          secondsRemaining = status.seconds_until_next_sync;
        } else {
          nextSyncTimestamp = null;
          secondsRemaining = null;
        }
      }
    } catch (error) {
      console.error('Error loading RSS status:', error);
    }
  }

  async function loadSyncs() {
    try {
      const { data, error } = await client.GET("/-/api/libfec/rss/syncs");
      if (data && !error) {
        syncs = (data as any).syncs || [];
      }
    } catch (error) {
      console.error('Error loading sync history:', error);
    }
  }

  function formatDuration(seconds: number): string {
    if (seconds <= 0) return "now";
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    if (minutes < 60) {
      return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
  }

  function formatProgress(): string {
    if (!status) return "Unknown";
    const phase = status.phase || "idle";

    switch (phase) {
      case "idle":
        return "Idle";
      case "syncing":
        return "Starting sync...";
      case "fetching":
        return "Fetching RSS feed...";
      case "exporting":
        if (status.total_count && status.total_count > 0) {
          const count = status.exported_count || 0;
          const total = status.total_count;
          const percent = Math.round((count / total) * 100);
          return `Exporting: ${count}/${total} (${percent}%)`;
        }
        return "Exporting filings...";
      case "complete":
        return "Sync complete";
      case "error":
        return "Error";
      default:
        return phase;
    }
  }

  function getNextSyncLabel(): string {
    if (!status?.running) return "";
    if (isActivelySyncing()) return "syncing now";
    if (secondsRemaining === null) return "starting soon";
    return formatDuration(secondsRemaining);
  }

  function getNextSyncTooltip(): string {
    if (!nextSyncTimestamp) return "";
    return nextSyncTimestamp.toLocaleString();
  }

  function formatDateTime(isoString: string): string {
    const date = new Date(isoString);
    return date.toLocaleString();
  }

  function syncStatusBadge(syncStatus: string): string {
    switch (syncStatus) {
      case 'completed': return 'badge-success';
      case 'running': return 'badge-info';
      case 'failed': return 'badge-danger';
      default: return 'badge-secondary';
    }
  }
</script>

<section class="rss-section">
  <h2>RSS Feed Watcher</h2>

  {#if status === null}
    <p>Loading...</p>
  {:else if status.running}
    <div class="status-card enabled">
      <div class="status-header">
        <span class="status-badge running">Running</span>
        <span class="status-indicator">
          {#if isActivelySyncing()}
            <span class="pulse"></span> Syncing
          {:else}
            Next sync: <strong class="countdown" title={getNextSyncTooltip()}>{getNextSyncLabel()}</strong>
          {/if}
        </span>
      </div>

      <div class="config-display">
        <div class="config-item">
          <span class="label">Interval:</span>
          <span class="value">{status.interval_seconds}s</span>
        </div>
      </div>

      {#if isActivelySyncing()}
        <div class="progress-section">
          <div class="progress-label">{formatProgress()}</div>
          {#if status.total_count > 0}
            <div class="progress-bar">
              <div
                class="progress-fill"
                style="width: {(status.exported_count / status.total_count) * 100}%"
              ></div>
            </div>
          {/if}
        </div>
      {/if}

      {#if status.error_message}
        <div class="error-box">
          <strong>Error:</strong> {status.error_message}
        </div>
      {/if}
    </div>
  {:else}
    <div class="status-card disabled">
      <p>RSS watcher is not running.</p>
      <p class="hint">To enable, add <code>rss-sync-interval-seconds</code> to your datasette.yaml plugin config:</p>
      <pre>plugins:
  datasette-libfec:
    rss-sync-interval-seconds: 60</pre>
    </div>
  {/if}

  {#if syncs.length > 0}
    <div class="sync-history">
      <h3>Recent Syncs</h3>
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Status</th>
            <th>Exported</th>
            <th>Feed Items</th>
          </tr>
        </thead>
        <tbody>
          {#each syncs as sync}
            <tr>
              <td>{formatDateTime(sync.created_at)}</td>
              <td><span class="badge {syncStatusBadge(sync.status)}">{sync.status}</span></td>
              <td>{sync.exported_count}</td>
              <td>{sync.total_feed_items ?? '-'}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</section>

<style>
  .rss-section {
    flex: 1;
  }

  .status-card {
    padding: 1.5em;
    border-radius: 8px;
    margin-bottom: 1.5em;
  }

  .status-card.enabled {
    background: #d4edda;
    border: 1px solid #c3e6cb;
  }

  .status-card.disabled {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
  }

  .status-card.disabled .hint {
    color: #666;
    font-size: 0.9em;
    margin-top: 1em;
  }

  .status-card.disabled pre {
    background: #e9ecef;
    padding: 1em;
    border-radius: 4px;
    font-size: 0.85em;
    overflow-x: auto;
  }

  .status-card.disabled code {
    background: #e9ecef;
    padding: 0.1em 0.3em;
    border-radius: 3px;
  }

  .status-header {
    display: flex;
    align-items: center;
    gap: 1em;
    margin-bottom: 1em;
  }

  .status-badge {
    padding: 0.25em 0.75em;
    border-radius: 4px;
    font-weight: 600;
    font-size: 0.9em;
  }

  .status-badge.running {
    background: #28a745;
    color: white;
  }

  .status-indicator {
    font-size: 0.95em;
    display: flex;
    align-items: center;
    gap: 0.5em;
  }

  .countdown {
    cursor: help;
    border-bottom: 1px dotted currentColor;
  }

  .pulse {
    width: 8px;
    height: 8px;
    background: #28a745;
    border-radius: 50%;
    animation: pulse 1.5s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.2); }
  }

  .config-display {
    display: flex;
    gap: 2em;
    padding: 0.75em 1em;
    background: white;
    border-radius: 4px;
    margin-bottom: 1em;
    font-size: 0.9em;
  }

  .config-item {
    display: flex;
    gap: 0.5em;
  }

  .config-item .label {
    color: #666;
  }

  .config-item .value {
    font-weight: 600;
  }

  .progress-section {
    padding: 1em;
    background: white;
    border-radius: 4px;
    margin-bottom: 1em;
  }

  .progress-label {
    font-size: 0.9em;
    margin-bottom: 0.5em;
  }

  .progress-bar {
    height: 20px;
    background: #e9ecef;
    border-radius: 10px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #28a745, #20c997);
    transition: width 0.3s ease;
  }

  .error-box {
    padding: 0.75em 1em;
    background: #f8d7da;
    border: 1px solid #f5c6cb;
    border-radius: 4px;
    color: #721c24;
    margin-bottom: 1em;
    font-size: 0.9em;
  }

  .sync-history {
    margin-top: 2em;
  }

  .sync-history h3 {
    margin-bottom: 0.75em;
    font-size: 1.1em;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9em;
  }

  th, td {
    padding: 0.5em 0.75em;
    text-align: left;
    border-bottom: 1px solid #dee2e6;
  }

  th {
    background: #f8f9fa;
    font-weight: 600;
  }

  .badge {
    padding: 0.2em 0.5em;
    border-radius: 3px;
    font-size: 0.85em;
    font-weight: 500;
  }

  .badge-success {
    background: #d4edda;
    color: #155724;
  }

  .badge-info {
    background: #cce5ff;
    color: #004085;
  }

  .badge-danger {
    background: #f8d7da;
    color: #721c24;
  }

  .badge-secondary {
    background: #e9ecef;
    color: #495057;
  }
</style>

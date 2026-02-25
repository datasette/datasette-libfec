<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import createClient from 'openapi-fetch';
  import type { paths } from '../../api.d.ts';
  import { databaseName as databaseNameStore } from '../stores';

  const dbName = get(databaseNameStore);
  const client = createClient<paths>({ baseUrl: '/' });

  type RssStatus = NonNullable<
    paths['/{database}/-/api/libfec/rss/status']['get']['responses']['200']['content']['application/json']
  >;
  type RssConfig = NonNullable<
    paths['/{database}/-/api/libfec/rss/config']['get']['responses']['200']['content']['application/json']
  >;

  let status = $state<RssStatus | null>(null);
  let config = $state<RssConfig | null>(null);
  let saving = $state(false);

  // Form state
  let formIntervalSeconds = $state(60);
  let formCoverOnly = $state(true);
  let formStateFilter = $state('');
  let formSinceDuration = $state('1 day');

  // Client-side countdown
  let nextSyncTimestamp = $state<Date | null>(null);
  let secondsRemaining = $state<number | null>(null);

  function isActivelySyncing(): boolean {
    return (
      status != null &&
      (status.phase === 'fetching' || status.phase === 'exporting' || status.phase === 'syncing')
    );
  }

  onMount(() => {
    loadStatus();
    loadConfig();

    const countdownInterval = setInterval(() => {
      if (nextSyncTimestamp && status?.running && !isActivelySyncing()) {
        const remaining = Math.floor((nextSyncTimestamp.getTime() - Date.now()) / 1000);
        secondsRemaining = Math.max(0, remaining);
      }
    }, 1000);

    const statusInterval = setInterval(
      () => {
        loadStatus();
      },
      isActivelySyncing() ? 2000 : 5000
    );

    return () => {
      clearInterval(countdownInterval);
      clearInterval(statusInterval);
    };
  });

  async function loadStatus() {
    const { data } = await client.GET('/{database}/-/api/libfec/rss/status', {
      params: { path: { database: dbName } },
    });
    if (!data) return;
    status = data;

    if (data.seconds_until_next_sync != null) {
      nextSyncTimestamp = new Date(Date.now() + data.seconds_until_next_sync * 1000);
      secondsRemaining = data.seconds_until_next_sync;
    } else {
      nextSyncTimestamp = null;
      secondsRemaining = null;
    }
  }

  async function loadConfig() {
    const { data } = await client.GET('/{database}/-/api/libfec/rss/config', {
      params: { path: { database: dbName } },
    });
    if (!data) return;
    config = data;
    formIntervalSeconds = data.interval_seconds;
    formCoverOnly = data.cover_only;
    formStateFilter = data.state_filter ?? '';
    formSinceDuration = data.since_duration;
  }

  async function toggleEnabled() {
    if (!config) return;
    saving = true;
    const { data } = await client.POST('/{database}/-/api/libfec/rss/config/update', {
      params: { path: { database: dbName } },
      body: { enabled: !config.enabled },
    });
    if (data) {
      config = data as unknown as RssConfig;
    }
    await loadStatus();
    saving = false;
  }

  async function saveSettings() {
    saving = true;
    const { data } = await client.POST('/{database}/-/api/libfec/rss/config/update', {
      params: { path: { database: dbName } },
      body: {
        interval_seconds: formIntervalSeconds,
        cover_only: formCoverOnly,
        state_filter: formStateFilter || null,
        since_duration: formSinceDuration,
      },
    });
    if (data) {
      config = data as unknown as RssConfig;
    }
    await loadStatus();
    saving = false;
  }

  function formatDuration(seconds: number): string {
    if (seconds <= 0) return 'now';
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
    if (!status) return '';
    switch (status.phase) {
      case 'idle':
        return 'Idle';
      case 'syncing':
        return 'Starting sync...';
      case 'fetching':
        return 'Fetching RSS feed...';
      case 'exporting':
        if (status.total_count > 0) {
          const pct = Math.round((status.exported_count / status.total_count) * 100);
          return `Exporting: ${status.exported_count}/${status.total_count} (${pct}%)`;
        }
        return 'Exporting filings...';
      case 'complete':
        return 'Sync complete';
      case 'waiting':
        return 'Waiting for next sync';
      case 'error':
        return 'Error';
      default:
        return status.phase;
    }
  }
</script>

<section class="rss-section">
  <h2>RSS Feed Watcher</h2>

  {#if status === null || config === null}
    <p>Loading...</p>
  {:else}
    <div class="status-card" class:enabled={config.enabled} class:disabled={!config.enabled}>
      <div class="status-header">
        {#if config.enabled}
          <span class="status-badge running">Enabled</span>
          <span class="status-indicator">
            {#if isActivelySyncing()}
              <span class="pulse"></span> {formatProgress()}
            {:else if secondsRemaining != null}
              Next sync: <strong class="countdown">{formatDuration(secondsRemaining)}</strong>
            {:else}
              Starting...
            {/if}
          </span>
        {:else}
          <span class="status-badge disabled-badge">Disabled</span>
        {/if}
        <button
          class="toggle-btn"
          class:enabled={config.enabled}
          onclick={toggleEnabled}
          disabled={saving}
        >
          {saving ? '...' : config.enabled ? 'Disable' : 'Enable'}
        </button>
      </div>

      {#if config.enabled && isActivelySyncing() && status.total_count > 0}
        <div class="progress-section">
          <div class="progress-bar">
            <div
              class="progress-fill"
              style="width: {(status.exported_count / status.total_count) * 100}%"
            ></div>
          </div>
        </div>
      {/if}

      {#if status.error_message}
        <div class="error-box">
          <strong>Error:</strong>
          {status.error_message}
        </div>
      {/if}

      <div class="config-form">
        <h3>Settings</h3>
        <div class="form-grid">
          <label class="form-label" for="rss-interval">Interval (seconds)</label>
          <input id="rss-interval" type="number" min="10" bind:value={formIntervalSeconds} />

          <label class="form-label" for="rss-since">Since duration</label>
          <input id="rss-since" type="text" bind:value={formSinceDuration} placeholder="1 day" />

          <label class="form-label" for="rss-state">State filter</label>
          <input
            id="rss-state"
            type="text"
            maxlength="2"
            bind:value={formStateFilter}
            placeholder="All states"
          />

          <label class="form-label" for="rss-cover-only">Cover pages only</label>
          <label class="checkbox-label">
            <input id="rss-cover-only" type="checkbox" bind:checked={formCoverOnly} />
            Only import cover pages
          </label>
        </div>
        <button class="save-btn" onclick={saveSettings} disabled={saving}>
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
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
  .status-badge.disabled-badge {
    background: #6c757d;
    color: white;
  }
  .status-indicator {
    font-size: 0.95em;
    display: flex;
    align-items: center;
    gap: 0.5em;
    flex: 1;
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
    0%,
    100% {
      opacity: 1;
      transform: scale(1);
    }
    50% {
      opacity: 0.5;
      transform: scale(1.2);
    }
  }
  .toggle-btn {
    margin-left: auto;
    padding: 0.4em 1em;
    border: 1px solid #ccc;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9em;
    background: white;
  }
  .toggle-btn.enabled {
    border-color: #dc3545;
    color: #dc3545;
  }
  .toggle-btn:not(.enabled) {
    border-color: #28a745;
    color: #28a745;
  }
  .toggle-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  .progress-section {
    padding: 0.5em 0;
    margin-bottom: 1em;
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
  .config-form {
    margin-top: 1em;
    padding: 1em;
    background: white;
    border-radius: 4px;
  }
  .config-form h3 {
    margin: 0 0 0.75em;
    font-size: 1em;
  }
  .form-grid {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 0.5em 1em;
    align-items: center;
    margin-bottom: 1em;
  }
  .form-label {
    font-size: 0.9em;
    color: #333;
  }
  .form-grid input[type='number'],
  .form-grid input[type='text'] {
    padding: 0.35em 0.5em;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.9em;
    max-width: 200px;
  }
  .checkbox-label {
    font-size: 0.9em;
    display: flex;
    align-items: center;
    gap: 0.4em;
  }
  .save-btn {
    padding: 0.4em 1.2em;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9em;
  }
  .save-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
</style>

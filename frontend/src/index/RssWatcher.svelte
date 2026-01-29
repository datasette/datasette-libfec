<script lang="ts">
  import { onMount } from 'svelte';
  import createClient from "openapi-fetch";
  import type { paths } from "../../api.d.ts";

  const client = createClient<paths>({ baseUrl: "/" });

  interface RssConfig {
    state: string | null;
    cover_only: boolean;
    interval: number;
    output_db?: string;
    next_sync_time?: number;
    currently_syncing?: boolean;
    phase?: string;
    exported_count?: number;
    total_count?: number;
    current_filing_id?: string;
    feed_title?: string;
    feed_last_modified?: string;
    error_message?: string;
    error_code?: number;
    error_data?: string;
    sync_start_time?: number;
  }

  let rssRunning = $state(false);
  let rssLoading = $state(false);
  let rssState = $state("");
  let rssCoverOnly = $state(true);
  let rssInterval = $state(60);
  let rssConfig = $state<RssConfig | null>(null);
  let nextSyncLabel = $state<string>("");

  function isActivelySyncing(): boolean {
    return rssConfig != null &&
           (rssConfig.phase === 'fetching' || rssConfig.phase === 'exporting');
  }

  onMount(() => {
    loadRssStatus();

    const labelInterval = setInterval(() => {
      updateNextSyncLabel();
    }, 1000);

    const statusInterval = setInterval(() => {
      if (rssRunning) {
        loadRssStatus();
      }
    }, isActivelySyncing() ? 1000 : 5000);

    return () => {
      clearInterval(labelInterval);
      clearInterval(statusInterval);
    };
  });

  async function loadRssStatus() {
    try {
      const {data, error} = await client.GET("/-/api/libfec/rss/status");
      if (data && !error) {
        rssRunning = data.running;
        if (data.config) {
          const config = data.config as unknown as RssConfig;
          rssConfig = config;
          if (config.state) rssState = config.state;
          rssCoverOnly = config.cover_only;
          rssInterval = config.interval;
          updateNextSyncLabel();
        }
      }
    } catch (error) {
      console.error('Error loading RSS status:', error);
    }
  }

  function formatDuration(seconds: number): string {
    if (seconds < 0) return "soon";
    if (seconds < 60) return `in ${Math.floor(seconds)} second${Math.floor(seconds) === 1 ? '' : 's'}`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    if (minutes < 60) {
      return `in ${minutes} minute${minutes === 1 ? '' : 's'}${remainingSeconds > 0 ? ` ${remainingSeconds} second${remainingSeconds === 1 ? '' : 's'}` : ''}`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `in ${hours} hour${hours === 1 ? '' : 's'}${remainingMinutes > 0 ? ` ${remainingMinutes} minute${remainingMinutes === 1 ? '' : 's'}` : ''}`;
  }

  function formatProgress(): string {
    if (!rssConfig) return "Unknown";

    const phase = rssConfig.phase || "idle";

    switch (phase) {
      case "idle":
        return "Idle";
      case "fetching":
        return "Fetching RSS feed...";
      case "exporting":
        if (rssConfig.total_count && rssConfig.total_count > 0) {
          const count = rssConfig.exported_count || 0;
          const total = rssConfig.total_count;
          const percent = Math.round((count / total) * 100);
          return `Exporting: ${count}/${total} filings (${percent}%)`;
        }
        return "Exporting filings...";
      case "complete":
        return "Sync complete";
      case "canceled":
        return "Sync canceled";
      case "error":
        return "Error";
      default:
        return phase;
    }
  }

  function updateNextSyncLabel() {
    if (!rssConfig || !rssRunning) {
      nextSyncLabel = "";
      return;
    }

    if (rssConfig.currently_syncing) {
      nextSyncLabel = "currently running";
      return;
    }

    if (!rssConfig.next_sync_time) {
      nextSyncLabel = "starting soon";
      return;
    }

    const now = Date.now() / 1000;
    const remaining = rssConfig.next_sync_time - now;

    nextSyncLabel = formatDuration(remaining);
  }

  async function startRssWatcher() {
    rssLoading = true;
    try {
      const {data, error} = await client.POST("/-/api/libfec/rss/start", {
        body: {
          state: rssState || null,
          cover_only: rssCoverOnly,
          interval: rssInterval
        }
      });
      if (error) {
        alert(`Error starting RSS watcher: ${JSON.stringify(error)}`);
        return;
      }
      if (data) {
        rssRunning = data.running;
        rssConfig = data.config as unknown as RssConfig | null;
        updateNextSyncLabel();
        alert(`RSS watcher started successfully`);
      }
    } finally {
      rssLoading = false;
    }
  }

  async function stopRssWatcher() {
    rssLoading = true;
    try {
      const {data, error} = await client.POST("/-/api/libfec/rss/stop", {});
      if (error) {
        alert(`Error stopping RSS watcher: ${JSON.stringify(error)}`);
        return;
      }
      if (data) {
        rssRunning = data.running;
        rssConfig = null;
        nextSyncLabel = "";
        alert(`RSS watcher stopped`);
      }
    } finally {
      rssLoading = false;
    }
  }
</script>

<section class="rss-section">
  <h2>Watch RSS Feed</h2>
  <p>Automatically watch and import new FEC filings from the RSS feed.</p>

  {#if rssRunning}
    <div class="rss-status running">
      <strong>RSS Watcher is Running</strong>
      {#if rssConfig}
        <div class="rss-config">
          <div>State: {rssConfig.state || 'All states'}</div>
          <div>Cover Only: {rssConfig.cover_only ? 'Yes' : 'No'}</div>
          <div>Interval: {rssConfig.interval} seconds</div>
          {#if nextSyncLabel}
            <div class="next-sync">Next sync: {nextSyncLabel}</div>
          {/if}
        </div>

        <div class="progress-section">
          <div class="progress-status">
            Status: <strong>{formatProgress()}</strong>
          </div>

          {#if rssConfig.phase === 'exporting' && rssConfig.total_count && rssConfig.total_count > 0}
            <div class="progress-bar">
              <div
                class="progress-fill"
                style="width: {((rssConfig.exported_count || 0) / rssConfig.total_count) * 100}%"
              ></div>
            </div>
          {/if}

          {#if rssConfig.current_filing_id}
            <div class="current-filing">
              Processing: <code>{rssConfig.current_filing_id}</code>
            </div>
          {/if}

          {#if rssConfig.error_message}
            <div class="error-message">
              <strong>Error:</strong> {rssConfig.error_message}
              {#if rssConfig.error_code}
                <div class="error-code">Code: {rssConfig.error_code}</div>
              {/if}
              {#if rssConfig.error_data}
                <div class="error-details">
                  <strong>Details:</strong>
                  <pre>{rssConfig.error_data}</pre>
                </div>
              {/if}
            </div>
          {/if}
        </div>
      {/if}
      <button
        type="button"
        class="button-danger"
        disabled={rssLoading}
        onclick={stopRssWatcher}
      >
        {rssLoading ? "Stopping..." : "Stop Watcher"}
      </button>
    </div>
  {:else}
    <form onsubmit={(e) => { e.preventDefault(); startRssWatcher(); }}>
      <div class="form-group">
        <label for="rss-state">
          State (optional)
        </label>
        <input
          type="text"
          id="rss-state"
          name="rss-state"
          bind:value={rssState}
          placeholder="CA,NY,TX etc."
          maxlength="2"
        />
        <small>Two-letter state code, or leave empty for all states</small>
      </div>

      <div class="form-group">
        <label>
          <input
            type="checkbox"
            bind:checked={rssCoverOnly}
          />
          Cover pages only
        </label>
        <small>Import only cover pages (faster)</small>
      </div>

      <div class="form-group">
        <label for="rss-interval">
          Check Interval (seconds)
        </label>
        <input
          type="number"
          id="rss-interval"
          name="rss-interval"
          bind:value={rssInterval}
          min="1"
          max="3600"
        />
        <small>How often to check the RSS feed (default: 60 seconds)</small>
      </div>

      <button
        type="submit"
        disabled={rssLoading}
      >
        {rssLoading ? "Starting..." : "Start RSS Watcher"}
      </button>
    </form>
  {/if}
</section>

<style>
  .rss-section {
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

  .form-group input[type="text"],
  .form-group input[type="number"] {
    max-width: 400px;
    padding: 0.5em;
    font-size: 1em;
    border: 1px solid #ccc;
    border-radius: 4px;
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

  .rss-status {
    padding: 1.5em;
    border-radius: 4px;
    background: #f8f9fa;
    border: 1px solid #dee2e6;
  }

  .rss-status.running {
    background: #d4edda;
    border-color: #c3e6cb;
  }

  .rss-status strong {
    display: block;
    margin-bottom: 1em;
    font-size: 1.1em;
  }

  .rss-config {
    margin: 1em 0;
    padding: 1em;
    background: white;
    border-radius: 4px;
    font-family: monospace;
  }

  .rss-config div {
    margin: 0.5em 0;
  }

  .rss-config .next-sync {
    color: #0066cc;
    font-weight: 600;
    margin-top: 1em;
    padding-top: 0.75em;
    border-top: 1px solid #e0e0e0;
  }

  small {
    display: block;
    color: #666;
    font-size: 0.85em;
    margin-top: 0.25em;
  }

  input[type="checkbox"] {
    margin-right: 0.5em;
  }

  .progress-section {
    margin: 1.5em 0;
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

  .current-filing {
    margin-top: 0.75em;
    font-size: 0.9em;
    color: #495057;
  }

  .current-filing code {
    background: #f8f9fa;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
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

  .error-code {
    font-size: 0.85em;
    margin-top: 0.25em;
    opacity: 0.8;
  }

  .error-details {
    margin-top: 0.5em;
    font-size: 0.85em;
  }

  .error-details pre {
    margin: 0.25em 0 0 0;
    padding: 0.5em;
    background: #fff;
    border: 1px solid #f5c6cb;
    border-radius: 3px;
    overflow-x: auto;
    font-size: 0.9em;
    white-space: pre-wrap;
    word-wrap: break-word;
  }
</style>

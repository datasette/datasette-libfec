<script lang="ts">
  import { onMount } from 'svelte';
  import createClient from "openapi-fetch";
  import type { paths } from "../api.d.ts";
  import RecentFilings from './RecentFilings.svelte';

  const client = createClient<paths>({ baseUrl: "/" });

  type TargetKind = "committee" | "candidate" | "contest";

  let isLoading = $state(false);
  let kind: TargetKind = $state("committee");
  let id = $state("C00498667");
  let cycle = $state(2026);

  // RSS Watcher state
  interface RssConfig {
    state: string | null;
    cover_only: boolean;
    interval: number;
    output_db?: string;
    next_sync_time?: number;
    currently_syncing?: boolean;
  }

  let rssRunning = $state(false);
  let rssLoading = $state(false);
  let rssState = $state("CA");
  let rssCoverOnly = $state(true);
  let rssInterval = $state(60);
  let rssConfig = $state<RssConfig | null>(null);
  let nextSyncLabel = $state<string>("");

  onMount(() => {
    loadRssStatus();

    // Update next sync label every second
    const labelInterval = setInterval(() => {
      updateNextSyncLabel();
    }, 1000);

    // Poll RSS status every 5 seconds to keep sync status fresh
    const statusInterval = setInterval(() => {
      if (rssRunning) {
        loadRssStatus();
      }
    }, 5000);

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

  async function onSubmit(e: SubmitEvent) {
    e.preventDefault();

    if (!id) {
      alert('Please enter an ID.');
      return;
    }

    isLoading = true;
    try {
      const {data, error} = await client.POST("/-/api/libfec", {
        body: {
          kind: kind,
          id: id,
          cycle: cycle
        }
      });
      if (error) {
        alert(`Error starting import: ${JSON.stringify(error)}`);
        return;
      }
      alert(`Import started successfully: ${JSON.stringify(data)}`);
    } finally {
      isLoading = false;
    }
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

<main>
  <h1>FEC Data Import</h1>
  <p>Import Federal Election Commission data into your Datasette database.</p>

  <section class="import-section">
    <h2>Import Data</h2>
    <p>Select the type of FEC data you want to import, provide an ID, and choose an election cycle.</p>

    <form onsubmit={onSubmit}>
      <!-- Target Kind Selection -->
      <div class="form-group">
        <fieldset>
          <legend>Import Type</legend>
          <div class="radio-group">
            <div>
              <input
                id="committee"
                name="kind"
                type="radio"
                value="committee"
                bind:group={kind}
              />
              <label for="committee">
                Committee
              </label>
            </div>
            <div>
              <input
                id="candidate"
                name="kind"
                type="radio"
                value="candidate"
                bind:group={kind}
              />
              <label for="candidate">
                Candidate
              </label>
            </div>
            <div>
              <input
                id="contest"
                name="kind"
                type="radio"
                value="contest"
                bind:group={kind}
              />
              <label for="contest">
                Contest
              </label>
            </div>
          </div>
        </fieldset>
      </div>

      <!-- ID Input -->
      <div class="form-group">
        <label for="id">
          ID
        </label>
        <input
          type="text"
          id="id"
          name="id"
          bind:value={id}
          placeholder="e.g. C00498667"
        />
      </div>

      <!-- Cycle Input -->
      <div class="form-group">
        <label for="cycle">
          Election Cycle
        </label>
        <select
          id="cycle"
          name="cycle"
          bind:value={cycle}
        >
          <option value={2026}>2026</option>
          <option value={2024}>2024</option>
          <option value={2022}>2022</option>
        </select>
      </div>

      <!-- Submit Button -->
      <button
        type="submit"
        disabled={isLoading}
      >
        {isLoading ? "Importing..." : "Import Data"}
      </button>
    </form>
  </section>

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
            placeholder="e.g. CA (leave empty for all states)"
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

  <RecentFilings />
</main>

<style>
  .import-section {
    margin: 2em 0;
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
  .form-group select {
    width: 100%;
    max-width: 400px;
    padding: 0.5em;
    font-size: 1em;
    border: 1px solid #ccc;
    border-radius: 4px;
  }

  fieldset {
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 1em;
  }

  legend {
    font-weight: bold;
    padding: 0 0.5em;
  }

  .radio-group {
    display: flex;
    gap: 1.5em;
    flex-wrap: wrap;
  }

  .radio-group div {
    display: flex;
    align-items: center;
    gap: 0.5em;
  }

  .radio-group input[type="radio"] {
    cursor: pointer;
  }

  .radio-group label {
    cursor: pointer;
    margin: 0;
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
    padding: 0.75em 1.5em;
    font-size: 1em;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .button-danger:hover:not(:disabled) {
    background: #c82333;
  }

  .button-danger:disabled {
    background: #999;
    cursor: not-allowed;
  }

  .rss-section {
    margin: 3em 0;
    padding-top: 2em;
    border-top: 2px solid #ddd;
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

  input[type="number"] {
    width: 100%;
    max-width: 200px;
  }
</style>

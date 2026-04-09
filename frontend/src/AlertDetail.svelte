<script lang="ts">
  import { loadPageData } from './page_data/load.ts';
  import { databaseName as databaseNameStore, basePath as basePathStore } from './stores';
  import { get } from 'svelte/store';
  import Breadcrumb, { type BreadcrumbItem } from './components/Breadcrumb.svelte';

  interface CronRun {
    started_at: string;
    status: string;
    duration_ms: number | null;
    error_message: string | null;
  }

  interface Subscription {
    notifier: string;
    destination_label: string;
  }

  interface LogEntry {
    logged_at: string;
    new_ids: string[];
  }

  interface AlertDetailPageData {
    database_name: string;
    alert_id: string;
    alert_type: string;
    type_label: string;
    slug: string;
    created_at: string | null;
    frequency: string;
    last_check_at: string | null;
    custom_config: Record<string, any>;
    criteria: string[];
    subscriptions: Subscription[];
    logs: LogEntry[];
    cron_runs: CronRun[];
    total_runs: number;
    success_runs: number;
    error_runs: number;
    queue_pending: number;
    queue_done: number;
  }

  const pageData = loadPageData<AlertDetailPageData>();
  databaseNameStore.set(pageData.database_name);
  const bp = get(basePathStore);

  const breadcrumbItems: BreadcrumbItem[] = [
    { label: 'FEC Data', href: bp },
    { label: 'Alerts', href: `${bp}/alerts` },
    { label: pageData.type_label },
  ];
</script>

<div class="alert-detail-page">
  <Breadcrumb items={breadcrumbItems} />

  <div class="header">
    <h1>
      <span class="type-badge type-{pageData.slug.replace('fec-', '')}">
        {pageData.type_label}
      </span>
    </h1>
    <p class="subtitle">
      Created: {pageData.created_at || 'unknown'} · Frequency: {pageData.frequency}
    </p>
  </div>

  <section class="section">
    <h2>Watching For</h2>
    <ul class="criteria-list">
      {#each pageData.criteria as c}
        <li>{c}</li>
      {/each}
    </ul>
  </section>

  <section class="section">
    <h2>Stats</h2>
    <div class="stat-grid">
      <div class="stat">
        <div class="value">{pageData.total_runs}</div>
        <div class="label">Total checks</div>
      </div>
      <div class="stat">
        <div class="value ok">{pageData.success_runs}</div>
        <div class="label">Successful</div>
      </div>
      <div class="stat">
        <div class="value err">{pageData.error_runs}</div>
        <div class="label">Errors</div>
      </div>
      <div class="stat">
        <div class="value">{pageData.queue_pending}</div>
        <div class="label">Queue pending</div>
      </div>
      <div class="stat">
        <div class="value">{pageData.queue_done}</div>
        <div class="label">Queue processed</div>
      </div>
      <div class="stat">
        <div class="value">{pageData.logs.length}</div>
        <div class="label">Notifications sent</div>
      </div>
    </div>
  </section>

  <section class="section">
    <h2>Destinations</h2>
    <table>
      <thead><tr><th>Notifier</th><th>Destination</th></tr></thead>
      <tbody>
        {#each pageData.subscriptions as sub}
          <tr><td>{sub.notifier}</td><td>{sub.destination_label}</td></tr>
        {:else}
          <tr><td colspan="2">None</td></tr>
        {/each}
      </tbody>
    </table>
  </section>

  {#if pageData.logs.length > 0}
    <section class="section">
      <h2>Recent Notifications</h2>
      <table>
        <thead><tr><th>Time</th><th>Items</th></tr></thead>
        <tbody>
          {#each pageData.logs as log}
            <tr>
              <td class="time-cell">{log.logged_at}</td>
              <td>{log.new_ids.join(', ')}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </section>
  {/if}

  <section class="section">
    <h2>Recent Cron Runs</h2>
    <table>
      <thead><tr><th>Started</th><th>Status</th><th>Duration</th><th>Error</th></tr></thead>
      <tbody>
        {#each pageData.cron_runs as run}
          <tr>
            <td class="time-cell">{run.started_at}</td>
            <td class={run.status === 'success' ? 'ok' : 'err'}>{run.status}</td>
            <td>{run.duration_ms ?? '—'}ms</td>
            <td class="err">{run.error_message || ''}</td>
          </tr>
        {:else}
          <tr><td colspan="4">No runs yet</td></tr>
        {/each}
      </tbody>
    </table>
  </section>

  <section class="section">
    <h2>Config</h2>
    <pre class="config-json">{JSON.stringify(pageData.custom_config, null, 2)}</pre>
  </section>
</div>

<style>
  .alert-detail-page {
    max-width: 960px;
    margin: 0 auto;
    padding: 2rem;
  }

  .header h1 { margin-bottom: 0.25rem; }
  .subtitle { color: #666; margin-top: 0; font-size: 0.9rem; }

  .type-badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 12px;
    font-size: 0.9rem;
    font-weight: 600;
  }
  .type-filing { background: #e0f0ff; color: #0066cc; }
  .type-contributor { background: #f0e0ff; color: #6600cc; }

  .section { margin: 1.5rem 0; }
  .section h2 {
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
    border-bottom: 1px solid #eee;
    padding-bottom: 0.25rem;
  }

  .criteria-list { padding-left: 1.25rem; }
  .criteria-list li { margin: 0.25rem 0; }

  .stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 0.75rem;
  }
  .stat {
    padding: 0.75rem;
    background: #f8f8f8;
    border-radius: 6px;
    text-align: center;
  }
  .stat .value { font-size: 1.5rem; font-weight: 700; }
  .stat .label { font-size: 0.75rem; color: #666; }

  table { border-collapse: collapse; width: 100%; font-size: 0.85rem; }
  th, td { padding: 0.4rem 0.6rem; text-align: left; border-bottom: 1px solid #eee; }
  th { background: #f5f5f5; font-weight: 600; }

  .ok { color: green; }
  .err { color: red; }
  .time-cell { font-size: 0.8rem; white-space: nowrap; }

  .config-json {
    background: #f5f5f5;
    padding: 0.75rem;
    border-radius: 4px;
    font-size: 0.8rem;
    overflow-x: auto;
  }
</style>

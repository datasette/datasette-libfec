<script lang="ts">
  import type {
    AlertsPageData,
    WatchlistData,
    AlertLogData,
    DestinationOption,
  } from './page_data/AlertsPageData.types.ts';
  import { loadPageData } from './page_data/load.ts';
  import { get } from 'svelte/store';
  import { databaseName as databaseNameStore, basePath as basePathStore } from './stores';
  // openapi-fetch no longer needed — using fetch directly for datasette-alerts API
  import Breadcrumb, { type BreadcrumbItem } from './components/Breadcrumb.svelte';
  import CommitteeSearch from './alerts/CommitteeSearch.svelte';
  import ContributorForm from './alerts/ContributorForm.svelte';
  import ContestForm from './alerts/ContestForm.svelte';

  const pageData = loadPageData<AlertsPageData>();
  databaseNameStore.set(pageData.database_name);
  const bp = get(basePathStore);
  const destinations: DestinationOption[] = (pageData.destinations ?? []) as DestinationOption[];
  const watchlists: WatchlistData[] = (pageData.watchlists ?? []) as WatchlistData[];
  const recentAlerts: AlertLogData[] = (pageData.recent_alerts ?? []) as AlertLogData[];

  const breadcrumbItems: BreadcrumbItem[] = [{ label: 'FEC Data', href: bp }, { label: 'Alerts' }];

  // --- Create watchlist form ---
  type WatchlistType = 'filing' | 'contributor';
  type FilingMode = 'committees' | 'contest' | 'all';

  let watchlistName = $state('');
  let watchlistType = $state<WatchlistType>(
    (pageData.prefill_template as WatchlistType) || 'filing'
  );
  let filingMode = $state<FilingMode>('committees');
  let selectedCommittees = $state<{ committee_id: string; name: string }[]>([]);
  let contestRace = $state({
    office: 'H',
    state: '',
    district: '',
    cycle: new Date().getFullYear(),
  });
  let stateFilter = $state('');
  let contributors = $state<
    { first_name: string; last_name: string; city: string; state: string }[]
  >([]);
  let selectedDestinationId = $state(destinations.length > 0 ? (destinations[0]?.id ?? '') : '');
  let submitting = $state(false);
  let error = $state<string | null>(null);

  const usStates = [
    'AL',
    'AK',
    'AZ',
    'AR',
    'CA',
    'CO',
    'CT',
    'DE',
    'FL',
    'GA',
    'HI',
    'ID',
    'IL',
    'IN',
    'IA',
    'KS',
    'KY',
    'LA',
    'ME',
    'MD',
    'MA',
    'MI',
    'MN',
    'MS',
    'MO',
    'MT',
    'NE',
    'NV',
    'NH',
    'NJ',
    'NM',
    'NY',
    'NC',
    'ND',
    'OH',
    'OK',
    'OR',
    'PA',
    'RI',
    'SC',
    'SD',
    'TN',
    'TX',
    'UT',
    'VT',
    'VA',
    'WA',
    'WV',
    'WI',
    'WY',
    'DC',
    'AS',
    'GU',
    'MP',
    'PR',
    'VI',
  ];

  // Pre-fill committee from URL param
  if (pageData.prefill_committee_id) {
    selectedCommittees = [{ committee_id: pageData.prefill_committee_id, name: '' }];
  }

  function criteriaDescription(wl: WatchlistData): string {
    const parts: string[] = [];
    const committeeIds = wl.committee_ids ?? [];
    const races = wl.races ?? [];
    const contribs = wl.contributors ?? [];
    if (committeeIds.length > 0) parts.push(`${committeeIds.length} committee(s)`);
    if (races.length > 0) {
      for (const r of races) {
        parts.push(`${r.office || ''} ${r.state || ''} ${r.district || ''}`);
      }
    }
    if (contribs.length > 0) {
      for (const c of contribs) {
        const name = [c.first_name, c.last_name].filter(Boolean).join(' ');
        const loc = c.state ? ` (${c.state})` : '';
        parts.push(name + loc);
      }
    }
    return parts.join(', ') || 'All filings';
  }

  async function handleSubmit(e: Event) {
    e.preventDefault();
    error = null;

    if (!watchlistName.trim()) {
      error = 'Please enter a name.';
      return;
    }
    if (
      watchlistType === 'filing' &&
      filingMode === 'committees' &&
      selectedCommittees.length === 0
    ) {
      error = 'Please add at least one committee.';
      return;
    }
    if (watchlistType === 'filing' && filingMode === 'contest' && !contestRace.state) {
      error = 'Please select a state for the contest.';
      return;
    }
    if (watchlistType === 'contributor' && contributors.length === 0) {
      error = 'Please add at least one contributor.';
      return;
    }
    if (!selectedDestinationId) {
      error = 'Please select a destination.';
      return;
    }

    submitting = true;

    // Build committee_ids and races based on filing mode
    let committeeIds: string[] = [];
    let races: { office: string; state: string; district: string; cycle: number }[] = [];
    if (watchlistType === 'filing') {
      if (filingMode === 'committees') {
        committeeIds = selectedCommittees.map((c) => c.committee_id);
      } else if (filingMode === 'contest') {
        races = [contestRace];
      }
      // 'all' mode: empty committee_ids and races
    }

    try {
      const resp = await fetch(`/${pageData.database_name}/-/api/libfec/alerts/new`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: watchlistName.trim(),
          alert_type: watchlistType === 'filing' ? 'fec-filing' : 'fec-contributor',
          frequency: '+1 second',
          destination_id: selectedDestinationId,
          committee_ids: committeeIds,
          races,
          state_filter: stateFilter,
          contributors: watchlistType === 'contributor' ? contributors : [],
        }),
      });
      const result = await resp.json();
      if (!result.ok) {
        error = result.error ?? 'Failed to create alert';
        return;
      }
      window.location.reload();
    } catch (e: unknown) {
      error = e instanceof Error ? e.message : 'Unknown error';
    } finally {
      submitting = false;
    }
  }

  async function deleteWatchlist(id: string) {
    await fetch(`/${pageData.database_name}/-/api/libfec/alerts/${id}/delete`, { method: 'POST' });
    window.location.reload();
  }
</script>

<div class="alerts-page">
  <Breadcrumb items={breadcrumbItems} />
  <h1>Alerts</h1>

  {#if !pageData.alerts_available}
    <div class="info-banner">
      <strong>datasette-alerts</strong> is not installed or you do not have permission to use
      alerts. Install
      <code>datasette-alerts</code> and a notifier plugin (e.g.,
      <code>datasette-alerts-slack</code>) to enable notifications.
    </div>
  {:else}
    <!-- Watchlists -->
    <section class="section">
      <h2>Watchlists</h2>
      {#if watchlists.length > 0}
        <table class="watchlists-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Watching</th>
              <th>Destination</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {#each watchlists as wl}
              <tr class:disabled={!wl.enabled}>
                <td class="type-cell">
                  <span class="type-badge type-{wl.watchlist_type}">
                    {wl.watchlist_type === 'filing' ? 'Filing' : 'Contributor'}
                  </span>
                </td>
                <td class="criteria-cell">
                  <a href="/{pageData.database_name}/-/libfec/alerts/{wl.id}">
                    {criteriaDescription(wl)}
                  </a>
                </td>
                <td>{wl.destination_label || wl.destination_id}</td>
                <td class="actions-cell">
                  <a class="detail-link" href="/{pageData.database_name}/-/libfec/alerts/{wl.id}">
                    View
                  </a>
                  <button
                    type="button"
                    class="action-btn danger"
                    onclick={() => deleteWatchlist(wl.id)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      {:else}
        <p class="muted">No watchlists configured yet.</p>
      {/if}
    </section>

    <!-- Recent Alerts -->
    {#if recentAlerts.length > 0}
      <section class="section">
        <h2>Recent Alerts</h2>
        <table class="log-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Watchlist</th>
              <th>Filing</th>
              <th>Message</th>
            </tr>
          </thead>
          <tbody>
            {#each recentAlerts as log}
              <tr>
                <td class="time-cell">{log.sent_at || ''}</td>
                <td>{log.watchlist_name || ''}</td>
                <td>
                  <a href="{bp}/filing/{log.filing_id}">FEC-{log.filing_id}</a>
                </td>
                <td class="message-cell">{log.message_text || ''}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </section>
    {/if}

    <!-- Create Watchlist -->
    <section class="section create-section">
      <h2>Create Watchlist</h2>
      <form onsubmit={handleSubmit}>
        <div class="form-field">
          <label for="watchlist-name">Name</label>
          <input
            id="watchlist-name"
            type="text"
            bind:value={watchlistName}
            placeholder="e.g., CA Senate filings"
          />
        </div>

        <fieldset class="type-selector">
          <legend>Type</legend>
          <label>
            <input
              type="radio"
              name="watchlist_type"
              value="filing"
              checked={watchlistType === 'filing'}
              onchange={() => (watchlistType = 'filing')}
            />
            Filing
            <span class="type-desc">Watch for new FEC filings</span>
          </label>
          <label>
            <input
              type="radio"
              name="watchlist_type"
              value="contributor"
              checked={watchlistType === 'contributor'}
              onchange={() => (watchlistType = 'contributor')}
            />
            Contributor
            <span class="type-desc">Watch for specific individuals in Schedule A data</span>
          </label>
        </fieldset>

        {#if watchlistType === 'filing'}
          <fieldset class="type-selector">
            <legend>Watch for filings from</legend>
            <label>
              <input
                type="radio"
                name="filing_mode"
                value="committees"
                checked={filingMode === 'committees'}
                onchange={() => (filingMode = 'committees')}
              />
              Specific committees
              <span class="type-desc">Search and select FEC committees</span>
            </label>
            <label>
              <input
                type="radio"
                name="filing_mode"
                value="contest"
                checked={filingMode === 'contest'}
                onchange={() => (filingMode = 'contest')}
              />
              Congressional contest
              <span class="type-desc">All committees associated with a race</span>
            </label>
            <label>
              <input
                type="radio"
                name="filing_mode"
                value="all"
                checked={filingMode === 'all'}
                onchange={() => (filingMode = 'all')}
              />
              All filings
              <span class="type-desc">Every new filing (can be noisy)</span>
            </label>
          </fieldset>

          {#if filingMode === 'committees'}
            <div class="form-field">
              <label>Committees</label>
              <CommitteeSearch
                databaseName={pageData.database_name}
                {selectedCommittees}
                onchange={(c) => (selectedCommittees = c)}
              />
            </div>
          {:else if filingMode === 'contest'}
            <div class="form-field">
              <label>Contest</label>
              <ContestForm race={contestRace} onchange={(r) => (contestRace = r)} />
            </div>
          {:else}
            <p class="hint">
              You will receive a notification for every new filing. Consider adding a state filter
              to reduce volume.
            </p>
          {/if}

          <div class="form-field">
            <label for="state-filter">State filter <span class="type-desc">(optional)</span></label>
            <select id="state-filter" bind:value={stateFilter} style="max-width: 200px;">
              <option value="">All states</option>
              {#each usStates as s}
                <option value={s}>{s}</option>
              {/each}
            </select>
          </div>
        {:else}
          <div class="form-field">
            <label>Contributors</label>
            <ContributorForm {contributors} onchange={(c) => (contributors = c)} />
          </div>
        {/if}

        <div class="form-field">
          <label for="destination-select">Destination</label>
          {#if destinations.length === 0}
            <p class="muted">
              No destinations configured.
              <a href="/-/{pageData.database_name}/datasette-alerts/destinations">
                Set up a destination
              </a>
              first.
            </p>
          {:else}
            <select id="destination-select" bind:value={selectedDestinationId}>
              {#each destinations as dest}
                <option value={dest.id}>{dest.label} ({dest.notifier})</option>
              {/each}
            </select>
            <a
              class="new-dest-link"
              href="/-/{pageData.database_name}/datasette-alerts/destinations"
            >
              + Create new destination
            </a>
          {/if}
        </div>

        <div class="form-actions">
          <button type="submit" disabled={submitting}>
            {submitting ? 'Creating...' : 'Create Watchlist'}
          </button>
        </div>

        {#if error}
          <p class="error">{error}</p>
        {/if}
      </form>
    </section>
  {/if}
</div>

<style>
  .alerts-page {
    max-width: 960px;
    margin: 0 auto;
    padding: 2rem;
  }

  h1 {
    font-size: 2rem;
    margin: 0 0 1.5rem 0;
  }

  h2 {
    font-size: 1.25rem;
    margin: 0 0 0.75rem 0;
  }

  .section {
    margin-bottom: 2rem;
  }

  .info-banner {
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 4px;
    padding: 1rem;
  }

  .info-banner code {
    background: rgba(0, 0, 0, 0.06);
    padding: 0.15em 0.3em;
    border-radius: 3px;
  }

  .watchlists-table,
  .log-table {
    width: 100%;
    border-collapse: collapse;
  }

  .watchlists-table th,
  .watchlists-table td,
  .log-table th,
  .log-table td {
    padding: 0.5rem 0.75rem;
    text-align: left;
    border-bottom: 1px solid #e0e0e0;
  }

  .watchlists-table th,
  .log-table th {
    background: #f5f5f5;
    font-weight: 600;
    font-size: 0.85rem;
  }

  tr.disabled {
    opacity: 0.5;
  }

  .type-cell {
    text-transform: capitalize;
  }

  .criteria-cell {
    font-size: 0.85rem;
    color: #666;
  }

  .time-cell {
    font-size: 0.8rem;
    white-space: nowrap;
  }

  .message-cell {
    font-size: 0.85rem;
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .actions-cell {
    white-space: nowrap;
  }

  .action-btn {
    padding: 0.2rem 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    background: white;
    cursor: pointer;
    font-size: 0.75rem;
    margin-left: 0.25rem;
  }

  .action-btn:hover {
    background: #f0f0f0;
  }

  .action-btn.danger {
    border-color: #c00;
    color: #c00;
  }

  .action-btn.danger:hover {
    background: #fef2f2;
  }

  .muted {
    color: #666;
    font-size: 0.9rem;
  }

  .create-section {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1.5rem;
  }

  form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .form-field {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .form-field > label {
    font-weight: 600;
    font-size: 0.9rem;
  }

  .form-field input[type='text'] {
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.9rem;
  }

  .type-selector {
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 0.75rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .type-selector label {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
    cursor: pointer;
  }

  .type-desc {
    font-size: 0.8rem;
    color: #666;
  }

  select {
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.9rem;
  }

  .form-actions {
    padding-top: 0.5rem;
  }

  button[type='submit'] {
    padding: 0.5rem 1.25rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
  }

  button[type='submit']:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .error {
    color: #c00;
    margin: 0;
  }

  .hint {
    font-size: 0.83rem;
    color: #888;
    margin: 0;
  }

  .type-badge {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 12px;
    font-size: 0.78rem;
    font-weight: 500;
  }
  .type-filing {
    background: #e0f0ff;
    color: #0066cc;
  }
  .type-contributor {
    background: #f0e0ff;
    color: #6600cc;
  }

  .detail-link {
    font-size: 0.8rem;
    color: #0066cc;
    text-decoration: none;
    margin-right: 0.5rem;
  }
  .detail-link:hover {
    text-decoration: underline;
  }

  .new-dest-link {
    font-size: 0.83rem;
    color: #0066cc;
    text-decoration: none;
  }

  .new-dest-link:hover {
    text-decoration: underline;
  }

  .log-table a {
    color: #0066cc;
    text-decoration: none;
  }

  .log-table a:hover {
    text-decoration: underline;
  }
</style>

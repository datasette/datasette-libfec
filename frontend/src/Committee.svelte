<script lang="ts">
  import type { CommitteePageData } from './page_data/CommitteePageData.types.ts';
  import { loadPageData } from './page_data/load.ts';
  import { get } from 'svelte/store';
  import { databaseName as databaseNameStore, basePath as basePathStore } from './stores';
  import { query } from './api';
  import { useQuery } from './useQuery.svelte';
  import Breadcrumb, { type BreadcrumbItem } from './components/Breadcrumb.svelte';
  import CommitteeSankey from './components/CommitteeSankey.svelte';
  import OverflowMenu from './components/OverflowMenu.svelte';

  const pageData = loadPageData<CommitteePageData>();
  databaseNameStore.set(pageData.database_name);
  const basePath = get(basePathStore);

  const officeNames: Record<string, string> = {
    H: 'House',
    S: 'Senate',
    P: 'President',
  };

  const committeeTypeLabels: Record<string, string> = {
    C: 'Communication Cost',
    D: 'Delegate Committee',
    E: 'Electioneering Communication',
    H: 'House Campaign',
    I: 'Independent Expenditure Filer',
    N: 'PAC - Nonqualified',
    O: 'Super PAC (Independent Expenditure-Only)',
    P: 'Presidential Campaign',
    Q: 'PAC - Qualified',
    S: 'Senate Campaign',
    U: 'Single Candidate Independent Expenditure',
    V: 'Hybrid PAC - Nonqualified',
    W: 'Hybrid PAC - Qualified',
    X: 'Party Committee - Nonqualified',
    Y: 'Party Committee - Qualified',
    Z: 'National Party Nonfederal Account',
  };

  function getCommitteeTypeLabel(type: string | null | undefined): string | null {
    if (!type) return null;
    return committeeTypeLabels[type] || null;
  }

  // Determine if this is a principal campaign committee
  const isPrincipal = pageData.committee?.designation === 'P' && pageData.candidate;
  const committeeTypeLabel = getCommitteeTypeLabel(pageData.committee?.committee_type);

  // Build contest label + URL for the candidate's race
  function getContestInfo(): { label: string; href: string } | null {
    const cand = pageData.candidate;
    if (!cand?.office || !cand?.state) return null;

    let label = cand.state + '-' + (officeNames[cand.office] || cand.office);
    if (cand.office === 'H' && cand.district) {
      label = cand.state + '-' + cand.district;
    } else if (cand.office === 'S') {
      label = cand.state + ' Senate';
    } else if (cand.office === 'P') {
      label = 'President';
    }

    const params = new URLSearchParams();
    params.set('state', cand.state);
    params.set('office', cand.office);
    params.set('cycle', pageData.cycle.toString());
    if (cand.office === 'H' && cand.district) {
      params.set('district', cand.district.toString());
    }

    return { label, href: `${basePath}/contest?${params.toString()}` };
  }

  const contestInfo = getContestInfo();

  // --- Cycle state ---
  let selectedCycle = $state(pageData.cycle);

  // Fetch available cycles from filing coverage dates
  async function fetchCycles() {
    const sql = `
WITH filing_years AS (
  SELECT DISTINCT CAST(strftime('%Y', fil.coverage_through_date) AS INTEGER) AS yr
  FROM libfec_filings fil
  WHERE fil.filer_id = :committee_id
    AND fil.coverage_through_date IS NOT NULL
),
final AS (
  SELECT DISTINCT CASE WHEN yr % 2 = 1 THEN yr + 1 ELSE yr END AS cycle
  FROM filing_years
  ORDER BY cycle DESC
)
SELECT * FROM final`;
    const rows = await query(pageData.database_name, sql, {
      committee_id: pageData.committee_id,
    });
    return (rows as { cycle: number }[]).map((r) => r.cycle);
  }

  const cyclesResult = useQuery(fetchCycles);

  // Sync cycle to URL param
  $effect(() => {
    const url = new URL(window.location.href);
    url.searchParams.set('cycle', String(selectedCycle));
    window.history.replaceState({}, '', url.toString());
  });

  // Build breadcrumb items
  function getBreadcrumbItems(): BreadcrumbItem[] {
    const items: BreadcrumbItem[] = [{ label: 'FEC Data', href: basePath }];

    const cand = pageData.candidate;
    if (cand?.office && cand?.state) {
      let contestLabel = cand.state + ' ' + (officeNames[cand.office] || cand.office);
      if (cand.office === 'H' && cand.district) {
        contestLabel += ' ' + cand.district;
      }

      const contestParams = new URLSearchParams();
      contestParams.set('state', cand.state);
      contestParams.set('office', cand.office);
      contestParams.set('cycle', pageData.cycle.toString());
      if (cand.office === 'H' && cand.district) {
        contestParams.set('district', cand.district.toString());
      }

      items.push({ label: contestLabel, href: `${basePath}/contest?${contestParams.toString()}` });

      items.push({
        label: cand.name || 'Candidate',
        href: `${basePath}/candidate/${cand.candidate_id}?cycle=${pageData.cycle}`,
      });
    }

    items.push({ label: 'Committee' });
    return items;
  }

  const breadcrumbItems = getBreadcrumbItems();

  const alertUrl = $derived(() => {
    const params = new URLSearchParams();
    params.set('filer_id__exact', pageData.committee_id);
    params.set('table_name', 'libfec_filings');
    return `/-/${pageData.database_name}/datasette-alerts/new?${params.toString()}`;
  });
</script>

<div class="committee-page">
  <div class="header">
    <Breadcrumb items={breadcrumbItems} />
    <div class="title-row">
      <h1>
        {pageData.committee?.name || pageData.committee_id}
        {#if pageData.committee?.party_affiliation}
          <span class="party-badge">{pageData.committee.party_affiliation}</span>
        {/if}
      </h1>

      <div class="title-right">
        {#if cyclesResult.data && cyclesResult.data.length > 0}
          <div class="cycle-select">
            <label for="cycle-select">Cycle:</label>
            <select id="cycle-select" bind:value={selectedCycle}>
              {#each cyclesResult.data as yr}
                <option value={yr}>{yr}</option>
              {/each}
            </select>
          </div>
        {/if}

        <OverflowMenu>
          <a
            href="https://www.fec.gov/data/committee/{pageData.committee_id}/?cycle={selectedCycle}"
            target="_blank"
            rel="noopener noreferrer"
          >
            View on FEC.gov &rarr;
          </a>
          {#if pageData.alerts_available}
            <a href={alertUrl()}>Subscribe to new filings </a>
          {/if}
        </OverflowMenu>
      </div>
    </div>

    {#if isPrincipal}
      <p class="subtitle">
        Principal campaign committee for
        <a href="{basePath}/candidate/{pageData.candidate?.candidate_id}?cycle={pageData.cycle}">
          {pageData.candidate?.name}
        </a>
        {#if contestInfo}
          , running in <a href={contestInfo.href}>{contestInfo.label}</a>
        {/if}
      </p>
    {:else if committeeTypeLabel}
      <p class="subtitle">{committeeTypeLabel}</p>
    {/if}
  </div>

  {#if pageData.error}
    <div class="error-box">
      <strong>Error:</strong>
      {pageData.error}
    </div>
  {/if}

  {#if !pageData.committee && !pageData.error}
    <div class="info-section">
      <p>Committee not found.</p>
    </div>
  {/if}

  {#if pageData.committee?.committee_type}
    <CommitteeSankey
      committeeId={pageData.committee_id}
      committeeType={pageData.committee.committee_type}
      databaseName={pageData.database_name}
      {selectedCycle}
    />
  {/if}

  {#if pageData.filings && pageData.filings.length > 0}
    <section class="filings-section">
      <h2>Filings ({pageData.filings.length})</h2>
      <table class="filings-table">
        <thead>
          <tr>
            <th>Filing ID</th>
            <th>Form</th>
            <th>Coverage Period</th>
          </tr>
        </thead>
        <tbody>
          {#each pageData.filings as filing}
            <tr>
              <td>
                <a href="{basePath}/filing/{filing.filing_id}">
                  FEC-{filing.filing_id}
                </a>
              </td>
              <td>{filing.cover_record_form || 'N/A'}</td>
              <td>
                {#if filing.coverage_from_date && filing.coverage_through_date}
                  {filing.coverage_from_date} to {filing.coverage_through_date}
                {:else}
                  N/A
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </section>
  {/if}

  {#if pageData.committee}
    <div class="footer-info">
      {#if pageData.committee.treasurer_name}
        <div class="footer-item">
          <span class="footer-label">Treasurer:</span>
          {pageData.committee.treasurer_name}
        </div>
      {/if}

      {#if pageData.committee.address_street1 || pageData.committee.address_city}
        <div class="footer-item">
          <span class="footer-label">Address:</span>
          {#if pageData.committee.address_street1}
            {pageData.committee.address_street1},
          {/if}
          {#if pageData.committee.address_street2}
            {pageData.committee.address_street2},
          {/if}
          {#if pageData.committee.address_city}
            {pageData.committee.address_city},
          {/if}
          {#if pageData.committee.address_state}
            {pageData.committee.address_state}
          {/if}
          {#if pageData.committee.address_zip}
            {pageData.committee.address_zip}
          {/if}
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .committee-page {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }

  .header {
    margin-bottom: 2rem;
  }

  .title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .header h1 {
    font-size: 2rem;
    margin: 0;
  }

  .party-badge {
    display: inline-block;
    padding: 0.25em 0.75em;
    background: #e9ecef;
    border-radius: 4px;
    font-size: 0.9rem;
    font-weight: 600;
    color: #495057;
  }

  .subtitle {
    margin: 0.75rem 0 1rem 0;
    font-size: 1.1rem;
    color: #333;
  }

  .subtitle a {
    color: #0066cc;
    text-decoration: none;
  }

  .subtitle a:hover {
    text-decoration: underline;
  }

  .title-right {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .cycle-select {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .cycle-select label {
    font-size: 0.9rem;
    color: #666;
  }

  .cycle-select select {
    padding: 0.25rem 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.9rem;
  }

  .error-box {
    background: #fee;
    border: 1px solid #c00;
    padding: 1rem;
    border-radius: 4px;
    margin-bottom: 1rem;
    color: #900;
  }

  .info-section {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1.5rem;
  }

  .filings-section {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1.5rem;
  }

  .filings-section h2 {
    font-size: 1.25rem;
    margin-bottom: 1rem;
  }

  .filings-table {
    width: 100%;
    border-collapse: collapse;
  }

  .filings-table th,
  .filings-table td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid #e0e0e0;
  }

  .filings-table th {
    background: #f5f5f5;
    font-weight: 600;
  }

  .filings-table a {
    color: #0066cc;
    text-decoration: none;
  }

  .filings-table a:hover {
    text-decoration: underline;
  }

  .footer-info {
    margin-top: 2rem;
    padding-top: 1.5rem;
    border-top: 1px solid #e0e0e0;
    font-size: 0.9rem;
    color: #666;
  }

  .footer-item {
    margin-bottom: 0.5rem;
  }

  .footer-label {
    font-weight: 600;
  }
</style>

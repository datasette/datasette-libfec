<script lang="ts">
  import type { CommitteePageData } from './page_data/CommitteePageData.types.ts';
  import { loadPageData } from './page_data/load.ts';
  import Breadcrumb, { type BreadcrumbItem } from './components/Breadcrumb.svelte';

  const pageData = loadPageData<CommitteePageData>();

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

  // Build breadcrumb items
  function getBreadcrumbItems(): BreadcrumbItem[] {
    const items: BreadcrumbItem[] = [{ label: 'FEC Data', href: '/-/libfec' }];

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

      items.push({ label: contestLabel, href: `/-/libfec/contest?${contestParams.toString()}` });

      items.push({
        label: cand.name || 'Candidate',
        href: `/-/libfec/candidate/${cand.candidate_id}?cycle=${pageData.cycle}`,
      });
    }

    items.push({ label: 'Committee' });
    return items;
  }

  const breadcrumbItems = getBreadcrumbItems();
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

      <div class="external-link">
        <a
          href="https://www.fec.gov/data/committee/{pageData.committee_id}/"
          target="_blank"
          rel="noopener noreferrer"
        >
          View on FEC.gov &rarr;
        </a>
      </div>
    </div>

    {#if isPrincipal}
      <p class="subtitle">
        Principal campaign committee for
        <a href="/-/libfec/candidate/{pageData.candidate?.candidate_id}?cycle={pageData.cycle}">
          {pageData.candidate?.name}
        </a>
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
                <a href="/-/libfec/filing/{filing.filing_id}">
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

  .external-link {
    margin-top: 0.5rem;
  }

  .external-link a {
    color: #0066cc;
    text-decoration: none;
    font-size: 0.9rem;
  }

  .external-link a:hover {
    text-decoration: underline;
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

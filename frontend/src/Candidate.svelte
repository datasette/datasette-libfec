<script lang="ts">
  import type { CandidatePageData } from './page_data/CandidatePageData.types.ts';
  import { loadPageData } from './page_data/load.ts';

  const pageData = loadPageData<CandidatePageData>();

  const officeNames: Record<string, string> = {
    H: 'House',
    S: 'Senate',
    P: 'President',
  };

  function getStatusLabel(status: string | null | undefined): string | null {
    if (!status) return null;
    const statuses: Record<string, string> = {
      I: 'Incumbent',
      C: 'Challenger',
      O: 'Open Seat',
    };
    return statuses[status] || status;
  }

  function getContestUrl(candidate: any): string {
    const params = new URLSearchParams();
    params.set('state', candidate.state);
    params.set('office', candidate.office);
    params.set('cycle', pageData.cycle.toString());
    if (candidate.office === 'H' && candidate.district) {
      params.set('district', candidate.district.toString());
    }
    return `/-/libfec/contest?${params.toString()}`;
  }

  // Build office description
  function getOfficeDescription(candidate: any): string {
    let desc = candidate.state + ' ' + (officeNames[candidate.office] || candidate.office);
    if (candidate.office === 'H' && candidate.district) {
      desc += ' District ' + candidate.district;
    }
    return desc;
  }

  const statusLabel = getStatusLabel(pageData.candidate?.incumbent_challenger_status);
</script>

<div class="candidate-page">
  <div class="header">
    <div class="breadcrumb">
      <a href="/-/libfec">FEC Data</a>
      {#if pageData.candidate}
        &rarr;
        <a href={getContestUrl(pageData.candidate)}>
          {pageData.candidate.state}
          {pageData.candidate.office
            ? officeNames[pageData.candidate.office] || pageData.candidate.office
            : ''}
          {#if pageData.candidate.office === 'H' && pageData.candidate.district}
            {pageData.candidate.district}
          {/if}
        </a>
      {/if}
      &rarr; Candidate
    </div>

    <div class="title-row">
      <h1>
        {pageData.candidate?.name || pageData.candidate_id}
        {#if pageData.candidate?.party_affiliation}
          <span class="party-badge {pageData.candidate.party_affiliation.toLowerCase()}">
            {pageData.candidate.party_affiliation}
          </span>
        {/if}
      </h1>

      <div class="external-link">
        <a
          href="https://www.fec.gov/data/candidate/{pageData.candidate_id}/"
          target="_blank"
          rel="noopener noreferrer"
        >
          View on FEC.gov &rarr;
        </a>
      </div>
    </div>

    {#if pageData.candidate}
      <p class="subtitle">
        {#if statusLabel}{statusLabel} for{:else}Running for{/if}
        <a href={getContestUrl(pageData.candidate)}>{getOfficeDescription(pageData.candidate)}</a>
        in {pageData.cycle}
      </p>
    {/if}
  </div>

  {#if pageData.error}
    <div class="error-box">
      <strong>Error:</strong>
      {pageData.error}
    </div>
  {/if}

  {#if !pageData.candidate && !pageData.error}
    <div class="info-section">
      <p>Candidate not found.</p>
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

  {#if pageData.committee || pageData.candidate?.address_street1 || pageData.candidate?.address_city}
    <div class="footer-info">
      {#if pageData.committee}
        <div class="footer-item">
          <span class="footer-label">Principal Committee:</span>
          <a href="/-/libfec/committee/{pageData.committee.committee_id}?cycle={pageData.cycle}">
            {pageData.committee.name || pageData.committee.committee_id}
          </a>
        </div>
      {/if}

      {#if pageData.candidate?.address_street1 || pageData.candidate?.address_city}
        <div class="footer-item">
          <span class="footer-label">Address:</span>
          {#if pageData.candidate.address_street1}
            {pageData.candidate.address_street1},
          {/if}
          {#if pageData.candidate.address_street2}
            {pageData.candidate.address_street2},
          {/if}
          {#if pageData.candidate.address_city}
            {pageData.candidate.address_city},
          {/if}
          {#if pageData.candidate.address_state}
            {pageData.candidate.address_state}
          {/if}
          {#if pageData.candidate.address_zip}
            {pageData.candidate.address_zip}
          {/if}
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .candidate-page {
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

  .party-badge.dem {
    background: #cce5ff;
    color: #004085;
  }

  .party-badge.rep {
    background: #f8d7da;
    color: #721c24;
  }

  .party-badge.lib {
    background: #fff3cd;
    color: #856404;
  }

  .party-badge.gre {
    background: #d4edda;
    color: #155724;
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

  .external-link a {
    color: #0066cc;
    text-decoration: none;
    font-size: 0.9rem;
  }

  .external-link a:hover {
    text-decoration: underline;
  }

  .breadcrumb {
    font-size: 0.9rem;
    color: #666;
    margin-bottom: 0.5rem;
  }

  .breadcrumb a {
    color: #0066cc;
    text-decoration: none;
  }

  .breadcrumb a:hover {
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

  .footer-item a {
    color: #0066cc;
    text-decoration: none;
  }

  .footer-item a:hover {
    text-decoration: underline;
  }

  .footer-label {
    font-weight: 600;
  }
</style>

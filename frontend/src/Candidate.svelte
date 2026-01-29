<script lang="ts">
  import type { CandidatePageData } from "./page_data/CandidatePageData.types.ts";
  import { loadPageData } from "./page_data/load.ts";

  const pageData = loadPageData<CandidatePageData>();

  const officeNames: Record<string, string> = {
    'H': 'House',
    'S': 'Senate',
    'P': 'President'
  };

  function getPartyLabel(party: string | null | undefined): string {
    if (!party) return 'Unknown';
    const parties: Record<string, string> = {
      'DEM': 'Democrat',
      'REP': 'Republican',
      'LIB': 'Libertarian',
      'GRE': 'Green',
      'IND': 'Independent',
      'NPA': 'No Party Affiliation'
    };
    return parties[party] || party;
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
</script>

<div class="candidate-page">
  <div class="header">
    <h1>{pageData.candidate?.name || pageData.candidate_id}</h1>
    <div class="breadcrumb">
      <a href="/-/libfec">FEC Data</a>
      {#if pageData.candidate}
        &rarr;
        <a href={getContestUrl(pageData.candidate)}>
          {pageData.candidate.state}
          {pageData.candidate.office ? officeNames[pageData.candidate.office] || pageData.candidate.office : ''}
          {#if pageData.candidate.office === 'H' && pageData.candidate.district}
            District {pageData.candidate.district}
          {/if}
        </a>
      {/if}
      &rarr; Candidate
    </div>
  </div>

  {#if pageData.error}
    <div class="error-box">
      <strong>Error:</strong> {pageData.error}
    </div>
  {/if}

  {#if pageData.candidate}
    <div class="content-grid">
      <section class="info-section">
        <h2>Candidate Information</h2>
        <div class="section-box">
          <dl>
            <dt>Candidate ID:</dt>
            <dd>{pageData.candidate.candidate_id}</dd>

            <dt>Party:</dt>
            <dd>
              <span class="party {pageData.candidate.party_affiliation?.toLowerCase()}">
                {getPartyLabel(pageData.candidate.party_affiliation)}
              </span>
            </dd>

            <dt>Office:</dt>
            <dd>
              <a href={getContestUrl(pageData.candidate)}>
                {pageData.candidate.state}
                {pageData.candidate.office ? officeNames[pageData.candidate.office] || pageData.candidate.office : ''}
                {#if pageData.candidate.office === 'H' && pageData.candidate.district}
                  District {pageData.candidate.district}
                {/if}
              </a>
            </dd>

            {#if pageData.candidate.incumbent_challenger_status}
              <dt>Status:</dt>
              <dd>
                {#if pageData.candidate.incumbent_challenger_status === 'I'}
                  Incumbent
                {:else if pageData.candidate.incumbent_challenger_status === 'C'}
                  Challenger
                {:else if pageData.candidate.incumbent_challenger_status === 'O'}
                  Open Seat
                {:else}
                  {pageData.candidate.incumbent_challenger_status}
                {/if}
              </dd>
            {/if}

            <dt>Election Cycle:</dt>
            <dd>{pageData.cycle}</dd>
          </dl>
        </div>

        {#if pageData.candidate.address_street1 || pageData.candidate.address_city}
          <div class="section-box">
            <h3>Address</h3>
            <address>
              {#if pageData.candidate.address_street1}
                {pageData.candidate.address_street1}<br>
              {/if}
              {#if pageData.candidate.address_street2}
                {pageData.candidate.address_street2}<br>
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
            </address>
          </div>
        {/if}

        <div class="external-links">
          <a
            href="https://www.fec.gov/data/candidate/{pageData.candidate_id}/"
            target="_blank"
            rel="noopener noreferrer"
          >
            View on FEC.gov &rarr;
          </a>
        </div>
      </section>

      {#if pageData.committee}
        <section class="info-section">
          <h2>Principal Committee</h2>
          <div class="section-box">
            <dl>
              <dt>Committee Name:</dt>
              <dd>
                <a href="/-/libfec/committee/{pageData.committee.committee_id}?cycle={pageData.cycle}">
                  {pageData.committee.name || 'Unknown'}
                </a>
              </dd>

              <dt>Committee ID:</dt>
              <dd>
                <a href="/-/libfec/committee/{pageData.committee.committee_id}?cycle={pageData.cycle}">
                  {pageData.committee.committee_id}
                </a>
              </dd>

              {#if pageData.committee.committee_type}
                <dt>Type:</dt>
                <dd>{pageData.committee.committee_type}</dd>
              {/if}

              {#if pageData.committee.designation}
                <dt>Designation:</dt>
                <dd>{pageData.committee.designation}</dd>
              {/if}
            </dl>
          </div>
        </section>
      {/if}
    </div>

  {:else if !pageData.error}
    <div class="info-section">
      <p>Candidate not found.</p>
    </div>
  {/if}

  {#if pageData.filings && pageData.filings.length > 0}
    <section class="filings-section">
      <h2>Recent Filings ({pageData.filings.length})</h2>
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

  .header h1 {
    font-size: 2rem;
    margin-bottom: 0.5rem;
  }

  .breadcrumb {
    font-size: 0.9rem;
    color: #666;
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

  .content-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .info-section {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1.5rem;
  }

  .info-section h2 {
    font-size: 1.25rem;
    margin-bottom: 1rem;
  }

  .section-box {
    background: #f9f9f9;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 1rem;
    margin-bottom: 1rem;
  }

  .section-box h3 {
    font-size: 1rem;
    margin-bottom: 0.5rem;
  }

  dl {
    display: grid;
    grid-template-columns: max-content 1fr;
    gap: 0.5rem 1rem;
  }

  dt {
    font-weight: 600;
    color: #666;
  }

  dd {
    margin: 0;
  }

  dd a {
    color: #0066cc;
    text-decoration: none;
  }

  dd a:hover {
    text-decoration: underline;
  }

  .party {
    display: inline-block;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.9rem;
  }

  .party.dem {
    background: #cce5ff;
    color: #004085;
  }

  .party.rep {
    background: #f8d7da;
    color: #721c24;
  }

  .party.lib {
    background: #fff3cd;
    color: #856404;
  }

  .party.gre {
    background: #d4edda;
    color: #155724;
  }

  address {
    font-style: normal;
    line-height: 1.6;
  }

  .external-links {
    margin-top: 1rem;
  }

  .external-links a {
    color: #0066cc;
    text-decoration: none;
  }

  .external-links a:hover {
    text-decoration: underline;
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
</style>

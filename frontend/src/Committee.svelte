<script lang="ts">
  import type { CommitteePageData } from "./page_data/CommitteePageData.types.ts";
  import { loadPageData } from "./page_data/load.ts";

  const pageData = loadPageData<CommitteePageData>();

  const officeNames: Record<string, string> = {
    'H': 'House',
    'S': 'Senate',
    'P': 'President'
  };

  function getCommitteeTypeLabel(type: string | null | undefined): string {
    if (!type) return 'Unknown';
    const types: Record<string, string> = {
      'C': 'Communication Cost',
      'D': 'Delegate Committee',
      'E': 'Electioneering Communication',
      'H': 'House Campaign',
      'I': 'Independent Expenditor',
      'N': 'PAC - Nonqualified',
      'O': 'Super PAC (Independent Expenditure-Only)',
      'P': 'Presidential Campaign',
      'Q': 'PAC - Qualified',
      'S': 'Senate Campaign',
      'U': 'Single Candidate Independent Expenditure',
      'V': 'PAC with Non-Contribution Account',
      'W': 'PAC with Non-Contribution Account - Nonqualified',
      'X': 'Party - Nonqualified',
      'Y': 'Party - Qualified',
      'Z': 'National Party Nonfederal Account'
    };
    return types[type] || type;
  }

  function getDesignationLabel(designation: string | null | undefined): string {
    if (!designation) return 'Unknown';
    const designations: Record<string, string> = {
      'A': 'Authorized by Candidate',
      'B': 'Lobbyist/Registrant PAC',
      'D': 'Leadership PAC',
      'J': 'Joint Fundraising Committee',
      'P': 'Principal Campaign Committee',
      'U': 'Unauthorized'
    };
    return designations[designation] || designation;
  }
</script>

<div class="committee-page">
  <div class="header">
    <h1>{pageData.committee?.name || pageData.committee_id}</h1>
    <div class="breadcrumb">
      <a href="/-/libfec">FEC Data</a>
      {#if pageData.candidate?.office && pageData.candidate?.state}
        &rarr;
        <a href="/-/libfec/contest?state={pageData.candidate.state}&office={pageData.candidate.office}{pageData.candidate.office === 'H' && pageData.candidate.district ? '&district=' + pageData.candidate.district : ''}&cycle={pageData.cycle}">
          {pageData.candidate.state} {officeNames[pageData.candidate.office] || pageData.candidate.office}
          {#if pageData.candidate.office === 'H' && pageData.candidate.district}
            {pageData.candidate.district}
          {/if}
        </a>
      {/if}
      {#if pageData.candidate}
        &rarr;
        <a href="/-/libfec/candidate/{pageData.candidate.candidate_id}?cycle={pageData.cycle}">
          {pageData.candidate.name}
        </a>
      {/if}
      &rarr; Committee
    </div>
  </div>

  {#if pageData.error}
    <div class="error-box">
      <strong>Error:</strong> {pageData.error}
    </div>
  {/if}

  {#if pageData.committee}
    <div class="content-grid">
      <section class="info-section">
        <h2>Committee Information</h2>
        <div class="section-box">
          <dl>
            <dt>Committee ID:</dt>
            <dd>{pageData.committee.committee_id}</dd>

            {#if pageData.committee.committee_type}
              <dt>Type:</dt>
              <dd>{getCommitteeTypeLabel(pageData.committee.committee_type)}</dd>
            {/if}

            {#if pageData.committee.designation}
              <dt>Designation:</dt>
              <dd>{getDesignationLabel(pageData.committee.designation)}</dd>
            {/if}

            {#if pageData.committee.party_affiliation}
              <dt>Party:</dt>
              <dd>{pageData.committee.party_affiliation}</dd>
            {/if}

            {#if pageData.committee.filing_frequency}
              <dt>Filing Frequency:</dt>
              <dd>{pageData.committee.filing_frequency}</dd>
            {/if}

            <dt>Election Cycle:</dt>
            <dd>{pageData.cycle}</dd>
          </dl>
        </div>

        {#if pageData.committee.address_street1 || pageData.committee.address_city}
          <div class="section-box">
            <h3>Address</h3>
            <address>
              {#if pageData.committee.address_street1}
                {pageData.committee.address_street1}<br>
              {/if}
              {#if pageData.committee.address_street2}
                {pageData.committee.address_street2}<br>
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
            </address>
          </div>
        {/if}

        {#if pageData.committee.treasurer_name}
          <div class="section-box">
            <h3>Treasurer</h3>
            <p>{pageData.committee.treasurer_name}</p>
          </div>
        {/if}

        <div class="external-links">
          <a
            href="https://www.fec.gov/data/committee/{pageData.committee_id}/"
            target="_blank"
            rel="noopener noreferrer"
          >
            View on FEC.gov &rarr;
          </a>
        </div>
      </section>

      {#if pageData.candidate}
        <section class="info-section">
          <h2>Associated Candidate</h2>
          <div class="section-box">
            <dl>
              <dt>Candidate Name:</dt>
              <dd>
                <a href="/-/libfec/candidate/{pageData.candidate.candidate_id}?cycle={pageData.cycle}">
                  {pageData.candidate.name || 'Unknown'}
                </a>
              </dd>

              <dt>Candidate ID:</dt>
              <dd>
                <a href="/-/libfec/candidate/{pageData.candidate.candidate_id}?cycle={pageData.cycle}">
                  {pageData.candidate.candidate_id}
                </a>
              </dd>

              {#if pageData.candidate.office && pageData.candidate.state}
                <dt>Contest:</dt>
                <dd>
                  <a href="/-/libfec/contest?state={pageData.candidate.state}&office={pageData.candidate.office}{pageData.candidate.office === 'H' && pageData.candidate.district ? '&district=' + pageData.candidate.district : ''}&cycle={pageData.cycle}">
                    {pageData.candidate.state}
                    {officeNames[pageData.candidate.office] || pageData.candidate.office}
                    {#if pageData.candidate.office === 'H' && pageData.candidate.district}
                      District {pageData.candidate.district}
                    {/if}
                  </a>
                </dd>
              {/if}

              {#if pageData.candidate.party_affiliation}
                <dt>Party:</dt>
                <dd>{pageData.candidate.party_affiliation}</dd>
              {/if}
            </dl>
          </div>
        </section>
      {/if}
    </div>

  {:else if !pageData.error}
    <div class="info-section">
      <p>Committee not found.</p>
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
  .committee-page {
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

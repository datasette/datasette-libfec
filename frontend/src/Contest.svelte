<script lang="ts">
  import type { ContestPageData, Candidate } from "./page_data/ContestPageData.types.ts";
  import { loadPageData } from "./page_data/load.ts";

  const pageData = loadPageData<ContestPageData>();

  const officeNames: Record<string, string> = {
    'H': 'House',
    'S': 'Senate',
    'P': 'President'
  };

  function formatCurrency(value: number | null | undefined): string {
    if (value == null) return '—';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(value);
  }

  function getCandidateUrl(candidate: Candidate): string {
    if (candidate.principal_campaign_committee) {
      return `/-/libfec/committee/${candidate.principal_campaign_committee}?cycle=${pageData.cycle}`;
    }
    return `/-/libfec/candidate/${candidate.candidate_id}?cycle=${pageData.cycle}`;
  }

  // Sort: incumbents first, then by cash on hand descending
  const sortedCandidates = (pageData.candidates ?? []).slice().sort((a, b) => {
    const aIncumbent = a.incumbent_challenger_status === 'I' ? 1 : 0;
    const bIncumbent = b.incumbent_challenger_status === 'I' ? 1 : 0;
    if (aIncumbent !== bIncumbent) return bIncumbent - aIncumbent;
    return (b.f3_cash_on_hand_end ?? 0) - (a.f3_cash_on_hand_end ?? 0);
  });
</script>

<div class="contest-page">
  <div class="header">
    <h1>{pageData.contest_description}</h1>
    <div class="meta">
      <span class="cycle">{pageData.cycle} Election Cycle</span>
      <span class="office">{officeNames[pageData.office] || pageData.office}</span>
    </div>
    <div class="breadcrumb">
      <a href="/-/libfec">FEC Data</a> &rarr; Contest
    </div>
  </div>
  <div> 
    <a href="https://www.fec.gov/data/elections/house/{pageData.state}/{pageData.district}/{pageData.cycle}/" target="_blank" rel="noopener noreferrer">
      fec.gov 
  </div>

  {#if pageData.error}
    <div class="error-box">
      <strong>Error:</strong> {pageData.error}
    </div>
  {/if}

  <section class="candidates-section">
    <h2>Candidates ({pageData.candidates?.length ?? 0})</h2>

    {#if !pageData.candidates || pageData.candidates.length === 0}
      <p class="no-data">No candidates found for this contest.</p>
    {:else}
      <table class="candidates-table">
        <thead>
          <tr>
            <th>Candidate</th>
            <th>Party</th>
            <th>Coverage Through</th>
            <th class="numeric">
              Cash on Hand
              <span class="info-icon" title="Form F3 Line 27, Cash on Hand at close of reporting period">i</span>
            </th>
            <th class="numeric">
              Spent This Cycle
              <span class="info-icon" title="Form F3 Line 22, Total disbursements for entire election cycle">i</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {#each sortedCandidates as candidate}
            <tr>
              <td>
                <a href={getCandidateUrl(candidate)}>
                  {candidate.name || 'Unknown'}
                </a>
                {#if candidate.incumbent_challenger_status === 'I'}
                  <span class="status-badge incumbent">Incumbent</span>
                {/if}
              </td>
              <td>
                {#if candidate.party_affiliation}
                  <span class="party-badge {candidate.party_affiliation.toLowerCase()}">
                    {candidate.party_affiliation}
                  </span>
                {/if}
              </td>
              <td>{candidate.f3_coverage_through_date ?? '—'}</td>
              <td class="numeric">{formatCurrency(candidate.f3_cash_on_hand_end)}</td>
              <td class="numeric">{formatCurrency(candidate.f3_total_disbursements)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </section>
</div>

<style>
  .contest-page {
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

  .meta {
    display: flex;
    gap: 1rem;
    margin-bottom: 0.5rem;
  }

  .cycle {
    background: #e0e0e0;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.9rem;
  }

  .office {
    background: #d0e0f0;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.9rem;
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

  .candidates-section {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1.5rem;
  }

  .candidates-section h2 {
    font-size: 1.5rem;
    margin-bottom: 1rem;
  }

  .no-data {
    color: #666;
    font-style: italic;
  }

  .candidates-table {
    width: 100%;
    border-collapse: collapse;
  }

  .candidates-table th,
  .candidates-table td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid #e0e0e0;
  }

  .candidates-table th {
    background: #f5f5f5;
    font-weight: 600;
  }

  .candidates-table th.numeric,
  .candidates-table td.numeric {
    text-align: right;
  }

  .candidates-table a {
    color: #0066cc;
    text-decoration: none;
  }

  .candidates-table a:hover {
    text-decoration: underline;
  }

  .party-badge {
    display: inline-block;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
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

  .status-badge {
    display: inline-block;
    padding: 0.15rem 0.4rem;
    border-radius: 3px;
    font-size: 0.75rem;
    margin-left: 0.5rem;
  }

  .status-badge.incumbent {
    background: #e0e0e0;
    color: #333;
  }

  .info-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 14px;
    height: 14px;
    margin-left: 4px;
    font-size: 10px;
    font-style: italic;
    font-weight: 600;
    color: #666;
    background: #e0e0e0;
    border-radius: 50%;
    cursor: help;
    vertical-align: middle;
  }
</style>

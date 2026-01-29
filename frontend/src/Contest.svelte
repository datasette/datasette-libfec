<script lang="ts">
  import type { ContestPageData } from "./page_data/ContestPageData.types.ts";
  import { loadPageData } from "./page_data/load.ts";

  const pageData = loadPageData<ContestPageData>();

  const officeNames: Record<string, string> = {
    'H': 'House',
    'S': 'Senate',
    'P': 'President'
  };

  function getPartyLabel(party: string | null | undefined): string {
    if (!party) return '';
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
      <div class="candidates-grid">
        {#each pageData.candidates as candidate}
          <div class="candidate-card">
            <div class="candidate-name">
              <a href="/-/libfec/candidate/{candidate.candidate_id}?cycle={pageData.cycle}">
                {candidate.name || 'Unknown'}
              </a>
            </div>

            {#if candidate.party_affiliation}
              <div class="party {candidate.party_affiliation.toLowerCase()}">
                {getPartyLabel(candidate.party_affiliation)}
              </div>
            {/if}

            <dl class="candidate-details">
              <dt>Candidate ID:</dt>
              <dd>
                <a href="/-/libfec/candidate/{candidate.candidate_id}?cycle={pageData.cycle}">
                  {candidate.candidate_id}
                </a>
              </dd>

              {#if candidate.incumbent_challenger_status}
                <dt>Status:</dt>
                <dd>
                  {#if candidate.incumbent_challenger_status === 'I'}
                    Incumbent
                  {:else if candidate.incumbent_challenger_status === 'C'}
                    Challenger
                  {:else if candidate.incumbent_challenger_status === 'O'}
                    Open Seat
                  {:else}
                    {candidate.incumbent_challenger_status}
                  {/if}
                </dd>
              {/if}

              {#if candidate.principal_campaign_committee}
                <dt>Committee:</dt>
                <dd>
                  <a href="/-/libfec/committee/{candidate.principal_campaign_committee}?cycle={pageData.cycle}">
                    {candidate.principal_campaign_committee}
                  </a>
                </dd>
              {/if}
            </dl>
          </div>
        {/each}
      </div>
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

  .candidates-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1rem;
  }

  .candidate-card {
    background: #f9f9f9;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 1rem;
  }

  .candidate-name {
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
  }

  .candidate-name a {
    color: #0066cc;
    text-decoration: none;
  }

  .candidate-name a:hover {
    text-decoration: underline;
  }

  .party {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.85rem;
    margin-bottom: 0.75rem;
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

  .candidate-details {
    display: grid;
    grid-template-columns: max-content 1fr;
    gap: 0.25rem 0.75rem;
    font-size: 0.9rem;
  }

  .candidate-details dt {
    font-weight: 600;
    color: #666;
  }

  .candidate-details dd {
    margin: 0;
  }

  .candidate-details a {
    color: #0066cc;
    text-decoration: none;
  }

  .candidate-details a:hover {
    text-decoration: underline;
  }
</style>

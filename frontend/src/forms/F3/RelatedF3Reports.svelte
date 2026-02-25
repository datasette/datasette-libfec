<script lang="ts">
  import { get } from 'svelte/store';
  import { databaseName, basePath as basePathStore } from '../../stores';
  import { query } from '../../api';
  import { useQuery } from '../../useQuery.svelte';

  interface CandidateReport {
    filing_id: string;
    filer_id: string;
    filer_name: string;
    candidate_name: string | null;
    candidate_id: string | null;
    total_receipts: number | null;
    operating_expenditures: number | null;
    cash_on_hand_close: number | null;
    is_current: boolean;
  }

  interface RaceInfo {
    state: string;
    office: string;
    district: string | null;
  }

  interface QueryResult {
    reports: CandidateReport[];
    raceInfo: RaceInfo | null;
  }

  interface Props {
    filingId: string;
    filerId: string;
    reportCode: string;
    coverageThroughDate: string;
  }

  let { filingId, filerId, reportCode, coverageThroughDate }: Props = $props();

  const dbName = get(databaseName);
  const bp = get(basePathStore);

  // First query to get the current candidate's race info
  async function fetchRaceInfo(): Promise<RaceInfo | null> {
    if (!filerId) return null;

    const sql = `
      SELECT state, office, district
      FROM libfec_candidates
      WHERE principal_campaign_committee = :filer_id
      LIMIT 1
    `;
    const results = await query(dbName, sql, { filer_id: filerId });
    return results.length > 0 ? results[0] : null;
  }

  // Query for all candidates in the race (including current)
  async function fetchCandidateReports(): Promise<QueryResult> {
    if (!reportCode || !coverageThroughDate || !filerId) {
      return { reports: [], raceInfo: null };
    }

    const raceInfo = await fetchRaceInfo();
    if (!raceInfo) return { reports: [], raceInfo: null };

    // Build query to find all candidates in the same race
    const sql = `
      SELECT
        f3.filing_id,
        fil.filer_id,
        fil.filer_name,
        cand.name as candidate_name,
        cand.candidate_id,
        f3.col_a_total_receipts as total_receipts,
        f3.col_a_operating_expenditures as operating_expenditures,
        f3.col_a_cash_on_hand_close_of_period as cash_on_hand_close
      FROM libfec_F3 f3
      JOIN libfec_filings fil ON f3.filing_id = fil.filing_id
      JOIN libfec_candidates cand ON cand.principal_campaign_committee = fil.filer_id
      WHERE f3.report_code = :report_code
        AND f3.coverage_through_date = :coverage_through_date
        AND cand.state = :state
        AND cand.office = :office
        ${raceInfo.district ? 'AND cand.district = :district' : ''}
      GROUP BY fil.filer_id
      ORDER BY f3.col_a_total_receipts DESC
    `;

    const params: Record<string, string> = {
      report_code: reportCode,
      coverage_through_date: coverageThroughDate,
      state: raceInfo.state,
      office: raceInfo.office,
    };
    if (raceInfo.district) {
      params.district = raceInfo.district;
    }

    const results = await query(dbName, sql, params);

    // Mark which one is the current filing
    const reports = results.map((r) => ({
      ...r,
      is_current: r.filing_id === filingId,
    }));

    return { reports, raceInfo };
  }

  const result = useQuery(fetchCandidateReports);

  function usd(value: number | null | undefined): string {
    if (value == null) return '-';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  }

  function buildContestLabel(raceInfo: RaceInfo): string {
    if (raceInfo.office === 'H' && raceInfo.district) {
      return `${raceInfo.state}-${raceInfo.district}`;
    } else if (raceInfo.office === 'S') {
      return `${raceInfo.state} Senate`;
    } else if (raceInfo.office === 'P') {
      return 'President';
    }
    return `${raceInfo.state} ${raceInfo.office}`;
  }

  function buildContestUrl(raceInfo: RaceInfo): string {
    const params = new URLSearchParams({
      state: raceInfo.state,
      office: raceInfo.office,
    });
    if (raceInfo.district) {
      params.set('district', raceInfo.district);
    }
    return `${bp}/contest?${params}`;
  }
</script>

{#if result.isLoading}
  <div class="related-reports">
    <h4>Candidates in Race</h4>
    <div class="loading">Loading...</div>
  </div>
{:else if result.data && result.data.reports.length > 1 && result.data.raceInfo}
  {@const raceInfo = result.data.raceInfo}
  {@const reports = result.data.reports}
  <div class="related-reports">
    <h4>
      <a href={buildContestUrl(raceInfo)} class="contest-link">{buildContestLabel(raceInfo)}</a>
      Candidates
    </h4>
    <p class="subtitle">F3 reports from the same period ending {coverageThroughDate}</p>
    <div class="table-container">
      <table class="reports-table">
        <thead>
          <tr>
            <th class="text-left">Candidate</th>
            <th class="text-left">Committee</th>
            <th class="text-right">Receipts</th>
            <th class="text-right">Operating Exp.</th>
            <th class="text-right">Cash on Hand</th>
          </tr>
        </thead>
        <tbody>
          {#each reports as report}
            <tr class:current={report.is_current}>
              <td>
                {#if report.is_current}
                  <span class="current-marker">★</span>
                  {report.candidate_name}
                {:else}
                  <a href="{bp}/filing/{report.filing_id}">{report.candidate_name}</a>
                {/if}
              </td>
              <td class="committee">{report.filer_name}</td>
              <td class="text-right">{usd(report.total_receipts)}</td>
              <td class="text-right">{usd(report.operating_expenditures)}</td>
              <td class="text-right">{usd(report.cash_on_hand_close)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
{/if}

<style>
  .related-reports {
    margin-top: 2rem;
    padding-top: 1.5rem;
    border-top: 1px solid #e5e7eb;
  }

  .related-reports h4 {
    font-size: 1rem;
    font-weight: 600;
    color: #374151;
    margin-bottom: 0.5rem;
  }

  .contest-link {
    color: #2563eb;
    text-decoration: none;
  }

  .contest-link:hover {
    text-decoration: underline;
  }

  .subtitle {
    font-size: 0.875rem;
    color: #6b7280;
    margin-bottom: 1rem;
  }

  .table-container {
    overflow-x: auto;
  }

  .reports-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
  }

  .reports-table th,
  .reports-table td {
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid #e5e5e5;
  }

  .reports-table th {
    font-weight: 600;
    color: #374151;
    border-bottom: 2px solid #d1d5db;
  }

  .reports-table tbody tr:hover {
    background: #f9fafb;
  }

  .reports-table tr.current {
    background: #fef3c7;
  }

  .reports-table tr.current:hover {
    background: #fde68a;
  }

  .text-left {
    text-align: left;
  }

  .text-right {
    text-align: right;
  }

  .committee {
    color: #6b7280;
    font-size: 0.85rem;
  }

  .current-marker {
    color: #d97706;
    margin-right: 0.25rem;
  }

  .reports-table a {
    color: #2563eb;
    text-decoration: none;
  }

  .reports-table a:hover {
    text-decoration: underline;
  }

  .loading {
    color: #6b7280;
    font-size: 0.9rem;
  }
</style>

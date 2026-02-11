<script lang="ts">
  import { loadPageData } from '../page_data/load.ts';
  import { query } from '../api.ts';
  import { useQuery } from '../useQuery.svelte.ts';
  import { getReportLabel } from '../utils/reportCodes.ts';
  import { STATE_NAMES } from '../utils/stateNames.ts';
  import { AVAILABLE_COLUMNS, DEFAULT_COLUMNS, getColumnsById, type ColumnDef } from './columns.ts';
  import ColumnSelector from './ColumnSelector.svelte';
  import Breadcrumb from '../components/Breadcrumb.svelte';

  interface FilingDayPageData {
    database_name: string;
    years: number[];
  }

  interface FilingReport {
    candidate_id: string;
    candidate_name: string | null;
    party_affiliation: string | null;
    state: string | null;
    district: string | null;
    incumbent_challenger_status: string | null;
    principal_campaign_committee: string | null;
    filing_id: string;
    [key: string]: string | number | null;
  }

  const pageData = loadPageData<FilingDayPageData>();

  // Common report codes for F3 filings
  const reportCodes = [
    'Q1',
    'Q2',
    'Q3',
    'MY',
    'YE',
    'M2',
    'M3',
    'M4',
    'M5',
    'M6',
    'M7',
    'M8',
    'M9',
    'M10',
    'M11',
    'M12',
    '12P',
    '12G',
    '30G',
    '30P',
    'TER',
  ];

  // Read initial state from URL params
  const urlParams = new URLSearchParams(window.location.search);

  // Parse columns from URL or use defaults
  function parseColumnsFromUrl(): string[] {
    const colsParam = urlParams.get('cols');
    if (colsParam) {
      const cols = colsParam.split(',').filter((c) => AVAILABLE_COLUMNS.some((ac) => ac.id === c));
      if (cols.length > 0) return cols;
    }
    return DEFAULT_COLUMNS;
  }

  // Filter state
  let reportCode = $state(urlParams.get('report') || 'Q1');
  let year = $state(urlParams.get('year') || String(2025));
  let office = $state(urlParams.get('office') || 'H');
  let stateFilter = $state(urlParams.get('state') || '');
  let district = $state(urlParams.get('district') || '');
  let partyFilter = $state(urlParams.get('party') || '');
  let statusFilter = $state(urlParams.get('status') || '');

  // Minimum cash on hand filter
  let minCashEnabled = $state(urlParams.has('min_cash'));
  let minCashAmount = $state(urlParams.get('min_cash') || '20000');

  // Column state
  let selectedColumnIds = $state<string[]>(parseColumnsFromUrl());
  let showColumnSelector = $state(false);

  // Sort state
  let sortColumn = $state<string>('total_individual');
  let sortDirection = $state<'asc' | 'desc'>('desc');

  // Derived: active column definitions
  const activeColumns = $derived(getColumnsById(selectedColumnIds));

  // State list for dropdown
  const states = Object.entries(STATE_NAMES).map(([code, name]) => ({
    code,
    name,
  }));

  // Static SQL query - no string concatenation, uses IIF() for conditional filtering
  const sql = `
WITH matching_filings AS (
  SELECT
    fil.filer_id,
    f3.filing_id,
    -- Receipts
    f3.col_a_total_individual_contributions as total_individual,
    f3.col_a_individual_contributions_itemized as large_individual,
    f3.col_a_individual_contributions_unitemized as small_individual,
    CASE WHEN f3.col_a_total_individual_contributions > 0
      THEN f3.col_a_individual_contributions_unitemized * 100.0 / f3.col_a_total_individual_contributions
      ELSE NULL END as small_donor_ratio,
    f3.col_a_candidate_loans as candidate_loans,
    f3.col_a_pac_contributions as pac_contributions,
    f3.col_a_political_party_contributions as party_contributions,
    f3.col_a_total_receipts as total_receipts,
    -- Disbursements
    f3.col_a_operating_expenditures as operating_expenditures,
    f3.col_a_total_refunds as total_refunds,
    f3.col_a_total_disbursements as total_disbursements,
    -- Cash on Hand
    f3.col_a_cash_beginning_reporting_period as cash_on_hand_begin,
    f3.col_a_cash_on_hand_close_of_period as cash_on_hand_end
  FROM libfec_filings fil
  JOIN libfec_F3 f3 ON fil.filing_id = f3.filing_id
  WHERE f3.report_code = :report_code
    AND strftime('%Y', f3.coverage_through_date) = :year
    AND IIF(:min_cash_enabled = '1', f3.col_a_cash_on_hand_close_of_period >= :min_cash, 1)
),
candidates_in_race AS (
  SELECT
    cand.candidate_id,
    cand.name as candidate_name,
    cand.party_affiliation,
    cand.state,
    cand.district,
    cand.incumbent_challenger_status,
    cand.principal_campaign_committee
  FROM libfec_candidates cand
  WHERE cand.office = :office
    AND IIF(:state = '', 1, cand.state = :state)
    AND IIF(:office != 'H' OR :district = '', 1, cand.district = :district)
    AND IIF(:party = '', 1,
        IIF(:party = 'OTH', cand.party_affiliation NOT IN ('DEM', 'REP'), cand.party_affiliation = :party))
    AND IIF(:status = '', 1, cand.incumbent_challenger_status = :status)
  GROUP BY cand.candidate_id
),
final AS (
  SELECT
    c.candidate_id,
    c.candidate_name,
    c.party_affiliation,
    c.state,
    c.district,
    c.incumbent_challenger_status,
    c.principal_campaign_committee,
    mf.*
  FROM candidates_in_race c
  JOIN matching_filings mf ON c.principal_campaign_committee = mf.filer_id
  ORDER BY mf.total_individual DESC
  LIMIT 500
)
SELECT * FROM final
`;

  function getQueryParams(): Record<string, string> {
    return {
      report_code: reportCode,
      year: year,
      office: office,
      state: stateFilter,
      district: district,
      party: partyFilter,
      status: statusFilter,
      min_cash_enabled: minCashEnabled ? '1' : '0',
      min_cash: minCashAmount,
    };
  }

  async function fetchReports(): Promise<FilingReport[]> {
    return await query(pageData.database_name, sql, getQueryParams());
  }

  const result = useQuery(fetchReports);

  // Update URL with current state
  function updateUrl() {
    const params = new URLSearchParams();
    params.set('report', reportCode);
    params.set('year', year);
    params.set('office', office);
    if (stateFilter) params.set('state', stateFilter);
    if (district) params.set('district', district);
    if (partyFilter) params.set('party', partyFilter);
    if (statusFilter) params.set('status', statusFilter);
    if (minCashEnabled) params.set('min_cash', minCashAmount);
    params.set('cols', selectedColumnIds.join(','));

    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.replaceState({}, '', newUrl);
  }

  // Refetch when filters change and update URL
  $effect(() => {
    // Access reactive variables to track them
    reportCode;
    year;
    office;
    stateFilter;
    district;
    partyFilter;
    statusFilter;
    minCashEnabled;
    minCashAmount;
    selectedColumnIds;

    updateUrl();
    result.refetch?.();
  });

  // Sorted reports with ranking
  const sortedReports = $derived(() => {
    if (!result.data) return [];

    const sorted = [...result.data].sort((a, b) => {
      const aVal = a[sortColumn];
      const bVal = b[sortColumn];

      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return 1;
      if (bVal == null) return -1;

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
      }

      const strA = String(aVal).toLowerCase();
      const strB = String(bVal).toLowerCase();
      return sortDirection === 'asc' ? strA.localeCompare(strB) : strB.localeCompare(strA);
    });

    return sorted;
  });

  function toggleSort(columnId: string) {
    if (sortColumn === columnId) {
      sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      sortColumn = columnId;
      sortDirection = 'desc';
    }
  }

  function getSortIndicator(columnId: string): string {
    if (sortColumn !== columnId) return '';
    return sortDirection === 'asc' ? ' \u25B2' : ' \u25BC';
  }

  function formatValue(value: number | null | undefined, column: ColumnDef): string {
    if (value == null) return '\u2014';
    if (column.isPercent) {
      return value.toFixed(1) + '%';
    }
    if (column.isCurrency) {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        maximumFractionDigits: 0,
      }).format(value);
    }
    return String(value);
  }

  function isZeroValue(value: number | null | undefined): boolean {
    return value === 0;
  }

  function formatCurrencyInput(value: string): string {
    const num = parseInt(value, 10);
    if (isNaN(num)) return '';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(num);
  }

  function parseCurrencyInput(formatted: string): string {
    // Remove $, commas, and whitespace
    const cleaned = formatted.replace(/[$,\s]/g, '');
    const num = parseInt(cleaned, 10);
    return isNaN(num) ? '20000' : String(num);
  }

  let minCashDisplay = $state(formatCurrencyInput(minCashAmount));

  function handleMinCashBlur() {
    minCashAmount = parseCurrencyInput(minCashDisplay);
    minCashDisplay = formatCurrencyInput(minCashAmount);
  }

  function handleMinCashFocus(e: FocusEvent) {
    // Show raw number on focus for easier editing
    minCashDisplay = minCashAmount;
    (e.target as HTMLInputElement).select();
  }

  function getCandidateUrl(report: FilingReport): string {
    if (report.principal_campaign_committee) {
      return `/-/libfec/committee/${report.principal_campaign_committee}`;
    }
    return `/-/libfec/candidate/${report.candidate_id}`;
  }

  function getContestUrl(report: FilingReport): string {
    const params = new URLSearchParams();
    if (report.state) params.set('state', report.state);
    params.set('office', office);
    if (office === 'H' && report.district) params.set('district', report.district);
    // Cycle is always an even year (odd years round up)
    const yearNum = parseInt(year, 10);
    const cycle = yearNum % 2 === 1 ? yearNum + 1 : yearNum;
    params.set('cycle', String(cycle));
    return `/-/libfec/contest?${params.toString()}`;
  }

  function getContestLabel(report: FilingReport): string {
    if (office === 'H' && report.district) {
      return `${report.state || ''}-${report.district}`;
    }
    return report.state || '';
  }

  function handleColumnsApply(columns: string[]) {
    selectedColumnIds = columns;
    // Reset sort to first column if current sort column is no longer visible
    const firstCol = columns[0];
    if (!columns.includes(sortColumn) && firstCol) {
      sortColumn = firstCol;
    }
  }

  function getSqlQueryUrl(): string {
    const params = new URLSearchParams();
    params.set('sql', sql.trim());
    const queryParams = getQueryParams();
    for (const [key, value] of Object.entries(queryParams)) {
      params.set(key, value);
    }
    return `/${pageData.database_name}/-/query?${params.toString()}`;
  }
</script>

<div class="filing-day-page">
  <div class="header">
    <Breadcrumb items={[{ label: 'FEC Data', href: '/-/libfec' }, { label: 'Filing Day' }]} />
    <h1>Filing Day</h1>
  </div>

  <section class="filters">
    <div class="filter-row">
      <label>
        Report
        <select bind:value={reportCode}>
          {#each reportCodes as code}
            <option value={code}>{code} - {getReportLabel(code)}</option>
          {/each}
        </select>
      </label>

      <label>
        Year
        <select bind:value={year}>
          {#each pageData.years as y}
            <option value={String(y)}>{y}</option>
          {/each}
        </select>
      </label>

      <label>
        Office
        <select bind:value={office}>
          <option value="H">House</option>
          <option value="S">Senate</option>
        </select>
      </label>

      <label>
        State
        <select bind:value={stateFilter}>
          <option value="">All States</option>
          {#each states as s}
            <option value={s.code}>{s.code} - {s.name}</option>
          {/each}
        </select>
      </label>

      {#if office === 'H'}
        <label>
          District
          <input
            type="text"
            bind:value={district}
            placeholder="e.g. 01"
            maxlength="2"
            class="district-input"
          />
        </label>
      {/if}
    </div>

    <div class="filter-row">
      <label>
        Party
        <select bind:value={partyFilter}>
          <option value="">All Parties</option>
          <option value="DEM">Democrat</option>
          <option value="REP">Republican</option>
          <option value="OTH">Other</option>
        </select>
      </label>

      <label>
        Status
        <select bind:value={statusFilter}>
          <option value="">All</option>
          <option value="I">Incumbents</option>
          <option value="C">Challengers</option>
          <option value="O">Open Seat</option>
        </select>
      </label>

      <label class="min-cash-filter">
        <span>Min COH</span>
        <input type="checkbox" bind:checked={minCashEnabled} />
        {#if minCashEnabled}
          <input
            type="text"
            bind:value={minCashDisplay}
            class="min-cash-input"
            onblur={handleMinCashBlur}
            onfocus={handleMinCashFocus}
          />
        {/if}
      </label>
    </div>
  </section>

  {#if result.error}
    <div class="error-box">
      <strong>Error:</strong>
      {result.error}
    </div>
  {/if}

  <section class="results-section">
    {#if result.isLoading}
      <p class="loading">Loading...</p>
    {:else if sortedReports().length === 0}
      <p class="no-data">No filings found matching your criteria.</p>
    {:else}
      <div class="results-header">
        <p class="result-count">
          {sortedReports().length >= 500 ? '500+' : sortedReports().length} filings found
        </p>
        <div class="results-actions">
          <button
            type="button"
            class="edit-columns-btn"
            onclick={() => (showColumnSelector = true)}
          >
            Edit Columns ({selectedColumnIds.length})
          </button>
          <a href={getSqlQueryUrl()} target="_blank" class="view-sql-link">View SQL</a>
        </div>
      </div>
      <div class="table-wrapper">
        <table class="reports-table">
          <thead>
            <tr>
              <th class="numeric">Rank</th>
              <th class="sortable" onclick={() => toggleSort('candidate_name')}>
                Candidate{getSortIndicator('candidate_name')}
              </th>
              <th class="sortable" onclick={() => toggleSort('party_affiliation')}>
                Party{getSortIndicator('party_affiliation')}
              </th>
              <th class="sortable" onclick={() => toggleSort('state')}>
                State/Dist{getSortIndicator('state')}
              </th>
              {#each activeColumns as column}
                <th
                  class="sortable numeric"
                  onclick={() => toggleSort(column.id)}
                  title={column.description}
                >
                  {column.shortLabel}{getSortIndicator(column.id)}
                </th>
              {/each}
              <th>Filing</th>
            </tr>
          </thead>
          <tbody>
            {#each sortedReports() as report, index}
              <tr>
                <td class="numeric rank">{index + 1}</td>
                <td>
                  <a href={getCandidateUrl(report)}>
                    {report.candidate_name || 'Unknown'}
                  </a>
                  {#if report.incumbent_challenger_status === 'I'}
                    <span class="status-badge incumbent">Inc</span>
                  {/if}
                </td>
                <td>
                  {#if report.party_affiliation}
                    <span class="party-badge {report.party_affiliation.toLowerCase()}">
                      {report.party_affiliation}
                    </span>
                  {/if}
                </td>
                <td>
                  <a href={getContestUrl(report)}>{getContestLabel(report)}</a>
                </td>
                {#each activeColumns as column}
                  <td class="numeric" class:zero-value={isZeroValue(report[column.id] as number)}
                    >{formatValue(report[column.id] as number, column)}</td
                  >
                {/each}
                <td><a href="/-/libfec/filing/{report.filing_id}">{report.filing_id}</a></td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </section>
</div>

{#if showColumnSelector}
  <ColumnSelector
    selectedColumns={selectedColumnIds}
    onClose={() => (showColumnSelector = false)}
    onApply={handleColumnsApply}
  />
{/if}

<style>
  .filing-day-page {
    max-width: 1600px;
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

  .filters {
    background: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1rem 1.5rem;
    margin-bottom: 1.5rem;
  }

  .filter-row {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    align-items: flex-end;
  }

  .filter-row + .filter-row {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid #ddd;
  }

  .filter-row label {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.9rem;
    font-weight: 500;
  }

  .filter-row select,
  .filter-row input {
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.9rem;
  }

  .district-input {
    width: 60px;
  }

  .min-cash-filter {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
    font-weight: 500;
  }

  .min-cash-filter input[type='checkbox'] {
    width: 16px;
    height: 16px;
  }

  .min-cash-input {
    width: 100px;
  }

  .edit-columns-btn {
    padding: 0.5rem 1rem;
    background: #0066cc;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    align-self: flex-end;
  }

  .edit-columns-btn:hover {
    background: #0055aa;
  }

  .error-box {
    background: #fee;
    border: 1px solid #c00;
    padding: 1rem;
    border-radius: 4px;
    margin-bottom: 1rem;
    color: #900;
  }

  .results-section {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1.5rem;
  }

  .loading {
    color: #666;
    font-style: italic;
  }

  .no-data {
    color: #666;
    font-style: italic;
  }

  .results-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .result-count {
    color: #666;
    margin: 0;
  }

  .results-actions {
    display: flex;
    gap: 1rem;
    align-items: center;
  }

  .view-sql-link {
    color: #0066cc;
    text-decoration: none;
    font-size: 0.9rem;
  }

  .view-sql-link:hover {
    text-decoration: underline;
  }

  .table-wrapper {
    overflow-x: auto;
  }

  .reports-table {
    width: 100%;
    border-collapse: collapse;
    white-space: nowrap;
  }

  .reports-table th,
  .reports-table td {
    padding: 0.5rem 0.75rem;
    text-align: left;
    border-bottom: 1px solid #e0e0e0;
  }

  .reports-table th {
    background: #f5f5f5;
    font-weight: 600;
    font-size: 0.85rem;
  }

  .reports-table th.sortable {
    cursor: pointer;
    user-select: none;
  }

  .reports-table th.sortable:hover {
    background: #e8e8e8;
  }

  .reports-table th.numeric,
  .reports-table td.numeric {
    text-align: right;
  }

  .reports-table td.zero-value {
    color: #999;
  }

  .reports-table td.rank {
    color: #666;
    font-weight: 500;
  }

  .reports-table a {
    color: #0066cc;
    text-decoration: none;
  }

  .reports-table a:hover {
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
    font-size: 0.7rem;
    margin-left: 0.5rem;
  }

  .status-badge.incumbent {
    background: #e0e0e0;
    color: #333;
  }
</style>

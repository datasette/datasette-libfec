<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { F3SankeyComponent, type InputRow } from '../../components/sankey';
  import { databaseName } from '../../stores';
  import { query } from '../../api';
  import StateContributors from './StateContributors.svelte';
  import TopPayees from './TopPayees.svelte';
  import { getReportLabel } from '../../utils/reportCodes';

  // F3 form data from database - extends InputRow with additional summary fields
  export interface F3FormData extends InputRow {
    report_code: string;
    
    // Summary totals
    col_a_total_disbursements: number | null;

    // Line 6: Net Contributions
    col_a_total_contributions_no_loans: number | null;
    col_b_total_contributions_no_loans: number | null;
    col_a_total_contributions_refunds: number | null;
    col_b_total_contributions_refunds: number | null;
    col_a_net_contributions: number | null;
    col_b_net_contributions: number | null;

    // Line 7: Net Operating Expenditures
    col_a_total_operating_expenditures: number | null;
    col_b_total_operating_expenditures: number | null;
    col_a_total_offset_to_operating_expenditures: number | null;
    col_b_total_offset_to_operating_expenditures: number | null;
    col_a_net_operating_expenditures: number | null;
    col_b_net_operating_expenditures: number | null;

    // Debts (Lines 9-10)
    col_a_debts_to: number | null;
    col_a_debts_by: number | null;

    // Election info
    election_state: string | null;
  }

  interface Props {
    formData: F3FormData;
    filingId: string;
  }

  let { formData, filingId }: Props = $props();

  const dbName = get(databaseName);

  // Check if formData has the required fields for the Sankey diagram
  const hasSankeyData = $derived(formData &&
    formData.col_a_total_receipts != null &&
    (formData.col_a_total_receipts > 0 || formData.col_a_operating_expenditures > 0));

  // F3FormData extends InputRow, so it's compatible with the Sankey component
  const sankeyItems: InputRow[] = $derived(hasSankeyData && formData ? [formData] : []);

  const reportTitle = $derived(getReportLabel(formData.report_code));

  function usd(value: number | null | undefined): string {
    if (value == null) return '$0';
    return '$' + value.toLocaleString();
  }

  const cashChange = $derived(
    (formData.col_a_cash_on_hand_close_of_period ?? 0) - (formData.col_a_cash_beginning_reporting_period ?? 0)
  );

  // Schedule data
  interface StateContribution {
    contributor_state: string;
    total_contributions: number;
  }

  interface TopPayee {
    payee: string;
    total_amount: number;
    purposes: string;
  }

  let stateContributions = $state<StateContribution[]>([]);
  let topPayees = $state<TopPayee[]>([]);
  let loadingSchedules = $state(true);

  const homeState = $derived(formData.election_state || null);

  onMount(async () => {
    if (!filingId) {
      loadingSchedules = false;
      return;
    }

    try {
      // Fetch contributions by state
      const stateQuerySql = `
        SELECT
          contributor_state,
          SUM(contribution_amount) as total_contributions
        FROM libfec_schedule_a
        WHERE filing_id = :filing_id
          AND contributor_state IS NOT NULL
          AND contributor_state != ''
        GROUP BY contributor_state
        ORDER BY total_contributions DESC
      `;
      stateContributions = await query(dbName, stateQuerySql, { filing_id: filingId });

      // Fetch top payees
      const payeeQuerySql = `
        SELECT
          COALESCE(payee_organization_name, payee_last_name || ', ' || payee_first_name) as payee,
          SUM(expenditure_amount) as total_amount,
          GROUP_CONCAT(DISTINCT expenditure_purpose_descrip) as purposes
        FROM libfec_schedule_b
        WHERE filing_id = :filing_id
        GROUP BY payee
        ORDER BY total_amount DESC
        LIMIT 20
      `;
      topPayees = await query(dbName, payeeQuerySql, { filing_id: filingId });
    } catch (e) {
      console.error('Error fetching schedule data:', e);
    } finally {
      loadingSchedules = false;
    }
  });
</script>

<div class="form-content">
  {#if formData}
    <h3 class="report-title">{formData.coverage_from_date.substring(0, 4)} {reportTitle}</h3>
    <span>{formData.coverage_from_date} to {formData.coverage_through_date}</span>

    <!-- Summary Cards -->
    <div class="summary-cards">
      <div class="card">
        <div class="card-label">Cash on Hand - Start</div>
        <div class="card-value">{usd(formData.col_a_cash_beginning_reporting_period)}</div>
      </div>
      <div class="card">
        <div class="card-label">Receipts</div>
        <div class="card-value receipts">{usd(formData.col_a_total_receipts)}</div>
      </div>
      <div class="card">
        <div class="card-label">Disbursements</div>
        <div class="card-value disbursements">{usd(formData.col_a_total_disbursements)}</div>
      </div>
      <div class="card">
        <div class="card-label">Cash on Hand - End</div>
        <div class="card-value">{usd(formData.col_a_cash_on_hand_close_of_period)}</div>
        <div class="card-change" class:positive={cashChange >= 0} class:negative={cashChange < 0}>
          {#if cashChange >= 0}
            <span class="arrow">&#x2191;</span>
          {:else}
            <span class="arrow">&#x2193;</span>
          {/if}
          {usd(Math.abs(cashChange))}
        </div>
      </div>
    </div>

    <!-- Sankey Diagram -->
    {#if hasSankeyData && sankeyItems.length > 0}
      <div class="section-box">
        <h4>Financial Activity</h4>
        <F3SankeyComponent items={sankeyItems} />
      </div>
    {/if}

    <!-- Financial Summary Table -->
    <div class="section-box">
      <h4>Financial Summary</h4>
      <div class="table-container">
        <table class="summary-table">
          <thead>
            <tr>
              <th></th>
              <th class="col-header">Column A<br><span class="col-subheader">This Period</span></th>
              <th class="col-header">Column B<br><span class="col-subheader">Election Cycle-To-Date</span></th>
            </tr>
          </thead>
          <tbody>
            <tr class="section-header">
              <td colspan="3">6. Net Contributions (other than loans)</td>
            </tr>
            <tr>
              <td class="indent">(a) Total Contributions (other than loans)</td>
              <td class="amount">{usd(formData.col_a_total_contributions_no_loans)}</td>
              <td class="amount">{usd(formData.col_b_total_contributions_no_loans)}</td>
            </tr>
            <tr>
              <td class="indent">(b) Total Contribution Refunds</td>
              <td class="amount">{usd(formData.col_a_total_contributions_refunds)}</td>
              <td class="amount">{usd(formData.col_b_total_contributions_refunds)}</td>
            </tr>
            <tr class="subtotal">
              <td class="indent">(c) Net Contributions (6(a) - 6(b))</td>
              <td class="amount">{usd(formData.col_a_net_contributions)}</td>
              <td class="amount">{usd(formData.col_b_net_contributions)}</td>
            </tr>

            <tr class="section-header">
              <td colspan="3">7. Net Operating Expenditures</td>
            </tr>
            <tr>
              <td class="indent">(a) Total Operating Expenditures</td>
              <td class="amount">{usd(formData.col_a_total_operating_expenditures)}</td>
              <td class="amount">{usd(formData.col_b_total_operating_expenditures)}</td>
            </tr>
            <tr>
              <td class="indent">(b) Total Offsets to Operating Expenditures</td>
              <td class="amount">{usd(formData.col_a_total_offset_to_operating_expenditures)}</td>
              <td class="amount">{usd(formData.col_b_total_offset_to_operating_expenditures)}</td>
            </tr>
            <tr class="subtotal">
              <td class="indent">(c) Net Operating Expenditures</td>
              <td class="amount">{usd(formData.col_a_net_operating_expenditures)}</td>
              <td class="amount">{usd(formData.col_b_net_operating_expenditures)}</td>
            </tr>

            <tr class="section-header">
              <td>8. Cash on Hand at Close of Reporting Period</td>
              <td class="amount">{usd(formData.col_a_cash_on_hand_close_of_period)}</td>
              <td class="amount"></td>
            </tr>

            <tr class="section-header">
              <td colspan="3">9. Debts and Obligations Owed TO the Committee</td>
            </tr>
            <tr>
              <td class="indent note">Itemize all on SCHEDULE C or SCHEDULE D</td>
              <td class="amount">{usd(formData.col_a_debts_to)}</td>
              <td class="amount"></td>
            </tr>

            <tr class="section-header">
              <td colspan="3">10. Debts and Obligations Owed BY the Committee</td>
            </tr>
            <tr>
              <td class="indent note">Itemize all on SCHEDULE C or SCHEDULE D</td>
              <td class="amount">{usd(formData.col_a_debts_by)}</td>
              <td class="amount"></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Contributions by State -->
    {#if !loadingSchedules}
      <StateContributors contributions={stateContributions} {homeState} />
    {/if}

    <!-- Top Payees -->
    {#if !loadingSchedules}
      <TopPayees payees={topPayees} />
    {/if}

    {#if loadingSchedules}
      <div class="loading-schedules">Loading schedule data...</div>
    {/if}
  {:else}
    <p>No form data available</p>
  {/if}
</div>

<style>
  .form-content {
    margin-top: 1rem;
  }

  .report-title {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 1rem;
  }

  .summary-cards {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  @media (max-width: 768px) {
    .summary-cards {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  .card {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  }

  .card-label {
    font-size: 0.85rem;
    font-weight: 500;
    color: #666;
  }

  .card-value {
    margin-top: 0.25rem;
    font-size: 1.25rem;
    font-weight: 600;
  }

  .card-value.receipts {
    color: #2563eb;
  }

  .card-value.disbursements {
    color: #dc2626;
  }

  .card-change {
    margin-top: 0.25rem;
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .card-change.positive {
    color: #16a34a;
  }

  .card-change.negative {
    color: #dc2626;
  }

  .arrow {
    font-weight: bold;
  }

  .section-box {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .section-box h4 {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #2563eb;
  }

  .table-container {
    overflow-x: auto;
    
    display: flex;
    justify-content: center;
  }

  .summary-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 1rem;
    max-width: 720px;
  }

  .summary-table th,
  .summary-table td {
    border: 1px solid #ddd;
    padding: 0.5rem;
  }

  .summary-table th {
    text-align: right;
    background: #f5f5f5;
    font-weight: 600;
  }

  .summary-table th:first-child {
    width: 50%;
  }

  .col-header {
    width: 25%;
    text-align: right;
  }

  .col-subheader {
    font-size: 0.9rem;
    font-weight: normal;
  }

  .section-header td {
    background: #f9f9f9;
    font-weight: 600;
  }

  .indent {
    padding-left: 1.5rem !important;
  }

  .note {
    font-style: italic;
    font-size: 0.9rem;
  }

  .subtotal td {
    font-weight: 600;
  }

  .amount {
    text-align: right;
  }

  .loading-schedules {
    text-align: center;
    color: #6b7280;
    padding: 2rem;
  }
</style>

<script lang="ts">
  import { F3SankeyComponent, type InputRow } from '../../components/sankey';
  import SummaryCards from '../../components/SummaryCards.svelte';
  import StateContributors from './StateContributors.svelte';
  import TopPayees from './TopPayees.svelte';
  import RelatedF3Reports from './RelatedF3Reports.svelte';
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
    filerId: string;
    databaseName: string;
  }

  let { formData, filingId, filerId, databaseName }: Props = $props();

  // Check if formData has the required fields for the Sankey diagram
  const hasSankeyData = $derived(
    formData &&
      formData.col_a_total_receipts != null &&
      (formData.col_a_total_receipts > 0 || formData.col_a_operating_expenditures > 0)
  );

  // F3FormData extends InputRow, so it's compatible with the Sankey component
  const sankeyItems: InputRow[] = $derived(hasSankeyData && formData ? [formData] : []);

  const reportTitle = $derived(getReportLabel(formData.report_code));

  function usd(value: number | null | undefined): string {
    if (value == null) return '$0';
    return '$' + value.toLocaleString();
  }

  const homeState = $derived(formData.election_state || null);
</script>

<div class="form-content">
  {#if formData}
    <h3 class="report-title">{formData.coverage_from_date.substring(0, 4)} {reportTitle}</h3>
    <span>{formData.coverage_from_date} to {formData.coverage_through_date}</span>

    <SummaryCards
      cashStart={formData.col_a_cash_beginning_reporting_period}
      receipts={formData.col_a_total_receipts}
      disbursements={formData.col_a_total_disbursements}
      cashEnd={formData.col_a_cash_on_hand_close_of_period}
    />

    <!-- Sankey Diagram -->
    {#if hasSankeyData && sankeyItems.length > 0}
      <div class="section-box">
        <h4>Financial Activity</h4>
        <F3SankeyComponent items={sankeyItems} {databaseName} {filingId} />
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
              <th class="col-header"
                >Column A<br /><span class="col-subheader">This Period</span></th
              >
              <th class="col-header"
                >Column B<br /><span class="col-subheader">Election Cycle-To-Date</span></th
              >
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

    <!-- Schedule Data -->
    <div class="schedule-row">
      <div class="schedule-col-1">
        <StateContributors {filingId} {homeState} />
      </div>
      <div class="schedule-col-2">
        <TopPayees {filingId} />
      </div>
    </div>

    <!-- Related Reports -->
    <RelatedF3Reports
      {filingId}
      {filerId}
      reportCode={formData.report_code}
      coverageThroughDate={formData.coverage_through_date}
    />
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

  .schedule-row {
    display: flex;
    gap: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .schedule-col-1 {
    flex: 2;
    min-width: 0;
  }

  .schedule-col-2 {
    flex: 3;
    min-width: 0;
  }

  @media (max-width: 1024px) {
    .schedule-row {
      flex-direction: column;
    }
  }
</style>

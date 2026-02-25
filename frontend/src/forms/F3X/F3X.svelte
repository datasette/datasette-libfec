<script lang="ts">
  import { F3XSankeyComponent, type F3XInputRow } from '../../components/sankey';
  import SummaryCards from '../../components/SummaryCards.svelte';
  import FilingNav from '../../components/FilingNav.svelte';
  import { getReportLabel } from '../../utils/reportCodes';
  import F3XSummaryTable from './F3XSummaryTable.svelte';
  import IndependentExpenditures from './IndependentExpenditures.svelte';
  import StateContributors from './StateContributors.svelte';
  import TopPayees from './TopPayees.svelte';

  interface Props {
    formData: any;
    filingId: string;
    filerId: string;
    databaseName: string;
  }

  let { formData, filingId, filerId, databaseName }: Props = $props();

  const hasSankeyData = $derived(
    formData &&
      formData.col_a_total_receipts != null &&
      (formData.col_a_total_receipts > 0 || formData.col_a_total_disbursements > 0)
  );

  const sankeyItems: F3XInputRow[] = $derived(hasSankeyData && formData ? [formData] : []);

  const reportTitle = $derived(getReportLabel(formData?.report_code));
</script>

<div class="form-content">
  {#if formData}
    <h3 class="report-title">{formData.coverage_from_date?.substring(0, 4)} {reportTitle}</h3>
    <span>{formData.coverage_from_date} to {formData.coverage_through_date}</span>

    <SummaryCards
      cashStart={formData.col_a_cash_on_hand_beginning_period}
      receipts={formData.col_a_total_receipts}
      disbursements={formData.col_a_total_disbursements}
      cashEnd={formData.col_a_cash_on_hand_close_of_period}
    />

    <!-- Sankey Diagram -->
    {#if hasSankeyData && sankeyItems.length > 0}
      <div class="section-box">
        <h4>Financial Activity</h4>
        <F3XSankeyComponent items={sankeyItems} {databaseName} {filingId} />
      </div>
    {/if}

    <!-- Schedule Data -->
    <div class="schedule-row">
      <div class="schedule-col-1">
        <StateContributors {filingId} />
      </div>
      <div class="schedule-col-2">
        <TopPayees {filingId} />
      </div>
    </div>

    <!-- Independent Expenditures -->
    <IndependentExpenditures {filingId} />

    <!-- Financial Summary Table -->
    <div class="section-box">
      <h4>Financial Summary</h4>
      <F3XSummaryTable {formData} />
    </div>

    <!-- Filing Navigation -->
    <FilingNav {filerId} coverageFromDate={formData.coverage_from_date} formType="F3X" />
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

  .section-box :global(h4) {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #2563eb;
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

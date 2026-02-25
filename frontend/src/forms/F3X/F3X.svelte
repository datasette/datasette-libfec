<script lang="ts">
  import { F3XSankeyComponent, type F3XInputRow } from '../../components/sankey';
  import SummaryCards from '../../components/SummaryCards.svelte';
  import { getReportLabel } from '../../utils/reportCodes';
  import F3XSummaryTable from './F3XSummaryTable.svelte';

  interface Props {
    formData: any;
    filingId: string;
    databaseName: string;
  }

  let { formData, filingId, databaseName }: Props = $props();

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

    <!-- Financial Summary Table -->
    <div class="section-box">
      <h4>Financial Summary</h4>
      <F3XSummaryTable {formData} />
    </div>
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
</style>

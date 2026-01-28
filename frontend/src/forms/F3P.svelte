<script lang="ts">
  interface Props {
    formData: any;
    filingId: string;
  }

  let { formData, filingId }: Props = $props();
</script>

<div class="form-content">
  <h3>F3P - Report of Receipts and Disbursements (Presidential)</h3>

  {#if formData}
    <div class="section-box">
      <h4>Committee Information</h4>
      <dl>
        <dt>Committee Name:</dt>
        <dd>{formData.committee_name || 'N/A'}</dd>

        <dt>Committee ID:</dt>
        <dd>{formData.filer_committee_id_number || 'N/A'}</dd>

        {#if formData.coverage_from_date && formData.coverage_through_date}
          <dt>Coverage Period:</dt>
          <dd>{formData.coverage_from_date} to {formData.coverage_through_date}</dd>
        {/if}

        {#if formData.report_code}
          <dt>Report Code:</dt>
          <dd>{formData.report_code}</dd>
        {/if}

        {#if formData.activity_primary}
          <dt>Activity Primary:</dt>
          <dd>{formData.activity_primary}</dd>
        {/if}

        {#if formData.activity_general}
          <dt>Activity General:</dt>
          <dd>{formData.activity_general}</dd>
        {/if}
      </dl>
    </div>

    <div class="section-box">
      <h4>Financial Summary</h4>
      <dl>
        {#if formData.col_a_cash_on_hand_beginning_period !== null && formData.col_a_cash_on_hand_beginning_period !== undefined}
          <dt>Cash on Hand (Beginning):</dt>
          <dd>${formData.col_a_cash_on_hand_beginning_period?.toLocaleString() || '0'}</dd>
        {/if}

        {#if formData.col_a_total_receipts !== null && formData.col_a_total_receipts !== undefined}
          <dt>Total Receipts:</dt>
          <dd>${formData.col_a_total_receipts?.toLocaleString() || '0'}</dd>
        {/if}

        {#if formData.col_a_total_disbursements !== null && formData.col_a_total_disbursements !== undefined}
          <dt>Total Disbursements:</dt>
          <dd>${formData.col_a_total_disbursements?.toLocaleString() || '0'}</dd>
        {/if}

        {#if formData.col_a_cash_on_hand_close_of_period !== null && formData.col_a_cash_on_hand_close_of_period !== undefined}
          <dt>Cash on Hand (Closing):</dt>
          <dd>${formData.col_a_cash_on_hand_close_of_period?.toLocaleString() || '0'}</dd>
        {/if}
      </dl>
    </div>
  {:else}
    <p>No form data available</p>
  {/if}
</div>

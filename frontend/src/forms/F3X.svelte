<script lang="ts">
  interface Props {
    formData: any;
    filingId: string;
  }

  let { formData, filingId }: Props = $props();
</script>

<div class="form-content">
  <h3>F3X - Report of Receipts and Disbursements (PACs/Party Committees)</h3>

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

        {#if formData.col_a_total_contributions !== null && formData.col_a_total_contributions !== undefined}
          <dt>Total Contributions:</dt>
          <dd>${formData.col_a_total_contributions?.toLocaleString() || '0'}</dd>
        {/if}

        {#if formData.col_a_individual_contribution_total !== null && formData.col_a_individual_contribution_total !== undefined}
          <dt>Individual Contributions:</dt>
          <dd>${formData.col_a_individual_contribution_total?.toLocaleString() || '0'}</dd>
        {/if}

        {#if formData.col_a_political_party_committees !== null && formData.col_a_political_party_committees !== undefined}
          <dt>Political Party Contributions:</dt>
          <dd>${formData.col_a_political_party_committees?.toLocaleString() || '0'}</dd>
        {/if}

        {#if formData.col_a_other_political_committees_pacs !== null && formData.col_a_other_political_committees_pacs !== undefined}
          <dt>Other PAC Contributions:</dt>
          <dd>${formData.col_a_other_political_committees_pacs?.toLocaleString() || '0'}</dd>
        {/if}
      </dl>
    </div>
  {:else}
    <p>No form data available</p>
  {/if}
</div>

<script lang="ts">
  import { F3SankeyComponent, type InputRow } from '../components/sankey';

  interface Props {
    formData: any;
    filingId: string;
  }

  let { formData, filingId: _filingId }: Props = $props();

  // Check if formData has the required fields for the Sankey diagram
  const hasSankeyData = $derived(formData &&
    formData.col_a_total_receipts != null &&
    (formData.col_a_total_receipts > 0 || formData.col_a_operating_expenditures > 0));

  // Cast formData to InputRow for Sankey (all fields should match)
  const sankeyItems: InputRow[] = $derived(hasSankeyData ? [formData as InputRow] : []);
</script>

<div class="form-content">
  <h3>F3 - Report of Receipts and Disbursements</h3>

  {#if formData}
    <div class="section-box">
      <h4>Committee Information</h4>
      <dl>
        <dt>Committee Name:</dt>
        <dd>{formData.committee_name || 'N/A'}</dd>

        <dt>Committee ID:</dt>
        <dd>
          {#if formData.filer_committee_id_number}
            <a href="/-/libfec/committee/{formData.filer_committee_id_number}">
              {formData.filer_committee_id_number}
            </a>
          {:else}
            N/A
          {/if}
        </dd>

        {#if formData.coverage_from_date && formData.coverage_through_date}
          <dt>Coverage Period:</dt>
          <dd>{formData.coverage_from_date} to {formData.coverage_through_date}</dd>
        {/if}

        {#if formData.report_code}
          <dt>Report Code:</dt>
          <dd>{formData.report_code}</dd>
        {/if}

        {#if formData.election_state}
          <dt>Election State:</dt>
          <dd>{formData.election_state}</dd>
        {/if}
      </dl>
    </div>

    <div class="section-box">
      <h4>Financial Summary</h4>
      <dl>
        {#if formData.col_a_total_receipts !== null && formData.col_a_total_receipts !== undefined}
          <dt>Total Receipts:</dt>
          <dd>${formData.col_a_total_receipts?.toLocaleString() || '0'}</dd>
        {/if}

        {#if formData.col_a_total_contributions !== null && formData.col_a_total_contributions !== undefined}
          <dt>Total Contributions:</dt>
          <dd>${formData.col_a_total_contributions?.toLocaleString() || '0'}</dd>
        {/if}

        {#if formData.col_a_total_individual_contributions !== null && formData.col_a_total_individual_contributions !== undefined}
          <dt>Individual Contributions:</dt>
          <dd>${formData.col_a_total_individual_contributions?.toLocaleString() || '0'}</dd>
        {/if}

        {#if formData.col_a_operating_expenditures !== null && formData.col_a_operating_expenditures !== undefined}
          <dt>Operating Expenditures:</dt>
          <dd>${formData.col_a_operating_expenditures?.toLocaleString() || '0'}</dd>
        {/if}

        {#if formData.col_a_cash_on_hand_close_of_period !== null && formData.col_a_cash_on_hand_close_of_period !== undefined}
          <dt>Cash on Hand:</dt>
          <dd>${formData.col_a_cash_on_hand_close_of_period?.toLocaleString() || '0'}</dd>
        {/if}

        {#if formData.col_a_debts_to !== null && formData.col_a_debts_to !== undefined}
          <dt>Debts Owed To:</dt>
          <dd>${formData.col_a_debts_to?.toLocaleString() || '0'}</dd>
        {/if}

        {#if formData.col_a_debts_by !== null && formData.col_a_debts_by !== undefined}
          <dt>Debts Owed By:</dt>
          <dd>${formData.col_a_debts_by?.toLocaleString() || '0'}</dd>
        {/if}
      </dl>
    </div>

    {#if hasSankeyData && sankeyItems.length > 0}
      <div class="section-box">
        <h4>Money Flow</h4>
        <F3SankeyComponent items={sankeyItems} />
      </div>
    {/if}
  {:else}
    <p>No form data available</p>
  {/if}
</div>

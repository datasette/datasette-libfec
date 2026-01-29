<script lang="ts">
  interface Props {
    formData: any;
    filingId: string;
  }

  let { formData, filingId: _filingId }: Props = $props();
</script>

<div class="form-content">
  <h3>F3S - Report of Receipts and Disbursements (Senate)</h3>

  {#if formData}
    <div class="section-box">
      <h4>Committee Information</h4>
      <dl>
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

        {#if formData.date_general_election}
          <dt>General Election Date:</dt>
          <dd>{formData.date_general_election}</dd>
        {/if}
      </dl>
    </div>

    <div class="section-box">
      <h4>Financial Summary</h4>
      <dl>
        {#if formData.e_total_contributions !== null && formData.e_total_contributions !== undefined}
          <dt>Total Contributions:</dt>
          <dd>${formData.e_total_contributions?.toLocaleString() || '0'}</dd>
        {/if}

        {#if formData.a_iii_individuals_total !== null && formData.a_iii_individuals_total !== undefined}
          <dt>Individual Contributions:</dt>
          <dd>${formData.a_iii_individuals_total?.toLocaleString() || '0'}</dd>
        {/if}

        {#if formData.b_political_party_committees !== null && formData.b_political_party_committees !== undefined}
          <dt>Political Party Contributions:</dt>
          <dd>${formData.b_political_party_committees?.toLocaleString() || '0'}</dd>
        {/if}

        {#if formData.c_all_other_political_committees_pacs !== null && formData.c_all_other_political_committees_pacs !== undefined}
          <dt>Other PAC Contributions:</dt>
          <dd>${formData.c_all_other_political_committees_pacs?.toLocaleString() || '0'}</dd>
        {/if}

        {#if formData.c_net_contributions !== null && formData.c_net_contributions !== undefined}
          <dt>Net Contributions:</dt>
          <dd>${formData.c_net_contributions?.toLocaleString() || '0'}</dd>
        {/if}

        {#if formData.c_net_operating_expenditures !== null && formData.c_net_operating_expenditures !== undefined}
          <dt>Net Operating Expenditures:</dt>
          <dd>${formData.c_net_operating_expenditures?.toLocaleString() || '0'}</dd>
        {/if}
      </dl>
    </div>
  {:else}
    <p>No form data available</p>
  {/if}
</div>

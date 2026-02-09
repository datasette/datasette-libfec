<script lang="ts">
  interface Props {
    formData: any;
    filingId: string;
  }

  let { formData, filingId: _filingId }: Props = $props();
</script>

<div class="form-content">
  <h3>F6 - Contributions and Loans from Candidate</h3>

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

        {#if formData.original_amendment_date}
          <dt>Original/Amendment Date:</dt>
          <dd>{formData.original_amendment_date}</dd>
        {/if}
      </dl>
    </div>

    {#if formData.candidate_last_name}
      <div class="section-box">
        <h4>Candidate Information</h4>
        <dl>
          <dt>Candidate Name:</dt>
          <dd>
            {formData.candidate_prefix || ''}
            {formData.candidate_first_name || ''}
            {formData.candidate_middle_name || ''}
            {formData.candidate_last_name}
            {formData.candidate_suffix || ''}
          </dd>

          {#if formData.candidate_id_number}
            <dt>Candidate ID:</dt>
            <dd>
              <a href="/-/libfec/candidate/{formData.candidate_id_number}">
                {formData.candidate_id_number}
              </a>
            </dd>
          {/if}

          {#if formData.candidate_office}
            <dt>Office:</dt>
            <dd>{formData.candidate_office}</dd>
          {/if}

          {#if formData.candidate_state}
            <dt>State:</dt>
            <dd>{formData.candidate_state}</dd>
          {/if}

          {#if formData.candidate_district}
            <dt>District:</dt>
            <dd>{formData.candidate_district}</dd>
          {/if}
        </dl>
      </div>
    {/if}

    {#if formData.street_1}
      <div class="section-box">
        <h4>Committee Address</h4>
        <address>
          {formData.street_1}<br />
          {#if formData.street_2}{formData.street_2}<br />{/if}
          {formData.city}, {formData.state}
          {formData.zip_code}
        </address>
      </div>
    {/if}
  {:else}
    <p>No form data available</p>
  {/if}
</div>

<script lang="ts">
  interface Props {
    formData: any;
    filingId: string;
  }

  let { formData, filingId: _filingId }: Props = $props();
</script>

<div class="form-content">
  <h3>F1 - Statement of Organization</h3>

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

        <dt>Committee Type:</dt>
        <dd>{formData.committee_type || 'N/A'}</dd>

        {#if formData.committee_email}
          <dt>Email:</dt>
          <dd>{formData.committee_email}</dd>
        {/if}

        {#if formData.committee_url}
          <dt>Website:</dt>
          <dd>
            <a href={formData.committee_url} target="_blank" rel="noopener noreferrer"
              >{formData.committee_url}</a
            >
          </dd>
        {/if}
      </dl>
    </div>

    {#if formData.street_1}
      <div class="section-box">
        <h4>Address</h4>
        <address>
          {formData.street_1}<br />
          {#if formData.street_2}{formData.street_2}<br />{/if}
          {formData.city}, {formData.state}
          {formData.zip_code}
        </address>
      </div>
    {/if}

    {#if formData.candidate_last_name}
      <div class="section-box">
        <h4>Candidate Information</h4>
        <dl>
          <dt>Candidate:</dt>
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

          {#if formData.candidate_office && formData.candidate_state}
            <dt>Contest:</dt>
            <dd>
              <a
                href="/-/libfec/contest?state={formData.candidate_state}&office={formData.candidate_office}{formData.candidate_district
                  ? '&district=' + formData.candidate_district
                  : ''}"
              >
                {formData.candidate_state}
                {formData.candidate_office === 'H'
                  ? 'House'
                  : formData.candidate_office === 'S'
                    ? 'Senate'
                    : formData.candidate_office === 'P'
                      ? 'President'
                      : formData.candidate_office}
                {#if formData.candidate_district}District {formData.candidate_district}{/if}
              </a>
            </dd>
          {:else}
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
          {/if}

          {#if formData.party_code}
            <dt>Party:</dt>
            <dd>{formData.party_code}</dd>
          {/if}
        </dl>
      </div>
    {/if}
  {:else}
    <p>No form data available</p>
  {/if}
</div>

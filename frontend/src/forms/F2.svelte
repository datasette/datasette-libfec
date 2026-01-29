<script lang="ts">
  interface Props {
    formData: any;
    filingId: string;
  }

  let { formData, filingId: _filingId }: Props = $props();
</script>

<div class="form-content">
  <h3>F2 - Statement of Candidacy</h3>

  {#if formData}
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

        {#if formData.candidate_party_code}
          <dt>Party:</dt>
          <dd>{formData.candidate_party_code}</dd>
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

        {#if formData.election_year}
          <dt>Election Year:</dt>
          <dd>{formData.election_year}</dd>
        {/if}
      </dl>
    </div>

    {#if formData.candidate_street_1}
      <div class="section-box">
        <h4>Candidate Address</h4>
        <address>
          {formData.candidate_street_1}<br />
          {#if formData.candidate_street_2}{formData.candidate_street_2}<br />{/if}
          {formData.candidate_city}, {formData.candidate_state} {formData.candidate_zip_code}
        </address>
      </div>
    {/if}

    {#if formData.committee_name}
      <div class="section-box">
        <h4>Principal Campaign Committee</h4>
        <dl>
          <dt>Committee Name:</dt>
          <dd>{formData.committee_name}</dd>

          {#if formData.committee_id_number}
            <dt>Committee ID:</dt>
            <dd>
              <a href="/-/libfec/committee/{formData.committee_id_number}">
                {formData.committee_id_number}
              </a>
            </dd>
          {/if}
        </dl>

        {#if formData.committee_street_1}
          <address>
            {formData.committee_street_1}<br />
            {#if formData.committee_street_2}{formData.committee_street_2}<br />{/if}
            {formData.committee_city}, {formData.committee_state} {formData.committee_zip_code}
          </address>
        {/if}
      </div>
    {/if}
  {:else}
    <p>No form data available</p>
  {/if}
</div>

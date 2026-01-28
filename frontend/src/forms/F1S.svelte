<script lang="ts">
  interface Props {
    formData: any;
    filingId: string;
  }

  let { formData, filingId }: Props = $props();
</script>

<div class="form-content">
  <h3>F1S - Statement of Organization (Supplemental)</h3>

  {#if formData}
    <div class="section-box">
      <h4>Committee Information</h4>
      <dl>
        <dt>Committee ID:</dt>
        <dd>{formData.filer_committee_id_number || 'N/A'}</dd>
      </dl>
    </div>

    {#if formData.joint_fund_participant_committee_name}
      <div class="section-box">
        <h4>Joint Fundraising Participant</h4>
        <dl>
          <dt>Committee Name:</dt>
          <dd>{formData.joint_fund_participant_committee_name}</dd>

          {#if formData.joint_fund_participant_committee_id_number}
            <dt>Committee ID:</dt>
            <dd>{formData.joint_fund_participant_committee_id_number}</dd>
          {/if}
        </dl>
      </div>
    {/if}

    {#if formData.affiliated_committee_name || formData.affiliated_last_name}
      <div class="section-box">
        <h4>Affiliated Committee/Candidate</h4>
        <dl>
          {#if formData.affiliated_committee_name}
            <dt>Committee Name:</dt>
            <dd>{formData.affiliated_committee_name}</dd>
          {/if}

          {#if formData.affiliated_committee_id_number}
            <dt>Committee ID:</dt>
            <dd>{formData.affiliated_committee_id_number}</dd>
          {/if}

          {#if formData.affiliated_last_name}
            <dt>Candidate Name:</dt>
            <dd>
              {formData.affiliated_prefix || ''}
              {formData.affiliated_first_name || ''}
              {formData.affiliated_middle_name || ''}
              {formData.affiliated_last_name}
              {formData.affiliated_suffix || ''}
            </dd>
          {/if}

          {#if formData.affiliated_candidate_id_number}
            <dt>Candidate ID:</dt>
            <dd>{formData.affiliated_candidate_id_number}</dd>
          {/if}

          {#if formData.affiliated_relationship_code}
            <dt>Relationship:</dt>
            <dd>{formData.affiliated_relationship_code}</dd>
          {/if}
        </dl>

        {#if formData.affiliated_street_1}
          <address>
            {formData.affiliated_street_1}<br />
            {#if formData.affiliated_street_2}{formData.affiliated_street_2}<br />{/if}
            {formData.affiliated_city}, {formData.affiliated_state} {formData.affiliated_zip_code}
          </address>
        {/if}
      </div>
    {/if}

    {#if formData.agent_last_name}
      <div class="section-box">
        <h4>Agent Information</h4>
        <dl>
          <dt>Name:</dt>
          <dd>
            {formData.agent_prefix || ''}
            {formData.agent_first_name || ''}
            {formData.agent_middle_name || ''}
            {formData.agent_last_name}
            {formData.agent_suffix || ''}
          </dd>
        </dl>

        {#if formData.agent_street_1}
          <address>
            {formData.agent_street_1}<br />
            {#if formData.agent_street_2}{formData.agent_street_2}<br />{/if}
            {formData.agent_city}, {formData.agent_state} {formData.agent_zip_code}
          </address>
        {/if}
      </div>
    {/if}
  {:else}
    <p>No form data available</p>
  {/if}
</div>

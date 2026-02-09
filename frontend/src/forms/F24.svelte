<script lang="ts">
  interface Props {
    formData: any;
    filingId: string;
  }

  let { formData, filingId: _filingId }: Props = $props();
</script>

<div class="form-content">
  <h3>F24 - 24/48 Hour Notice of Independent Expenditures</h3>

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

        {#if formData.report_type}
          <dt>Report Type:</dt>
          <dd>{formData.report_type}</dd>
        {/if}

        {#if formData.original_amendment_date}
          <dt>Original/Amendment Date:</dt>
          <dd>{formData.original_amendment_date}</dd>
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

    {#if formData.treasurer_last_name}
      <div class="section-box">
        <h4>Treasurer</h4>
        <dl>
          <dt>Name:</dt>
          <dd>
            {formData.treasurer_prefix || ''}
            {formData.treasurer_first_name || ''}
            {formData.treasurer_middle_name || ''}
            {formData.treasurer_last_name}
            {formData.treasurer_suffix || ''}
          </dd>

          {#if formData.date_signed}
            <dt>Date Signed:</dt>
            <dd>{formData.date_signed}</dd>
          {/if}
        </dl>
      </div>
    {/if}

    <div class="alert-box">
      <p>
        This is a 24/48 hour notice of independent expenditures. See schedules for expenditure
        details.
      </p>
    </div>
  {:else}
    <p>No form data available</p>
  {/if}
</div>

<style>
  .alert-box {
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 4px;
    padding: 1rem;
    margin-top: 1rem;
  }

  .alert-box p {
    margin: 0;
    color: #856404;
  }
</style>

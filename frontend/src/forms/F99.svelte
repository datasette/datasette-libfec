<script lang="ts">
  import { get } from 'svelte/store';
  import { basePath } from '../stores';

  const bp = get(basePath);

  interface Props {
    formData: any;
    filingId: string;
  }

  let { formData, filingId: _filingId }: Props = $props();
</script>

<div class="form-content">
  <h3>F99 - Miscellaneous Text</h3>

  {#if formData}
    <div class="section-box">
      <h4>Committee Information</h4>
      <dl>
        <dt>Committee Name:</dt>
        <dd>{formData.committee_name || 'N/A'}</dd>

        <dt>Committee ID:</dt>
        <dd>
          {#if formData.filer_committee_id_number}
            <a href="{bp}/committee/{formData.filer_committee_id_number}">
              {formData.filer_committee_id_number}
            </a>
          {:else}
            N/A
          {/if}
        </dd>

        {#if formData.date_signed}
          <dt>Date Signed:</dt>
          <dd>{formData.date_signed}</dd>
        {/if}

        {#if formData.text_code}
          <dt>Text Code:</dt>
          <dd>{formData.text_code}</dd>
        {/if}
      </dl>
    </div>

    {#if formData.text}
      <div class="section-box">
        <h4>Message</h4>
        <div class="text-content">
          {formData.text}
        </div>
      </div>
    {/if}

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
  {:else}
    <p>No form data available</p>
  {/if}
</div>

<style>
  .text-content {
    background: #f9f9f9;
    padding: 1rem;
    border-left: 3px solid #007bff;
    white-space: pre-wrap;
    font-family: inherit;
    line-height: 1.6;
  }
</style>

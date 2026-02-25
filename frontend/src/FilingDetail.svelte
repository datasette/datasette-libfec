<script lang="ts">
  import type { FilingDetailPageData } from './page_data/FilingDetailPageData.types.ts';
  import { loadPageData } from './page_data/load.ts';
  import { get } from 'svelte/store';
  import { databaseName as databaseNameStore, basePath as basePathStore } from './stores';
  import F1 from './forms/F1.svelte';
  import F1S from './forms/F1S.svelte';
  import F2 from './forms/F2.svelte';
  import F3 from './forms/F3/F3.svelte';
  import type { F3FormData } from './forms/F3/F3.svelte';
  import F3P from './forms/F3P.svelte';
  import F3S from './forms/F3S.svelte';
  import F3X from './forms/F3X/F3X.svelte';
  import F24 from './forms/F24.svelte';
  import F6 from './forms/F6.svelte';
  import F99 from './forms/F99.svelte';
  import Breadcrumb, { type BreadcrumbItem } from './components/Breadcrumb.svelte';

  const pageData = loadPageData<FilingDetailPageData>();

  // Aliases for easier access
  const filingData = pageData.filing;
  const formData = pageData.form_data;
  const filingId = pageData.filing_id;
  const databaseName = pageData.database_name;

  // Set the stores for child components to use
  databaseNameStore.set(databaseName);
  const basePath = get(basePathStore);

  // Determine report type for conditional rendering
  const reportType = filingData?.cover_record_form || 'Unknown';

  // Build breadcrumb items
  function getBreadcrumbItems(): BreadcrumbItem[] {
    const items: BreadcrumbItem[] = [{ label: 'FEC Data', href: basePath }];

    if (filingData?.filer_id) {
      items.push({
        label: filingData.filer_name || filingData.filer_id,
        href: `${basePath}/committee/${filingData.filer_id}`,
      });
    }

    items.push({ label: `Filing ${filingId}` });
    return items;
  }

  const breadcrumbItems = getBreadcrumbItems();
</script>

<div class="filing-detail">
  <div class="header">
    <Breadcrumb items={breadcrumbItems} />
    <h1>FEC-{filingId} {reportType}</h1>
    {#if filingData?.filer_name}
      <div class="filer-info">
        <span class="filer-name">
          {#if filingData.filer_id}
            <a href="{basePath}/committee/{filingData.filer_id}">
              {filingData.filer_name}
            </a>
          {:else}
            {filingData.filer_name}
          {/if}
        </span>
        {#if filingData.filer_id}
          <span class="filer-id">({filingData.filer_id})</span>
        {/if}
      </div>
    {/if}
    <div class="links">
      <a href="/{databaseName}/libfec_filings/{filingId}" target="_blank" rel="noopener noreferrer">
        Row page
      </a>
      <a
        href="https://docquery.fec.gov/cgi-bin/forms/{filingData?.filer_id ?? ''}/{filingId}"
        target="_blank"
        rel="noopener noreferrer"
      >
        fec.gov →
      </a>
      <a
        href="https://docquery.fec.gov/dcdev/posted/{filingId}.fec"
        target="_blank"
        rel="noopener noreferrer"
      >
        .fec file
      </a>
    </div>
  </div>

  <section class="info-section">
    {#if reportType === 'F1'}
      <F1 {formData} {filingId} />
    {:else if reportType === 'F1S'}
      <F1S {formData} {filingId} />
    {:else if reportType === 'F2'}
      <F2 {formData} {filingId} />
    {:else if reportType === 'F3'}
      <F3
        formData={formData as unknown as F3FormData}
        {filingId}
        filerId={filingData?.filer_id ?? ''}
        {databaseName}
      />
    {:else if reportType === 'F3P'}
      <F3P {formData} {filingId} />
    {:else if reportType === 'F3S'}
      <F3S {formData} {filingId} />
    {:else if reportType === 'F3X'}
      <F3X {formData} {filingId} {databaseName} />
    {:else if reportType === 'F24'}
      <F24 {formData} {filingId} />
    {:else if reportType === 'F6'}
      <F6 {formData} {filingId} />
    {:else if reportType === 'F99'}
      <F99 {formData} {filingId} />
    {:else}
      <div class="form-content">
        <h3>Filing Details</h3>
        <p>Form type {reportType} - detailed view coming soon</p>

        <div class="section-box">
          <h4>Basic Information</h4>
          <dl>
            <dt>Filing ID:</dt>
            <dd>{filingId}</dd>

            <dt>Filer Name:</dt>
            <dd>{filingData?.filer_name || 'N/A'}</dd>

            <dt>Coverage Period:</dt>
            <dd>
              {#if filingData?.coverage_from_date && filingData?.coverage_through_date}
                {filingData.coverage_from_date} to {filingData.coverage_through_date}
              {:else}
                N/A
              {/if}
            </dd>
          </dl>
        </div>

        <details>
          <summary>Raw Filing Data</summary>
          <pre>{JSON.stringify(filingData, null, 2)}</pre>
        </details>
      </div>
    {/if}
  </section>
</div>

<style>
  .filing-detail {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }

  .header {
    margin-bottom: 2rem;
  }

  .header h1 {
    font-size: 2rem;
    margin-bottom: 0.5rem;
  }

  .filer-info {
    margin-bottom: 0.75rem;
    font-size: 1.1rem;
  }

  .filer-name a {
    color: #0066cc;
    text-decoration: none;
  }

  .filer-name a:hover {
    text-decoration: underline;
  }

  .filer-id {
    color: #666;
    font-size: 0.9rem;
    font-family: monospace;
  }

  .links {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .links a {
    color: #0066cc;
    text-decoration: none;
  }

  .links a:hover {
    text-decoration: underline;
  }

  .info-section {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1.5rem;
  }

  .info-section h2 {
    font-size: 1.5rem;
    margin-bottom: 1rem;
  }

  .form-content h3 {
    font-size: 1.25rem;
    margin-bottom: 1rem;
  }

  .section-box {
    background: #f9f9f9;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 1rem;
    margin-bottom: 1.5rem;
  }

  .section-box h4 {
    font-size: 1.1rem;
    margin-bottom: 0.75rem;
    font-weight: 600;
  }

  /* Global styles for child components */
  :global(.form-content .section-box) {
    background: #f9f9f9;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 1rem;
    margin-bottom: 1.5rem;
  }

  :global(.form-content .section-box h4) {
    font-size: 1.1rem;
    margin-bottom: 0.75rem;
    font-weight: 600;
  }

  :global(.form-content address) {
    font-style: normal;
    line-height: 1.6;
  }

  :global(.form-content dl) {
    display: grid;
    grid-template-columns: max-content 1fr;
    gap: 0.5rem 1rem;
  }

  :global(.form-content dt) {
    font-weight: 600;
  }

  :global(.form-content dd) {
    margin: 0;
  }

  dl {
    display: grid;
    grid-template-columns: max-content 1fr;
    gap: 0.5rem 1rem;
  }

  dt {
    font-weight: 600;
  }

  dd {
    margin: 0;
  }

  details {
    margin-top: 1rem;
  }

  pre {
    background: #f5f5f5;
    padding: 1rem;
    border-radius: 4px;
    overflow-x: auto;
  }
</style>

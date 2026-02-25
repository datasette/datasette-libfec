<script lang="ts">
  import type { ImportPageData } from './page_data/ImportPageData.types.ts';
  import { loadPageData } from './page_data/load.ts';
  import { get } from 'svelte/store';
  import { databaseName as databaseNameStore, basePath } from './stores';
  import ImportForm from './index/ImportForm.svelte';
  import ExportHistory from './index/ExportHistory.svelte';

  const pageData = loadPageData<ImportPageData>();
  databaseNameStore.set(pageData.database_name);
  const bp = get(basePath);
</script>

<main>
  <p><a href={bp}>&larr; Back to FEC Import</a></p>
  <h1>Import FEC Data</h1>
  <p>Import Federal Election Commission data into your Datasette database.</p>

  <ImportForm />
  <ExportHistory />
</main>

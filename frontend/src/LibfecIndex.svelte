<script lang="ts">
  import type { IndexPageData } from "./page_data/IndexPageData.types.ts";
  import { loadPageData } from "./page_data/load.ts";
  import ImportForm from './index/ImportForm.svelte';
  import RssWatcher from './index/RssWatcher.svelte';
  import RecentFilings from './components/RecentFilings.svelte';
  import ExportHistory from './index/ExportHistory.svelte';
  import RssSyncHistory from './index/RssSyncHistory.svelte';

  const pageData = loadPageData<IndexPageData>();
</script>

<main>
  <h1>FEC Data Import</h1>
  <p>Import Federal Election Commission data into your Datasette database.</p>

  <div style="display: flex; grid-gap: 1rem;">
    <ImportForm />
    <RssWatcher />
  </div>
  <ExportHistory />
  <RssSyncHistory />
  <RecentFilings databaseName={pageData.database_name} />
</main>

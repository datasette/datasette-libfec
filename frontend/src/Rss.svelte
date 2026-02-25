<script lang="ts">
  import type { RssPageData } from './page_data/RssPageData.types.ts';
  import { loadPageData } from './page_data/load.ts';
  import { get } from 'svelte/store';
  import { databaseName as databaseNameStore, basePath } from './stores';
  import RssWatcher from './index/RssWatcher.svelte';
  import RssSyncHistory from './index/RssSyncHistory.svelte';

  const pageData = loadPageData<RssPageData>();
  databaseNameStore.set(pageData.database_name);
  const bp = get(basePath);
</script>

<main>
  <p><a href={bp}>&larr; Back to FEC Import</a></p>
  <h1>RSS Watcher</h1>
  <p>Automatically watch and import new FEC filings from the RSS feed.</p>

  <RssWatcher />
  <RssSyncHistory />
</main>

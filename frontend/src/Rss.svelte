<script lang="ts">
  import RssWatcher from './index/RssWatcher.svelte';
  import RssSyncHistory from './index/RssSyncHistory.svelte';
</script>

<main>
  <p><a href="/-/libfec">&larr; Back to FEC Import</a></p>
  <h1>RSS Watcher</h1>
  <p>Automatically watch and import new FEC filings from the RSS feed.</p>

  <RssWatcher />
  <RssSyncHistory />
</main>

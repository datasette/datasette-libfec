<script lang="ts">
  import ImportForm from './index/ImportForm.svelte';
  import ExportHistory from './index/ExportHistory.svelte';
</script>

<main>
  <p><a href="/-/libfec">&larr; Back to FEC Import</a></p>
  <h1>Import FEC Data</h1>
  <p>Import Federal Election Commission data into your Datasette database.</p>

  <ImportForm />
  <ExportHistory />
</main>

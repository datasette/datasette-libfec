<script lang="ts">
  import type { IndexPageData } from './page_data/IndexPageData.types.ts';
  import { loadPageData } from './page_data/load.ts';
  import RecentFilings from './components/RecentFilings.svelte';

  const pageData = loadPageData<IndexPageData>();
</script>

<main>
  <h1>FEC Data</h1>
  <p>Federal Election Commission data explorer.</p>

  <div class="nav-cards">
    <a href="/-/libfec/filing-day" class="nav-card">
      <h2>Filing Day</h2>
      <p>Compare F3 reports from candidates for a specific reporting period.</p>
    </a>
  </div>

  {#if pageData.can_write}
    <div class="nav-cards">
      <a href="/-/libfec/import" class="nav-card">
        <h2>Import Data</h2>
        <p>Import FEC filings for candidates, committees, or contests.</p>
      </a>
      <a href="/-/libfec/rss" class="nav-card">
        <h2>RSS Watcher</h2>
        <p>Automatically watch and import new filings from the FEC RSS feed.</p>
      </a>
    </div>
  {/if}

  <RecentFilings databaseName={pageData.database_name} />
</main>

<style>
  .nav-cards {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
  }

  .nav-card {
    flex: 1;
    padding: 1.5rem;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    background: #f8f9fa;
    text-decoration: none;
    color: inherit;
    transition:
      border-color 0.2s,
      box-shadow 0.2s;
  }

  .nav-card:hover {
    border-color: #0066cc;
    box-shadow: 0 2px 8px rgba(0, 102, 204, 0.15);
  }

  .nav-card h2 {
    margin: 0 0 0.5rem 0;
    color: #0066cc;
    font-size: 1.25rem;
  }

  .nav-card p {
    margin: 0;
    color: #495057;
    font-size: 0.9rem;
  }
</style>

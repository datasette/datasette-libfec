<script lang="ts">
  export interface BreadcrumbItem {
    label: string;
    href?: string;
  }

  let { items }: { items: BreadcrumbItem[] } = $props();
</script>

<nav class="breadcrumb" aria-label="Breadcrumb">
  {#each items as item, index}
    {#if index > 0}
      <span class="separator" aria-hidden="true">&rarr;</span>
    {/if}
    {#if item.href}
      <a href={item.href}>{item.label}</a>
    {:else}
      <span class="current" aria-current="page">{item.label}</span>
    {/if}
  {/each}
</nav>

<style>
  .breadcrumb {
    font-size: 0.9rem;
    color: #666;
    margin-bottom: 0.5rem;
  }

  .breadcrumb a {
    color: #0066cc;
    text-decoration: none;
  }

  .breadcrumb a:hover {
    text-decoration: underline;
  }

  .separator {
    margin: 0 0.25rem;
  }

  .current {
    color: #666;
  }
</style>

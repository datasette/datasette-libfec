<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Props {
    children: Snippet;
  }

  let { children }: Props = $props();

  let open = $state(false);

  function toggle(e: MouseEvent) {
    e.stopPropagation();
    open = !open;
  }

  function handleWindowClick() {
    if (open) open = false;
  }
</script>

<svelte:window onclick={handleWindowClick} />

<div class="overflow-menu">
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <button class="overflow-btn" onclick={toggle} aria-label="More actions" aria-expanded={open}>
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      fill="currentColor"
      viewBox="0 0 16 16"
    >
      <path
        d="M9.5 13a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0m0-5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0m0-5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0"
      />
    </svg>
  </button>
  {#if open}
    <div class="overflow-dropdown">
      {@render children()}
    </div>
  {/if}
</div>

<style>
  .overflow-menu {
    position: relative;
  }

  .overflow-btn {
    background: none;
    border: 1px solid transparent;
    border-radius: 4px;
    cursor: pointer;
    padding: 0.25rem 0.4rem;
    color: #666;
    display: flex;
    align-items: center;
  }

  .overflow-btn:hover {
    background: #f0f0f0;
    border-color: #ccc;
  }

  .overflow-dropdown {
    position: absolute;
    right: 0;
    top: 100%;
    margin-top: 4px;
    background: white;
    border: 1px solid #ddd;
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
    min-width: 160px;
    z-index: 100;
    padding: 0.25rem 0;
  }

  .overflow-dropdown :global(a) {
    display: block;
    padding: 0.5rem 0.75rem;
    color: #333;
    text-decoration: none;
    font-size: 0.9rem;
    white-space: nowrap;
  }

  .overflow-dropdown :global(a:hover) {
    background: #f5f5f5;
  }
</style>

<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Props {
    title: string;
    onClose: () => void;
    header?: Snippet;
    children: Snippet;
  }

  let { title, onClose, header, children }: Props = $props();

  function handleBackdropClick() {
    onClose();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      onClose();
    }
  }

  function handlePanelClick(e: MouseEvent) {
    e.stopPropagation();
  }
</script>

<svelte:window onkeydown={handleKeydown} />

<div
  class="popover-backdrop"
  onclick={handleBackdropClick}
  onkeydown={handleKeydown}
  role="button"
  tabindex="-1"
  aria-label="Close"
>
  <div
    class="popover-panel"
    onclick={handlePanelClick}
    onkeydown={handleKeydown}
    role="dialog"
    aria-modal="true"
    tabindex="-1"
  >
    <div class="popover-header">
      {#if header}
        {@render header()}
      {:else}
        <h3>{title}</h3>
      {/if}
      <button type="button" class="popover-close" onclick={onClose} aria-label="Close">
        &times;
      </button>
    </div>
    <div class="popover-body">
      {@render children()}
    </div>
  </div>
</div>

<style>
  .popover-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.35);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .popover-panel {
    background: white;
    border-radius: 8px;
    width: 90%;
    max-width: 750px;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  }

  .popover-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1em 1.25em;
    border-bottom: 1px solid #dee2e6;
    flex-shrink: 0;
  }

  .popover-header h3 {
    margin: 0;
    font-size: 1.1em;
  }

  .popover-close {
    background: none;
    border: none;
    font-size: 1.5em;
    line-height: 1;
    cursor: pointer;
    color: #6c757d;
    padding: 0 0.25em;
  }

  .popover-close:hover {
    color: #333;
  }

  .popover-body {
    padding: 1.25em;
    overflow-y: auto;
    flex: 1;
  }
</style>

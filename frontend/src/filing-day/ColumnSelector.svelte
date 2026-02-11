<script lang="ts">
  import { getColumnsByCategory } from './columns.ts';

  interface Props {
    selectedColumns: string[];
    onClose: () => void;
    onApply: (columns: string[]) => void;
  }

  let { selectedColumns, onClose, onApply }: Props = $props();

  // Local state for checkboxes - initialize from prop
  function initSelection(): Set<string> {
    return new Set(selectedColumns);
  }
  let localSelection = $state<Set<string>>(initSelection());

  const receiptsColumns = getColumnsByCategory('receipts');
  const disbursementsColumns = getColumnsByCategory('disbursements');
  const balanceColumns = getColumnsByCategory('balance');

  function toggleColumn(id: string) {
    if (localSelection.has(id)) {
      localSelection.delete(id);
    } else {
      localSelection.add(id);
    }
    // Trigger reactivity by reassigning
    localSelection = new Set(localSelection);
  }

  function handleApply() {
    onApply(Array.from(localSelection));
    onClose();
  }

  function handleBackdropClick() {
    onClose();
  }

  function handleBackdropKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      onClose();
    }
  }

  function handleModalClick(e: MouseEvent) {
    e.stopPropagation();
  }

  function handleModalKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      e.stopPropagation();
      onClose();
    }
  }
</script>

<div
  class="modal-backdrop"
  onclick={handleBackdropClick}
  onkeydown={handleBackdropKeydown}
  role="button"
  tabindex="-1"
  aria-label="Close modal"
>
  <div
    class="modal"
    onclick={handleModalClick}
    onkeydown={handleModalKeydown}
    role="dialog"
    aria-modal="true"
    tabindex="-1"
  >
    <div class="modal-header">
      <h2>Select Columns</h2>
      <button class="close-btn" onclick={onClose} aria-label="Close">&times;</button>
    </div>

    <div class="modal-body">
      <div class="columns-grid">
        <div class="column-group">
          <h3>Receipts</h3>
          {#each receiptsColumns as column}
            <label class="column-option">
              <input
                type="checkbox"
                checked={localSelection.has(column.id)}
                onchange={() => toggleColumn(column.id)}
              />
              <span class="column-info">
                <span class="column-label">{column.label}</span>
              </span>
            </label>
          {/each}
        </div>

        <div class="column-group">
          <h3>Disbursements</h3>
          {#each disbursementsColumns as column}
            <label class="column-option">
              <input
                type="checkbox"
                checked={localSelection.has(column.id)}
                onchange={() => toggleColumn(column.id)}
              />
              <span class="column-info">
                <span class="column-label">{column.label}</span>
              </span>
            </label>
          {/each}
        </div>

        <div class="column-group">
          <h3>Cash on Hand</h3>
          {#each balanceColumns as column}
            <label class="column-option">
              <input
                type="checkbox"
                checked={localSelection.has(column.id)}
                onchange={() => toggleColumn(column.id)}
              />
              <span class="column-info">
                <span class="column-label">{column.label}</span>
              </span>
            </label>
          {/each}
        </div>
      </div>
    </div>

    <div class="modal-footer">
      <button type="button" class="btn-secondary" onclick={onClose}>Cancel</button>
      <button
        type="button"
        class="btn-primary"
        onclick={handleApply}
        disabled={localSelection.size === 0}
      >
        Apply ({localSelection.size} columns)
      </button>
    </div>
  </div>
</div>

<style>
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal {
    background: white;
    border-radius: 8px;
    width: 90%;
    max-width: 750px;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid #e0e0e0;
  }

  .modal-header h2 {
    margin: 0;
    font-size: 1.25rem;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0;
    line-height: 1;
    color: #666;
  }

  .close-btn:hover {
    color: #333;
  }

  .modal-body {
    padding: 1rem 1.5rem;
    overflow-y: auto;
    flex: 1;
  }

  .columns-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 1.5rem;
  }

  .column-group h3 {
    margin: 0 0 0.75rem 0;
    font-size: 0.9rem;
    font-weight: 600;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .column-option {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0;
    cursor: pointer;
  }

  .column-option:hover {
    background: #f5f5f5;
    margin: 0 -0.5rem;
    padding-left: 0.5rem;
    padding-right: 0.5rem;
    border-radius: 4px;
  }

  .column-option input[type='checkbox'] {
    width: 16px;
    height: 16px;
    cursor: pointer;
  }

  .column-label {
    font-size: 0.9rem;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    padding: 1rem 1.5rem;
    border-top: 1px solid #e0e0e0;
  }

  .btn-secondary {
    padding: 0.5rem 1rem;
    background: #f0f0f0;
    border: 1px solid #ccc;
    border-radius: 4px;
    cursor: pointer;
  }

  .btn-secondary:hover {
    background: #e0e0e0;
  }

  .btn-primary {
    padding: 0.5rem 1rem;
    background: #0066cc;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .btn-primary:hover:not(:disabled) {
    background: #0055aa;
  }

  .btn-primary:disabled {
    background: #ccc;
    cursor: not-allowed;
  }
</style>

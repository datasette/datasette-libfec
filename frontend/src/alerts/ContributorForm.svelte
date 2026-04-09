<script lang="ts">
  interface ContributorCriteria {
    first_name: string;
    last_name: string;
    city: string;
    state: string;
  }

  interface Props {
    contributors: ContributorCriteria[];
    onchange: (contributors: ContributorCriteria[]) => void;
  }

  let { contributors, onchange }: Props = $props();

  let firstName = $state('');
  let lastName = $state('');
  let city = $state('');
  let stateCode = $state('');

  function addContributor() {
    if (!lastName && !firstName) return;
    const newList = [
      ...contributors,
      { first_name: firstName, last_name: lastName, city, state: stateCode },
    ];
    onchange(newList);
    firstName = '';
    lastName = '';
    city = '';
    stateCode = '';
  }

  function removeContributor(index: number) {
    onchange(contributors.filter((_, i) => i !== index));
  }
</script>

<div class="contributor-form">
  {#if contributors.length > 0}
    <div class="contributor-list">
      {#each contributors as c, i}
        <div class="contributor-item">
          <span>
            {c.first_name || '*'}
            {c.last_name || '*'}
            {#if c.city || c.state}
              — {c.city}{c.city && c.state ? ', ' : ''}{c.state}
            {/if}
          </span>
          <button type="button" class="remove-btn" onclick={() => removeContributor(i)}>
            Remove
          </button>
        </div>
      {/each}
    </div>
  {/if}

  <div class="add-form">
    <div class="field-row">
      <input type="text" placeholder="First name" bind:value={firstName} />
      <input type="text" placeholder="Last name" bind:value={lastName} />
    </div>
    <div class="field-row">
      <input type="text" placeholder="City" bind:value={city} />
      <input
        type="text"
        placeholder="State (2-letter)"
        bind:value={stateCode}
        maxlength="2"
        style="max-width: 120px;"
      />
      <button
        type="button"
        class="add-btn"
        onclick={addContributor}
        disabled={!lastName && !firstName}
      >
        Add
      </button>
    </div>
  </div>
</div>

<style>
  .contributor-list {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    margin-bottom: 0.5rem;
  }

  .contributor-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.4rem 0.6rem;
    background: #f8f8f8;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    font-size: 0.9rem;
  }

  .remove-btn {
    padding: 0.15rem 0.4rem;
    border: 1px solid #c00;
    border-radius: 4px;
    background: #fff;
    color: #c00;
    cursor: pointer;
    font-size: 0.75rem;
  }

  .remove-btn:hover {
    background: #fef2f2;
  }

  .add-form {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  .field-row {
    display: flex;
    gap: 0.5rem;
  }

  .field-row input {
    flex: 1;
    padding: 0.4rem 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.85rem;
  }

  .add-btn {
    padding: 0.4rem 0.75rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    background: #f8f8f8;
    cursor: pointer;
    font-size: 0.85rem;
    white-space: nowrap;
  }

  .add-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .add-btn:hover:not(:disabled) {
    background: #e8e8e8;
  }
</style>

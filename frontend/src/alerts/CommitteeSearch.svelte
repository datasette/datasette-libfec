<script lang="ts">
  import { query } from '../api';

  interface CommitteeResult {
    committee_id: string;
    name: string;
  }

  interface Props {
    databaseName: string;
    selectedCommittees: CommitteeResult[];
    onchange: (committees: CommitteeResult[]) => void;
  }

  let { databaseName, selectedCommittees, onchange }: Props = $props();

  let searchText = $state('');
  let results = $state<CommitteeResult[]>([]);
  let showDropdown = $state(false);
  let searching = $state(false);
  let debounceTimer: ReturnType<typeof setTimeout> | undefined;

  function handleInput(e: Event) {
    const value = (e.target as HTMLInputElement).value;
    searchText = value;

    if (debounceTimer) clearTimeout(debounceTimer);

    if (value.length < 2) {
      results = [];
      showDropdown = false;
      return;
    }

    debounceTimer = setTimeout(() => doSearch(value), 250);
  }

  async function doSearch(term: string) {
    searching = true;
    try {
      const sql = `
WITH final AS (
  SELECT committee_id, name
  FROM libfec_committees
  WHERE name LIKE :term OR committee_id LIKE :term
  GROUP BY committee_id
  ORDER BY name
  LIMIT 20
)
SELECT * FROM final`;
      const rows = await query(databaseName, sql, { term: `%${term}%` });
      // Filter out already selected
      const selectedIds = new Set(selectedCommittees.map((c) => c.committee_id));
      results = (rows as CommitteeResult[]).filter((r) => !selectedIds.has(r.committee_id));
      showDropdown = results.length > 0;
    } catch {
      results = [];
    }
    searching = false;
  }

  function addCommittee(c: CommitteeResult) {
    onchange([...selectedCommittees, c]);
    searchText = '';
    showDropdown = false;
    results = [];
  }

  function removeCommittee(committeeId: string) {
    onchange(selectedCommittees.filter((c) => c.committee_id !== committeeId));
  }

  function handleBlur() {
    setTimeout(() => {
      showDropdown = false;
    }, 200);
  }
</script>

<div class="committee-search">
  {#if selectedCommittees.length > 0}
    <div class="selected-list">
      {#each selectedCommittees as c}
        <div class="selected-item">
          <span class="selected-name">{c.name}</span>
          <span class="selected-id">({c.committee_id})</span>
          <button type="button" class="remove-btn" onclick={() => removeCommittee(c.committee_id)}>
            &times;
          </button>
        </div>
      {/each}
    </div>
  {/if}

  <input
    type="text"
    placeholder="Search by committee name or ID..."
    value={searchText}
    oninput={handleInput}
    onfocus={() => {
      if (results.length > 0) showDropdown = true;
    }}
    onblur={handleBlur}
  />
  {#if searching}
    <span class="searching">Searching...</span>
  {/if}
  {#if showDropdown}
    <ul class="dropdown">
      {#each results as c}
        <li>
          <button type="button" onclick={() => addCommittee(c)}>
            <span class="result-name">{c.name}</span>
            <span class="result-id">{c.committee_id}</span>
          </button>
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .committee-search {
    position: relative;
  }

  .selected-list {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    margin-bottom: 0.5rem;
  }

  .selected-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0.6rem;
    background: #f0f4ff;
    border: 1px solid #c0d0f0;
    border-radius: 4px;
    font-size: 0.85rem;
  }

  .selected-name {
    font-weight: 500;
  }

  .selected-id {
    color: #666;
    font-size: 0.8rem;
  }

  .remove-btn {
    margin-left: auto;
    padding: 0 0.35rem;
    border: none;
    background: none;
    color: #999;
    cursor: pointer;
    font-size: 1.1rem;
    line-height: 1;
  }

  .remove-btn:hover {
    color: #c00;
  }

  input {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.9rem;
    box-sizing: border-box;
  }

  .searching {
    font-size: 0.8rem;
    color: #666;
    margin-left: 0.5rem;
  }

  .dropdown {
    position: absolute;
    top: calc(100%);
    left: 0;
    right: 0;
    background: white;
    border: 1px solid #ccc;
    border-top: none;
    border-radius: 0 0 4px 4px;
    list-style: none;
    margin: 0;
    padding: 0;
    max-height: 250px;
    overflow-y: auto;
    z-index: 10;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }

  .dropdown li button {
    display: flex;
    justify-content: space-between;
    width: 100%;
    padding: 0.5rem 0.75rem;
    border: none;
    background: none;
    cursor: pointer;
    text-align: left;
    font-size: 0.9rem;
  }

  .dropdown li button:hover {
    background: #f0f4ff;
  }

  .result-name {
    font-weight: 500;
  }

  .result-id {
    color: #666;
    font-size: 0.8rem;
  }
</style>

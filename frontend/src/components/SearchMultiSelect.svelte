<script lang="ts">
  import createClient from 'openapi-fetch';
  import type { paths } from '../../api.d.ts';

  const client = createClient<paths>({ baseUrl: '/' });

  interface SearchResult {
    status: string;
    cycle: number;
    query: string;
    candidate_count: number;
    committee_count: number;
    candidates: Array<{
      candidate_id: string;
      name: string;
      election_year: number;
      office: string;
      state: string;
      district: string;
      principal_campaign_committee: string | null;
    }>;
    committees: Array<{
      committee_id: string;
      name: string;
      committee_type: string;
      designation: string;
      party_affiliation: string;
      connected_org_name: string;
      candidate_id: string | null;
    }>;
  }

  export interface SelectedItem {
    type: 'candidate' | 'committee';
    id: string;
    name: string;
    cycle: number;
    data: any;
  }

  type SearchItem = {
    type: 'candidate' | 'committee';
    id: string;
    name: string;
    data: any;
  };

  // Props
  interface Props {
    selected?: SelectedItem[];
    cycle?: number;
    placeholder?: string;
    onselect?: (items: SelectedItem[]) => void;
  }

  let {
    selected = $bindable([]),
    cycle = 2026,
    placeholder = 'Search for candidate or committee...',
    onselect,
  }: Props = $props();

  // Internal state
  let searchQuery = $state('');
  let searchLoading = $state(false);
  let searchResults = $state<SearchResult | null>(null);
  let searchDebounceTimer: ReturnType<typeof setTimeout> | null = null;
  let showSearchResults = $state(false);
  let selectedIndex = $state(-1);
  let searchInputRef: HTMLInputElement | null = null;

  function getAllSearchItems(): SearchItem[] {
    if (!searchResults) return [];

    const items: SearchItem[] = [];

    // Add candidates
    for (const candidate of searchResults.candidates) {
      // Skip if already selected
      if (selected.some((s) => s.id === candidate.candidate_id)) {
        continue;
      }
      items.push({
        type: 'candidate',
        id: candidate.candidate_id,
        name: candidate.name,
        data: candidate,
      });
    }

    // Add committees
    for (const committee of searchResults.committees) {
      // Skip if already selected
      if (selected.some((s) => s.id === committee.committee_id)) {
        continue;
      }
      items.push({
        type: 'committee',
        id: committee.committee_id,
        name: committee.name,
        data: committee,
      });
    }

    return items;
  }

  async function performSearch() {
    if (!searchQuery.trim()) {
      searchResults = null;
      showSearchResults = false;
      return;
    }

    searchLoading = true;
    try {
      const { data, error } = await client.POST('/-/api/libfec/search', {
        body: {
          query: searchQuery,
          cycle: cycle,
          limit: 100,
        },
      });
      if (error) {
        console.error('Search error:', error);
        searchResults = null;
        showSearchResults = false;
        return;
      }
      if (data) {
        searchResults = data as unknown as SearchResult;
        showSearchResults = true;
        selectedIndex = -1;
      }
    } finally {
      searchLoading = false;
    }
  }

  function onSearchInput() {
    // Clear previous timer
    if (searchDebounceTimer) {
      clearTimeout(searchDebounceTimer);
    }

    // Set new timer
    searchDebounceTimer = setTimeout(() => {
      performSearch();
    }, 200);
  }

  function onSearchKeyDown(e: KeyboardEvent) {
    if (!showSearchResults || !searchResults) return;

    const items = getAllSearchItems();
    if (items.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      selectedIndex = Math.max(selectedIndex - 1, -1);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedIndex >= 0 && selectedIndex < items.length) {
        const item = items[selectedIndex];
        if (item) {
          selectSearchItem(item);
        }
      }
    } else if (e.key === 'Escape') {
      showSearchResults = false;
      selectedIndex = -1;
    }
  }

  function selectSearchItem(item: SearchItem) {
    // Add to selected items
    const newItem: SelectedItem = {
      type: item.type,
      id: item.id,
      name: item.name,
      cycle: searchResults?.cycle || cycle,
      data: item.data,
    };

    const itemsToAdd: SelectedItem[] = [newItem];

    // If selecting a candidate with a principal campaign committee, also add the committee
    if (item.type === 'candidate' && item.data.principal_campaign_committee) {
      const committeeId = item.data.principal_campaign_committee;
      // Check if committee is not already selected
      if (!selected.some((s) => s.id === committeeId)) {
        // Find the committee in search results
        const committee = searchResults?.committees.find((c) => c.committee_id === committeeId);
        if (committee) {
          itemsToAdd.push({
            type: 'committee',
            id: committee.committee_id,
            name: committee.name,
            cycle: searchResults?.cycle || cycle,
            data: committee,
          });
        }
      }
    }

    selected = [...selected, ...itemsToAdd];

    // Clear search
    searchQuery = '';
    showSearchResults = false;
    selectedIndex = -1;
    searchResults = null;

    // Focus back on input
    searchInputRef?.focus();

    // Notify parent
    if (onselect) {
      onselect(selected);
    }
  }

  function removeItem(id: string) {
    selected = selected.filter((item) => item.id !== id);

    // Notify parent
    if (onselect) {
      onselect(selected);
    }
  }

  function onSearchBlur() {
    // Delay hiding to allow clicking on results
    return; // TMP
    setTimeout(() => {
      showSearchResults = false;
      selectedIndex = -1;
    }, 200);
  }

  function onSearchFocus() {
    if (searchResults && searchQuery.trim()) {
      showSearchResults = true;
    }
  }
</script>

<div class="search-multi-select">
  <!-- Selected items pills -->
  {#if selected.length > 0}
    <div class="selected-pills">
      {#each selected as item}
        <div
          class="pill"
          class:candidate={item.type === 'candidate'}
          class:committee={item.type === 'committee'}
        >
          <span class="pill-type">{item.type === 'candidate' ? 'Candidate' : 'Committee'}</span>
          <span class="pill-name">{item.name}</span>
          <code class="pill-id">{item.id}</code>
          <button
            type="button"
            class="pill-remove"
            onclick={() => removeItem(item.id)}
            aria-label="Remove {item.name}">×</button
          >
        </div>
      {/each}
    </div>
  {/if}

  <!-- Search input -->
  <div class="search-container">
    <input
      type="text"
      class="search-input"
      bind:this={searchInputRef}
      bind:value={searchQuery}
      oninput={onSearchInput}
      onkeydown={onSearchKeyDown}
      onblur={onSearchBlur}
      onfocus={onSearchFocus}
      {placeholder}
      autocomplete="off"
    />

    {#if showSearchResults && searchResults}
      <div class="search-dropdown">
        {#if searchLoading}
          <div class="search-loading">Searching...</div>
        {:else if searchResults.candidate_count === 0 && searchResults.committee_count === 0}
          <div class="search-empty">No results found for "{searchResults.query}"</div>
        {:else}
          {@const items = getAllSearchItems()}
          {#if items.length === 0}
            <div class="search-empty">All results already selected</div>
          {:else}
            <div class="search-results-list">
              {#each items as item, idx}
                {@const isSelected = idx === selectedIndex}
                <div
                  class="search-result-item"
                  class:selected={isSelected}
                  onmousedown={(e) => {
                    e.preventDefault();
                    selectSearchItem(item);
                  }}
                  role="option"
                  aria-selected={isSelected}
                  tabindex={idx === selectedIndex ? 0 : -1}
                >
                  <div class="result-main">
                    <span
                      class="result-type-badge"
                      class:candidate={item.type === 'candidate'}
                      class:committee={item.type === 'committee'}
                    >
                      {item.type === 'candidate' ? 'Candidate' : 'Committee'}
                    </span>
                    <span class="result-name">{item.name}</span>
                    <code class="result-id">{item.id}</code>
                    {#if item.type === 'candidate'}
                      <span class="result-info">
                        {item.data.office} · {item.data.state}{item.data.district} · {item.data
                          .election_year}
                      </span>
                    {:else}
                      <span class="result-info">
                        {item.data.committee_type}
                        {#if item.data.party_affiliation}
                          · {item.data.party_affiliation}
                        {/if}
                      </span>
                    {/if}
                  </div>
                </div>
              {/each}
            </div>
            <div class="search-footer">
              Found {searchResults.candidate_count} candidate{searchResults.candidate_count !== 1
                ? 's'
                : ''} and {searchResults.committee_count} committee{searchResults.committee_count !==
              1
                ? 's'
                : ''}
            </div>
          {/if}
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  .search-multi-select {
    display: flex;
    flex-direction: column;
    gap: 0.75em;
  }

  .selected-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5em;
  }

  .pill {
    display: inline-flex;
    align-items: center;
    gap: 0.5em;
    padding: 0.5em 0.75em;
    border-radius: 20px;
    font-size: 0.9em;
    border: 2px solid;
    background: white;
  }

  .pill.candidate {
    border-color: #28a745;
    background: #d4edda;
  }

  .pill.committee {
    border-color: #17a2b8;
    background: #d1ecf1;
  }

  .pill-type {
    font-size: 0.75em;
    font-weight: 600;
    text-transform: uppercase;
    opacity: 0.7;
  }

  .pill-name {
    font-weight: 500;
  }

  .pill-id {
    font-family: 'Courier New', monospace;
    font-size: 0.85em;
    opacity: 0.8;
  }

  .pill-remove {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 1.5em;
    height: 1.5em;
    border: none;
    background: rgba(0, 0, 0, 0.1);
    border-radius: 50%;
    cursor: pointer;
    font-size: 1.2em;
    line-height: 1;
    padding: 0;
    transition: background 0.15s;
  }

  .pill-remove:hover {
    background: rgba(0, 0, 0, 0.2);
  }

  .search-container {
    position: relative;
  }

  .search-input {
    width: 300px;
    padding: 0.75em 1em;
    font-size: 1em;
    border: 2px solid #ced4da;
    border-radius: 6px;
    outline: none;
    transition: border-color 0.2s;
  }

  .search-input:focus {
    border-color: #0066cc;
  }

  .search-dropdown {
    position: absolute;
    top: calc(100% + 0.5em);
    left: 0;
    right: 0;
    background: white;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    box-shadow:
      0 4px 6px rgba(0, 0, 0, 0.1),
      0 2px 4px rgba(0, 0, 0, 0.06);
    max-height: 400px;
    overflow-y: auto;
    z-index: 1000;
  }

  .search-loading,
  .search-empty {
    padding: 1.5em;
    text-align: center;
    color: #666;
  }

  .search-results-list {
    padding: 0.5em 0;
  }

  .search-result-item {
    padding: 0.75em 1em;
    cursor: pointer;
    transition: background 0.15s;
    border-bottom: 1px solid #f1f3f5;
  }

  .search-result-item:last-child {
    border-bottom: none;
  }

  .search-result-item:hover,
  .search-result-item.selected {
    background: #e7f3ff;
  }

  .result-main {
    display: flex;
    align-items: center;
    gap: 0.75em;
    margin-bottom: 0.4em;
  }

  .result-type-badge {
    display: inline-block;
    padding: 0.2em 0.6em;
    font-size: 0.75em;
    font-weight: 600;
    text-transform: uppercase;
    border-radius: 3px;
    letter-spacing: 0.5px;
  }

  .result-type-badge.candidate {
    background: #d4edda;
    color: #155724;
  }

  .result-type-badge.committee {
    background: #d1ecf1;
    color: #0c5460;
  }

  .result-name {
    font-weight: 500;
    color: #212529;
  }

  .result-id {
    font-family: 'Courier New', monospace;
    background: #f8f9fa;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-size: 0.9em;
  }

  .result-info {
    color: #6c757d;
  }

  .search-footer {
    padding: 0.75em 1em;
    background: #f8f9fa;
    border-top: 1px solid #dee2e6;
    font-size: 0.85em;
    color: #6c757d;
    text-align: center;
  }
</style>

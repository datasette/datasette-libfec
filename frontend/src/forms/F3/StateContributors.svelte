<script lang="ts">
  interface StateContribution {
    contributor_state: string;
    total_contributions: number;
  }

  interface Props {
    contributions: StateContribution[];
    homeState: string | null;
  }

  let { contributions, homeState }: Props = $props();

  const STATE_NAMES: Record<string, string> = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
    'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
    'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
    'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
    'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
    'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
    'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
    'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming',
    'DC': 'District of Columbia', 'PR': 'Puerto Rico', 'VI': 'Virgin Islands', 'GU': 'Guam',
  };

  function usd(value: number | null | undefined): string {
    if (value == null) return '$0';
    return '$' + value.toLocaleString();
  }

  const total = $derived(contributions.reduce((sum, row) => sum + (row.total_contributions || 0), 0));
  const top5 = $derived(contributions.slice(0, 5));
  const other = $derived(contributions.slice(5).reduce((sum, row) => sum + (row.total_contributions || 0), 0));
</script>

{#if contributions.length > 0}
  <div class="section-box">
    <h4>Individual Contributions by State</h4>
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th class="text-left">State</th>
            <th class="text-right">Amount</th>
            <th class="text-right">% of Total</th>
          </tr>
        </thead>
        <tbody>
          {#each top5 as row}
            <tr>
              <td>
                {STATE_NAMES[row.contributor_state] || row.contributor_state}
                {#if row.contributor_state === homeState}
                  <span class="home-badge">Home</span>
                {/if}
              </td>
              <td class="text-right">{usd(row.total_contributions)}</td>
              <td class="text-right muted">
                {((row.total_contributions || 0) / total * 100).toFixed(1)}%
              </td>
            </tr>
          {/each}
          {#if other > 0}
            <tr class="other-row">
              <td class="muted italic">Other ({contributions.length - 5} states)</td>
              <td class="text-right muted">{usd(other)}</td>
              <td class="text-right muted">
                {(other / total * 100).toFixed(1)}%
              </td>
            </tr>
          {/if}
          <tr class="total-row">
            <td>Total</td>
            <td class="text-right">{usd(total)}</td>
            <td class="text-right">100.0%</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
{/if}

<style>
  .section-box {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .section-box h4 {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #2563eb;
  }

  .table-container {
    overflow-x: auto;
  }

  .data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
  }

  .data-table th,
  .data-table td {
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid #e5e5e5;
  }

  .data-table th {
    font-weight: 600;
    color: #374151;
    border-bottom: 2px solid #d1d5db;
  }

  .data-table tbody tr:hover {
    background: #f9fafb;
  }

  .text-left {
    text-align: left;
  }

  .text-right {
    text-align: right;
  }

  .muted {
    color: #6b7280;
  }

  .italic {
    font-style: italic;
  }

  .home-badge {
    display: inline-block;
    margin-left: 0.5rem;
    padding: 0.1rem 0.4rem;
    background: #dbeafe;
    color: #1e40af;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 3px;
  }

  .other-row td {
    border-bottom: 1px solid #e5e5e5;
  }

  .total-row {
    font-weight: 700;
    border-top: 2px solid #9ca3af;
  }

  .total-row td {
    padding-top: 0.75rem;
  }
</style>

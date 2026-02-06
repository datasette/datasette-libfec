<script lang="ts">
  interface TopPayee {
    payee: string;
    total_amount: number;
    purposes: string;
  }

  interface Props {
    payees: TopPayee[];
  }

  let { payees }: Props = $props();

  function usd(value: number | null | undefined): string {
    if (value == null) return '$0';
    return '$' + value.toLocaleString();
  }

  const total = $derived(payees.reduce((sum, row) => sum + (row.total_amount || 0), 0));
  const top10 = $derived(payees.slice(0, 10));
  const other = $derived(payees.slice(10).reduce((sum, row) => sum + (row.total_amount || 0), 0));
</script>

{#if payees.length > 0}
  <div class="section-box">
    <h4>Top Expenditure Payees</h4>
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th class="text-left">Payee</th>
            <th class="text-right">Amount</th>
            <th class="text-left">Purpose</th>
            <th class="text-right">% of Total</th>
          </tr>
        </thead>
        <tbody>
          {#each top10 as row}
            <tr>
              <td class="payee-name" title={row.payee}>{row.payee || 'Unknown'}</td>
              <td class="text-right">{usd(row.total_amount)}</td>
              <td class="purpose" title={row.purposes}>{row.purposes || ''}</td>
              <td class="text-right muted">
                {((row.total_amount || 0) / total * 100).toFixed(1)}%
              </td>
            </tr>
          {/each}
          {#if other > 0}
            <tr class="other-row">
              <td class="muted italic">Other ({payees.length - 10} payees)</td>
              <td class="text-right muted">{usd(other)}</td>
              <td></td>
              <td class="text-right muted">
                {(other / total * 100).toFixed(1)}%
              </td>
            </tr>
          {/if}
          <tr class="total-row">
            <td>Total</td>
            <td class="text-right">{usd(total)}</td>
            <td></td>
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

  .payee-name {
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .purpose {
    max-width: 250px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 0.85rem;
    color: #6b7280;
  }
</style>

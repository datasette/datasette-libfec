<script lang="ts">
  import { get } from 'svelte/store';
  import { databaseName } from '../../stores';
  import { query } from '../../api';
  import { useQuery } from '../../useQuery.svelte';

  interface TopPayee {
    payee: string;
    payee_organization_name: string | null;
    payee_last_name: string | null;
    total_amount: number;
    purposes: string;
  }

  interface Props {
    filingId: string;
  }

  let { filingId }: Props = $props();

  const dbName = get(databaseName);

  async function fetchTopPayees(): Promise<TopPayee[]> {
    if (!filingId) return [];

    const sql = `
      SELECT
        COALESCE(payee_organization_name, payee_last_name || ', ' || payee_first_name) as payee,
        payee_organization_name,
        payee_last_name,
        SUM(expenditure_amount) as total_amount,
        GROUP_CONCAT(DISTINCT expenditure_purpose_descrip) as purposes
      FROM libfec_schedule_b
      WHERE 
        filing_id = :filing_id 
        AND form_type = 'SB17'
        AND memo_code != 'X'
      GROUP BY payee
      ORDER BY total_amount DESC
      LIMIT 20
    `;
    return query(dbName, sql, { filing_id: filingId });
  }

  const payees = useQuery(fetchTopPayees);

  function usd(value: number | null | undefined, round = false): string {
    if (value == null) return '$0';
    const v = round ? Math.round(value) : value;
    return '$' + v.toLocaleString();
  }

  function payeeUrl(row: TopPayee): string {
    const params = new URLSearchParams({
      _sort: 'rowid',
      filing_id__exact: filingId,
    });
    if (row.payee_organization_name) {
      params.set('payee_organization_name__exact', row.payee_organization_name);
    } else if (row.payee_last_name) {
      params.set('payee_last_name__exact', row.payee_last_name);
    }
    params.set('form_type__exact', 'SB17');
    return `/${dbName}/libfec_schedule_b?${params}`;
  }

  const total = $derived(
    (payees.data ?? []).reduce((sum, row) => sum + (row.total_amount || 0), 0)
  );
  const top10 = $derived((payees.data ?? []).slice(0, 10));
  const other = $derived(
    (payees.data ?? []).slice(10).reduce((sum, row) => sum + (row.total_amount || 0), 0)
  );
</script>

{#if payees.isLoading}
  <div class="section-box">
    <h4>Top Expenditure Payees</h4>
    <div class="loading">Loading...</div>
  </div>
{:else if payees.data && payees.data.length > 0}
  <div class="section-box">
    <h4>Top Expenditure Payees</h4>
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th class="text-left">Payee</th>
            <th class="text-left">Purpose</th>
            <th class="text-right">Amount</th>
            <th class="text-right">% of Total</th>
          </tr>
        </thead>
        <tbody>
          {#each top10 as row}
            <tr>
              <td class="payee-name" title={row.payee}>
                <a href={payeeUrl(row)}>{row.payee || 'Unknown'}</a>
              </td>
              <td class="purpose" title={row.purposes}>{row.purposes || ''}</td>
              <td class="text-right">{usd(row.total_amount, true)}</td>
              <td class="text-right muted">
                {(((row.total_amount || 0) / total) * 100).toFixed(1)}%
              </td>
            </tr>
          {/each}
          {#if other > 0}
            <tr class="other-row">
              <td class="muted italic">Other ({(payees.data?.length ?? 0) - 10} payees)</td>
              <td></td>
              <td class="text-right muted">{usd(other, true)}</td>
              <td class="text-right muted">
                {((other / total) * 100).toFixed(1)}%
              </td>
            </tr>
          {/if}
          <tr class="total-row">
            <td>Total</td>
            <td></td>
            <td class="text-right">{usd(total)}</td>
            <td class="text-right">100.0%</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p class="info-note">Only includes operating expenditures $200 or more.</p>
  </div>
{/if}

<style>
  .section-box {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1.5rem;
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
    max-width: 100px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 0.85rem;
    color: #6b7280;
  }

  .loading {
    text-align: center;
    color: #6b7280;
    padding: 1rem;
  }

  .info-note {
    margin-top: 0.75rem;
    font-size: 0.8rem;
    color: #6b7280;
    font-style: italic;
  }
</style>

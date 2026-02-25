<script lang="ts">
  import { get } from 'svelte/store';
  import { databaseName } from '../../stores';
  import { query } from '../../api';
  import { useQuery } from '../../useQuery.svelte';
  import { getStateName } from '../../utils/stateNames';

  interface CandidateRow {
    support_oppose_code: string;
    candidate_last_name: string;
    candidate_first_name: string;
    candidate_office: string;
    candidate_state: string;
    candidate_district: string;
    total: number;
    txn_count: number;
  }

  interface PurposeRow {
    expenditure_purpose_descrip: string;
    total: number;
    txn_count: number;
  }

  interface PayeeRow {
    payee: string;
    payee_organization_name: string | null;
    payee_last_name: string | null;
    total: number;
    txn_count: number;
    purposes: string;
  }

  interface Props {
    filingId: string;
  }

  let { filingId }: Props = $props();

  const dbName = get(databaseName);

  async function fetchCandidates(): Promise<CandidateRow[]> {
    if (!filingId) return [];
    const sql = `
      SELECT
        support_oppose_code,
        candidate_last_name,
        candidate_first_name,
        candidate_office,
        candidate_state,
        candidate_district,
        SUM(expenditure_amount) as total,
        COUNT(*) as txn_count
      FROM libfec_schedule_e
      WHERE filing_id = :filing_id
        AND (memo_code IS NULL OR memo_code = '')
      GROUP BY support_oppose_code, candidate_last_name, candidate_first_name,
               candidate_office, candidate_state, candidate_district
      ORDER BY total DESC
    `;
    return query(dbName, sql, { filing_id: filingId });
  }

  async function fetchPurposes(): Promise<PurposeRow[]> {
    if (!filingId) return [];
    const sql = `
      SELECT
        expenditure_purpose_descrip,
        SUM(expenditure_amount) as total,
        COUNT(*) as txn_count
      FROM libfec_schedule_e
      WHERE filing_id = :filing_id
        AND (memo_code IS NULL OR memo_code = '')
      GROUP BY expenditure_purpose_descrip
      ORDER BY total DESC
    `;
    return query(dbName, sql, { filing_id: filingId });
  }

  async function fetchPayees(): Promise<PayeeRow[]> {
    if (!filingId) return [];
    const sql = `
      SELECT
        COALESCE(payee_organization_name, payee_last_name || ', ' || payee_first_name) as payee,
        payee_organization_name,
        payee_last_name,
        SUM(expenditure_amount) as total,
        COUNT(*) as txn_count,
        GROUP_CONCAT(DISTINCT expenditure_purpose_descrip) as purposes
      FROM libfec_schedule_e
      WHERE filing_id = :filing_id
        AND (memo_code IS NULL OR memo_code = '')
      GROUP BY payee
      ORDER BY total DESC
      LIMIT 15
    `;
    return query(dbName, sql, { filing_id: filingId });
  }

  const candidates = useQuery(fetchCandidates);
  const purposes = useQuery(fetchPurposes);
  const payees = useQuery(fetchPayees);

  function usd(value: number | null | undefined, round = false): string {
    if (value == null) return '$0';
    const v = round ? Math.round(value) : value;
    return '$' + v.toLocaleString();
  }

  function candidateName(row: CandidateRow): string {
    return `${row.candidate_last_name}, ${row.candidate_first_name}`;
  }

  function officeLabel(office: string, state: string, district?: string): string {
    if (office === 'P') return 'President';
    if (office === 'S') return `Senate - ${getStateName(state)}`;
    if (office === 'H' && district) return `${getStateName(state)}-${district}`;
    if (office === 'H') return `House - ${getStateName(state)}`;
    return office;
  }

  function scheduleEUrl(params?: Record<string, string>): string {
    const base = new URLSearchParams({
      _sort: 'rowid',
      filing_id__exact: filingId,
    });
    if (params) {
      for (const [k, v] of Object.entries(params)) {
        base.set(k, v);
      }
    }
    return `/${dbName}/libfec_schedule_e?${base}`;
  }

  const totalSpending = $derived(
    (candidates.data ?? []).reduce((sum, row) => sum + (row.total || 0), 0)
  );
  const totalSupport = $derived(
    (candidates.data ?? [])
      .filter((r) => r.support_oppose_code === 'S')
      .reduce((sum, row) => sum + (row.total || 0), 0)
  );
  const totalOppose = $derived(
    (candidates.data ?? [])
      .filter((r) => r.support_oppose_code === 'O')
      .reduce((sum, row) => sum + (row.total || 0), 0)
  );

  const top10Candidates = $derived((candidates.data ?? []).slice(0, 10));
  const top10Payees = $derived((payees.data ?? []).slice(0, 10));
  const payeeTotal = $derived((payees.data ?? []).reduce((sum, row) => sum + (row.total || 0), 0));
  const payeeOther = $derived(
    (payees.data ?? []).slice(10).reduce((sum, row) => sum + (row.total || 0), 0)
  );

  const isLoading = $derived(candidates.isLoading || purposes.isLoading || payees.isLoading);
  const hasData = $derived((candidates.data?.length ?? 0) > 0 || (payees.data?.length ?? 0) > 0);
</script>

{#if isLoading}
  <div class="section-box">
    <h4>Independent Expenditures</h4>
    <div class="loading">Loading...</div>
  </div>
{:else if hasData}
  <div class="section-box">
    <h4>Independent Expenditures</h4>

    <!-- Support/Oppose summary bar -->
    {#if totalSpending > 0}
      <div class="so-summary">
        <div class="so-bar">
          <div class="so-bar-support" style="width: {(totalSupport / totalSpending) * 100}%"></div>
          <div class="so-bar-oppose" style="width: {(totalOppose / totalSpending) * 100}%"></div>
        </div>
        <div class="so-labels">
          <span class="badge badge-support">Support {usd(totalSupport, true)}</span>
          <span class="so-total">{usd(totalSpending, true)} total</span>
          <span class="badge badge-oppose">Oppose {usd(totalOppose, true)}</span>
        </div>
      </div>
    {/if}

    <div class="ie-grid">
      <!-- Candidates -->
      {#if top10Candidates.length > 0}
        <div class="ie-panel">
          <h5>Candidates</h5>
          <table class="data-table">
            <thead>
              <tr>
                <th class="text-left"></th>
                <th class="text-left">Candidate</th>
                <th class="text-left">Race</th>
                <th class="text-right">Amount</th>
              </tr>
            </thead>
            <tbody>
              {#each top10Candidates as row}
                <tr>
                  <td>
                    {#if row.support_oppose_code === 'S'}
                      <span class="badge badge-support">S</span>
                    {:else}
                      <span class="badge badge-oppose">O</span>
                    {/if}
                  </td>
                  <td class="candidate-name">
                    <a
                      href={scheduleEUrl({
                        candidate_last_name__exact: row.candidate_last_name,
                        support_oppose_code__exact: row.support_oppose_code,
                      })}
                    >
                      {candidateName(row)}
                    </a>
                  </td>
                  <td class="race muted">
                    {officeLabel(row.candidate_office, row.candidate_state, row.candidate_district)}
                  </td>
                  <td class="text-right">{usd(row.total, true)}</td>
                </tr>
              {/each}
              {#if (candidates.data?.length ?? 0) > 10}
                <tr class="other-row">
                  <td></td>
                  <td class="muted italic" colspan="2">
                    + {(candidates.data?.length ?? 0) - 10} more candidates
                  </td>
                  <td></td>
                </tr>
              {/if}
            </tbody>
          </table>
        </div>
      {/if}
    </div>

    <div class="ie-grid">
      <!-- Expenditure Purposes -->
      {#if (purposes.data?.length ?? 0) > 0}
        <div class="ie-panel">
          <h5>Expenditure Purposes</h5>
          <div class="purpose-bars">
            {#each purposes.data ?? [] as row}
              {@const pct = totalSpending > 0 ? (row.total / totalSpending) * 100 : 0}
              <div class="purpose-row">
                <div class="purpose-label">
                  <span>{row.expenditure_purpose_descrip}</span>
                  <span class="muted">{usd(row.total, true)}</span>
                </div>
                <div class="purpose-bar-track">
                  <div class="purpose-bar-fill" style="width: {pct}%"></div>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Top Payees -->
      {#if top10Payees.length > 0}
        <div class="ie-panel">
          <h5>Top Payees</h5>
          <table class="data-table">
            <thead>
              <tr>
                <th class="text-left">Payee</th>
                <th class="text-left">Purpose</th>
                <th class="text-right">Amount</th>
              </tr>
            </thead>
            <tbody>
              {#each top10Payees as row}
                <tr>
                  <td class="payee-name" title={row.payee}>
                    <a
                      href={scheduleEUrl(
                        row.payee_organization_name
                          ? { payee_organization_name__exact: row.payee_organization_name }
                          : row.payee_last_name
                            ? { payee_last_name__exact: row.payee_last_name }
                            : {}
                      )}
                    >
                      {row.payee || 'Unknown'}
                    </a>
                  </td>
                  <td class="purpose" title={row.purposes}>{row.purposes || ''}</td>
                  <td class="text-right">{usd(row.total, true)}</td>
                </tr>
              {/each}
              {#if payeeOther > 0}
                <tr class="other-row">
                  <td class="muted italic">
                    Other ({(payees.data?.length ?? 0) - 10} payees)
                  </td>
                  <td></td>
                  <td class="text-right muted">{usd(payeeOther, true)}</td>
                </tr>
              {/if}
              <tr class="total-row">
                <td>Total</td>
                <td></td>
                <td class="text-right">{usd(payeeTotal, true)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      {/if}
    </div>

    <p class="info-note">
      <a href={scheduleEUrl()}>View all independent expenditure transactions</a>
    </p>
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

  .ie-grid {
    display: flex;
    gap: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .ie-panel {
    flex: 1;
    min-width: 0;
  }

  .ie-panel h5 {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 0.75rem;
    color: #374151;
  }

  @media (max-width: 1024px) {
    .ie-grid {
      flex-direction: column;
    }
  }

  /* Support/Oppose summary */
  .so-summary {
    margin-bottom: 1.5rem;
  }

  .so-bar {
    display: flex;
    height: 8px;
    border-radius: 4px;
    overflow: hidden;
    background: #e5e7eb;
  }

  .so-bar-support {
    background: #22c55e;
  }

  .so-bar-oppose {
    background: #ef4444;
  }

  .so-labels {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 0.5rem;
    font-size: 0.85rem;
  }

  .so-total {
    color: #6b7280;
    font-weight: 600;
  }

  /* Badges */
  .badge {
    display: inline-block;
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.02em;
  }

  .badge-support {
    background: #dcfce7;
    color: #166534;
  }

  .badge-oppose {
    background: #fee2e2;
    color: #991b1b;
  }

  /* Tables */
  .data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
  }

  .data-table th,
  .data-table td {
    padding: 0.4rem 0.5rem;
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

  .candidate-name {
    max-width: 160px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .race {
    font-size: 0.8rem;
    white-space: nowrap;
  }

  .payee-name {
    max-width: 180px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .purpose {
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 0.8rem;
    color: #6b7280;
  }

  .other-row td {
    border-bottom: 1px solid #e5e5e5;
  }

  .total-row {
    font-weight: 700;
    border-top: 2px solid #9ca3af;
  }

  .total-row td {
    padding-top: 0.5rem;
  }

  /* Purpose bars */
  .purpose-bars {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .purpose-row {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }

  .purpose-label {
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
  }

  .purpose-bar-track {
    height: 6px;
    background: #e5e7eb;
    border-radius: 3px;
    overflow: hidden;
  }

  .purpose-bar-fill {
    height: 100%;
    background: #3b82f6;
    border-radius: 3px;
    min-width: 2px;
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

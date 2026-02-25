<script lang="ts">
  interface Props {
    cashStart: number | null | undefined;
    receipts: number | null | undefined;
    disbursements: number | null | undefined;
    cashEnd: number | null | undefined;
  }

  let { cashStart, receipts, disbursements, cashEnd }: Props = $props();

  function usd(value: number | null | undefined): string {
    if (value == null) return '$0';
    return '$' + value.toLocaleString();
  }

  const cashChange = $derived((cashEnd ?? 0) - (cashStart ?? 0));
</script>

<div class="summary-cards">
  <div class="card">
    <div class="card-label">Cash on Hand - Start</div>
    <div class="card-value">{usd(cashStart)}</div>
  </div>
  <div class="card">
    <div class="card-label">Receipts</div>
    <div class="card-value receipts">{usd(receipts)}</div>
  </div>
  <div class="card">
    <div class="card-label">Disbursements</div>
    <div class="card-value disbursements">{usd(disbursements)}</div>
  </div>
  <div class="card">
    <div class="card-label">Cash on Hand - End</div>
    <div class="card-value">{usd(cashEnd)}</div>
    <div class="card-change" class:positive={cashChange >= 0} class:negative={cashChange < 0}>
      {#if cashChange >= 0}
        <span class="arrow">&#x2191;</span>
      {:else}
        <span class="arrow">&#x2193;</span>
      {/if}
      {usd(Math.abs(cashChange))}
    </div>
  </div>
</div>

<style>
  .summary-cards {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  @media (max-width: 768px) {
    .summary-cards {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  .card {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }

  .card-label {
    font-size: 0.85rem;
    font-weight: 500;
    color: #666;
  }

  .card-value {
    margin-top: 0.25rem;
    font-size: 1.25rem;
    font-weight: 600;
  }

  .card-value.receipts {
    color: #2563eb;
  }

  .card-value.disbursements {
    color: #dc2626;
  }

  .card-change {
    margin-top: 0.25rem;
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .card-change.positive {
    color: #16a34a;
  }

  .card-change.negative {
    color: #dc2626;
  }

  .arrow {
    font-weight: bold;
  }
</style>

<script lang="ts">
  interface RaceSpec {
    office: string;
    state: string;
    district: string;
    cycle: number;
  }

  interface Props {
    race: RaceSpec;
    onchange: (race: RaceSpec) => void;
  }

  let { race, onchange }: Props = $props();

  const states = [
    'AL',
    'AK',
    'AZ',
    'AR',
    'CA',
    'CO',
    'CT',
    'DE',
    'FL',
    'GA',
    'HI',
    'ID',
    'IL',
    'IN',
    'IA',
    'KS',
    'KY',
    'LA',
    'ME',
    'MD',
    'MA',
    'MI',
    'MN',
    'MS',
    'MO',
    'MT',
    'NE',
    'NV',
    'NH',
    'NJ',
    'NM',
    'NY',
    'NC',
    'ND',
    'OH',
    'OK',
    'OR',
    'PA',
    'RI',
    'SC',
    'SD',
    'TN',
    'TX',
    'UT',
    'VT',
    'VA',
    'WA',
    'WV',
    'WI',
    'WY',
    'DC',
    'AS',
    'GU',
    'MP',
    'PR',
    'VI',
  ];

  function update(field: keyof RaceSpec, value: string | number) {
    onchange({ ...race, [field]: value });
  }
</script>

<div class="contest-form">
  <div class="field-row">
    <label>
      Office
      <select
        value={race.office}
        onchange={(e) => update('office', (e.target as HTMLSelectElement).value)}
      >
        <option value="H">House</option>
        <option value="S">Senate</option>
        <option value="P">President</option>
      </select>
    </label>
    <label>
      State
      <select
        value={race.state}
        onchange={(e) => update('state', (e.target as HTMLSelectElement).value)}
      >
        <option value="">Select state...</option>
        {#each states as s}
          <option value={s}>{s}</option>
        {/each}
      </select>
    </label>
    {#if race.office === 'H'}
      <label>
        District
        <input
          type="text"
          value={race.district}
          oninput={(e) => update('district', (e.target as HTMLInputElement).value)}
          placeholder="e.g. 12"
          maxlength="2"
          style="max-width: 70px;"
        />
      </label>
    {/if}
    <label>
      Cycle
      <input
        type="text"
        value={race.cycle}
        oninput={(e) => update('cycle', parseInt((e.target as HTMLInputElement).value) || 0)}
        maxlength="4"
        style="max-width: 70px;"
      />
    </label>
  </div>
</div>

<style>
  .contest-form {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  .field-row {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
    align-items: flex-end;
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
    font-size: 0.83rem;
    font-weight: 500;
  }

  select,
  input {
    padding: 0.4rem 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.85rem;
  }
</style>

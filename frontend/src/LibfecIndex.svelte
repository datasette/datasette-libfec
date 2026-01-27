<script lang="ts">
  import createClient from "openapi-fetch";
  import type { paths } from "../api.d.ts";

  const client = createClient<paths>({ baseUrl: "/" });

  type TargetKind = "committee" | "candidate" | "contest";

  let isLoading = $state(false);
  let kind: TargetKind = $state("committee");
  let id = $state("C00498667");
  let cycle = $state(2026);

  async function onSubmit(e: SubmitEvent) {
    e.preventDefault();

    if (!id) {
      alert('Please enter an ID.');
      return;
    }

    isLoading = true;
    try {
      const {data, error} = await client.POST("/-/api/libfec", {
        body: {
          kind: kind,
          id: id,
          cycle: cycle
        }
      });
      if (error) {
        alert(`Error starting import: ${JSON.stringify(error)}`);
        return;
      }
      alert(`Import started successfully: ${JSON.stringify(data)}`);
    } finally {
      isLoading = false;
    }
  }
</script>

<main>
  <h1>FEC Data Import</h1>
  <p>Import Federal Election Commission data into your Datasette database.</p>

  <section class="import-section">
    <h2>Import Data</h2>
    <p>Select the type of FEC data you want to import, provide an ID, and choose an election cycle.</p>

    <form onsubmit={onSubmit}>
      <!-- Target Kind Selection -->
      <div class="form-group">
        <fieldset>
          <legend>Import Type</legend>
          <div class="radio-group">
            <div>
              <input
                id="committee"
                name="kind"
                type="radio"
                value="committee"
                bind:group={kind}
              />
              <label for="committee">
                Committee
              </label>
            </div>
            <div>
              <input
                id="candidate"
                name="kind"
                type="radio"
                value="candidate"
                bind:group={kind}
              />
              <label for="candidate">
                Candidate
              </label>
            </div>
            <div>
              <input
                id="contest"
                name="kind"
                type="radio"
                value="contest"
                bind:group={kind}
              />
              <label for="contest">
                Contest
              </label>
            </div>
          </div>
        </fieldset>
      </div>

      <!-- ID Input -->
      <div class="form-group">
        <label for="id">
          ID
        </label>
        <input
          type="text"
          id="id"
          name="id"
          bind:value={id}
          placeholder="e.g. C00498667"
        />
      </div>

      <!-- Cycle Input -->
      <div class="form-group">
        <label for="cycle">
          Election Cycle
        </label>
        <select
          id="cycle"
          name="cycle"
          bind:value={cycle}
        >
          <option value={2026}>2026</option>
          <option value={2024}>2024</option>
          <option value={2022}>2022</option>
        </select>
      </div>

      <!-- Submit Button -->
      <button
        type="submit"
        disabled={isLoading}
      >
        {isLoading ? "Importing..." : "Import Data"}
      </button>
    </form>
  </section>
</main>

<style>
  .import-section {
    margin: 2em 0;
  }

  .form-group {
    margin-bottom: 1.5em;
  }

  .form-group label {
    display: block;
    font-weight: bold;
    margin-bottom: 0.5em;
  }

  .form-group input[type="text"],
  .form-group select {
    width: 100%;
    max-width: 400px;
    padding: 0.5em;
    font-size: 1em;
    border: 1px solid #ccc;
    border-radius: 4px;
  }

  fieldset {
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 1em;
  }

  legend {
    font-weight: bold;
    padding: 0 0.5em;
  }

  .radio-group {
    display: flex;
    gap: 1.5em;
    flex-wrap: wrap;
  }

  .radio-group div {
    display: flex;
    align-items: center;
    gap: 0.5em;
  }

  .radio-group input[type="radio"] {
    cursor: pointer;
  }

  .radio-group label {
    cursor: pointer;
    margin: 0;
  }

  button {
    padding: 0.75em 1.5em;
    font-size: 1em;
    background: #0066cc;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  button:hover:not(:disabled) {
    background: #0052a3;
  }

  button:disabled {
    background: #999;
    cursor: not-allowed;
  }
</style>

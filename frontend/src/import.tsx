import { render } from "preact";
import { useState } from "preact/hooks";
import createClient from "openapi-fetch";
import type { paths } from "../api.d.ts";

const client = createClient<paths>({ baseUrl: "/" });

type TargetKind = "committee" | "candidate" | "contest";

function App() {
  const [isLoading, setIsLoading] = useState(false);

  async function onSubmit(e: Event) {
    e.preventDefault();
    
    const formData = new FormData(e.target as HTMLFormElement);
    const kind = formData.get('kind') as TargetKind;
    const id = formData.get('id') as string;
    const cycle = parseInt(formData.get('cycle') as string, 10);
    
    if (!id) {
      alert('Please enter an ID.');
      return;
    }

    setIsLoading(true);
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
      setIsLoading(false);
    }
  }

  return (
    <div>
      <div>
        <h1>FEC Data Import</h1>
        
        <form onSubmit={onSubmit}>
          {/* Target Kind Selection */}
          <div>
            <label>
              Import Type
            </label>
            <fieldset>
              <div>
                <input
                  id="committee"
                  name="kind"
                  type="radio"
                  value="committee"
                  defaultChecked
                />
                <label htmlFor="committee">
                  Committee
                </label>
              </div>
              <div>
                <input
                  id="candidate"
                  name="kind"
                  type="radio"
                  value="candidate"
                />
                <label htmlFor="candidate">
                  Candidate
                </label>
              </div>
              <div>
                <input
                  id="contest"
                  name="kind"
                  type="radio"
                  value="contest"
                />
                <label htmlFor="contest">
                  Contest
                </label>
              </div>
            </fieldset>
          </div>

          {/* ID Input */}
          <div>
            <label htmlFor="id">
              ID
            </label>
            <input
              type="text"
              id="id"
              name="id"
              defaultValue="C00498667"
              placeholder="e.g. C00498667"
            />
          </div>

          {/* Cycle Input */}
          <div>
            <label htmlFor="cycle">
              Election Cycle
            </label>
            <select
              id="cycle"
              name="cycle"
              defaultValue="2026"
            >
              <option value="2026">2026</option>
              <option value="2024">2024</option>
              <option value="2022">2022</option>
            </select>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
          >
            {isLoading ? "Importing..." : "Import Data"}
          </button>
        </form>
      </div>
    </div>
  );
}

const root = document.getElementById('root');
if (root) {
  render(<App />, root);
}
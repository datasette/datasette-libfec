// Shared constants for the doc-screenshot harness. Imported by every other
// shots/*.mjs module and by each shot in shots/defs/.
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

// Free high port unique to this plugin (others in the family: paper 8486,
// sheets 8487, town 8489, skill-default 8490).
export const PORT = Number(process.env.SHOTS_PORT || 8491);
export const BASE = `http://localhost:${PORT}`;
// datasette database name == the data-db filename stem.
export const DB_NAME = 'data';
// The plugin's base UI path; each shot builds its per-page URL off this.
export const APP = `${BASE}/${DB_NAME}/-/libfec`;
// datasette-paper's base path (only the `paper` shot touches it).
export const PAPER = `${BASE}/-/paper`;

// Fixed signing secret — lets us mint a signed actor cookie for the paper doc
// owner. Must match datasette's --secret. NOT a real secret.
export const SECRET = 'screenshots-secret-not-for-prod';

const HERE = dirname(fileURLToPath(import.meta.url)); // frontend/scripts/shots
// Pre-built demo FEC database (run `just shots-fixture` to (re)generate). Unlike
// the other plugins in this family, libfec's data is a real FEC fixture .db, not
// something a startup plugin can seed — so this is the "seed".
export const FIXTURE_DB = resolve(HERE, '../shot-data/libfec.db');
export const DATA_DIR = '/tmp/datasette-libfec-shots-data'; // stem == DB_NAME
export const DATA_DB = `${DATA_DIR}/${DB_NAME}.db`;
// datasette-paper stores docs in the internal DB; a throwaway one, wiped each
// run, keeps the seeded doc's id deterministic. Only used for the `paper` shot.
export const INTERNAL_DB = `${DATA_DIR}/internal.db`;
// Throwaway plugin dir: friendly display name for the paper doc author.
export const PLUGINS_DIR = resolve(HERE, '../shot-plugins');
export const OUT = resolve(HERE, '../../../docs/screenshots');

export const VIEWPORT = { width: 1200, height: 900 };
// Cropped to the paper editor chrome + heading + the two stacked embed cards.
export const VIEWPORT_TALL = { width: 1200, height: 800 };

// The paper doc owner — create seeds an owner acl grant to this actor, and
// shot-plugins/profiles.py maps it to a friendly display name.
export const PAPER_ACTOR = 'alice';

// --- Concrete demo entities (from the fixture: 2024 Ohio Senate + big PACs) ---
export const SHERROD_BROWN = 'S6OH00163'; // candidate id
export const BERNIE_MORENO = 'S4OH00192'; // his 2024 Senate opponent
export const FAIRSHAKE = 'C00835959'; // crypto super PAC committee id
export const BROWN_YE_FILING = '1870297'; // Friends of Sherrod Brown, F3 YE 2024
// Candidates embedded as cards in the seeded paper doc.
export const PAPER_EMBED_CANDIDATES = [SHERROD_BROWN, BERNIE_MORENO];

// Absolute path of a shot's output PNG.
export const out = (name) => resolve(OUT, `${name}.png`);

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

// Fixed --secret for the throwaway server; stable so runs stay reproducible.
export const SECRET = 'screenshots-secret-not-for-prod';

const HERE = dirname(fileURLToPath(import.meta.url)); // frontend/scripts/shots
// Pre-built demo FEC database (run `just shots-fixture` to (re)generate). Unlike
// the other plugins in this family, libfec's data is a real FEC fixture .db, not
// something a startup plugin can seed — so this is the "seed".
export const FIXTURE_DB = resolve(HERE, '../shot-data/libfec.db');
export const DATA_DIR = '/tmp/datasette-libfec-shots-data'; // stem == DB_NAME
export const DATA_DB = `${DATA_DIR}/${DB_NAME}.db`;
export const OUT = resolve(HERE, '../../../docs/screenshots');

export const VIEWPORT = { width: 1200, height: 900 };

// --- Concrete demo entities (from the fixture: 2024 Ohio Senate + big PACs) ---
export const SHERROD_BROWN = 'S6OH00163'; // candidate id
export const FAIRSHAKE = 'C00835959'; // crypto super PAC committee id
export const BROWN_YE_FILING = '1870297'; // Friends of Sherrod Brown, F3 YE 2024

// Absolute path of a shot's output PNG.
export const out = (name) => resolve(OUT, `${name}.png`);

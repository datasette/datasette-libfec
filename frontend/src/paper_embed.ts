/**
 * datasette-paper embed integration for datasette-libfec.
 *
 * `export default`s a paper embed provider for the `libfec-candidate` kind:
 * paper `import()`s this bundle on demand and registers the provider for us
 * (see the descriptor in datasette_libfec/paper.py and
 * docs/EMBED_PROVIDERS.md in datasette-paper).
 *
 * Everything is client-side. resolve/search/mount fetch Datasette's *native*
 * table JSON API (`/{db}/libfec_candidates.json`) with the viewer's `ds_actor`
 * cookie, so per-viewer leak discipline is Datasette's table permissions plus
 * ours: a candidate in a db/table the viewer can't see yields `denied` /
 * `not_found` / no search hit — never a leaked name.
 *
 * Ref shape: stored refs are `/-/libfec/candidate/{db}/{candidate_id}`
 * (libfec namespace first so it sits under a static `ref_prefix` — the real
 * page URL `/{db}/-/libfec/candidate/{id}` leads with a variable db segment).
 * No external imports / no CSS import on purpose: a single standalone chunk
 * sidesteps datasette-vite's base-prefixed-asset 404s for code-split bundles.
 */

// bootstrap-icons/person-vcard — inline pill + block-card header icon. Static
// markup only (paper renders it as raw HTML, unsanitized — never interpolate
// resource data into it).
const VCARD_ICON =
  '<svg viewBox="0 0 16 16" fill="currentColor"><path d="M5 8a2 2 0 1 0 0-4 2 2 0 0 0 0 4m4-2.5a.5.5 0 0 1 .5-.5h4a.5.5 0 0 1 0 1h-4a.5.5 0 0 1-.5-.5M9 8a.5.5 0 0 1 .5-.5h4a.5.5 0 0 1 0 1h-4A.5.5 0 0 1 9 8m1 2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1-.5-.5"/><path d="M2 2a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2zM1 4a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H8.96q.04-.245.04-.5C9 10.567 7.21 9 5 9c-2.086 0-3.8 1.398-3.984 3.181A1 1 0 0 1 1 12z"/></svg>';

const REF_RE = /^\/-\/libfec\/candidate\/([^/]+)\/([^/]+)\/?$/;
const URL_RE = /^\/([^/]+)\/-\/libfec\/candidate\/([^/]+)\/?$/;

interface CandidateRow {
  candidate_id?: string;
  name?: string | null;
  party_affiliation?: string | null;
  office?: string | null;
  state?: string | null;
  district?: string | null;
  cycle?: number | null;
  principal_campaign_committee?: string | null;
}

interface Parsed {
  db: string;
  candidateId: string;
}

function parseRef(ref: string): Parsed | null {
  const m = REF_RE.exec(ref);
  if (!m) return null;
  const [, db, cid] = m;
  if (db === undefined || cid === undefined) return null;
  return { db: decodeURIComponent(db), candidateId: decodeURIComponent(cid) };
}

/** Real libfec page URL for the pill/card header link (cycle optional). */
function pageHref(p: Parsed, cycle?: number | null): string {
  const base = `/${encodeURIComponent(p.db)}/-/libfec/candidate/${encodeURIComponent(p.candidateId)}`;
  return cycle != null ? `${base}?cycle=${cycle}` : base;
}

const OFFICE_LABELS: Record<string, string> = {
  H: 'House',
  S: 'Senate',
  P: 'President',
};

function officeLabel(row: CandidateRow): string {
  const code = (row.office || '').toUpperCase();
  const name = OFFICE_LABELS[code] || code;
  if (!name) return '';
  if (code === 'H' && row.district) {
    const d = String(row.district).replace(/^0+/, '') || '0';
    return `${name}, ${row.state || ''}-${d}`.trim();
  }
  if (row.state) return `${name}, ${row.state}`;
  return name;
}

/** Normalize Datasette's table JSON (1.x `{rows:[...]}` or `_shape=array`). */
function rowsOf(j: unknown): CandidateRow[] {
  if (Array.isArray(j)) return j as CandidateRow[];
  if (j && typeof j === 'object' && Array.isArray((j as { rows?: unknown[] }).rows)) {
    return (j as { rows: CandidateRow[] }).rows;
  }
  return [];
}

/**
 * Fetch the most-recent-cycle row for one candidate via Datasette's native
 * table API. Returns the row, `"denied"` (403), or null (missing / error).
 */
async function fetchCandidate(p: Parsed): Promise<CandidateRow | 'denied' | null> {
  const url =
    `/${encodeURIComponent(p.db)}/libfec_candidates.json` +
    `?candidate_id__exact=${encodeURIComponent(p.candidateId)}` +
    `&_sort_desc=cycle&_size=1&_shape=array`;
  let res: Response;
  try {
    res = await fetch(url, { headers: { Accept: 'application/json' } });
  } catch {
    return null;
  }
  if (res.status === 403) return 'denied'; // never a label here
  if (!res.ok) return null;
  let j: unknown;
  try {
    j = await res.json();
  } catch {
    return null;
  }
  return rowsOf(j)[0] ?? null;
}

// --- types mirrored from paper's embed provider interface --------------------

type ResolveResult =
  | { status: 'ok'; kind: string; label: string; href: string; icon?: string }
  | { status: 'denied' }
  | { status: 'not_found' }
  | null;

interface PaperEmbedContext {
  ref: string;
  mode: string;
}

interface PickerSource {
  id: string;
  label: string;
  icon?: string;
  mode?: string;
}

interface SearchHit {
  ref: string;
  label: string;
  kind?: string;
  detail?: string;
}

// --- read-only card ----------------------------------------------------------

function fact(label: string, value: string): HTMLElement {
  const row = document.createElement('div');
  row.style.cssText = 'display:flex;gap:0.5rem;font-size:0.85rem;line-height:1.5;';
  const k = document.createElement('span');
  k.textContent = label;
  k.style.cssText = 'color:#6b7280;min-width:5.5rem;flex:0 0 auto;';
  const v = document.createElement('span');
  v.textContent = value; // text node — XSS-safe
  v.style.cssText = 'color:#111827;font-weight:500;';
  row.append(k, v);
  return row;
}

function renderCard(host: HTMLElement, row: CandidateRow, p: Parsed): void {
  host.replaceChildren();
  const card = document.createElement('div');
  card.style.cssText = 'padding:0.5rem 0.25rem;display:flex;flex-direction:column;gap:0.25rem;';

  const name = document.createElement('div');
  name.textContent = row.name || p.candidateId;
  name.style.cssText = 'font-size:1rem;font-weight:600;color:#111827;';
  card.appendChild(name);

  const office = officeLabel(row);
  if (office) card.appendChild(fact('Office', office));
  if (row.party_affiliation) card.appendChild(fact('Party', row.party_affiliation));
  if (row.cycle != null) card.appendChild(fact('Cycle', String(row.cycle)));
  if (row.principal_campaign_committee)
    card.appendChild(fact('Committee', row.principal_campaign_committee));
  card.appendChild(fact('Candidate ID', row.candidate_id || p.candidateId));

  host.appendChild(card);
}

function renderMessage(host: HTMLElement, text: string): void {
  host.replaceChildren();
  const el = document.createElement('div');
  el.textContent = text;
  el.style.cssText = 'padding:0.5rem 0.25rem;color:#6b7280;font-size:0.9rem;';
  host.appendChild(el);
}

// --- Paper embed provider (paper import()s this bundle + registers it) --------

const provider = {
  kind: 'libfec-candidate',

  /** Claim a stored ref (checked before paper's native .json resolution). */
  matchRef(ref: string): boolean {
    return REF_RE.test(ref);
  },

  /** Claim a pasted same-origin candidate page URL → the reordered ref. */
  matchUrl(url: URL): string | null {
    const m = URL_RE.exec(url.pathname);
    if (!m) return null;
    const [, db, cid] = m;
    if (db === undefined || cid === undefined) return null;
    return `/-/libfec/candidate/${db}/${cid}`;
  },

  /** Inline-pill identity. Leak discipline: denied/missing never yield a label. */
  async resolve(ref: string): Promise<ResolveResult> {
    const p = parseRef(ref);
    if (!p) return { status: 'not_found' };
    const row = await fetchCandidate(p);
    if (row === 'denied') return { status: 'denied' }; // never a label here
    if (!row) return { status: 'not_found' };
    return {
      status: 'ok',
      kind: 'libfec-candidate',
      label: row.name || p.candidateId,
      href: pageHref(p, row.cycle),
      icon: VCARD_ICON,
    };
  },

  /** Block card body. Paper owns the header; we fill `host` with the card. */
  mount(host: HTMLElement, ctx: PaperEmbedContext): () => void {
    let cancelled = false;
    const p = parseRef(ctx.ref);
    if (!p) {
      renderMessage(host, 'Invalid candidate reference');
      return () => {};
    }
    renderMessage(host, 'Loading candidate…');
    void (async () => {
      const row = await fetchCandidate(p);
      if (cancelled) return;
      if (row === 'denied') {
        renderMessage(host, "You don't have access to this candidate");
        return;
      }
      if (!row) {
        renderMessage(host, 'Candidate not found');
        return;
      }
      renderCard(host, row, p);
    })();
    return () => {
      cancelled = true;
      host.replaceChildren();
    };
  },

  /** Browsable `/`-menu source — mirrored by `sources` in paper.py so it shows
   *  before this bundle loads. */
  picker(): PickerSource {
    return { id: 'libfec-candidate', label: 'FEC candidate', icon: 'person-vcard', mode: 'block' };
  },

  /**
   * Viewer-filtered candidates matching `q`, fanned out across the databases
   * the viewer can see. Datasette's per-table permissions gate each db, so a
   * db/table the viewer can't read just yields no hits (no leak).
   */
  async search(q: string, limit: number): Promise<SearchHit[]> {
    const query = (q || '').trim();
    if (!query) return [];
    let dbs: string[];
    try {
      const res = await fetch('/-/databases.json', {
        headers: { Accept: 'application/json' },
      });
      if (!res.ok) return [];
      const list = (await res.json()) as Array<{ name?: string }>;
      dbs = list.map((d) => d.name).filter((n): n is string => !!n && !n.startsWith('_'));
    } catch {
      return [];
    }

    const perDb = Math.max(limit, 5);
    const hits: SearchHit[] = [];
    await Promise.all(
      dbs.map(async (db) => {
        const url =
          `/${encodeURIComponent(db)}/libfec_candidates.json` +
          `?name__contains=${encodeURIComponent(query)}` +
          `&_sort=name&_size=${perDb}&_shape=array`;
        let res: Response;
        try {
          res = await fetch(url, { headers: { Accept: 'application/json' } });
        } catch {
          return;
        }
        if (!res.ok) return; // 403/404 (no perm / no table) → skip, no leak
        let j: unknown;
        try {
          j = await res.json();
        } catch {
          return;
        }
        const seen = new Set<string>();
        for (const row of rowsOf(j)) {
          const cid = row.candidate_id;
          if (!cid || seen.has(cid)) continue; // de-dup across cycles
          seen.add(cid);
          const office = officeLabel(row);
          hits.push({
            ref: `/-/libfec/candidate/${encodeURIComponent(db)}/${encodeURIComponent(cid)}`,
            kind: 'libfec-candidate',
            label: row.name || cid,
            detail: [office, row.party_affiliation].filter(Boolean).join(' · '),
          });
        }
      })
    );

    const qLow = query.toLowerCase();
    hits.sort((a, b) => {
      const al = a.label.toLowerCase();
      const bl = b.label.toLowerCase();
      const aStarts = al.startsWith(qLow) ? 0 : 1;
      const bStarts = bl.startsWith(qLow) ? 0 : 1;
      return aStarts - bStarts || al.localeCompare(bl);
    });
    return hits.slice(0, limit);
  },
};

export default provider;

// Seed the deterministic paper document the `paper` shot screenshots, over
// paper's real create API. Returns an `ids` object (`{ paperDocId }`) the shot
// reads via its `url(ids)`. Only creates anything when the paper shot is in the
// run set — the server is booted with datasette-paper then.
import { PAPER, DB_NAME, PAPER_ACTOR, PAPER_EMBED_CANDIDATES } from './config.mjs';
import { signActorCookie } from './cookie.mjs';

// A block embed is a fenced ```paper-embed code block whose body is
// {config, mode, ref}; paper renders it via the provider that owns the ref's
// prefix (libfec, here), mounting our read-only FEC-candidate card.
function embedBlock(candidateId) {
  const body = JSON.stringify({
    config: {},
    mode: 'block',
    ref: `/-/libfec/candidate/${DB_NAME}/${candidateId}`,
  });
  return '```paper-embed\n' + body + '\n```';
}

export async function seed(needsPaper) {
  if (!needsPaper) return {};

  const blocks = PAPER_EMBED_CANDIDATES.map(embedBlock).join('\n\n');
  const content =
    '# 2024 Ohio Senate\n\n' +
    'The two campaigns in the race, embedded as live FEC-candidate cards:\n\n' +
    blocks +
    '\n';

  const resp = await fetch(`${PAPER}/api/docs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Cookie: `ds_actor=${signActorCookie(PAPER_ACTOR)}`,
    },
    body: JSON.stringify({ name: '2024 Ohio Senate', content }),
  });
  if (!resp.ok) {
    throw new Error(`create paper doc → ${resp.status}: ${await resp.text()}`);
  }
  const { id } = await resp.json();
  return { paperDocId: id };
}

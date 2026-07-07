"""Throwaway actor display names for the screenshot script.

Loaded via ``datasette --plugins-dir`` from shots/server.mjs (only for the
``paper`` shot) so the seeded paper document shows a friendly author name
("Alice Ada") instead of the raw ``alice`` id in its header. NOT shipped —
dev/screenshot use only.
"""

from datasette import hookimpl

DISPLAY_NAMES = {
    "alice": "Alice Ada",
    "bob": "Bob Babbage",
    "carol": "Carol Shaw",
}


@hookimpl
def actors_from_ids(actor_ids):
    out = {}
    for aid in actor_ids:
        sid = str(aid)
        actor = {"id": sid}
        if sid in DISPLAY_NAMES:
            actor["name"] = DISPLAY_NAMES[sid]
        out[sid] = actor
    return out

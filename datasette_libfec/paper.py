"""datasette-paper integration: a ``paper_embed_provider`` so an FEC candidate
can be referenced/embedded inside a paper document.

Paper resolves and renders embeds **entirely client-side** (see
``frontend/src/paper_embed.ts``): the bundle claims
``/-/libfec/candidate/{db}/{candidate_id}`` refs, fetches its own data from
Datasette's native table JSON API (``/{db}/libfec_candidates.json``) with the
viewer's cookie, and owns leak discipline. The backend's only job is to
*describe* this provider — its stable ``kind``, the ref namespace it owns, the
``/``-menu source, and where its JS/CSS bundle lives — so paper can lazy-load
that bundle on demand. There is no server-side resolve/render/search.

Why the ref is reordered (``/-/libfec/candidate/{db}/{id}``) rather than the
literal page path (``/{db}/-/libfec/candidate/{id}``): every libfec URL leads
with a *variable* ``{database}`` segment, and paper claims a stored ref for
lazy-loading by ``ref.startswith(prefix)`` (server-side ``provider_for_ref`` +
the frontend manifest). A literal-path ref could therefore never sit under a
static ``ref_prefix``, so existing embeds would not re-inject this bundle on
page reload. Reordering puts the libfec namespace first, giving a stable static
prefix; the bundle's ``matchUrl`` transforms the real pasted page URL into this
ref, and resolve/mount rebuild the real page URL for the pill/card link.

The hook is a no-op unless datasette-paper is installed (it owns the
``paper_embed_provider`` spec); when absent, nothing calls this.
"""

from __future__ import annotations

from datasette import hookimpl
from datasette_vite import vite_css_urls, vite_js_urls

# Vite entry that defines the read-only card + default-exports the paper provider.
_PAPER_EMBED_ENTRY = "src/paper_embed.ts"


class LibfecCandidateEmbedProvider:
    """Describes the FEC-candidate embed for datasette-paper's editor.

    ``kind`` must equal the bundle's default-exported provider ``kind``. The
    actual resolve/render/search all live in that bundle.
    """

    kind = "libfec-candidate"
    label = "FEC candidate"
    # Stored refs are ``/-/libfec/candidate/{db}/{candidate_id}`` — all under
    # this namespace. Lets paper inject our bundle for a doc's embeds before
    # running our matchRef (see the module docstring for why it's reordered).
    ref_prefixes = ["/-/libfec/candidate/"]
    # Mirrors the bundle's picker() source so the `/` menu can list it before
    # the bundle loads; picking it injects the bundle, then runs its search().
    sources = [
        {
            "id": "libfec-candidate",
            "label": "FEC candidate",
            "icon": "person-vcard",
            "mode": "block",
        },
    ]

    def frontend_assets(self, datasette):
        # Paper's embed loader does `import(url)` over a list of *string* URLs
        # (see embedProviders.ts); vite_js_urls returns `{"url", "module"}`
        # dicts (shaped for a script-tag consumer), so unwrap to the bare URL.
        # vite_css_urls already returns plain href strings.
        js = vite_js_urls(
            datasette=datasette,
            entrypoint=_PAPER_EMBED_ENTRY,
            plugin_package="datasette_libfec",
        )
        return {
            "js": [u["url"] if isinstance(u, dict) else u for u in js],
            "css": vite_css_urls(
                datasette=datasette,
                entrypoint=_PAPER_EMBED_ENTRY,
                plugin_package="datasette_libfec",
            ),
        }


@hookimpl
def paper_embed_provider(datasette):
    return LibfecCandidateEmbedProvider()

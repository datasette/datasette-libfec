#!/usr/bin/env bash
# Build the deterministic demo database the doc screenshots run against.
#
# Unlike the other plugins in the screenshot family (which seed via internal
# plugin APIs), datasette-libfec browses real FEC data, so the "seed" is a small
# fixed SQLite file produced by `libfec export`. We pin a marquee 2024 race plus
# a couple of big PACs, cover-only (no itemizations) so it stays small and fast.
#
# Network + the libfec cache are used the first time; subsequent runs are quick.
# Output is NOT committed (see frontend/.gitignore); regenerate with `just shots-fixture`.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$HERE/shot-data/libfec.db}"
mkdir -p "$(dirname "$OUT")"

# Keep downloaded .fec files around so re-runs don't re-fetch.
export LIBFEC_CACHE_DIRECTORY="${LIBFEC_CACHE_DIRECTORY:-$HOME/.cache/libfec}"
mkdir -p "$LIBFEC_CACHE_DIRECTORY"

echo "Building fixture → $OUT"

# 2024 Ohio Senate: Sherrod Brown (D, incumbent) vs Bernie Moreno (R) and the
# rest of the field — gives candidate, contest, and filing pages real content.
echo "  • OH-S 2024 (candidates + committees + F3 covers)"
libfec export OH-S --cycle 2024 --cover-only --clobber -o "$OUT"

# Big 2024 PACs — committee pages with F3X covers.
echo "  • Fairshake (C00835959) — crypto super PAC"
libfec export C00835959 --cycle 2024 --cover-only -o "$OUT"
echo "  • Senate Majority PAC (C00484642)"
libfec export C00484642 --cycle 2024 --cover-only -o "$OUT"

echo "Done. Tables:"
sqlite3 "$OUT" "SELECT '  ' || name FROM sqlite_master WHERE type='table' AND name LIKE 'libfec%';"

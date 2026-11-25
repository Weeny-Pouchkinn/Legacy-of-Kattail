# Railway jump repair - 2026-11-25

Removed the two impossible level-3 routes to province 20841 from
map/railways.txt: former lines 1308 (19461-20841) and 1309 (20839-20841).
Province 20841 has no shared land border in the current provinces.bmp, so no
contiguous land route can preserve either connection without changing geography.
The existing mainland links 19354-20839 and 19362-19461, and all other railway
links/levels, are preserved.
No province, hub, VP, history, adjacency or geometry was changed.

The repository's cached modding_documentation/province_adjacencies.csv still
lists historical neighbors for 20841. It is stale for these endpoints. The repair
uses the actual current province bitmap and the painter's native adjacency/rules.
Do not restore the deleted routes from that cached reference.

Files: map/railways.txt; this README.md and audit.json; painter README.md/MODLOG.md;
agent_memory CURRENT_STATUS.md/DECISIONS.md and terrain_refinement/README.md.
No new or renamed identifiers; removed only the above two native railway edges.
Audit includes exact hashes and original-byte backup path.

Validation:

- python -B tools/validate_map.py: passed, 21,515 provinces, 20,926 state-assigned
  provinces, 413 strategic regions, no X crossings.
- Read-only native RailwayStore probe: exact expected two-line deletion;
  removed edge set is exactly the two requested jumps, no new edges, all other
  link levels unchanged, mainland link retained, province 20841 has zero valid
  land neighbors. No drafts written. Counts recorded in audit.json.
- git diff --check, git diff --stat and the complete railway diff reviewed.

The preceding terrain refinement's protected railways hash and validator output
are historical snapshots from before this explicitly requested repair. Current
map validation passes; the former two-jump warning is resolved.

No game launch performed. No further implementation is pending for this repair.

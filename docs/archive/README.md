# Historical evidence and consolidation anchors

The current worktree was intentionally reduced on 2026-09-08 so that completed experiments, obsolete workflows and stale `next_action` files no longer compete with current authority.

No scientific evidence was erased from Git history.

## Canonical pre-cleanup snapshot

Full pre-consolidation `factorlab-overnight-open-lab` tree:

`21ddcceb79929f5cd318ac5b8aa4579539f70dd7`

Use this commit to recover historical:

- original overnight-open experiments;
- Gap-Fill V2 / V2.1 / cross-index protocols, receipts and runners;
- offshore-China branches;
- R2/R3/R5/R6/R7 Stage-1 runners, tests, workflows and receipts;
- old cloud/local handoffs;
- completed GitHub Actions workflow definitions;
- legacy development data packs not needed by the active R1 path.

Those artifacts remain authoritative **only for reconstructing their own historical frozen experiments**. Any embedded `current_status`, `next_action`, pending handoff or production statement is superseded for repository-wide action by the current root authority files.

## Retired temporary repository

Original one-commit state of `staryocean0/factorlab-overnight-gap-fill-repeat-2026`:

`e160390c8f9b700227b0c0203926c04bdce9f602`

That repository contained only a README, one manifest and two repeat-only parquet inputs. The two parquet Git blobs were already byte-identical in the canonical repository:

- annotated panel blob: `cd8b702f4fd28abb6d2f62209925ee4065a33087`;
- CSI1000 1m blob: `0512ad28fa9150d55d19984ab22cf484ecab596f`.

The canonical manifest superseded the temporary manifest only by recording the later user-authorized public placement. The scientific role stayed `repeat_only_not_fresh` and production authority stayed false.

The single retained copy is now under:

`../../archive/data/gap_fill_repeat_2026/`

## Restore policy

Do not restore a historical file merely because a future agent cannot find it in the current tree.

Restore or copy a legacy artifact into the active surface only when:

1. a new explicitly authorized identity genuinely depends on it;
2. the artifact's frozen role is still scientifically valid for that identity; and
3. restoring it will not create a second current authority or duplicate data path.

For ordinary historical inspection, read the anchored commit directly instead of repopulating the current tree.

# Governance: live pointers versus frozen evidence

Live pointers are current_authority_v1.json, overnight_factor_product_registry_v1.json, component_bindings_v1.json and repository_lifecycle_v1.json. The append-only overnight_reusable_blackbox_query_ledger_v1.json is reconciled against each public compact receipt.

Other original governance files are retained freeze-time evidence unless explicitly bound as a current component or the unopened Gap-Fill date gate. A parent state that once said “waiting for validation” remains an as-of snapshot; its completed child in current authority supersedes that execution instruction. Never edit an old state hash just to update such historical text.

See `docs/CURRENT_STATUS.md` for current decisions, `docs/WHITEPAPER.md` for scope and `docs/maintenance/20260912_reconciliation.json` for historical path resolution. Closed/insufficient downstream identities remain closed; historical blocks are not independent OOS.

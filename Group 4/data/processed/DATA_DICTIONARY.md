# Derived files

All outputs are rebuilt by `scripts/build_dol_hs6.py`. Year defaults to 2025.

| File stem | Row meaning |
| --- | --- |
| `dol_forced_labour_country_goods` | One country-good record with an FL interval active in the selected year |
| `dol_forced_labour_hs6_candidates` | Country-good-source mapping-HS6 candidate; potentially multiple rows per trade key |
| `dol_country_hs6_screening` | Unique ISO2 country and HS6 candidate; intended future join table |
| `dol_mapping_review` | Missing mapping, invalid-for-HS2022 prefix, or broad-prefix source mapping requiring review |
| `dol_mapping_coverage` | One row per active country-good pair, including those with no candidates |
| `validation_summary` | Counts and unresolved goods for the run |

`country_isocode` is the DOL ISO2 identifier. `good` / `dol_goods` preserve DOL product names. `fl` preserves the listing interval. `source_mapping_id` identifies the raw DOL mapping row, and `source_hts_code` preserves its punctuation and leading zeroes. `hs6` is a six-character string validated against HS2022. `hs6_description` is the UN reference label. `analysis_year` controls interval filtering; it is not the download year. `hs_revision` records the target classification.

Mapping methods: `exact_hs6` is a six-digit source code; `hts_prefix_to_hs6` collapses a longer code; `broad_prefix_expansion` expands a shorter prefix. All are candidates. `needs_scope_review=no` for exact-six source mappings does not verify revision equivalence or certify a shipment.

`screening_candidate=1` means a candidate link exists. `has_broad_expansion=1` means at least one contributing mapping expanded a broad prefix. `mapping_coverage=has_candidates` is not a claim of complete mapping coverage. `review_items` counts only missing/no-match/broad-prefix issues; longer-code aggregation still needs scope assessment even if this count is zero. The summary separately counts unmapped pairs. Absence of a candidate is unknown, not a zero-risk observation.

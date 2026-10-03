# US DOL / ILAB raw data

Downloaded directly from the US Department of Labor on 2026-10-03.

| Files | Official source | Records |
| --- | --- | ---: |
| `ILAB_ImportWatch_Core_Data.zip` / `.csv` | https://dataportal.dol.gov/datasets/10295 | 446 |
| `ILAB_ImportWatch_Goods_HS.zip` / `.csv` | https://dataportal.dol.gov/datasets/10294 | 300 |

ZIP files are original downloads. CSV files are byte-for-byte copies of the CSV members, with descriptive filenames. `sources.json` records download URLs, retrieval times, original member names and SHA-256 checksums. Both archive members have 2025-09-24 timestamps; that is not a claim that the observations measure calendar-year 2025.

## Meaning and preparation

- Core data covers multiple labour exploitation types. `fl` is the forced-labour listing date range; `cl` is child labour and `fcl` is forced/indentured child labour. Do not treat every record as forced labour or merge these categories silently. Interpret starting/ending years against the intended analysis year before filtering.
- Goods HS maps DOL product descriptions (`good`) to `hts_code`. Codes have mixed lengths. Read them as strings to preserve leading zeroes.
- This is the source mapping, **not a completed HS6 dataset**. For codes with at least six digits, removing dots and taking six digits gives a candidate HS6 prefix. Shorter codes need expansion using the correct HS revision and a documented classification table. Do not zero-pad broad headings to manufacture six-digit codes.
- Confirm the SingStat data's classification/revision before building the HS6 join. Keep the source HTS code and mapping method in derived data; review unmatched goods and many-to-many joins. Save transformed outputs outside `raw`.
- DOL flags country-good risks, not proof that a specific shipment used forced labour. See https://www.dol.gov/agencies/ilab/importwatch for scope and methodology.
- These raw archives may differ in coverage from the latest TVPRA List of Goods. The separate 2024 List of Goods Excel download returned Access Denied and is not included.

## Coverage observed in these downloads

The goods mapping contains IDs 1 through 300, ending at Soap when sorted numerically by ID. Nineteen goods with FL history in the core file have no mapping in this archive. This is a coverage limitation of the downloaded material; the package does not claim it is the complete current DOL list. Raw sources are preserved unchanged.

Derived HS2022 screening candidates and all mapping gaps are in `../../processed`. The main project README explains how they were built. This is a standalone handoff, with no Git setup required.

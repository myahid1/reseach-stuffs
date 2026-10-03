# Group 4: US DOL forced-labour data and HS6 screening

Standalone handoff prepared 4 October 2026. Unzip this folder and keep its structure. No Git is needed. Raw downloads, runnable code, an executed notebook, and derived CSVs are included.

## Start here

- Open `notebooks/02_dol_data_cleaning.ipynb` for the workflow and saved results.
- `data/raw/us_dol` contains original DOL ZIPs, unchanged extracted CSVs, and source/checksum records.
- `data/raw/reference` contains the official UN Comtrade HS2022 classification and provenance.
- `data/processed/dol_country_hs6_screening_2025.csv` is the deduplicated country/HS6 candidate table for a future trade-data join.
- `data/processed/dol_mapping_review_2025.csv` and `dol_mapping_coverage_2025.csv` show gaps and broad mappings needing review.

## Result and limits

The downloaded DOL snapshot has 446 country-good records and 300 mapping rows. Filtering its `fl` listing intervals for 2025 leaves **119 country-good pairs**. **91** have HS2022 candidates; **28** remain unmapped. There are **3,156 unique country/HS6 candidate pairs**, spanning **832 HS6 codes**.

These are screening candidates, not a fully validated forced-labour HS6 database. The DOL mapping archive has IDs 1–300 and lacks mappings for 19 goods with FL history. Two active country-good mapping records also have source prefixes absent from HS2022. Broad heading expansion can include products beyond a DOL good, while collapsing detailed HTS codes to HS6 can widen coverage. Review the provenance before interpreting trade values. An unmatched trade record must not be labelled risk-free.

**HS2022 is an explicit working assumption.** The group's SingStat files were not available, so their classification and country identifiers have not been checked and no trade data has been merged. If those files use SITC rather than HS, or another HS revision, use an appropriate concordance first.

Both DOL CSV members carry 24 September 2025 timestamps. They include historical listing intervals and are not measurements of labour incidence or trade flows during 2025. The download's coverage is not asserted to match the latest TVPRA report. The separately linked 2024 TVPRA Excel file was inaccessible and is not included.

## Method

1. Verify raw-file SHA-256 checksums. Read identifiers as strings.
2. Keep `fl` intervals active in the analysis year; do not include `cl`-only or `fcl`-only records. An open interval such as `2009-` remains active. Treat a stated ending year as the removal year, excluded. This boundary choice does not affect the supplied 2025 output; the only closed FL intervals end in 2015 and 2017.
3. Match the DOL `good` text exactly to the supplied goods mapping, without guessed aliases.
4. Remove dots from source HTS codes. Validate six-digit codes or the first six digits of longer codes against the UN HS2022 list. Expand shorter prefixes only to existing HS2022 codes, retaining the source code and marking broad scope for review. No code is invented by zero-padding. Existence in HS2022 does not establish that a historical tariff code kept the same meaning across revisions.
5. Preserve every source mapping in the detailed candidate file; deduplicate to country/HS6 only in the screening table. Save all unresolved entries separately.

## Run on Windows

Open this `Group 4` folder in VS Code. In its terminal:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/build_dol_hs6.py --year 2025
```

For the notebook, choose **Select Kernel → Python Environments → `.venv`**. Activation is optional; the commands above use the environment directly and require no execution-policy changes. A local environment has already been created on the original machine; it is deliberately excluded from the ZIP because environments are not portable.

The build script itself uses only Python's standard library and can also run as `python scripts/build_dol_hs6.py`. It rebuilds the selected year's derived files using the included raw snapshot without network access. To reproduce the tested package versions, install `requirements-lock.txt` instead of `requirements.txt` with Python 3.13 on Windows.

## Use the screening table safely

```python
screening = pd.read_csv(
    "data/processed/dol_country_hs6_screening_2025.csv",
    dtype={"country_isocode": "string", "hs6": "string"},
)
# Only after confirming trade classification is HS2022 and country codes are ISO2:
joined = trade.merge(screening, on=["country_isocode", "hs6"],
                     how="left", validate="many_to_one")
```

Use the **origin/producing country** relevant to DOL's country-good flag; a consignment or trading-partner country may differ for re-exports. Keep unmatched flags missing/unknown. Do not sum trade values after joining the detailed provenance table, which can contain multiple rows per country/HS6. Import CSVs with HS6 as text; opening directly in Excel can strip leading zeroes.

## Sources

- US DOL / ILAB core: https://dataportal.dol.gov/datasets/10295
- US DOL / ILAB goods mapping: https://dataportal.dol.gov/datasets/10294
- UN Comtrade HS2022: https://comtradeapi.un.org/files/v1/app/reference/H6.json
- DOL scope: https://www.dol.gov/agencies/ilab/importwatch

Cite US DOL/ILAB for labour-risk and source mapping data, and UN Comtrade for the classification. A DOL country-good listing does not establish that a particular shipment was made with forced labour.

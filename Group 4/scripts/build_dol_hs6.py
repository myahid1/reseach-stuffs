"""Build auditable HS2022 screening candidates from preserved DOL downloads.

Standard library only. Run from any working directory. No network requests.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict, Counter

ROOT = Path(__file__).resolve().parents[1]


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def active_in_year(value, year):
    """Ending year is treated as removal year (exclusive); blanks are not FL."""
    value = value.strip()
    if not value:
        return False
    match = re.fullmatch(r"(\d{4})-(\d{4})?", value)
    if not match:
        raise ValueError(f"Unrecognised listing interval: {value!r}")
    start, end = match.groups()
    return int(start) <= year and (not end or year < int(end))


def build(year=2025):
    raw = ROOT / "data" / "raw"
    out = ROOT / "data" / "processed"
    out.mkdir(parents=True, exist_ok=True)
    # Detect accidental source edits before deriving any outputs.
    for record in json.loads((raw / "us_dol" / "sources.json").read_text()):
        for file_key, hash_key in [("file", "sha256"), ("extracted_file", "extracted_sha256")]:
            assert hashlib.sha256((raw / "us_dol" / record[file_key]).read_bytes()).hexdigest() == record[hash_key]
    reference_path = raw / "reference" / "UN_Comtrade_H6_HS2022.json"
    reference_meta = json.loads((raw / "reference" / "sources.json").read_text())
    assert hashlib.sha256(reference_path.read_bytes()).hexdigest() == reference_meta["sha256"]
    reference = json.loads(reference_path.read_text(encoding="utf-8-sig"))
    assert reference["classCode"] == "H6" and reference["className"] == "HS2022"
    codes = {r["id"]: r["text"] for r in reference["results"] if r["aggrlevel"] == 6}
    assert all(re.fullmatch(r"\d{6}", code) for code in codes)
    core = read_csv(raw / "us_dol" / "ILAB_ImportWatch_Core_Data.csv")
    goods = read_csv(raw / "us_dol" / "ILAB_ImportWatch_Goods_HS.csv")
    assert len({(r["country_isocode"], r["good"]) for r in core}) == len(core)
    assert len({r["id"] for r in goods}) == len(goods)
    active = [{**r, "analysis_year": year} for r in core if active_in_year(r["fl"], year)]
    write_csv(out / f"dol_forced_labour_country_goods_{year}.csv", active, list(core[0]) + ["analysis_year"])
    source_by_good = defaultdict(list)
    for r in goods:
        source_by_good[r["good"]].append(r)
    candidates, review, coverage = [], [], []
    for row in active:
        base = {k: row[k] for k in ("country", "country_isocode", "good", "fl")}
        base.update(analysis_year=year, hs_revision="HS2022")
        mappings = source_by_good[row["good"]]
        found = set()
        issue_count = 0
        if not mappings:
            review.append({**base, "source_mapping_id": "", "source_hts_code": "", "reason": "no_mapping_in_download"})
            issue_count += 1
        for mapping in mappings:
            source = {**base, "source_mapping_id": mapping["id"], "source_hts_code": mapping["hts_code"]}
            digits = mapping["hts_code"].replace(".", "").strip()
            if not digits.isdigit():
                matches, method = [], "invalid_source_code"
            elif len(digits) >= 6:
                matches = [digits[:6]] if digits[:6] in codes else []
                method = "exact_hs6" if len(digits) == 6 else "hts_prefix_to_hs6"
            else:
                matches = sorted(code for code in codes if code.startswith(digits))
                method = "broad_prefix_expansion"
            if not matches:
                review.append({**source, "reason": "no_valid_HS2022_match"})
                issue_count += 1
            elif method == "broad_prefix_expansion":
                review.append({**source, "reason": "broad_prefix_expansion_needs_scope_review"})
                issue_count += 1
            for code in matches:
                candidates.append({**source, "hs6": code, "hs6_description": codes[code], "mapping_method": method,
                                   "needs_scope_review": "yes" if method != "exact_hs6" else "no",
                                   "status": "screening_candidate_not_shipment_evidence"})
                found.add(code)
        coverage.append({**base, "source_mapping_rows": len(mappings), "candidate_hs6_count": len(found),
                         "review_items": issue_count, "mapping_coverage": "has_candidates" if found else "unmapped"})
    candidate_fields = list(base) + ["source_mapping_id", "source_hts_code", "hs6", "hs6_description", "mapping_method", "needs_scope_review", "status"]
    candidates.sort(key=lambda r: (r["country_isocode"], r["good"], r["hs6"], r["source_mapping_id"]))
    write_csv(out / f"dol_forced_labour_hs6_candidates_{year}.csv", candidates, candidate_fields)
    write_csv(out / f"dol_mapping_review_{year}.csv", review, list(base) + ["source_mapping_id", "source_hts_code", "reason"])
    write_csv(out / f"dol_mapping_coverage_{year}.csv", coverage, list(base) + ["source_mapping_rows", "candidate_hs6_count", "review_items", "mapping_coverage"])
    # One row per country/HS6 avoids multiplying trade values on an ordinary join.
    grouped = defaultdict(list)
    for row in candidates:
        grouped[(row["country_isocode"], row["hs6"])].append(row)
    screening = []
    for (country, code), group in sorted(grouped.items()):
        screening.append({"country_isocode": country, "country": group[0]["country"], "hs6": code,
                          "hs_revision": "HS2022", "analysis_year": year,
                          "dol_goods": " | ".join(sorted({r["good"] for r in group})),
                          "mapping_methods": " | ".join(sorted({r["mapping_method"] for r in group})),
                          "has_broad_expansion": int(any(r["mapping_method"] == "broad_prefix_expansion" for r in group)),
                          "screening_candidate": 1})
    screening_fields = ["country_isocode", "country", "hs6", "hs_revision", "analysis_year", "dol_goods", "mapping_methods", "has_broad_expansion", "screening_candidate"]
    write_csv(out / f"dol_country_hs6_screening_{year}.csv", screening, screening_fields)
    assert all(r["hs6"] in codes and len(r["hs6"]) == 6 for r in screening)
    assert len({(r["country_isocode"], r["hs6"]) for r in screening}) == len(screening)
    assert len(coverage) == len(active)
    summary = dict(analysis_year=year, hs_revision="HS2022", raw_core_rows=len(core), raw_mapping_rows=len(goods),
                   hs2022_reference_codes=len(codes), active_fl_country_good_pairs=len(active),
                   mapped_country_good_pairs=sum(r["candidate_hs6_count"] > 0 for r in coverage),
                   unmapped_country_good_pairs=sum(r["candidate_hs6_count"] == 0 for r in coverage),
                   candidate_detail_rows=len(candidates), unique_country_hs6_candidates=len(screening),
                   unique_hs6_candidates=len({r["hs6"] for r in screening}),
                   review_counts=dict(Counter(r["reason"] for r in review)),
                   unmapped_goods=sorted({r["good"] for r in coverage if not r["candidate_hs6_count"]}),
                   warning="Partial historical DOL snapshot; screening candidates, not a complete validated risk universe. Absence is not zero risk.")
    (out / f"validation_summary_{year}.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2025)
    args = parser.parse_args()
    print(json.dumps(build(args.year), indent=2))

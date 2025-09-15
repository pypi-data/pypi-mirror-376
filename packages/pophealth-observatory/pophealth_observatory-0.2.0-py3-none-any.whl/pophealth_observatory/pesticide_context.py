"""Pesticide context integration scaffolding.

This module provides early-stage utilities for linking NHANES pesticide / metabolite
laboratory analytes to external narrative and structured sources. It will evolve into
an ingestion + retrieval layer supporting RAG pipelines.

Current capabilities (MVP):
  - Load curated analyte reference CSV (data/reference/pesticide_reference.csv)
  - Load source registry YAML (pesticide_sources.yml)
  - Simple lookup by analyte name or CAS RN
  - Basic fuzzy suggestions when no direct match

Planned (future iterations):
  - Automated source fetching & text extraction
  - Chemical entity recognition & snippet generation
  - Embedding index construction and semantic retrieval
  - RAG-style context assembly for Q&A

"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore


DATA_REFERENCE_DIR = Path("data/reference")
REFERENCE_CSV = DATA_REFERENCE_DIR / "pesticide_reference.csv"
SOURCES_YAML = DATA_REFERENCE_DIR / "pesticide_sources.yml"


@dataclass
class PesticideAnalyte:
    analyte_name: str
    parent_pesticide: str
    metabolite_class: str
    cas_rn: str
    parent_cas_rn: str | None
    epa_pc_code: str | None
    pubchem_cid: str | None
    typical_matrix: str | None
    unit: str | None
    nhanes_lod: str | None
    first_cycle_measured: str | None
    last_cycle_measured: str | None
    current_measurement_flag: bool
    notes: str | None

    def to_dict(self) -> dict[str, Any]:  # convenience
        return {
            "analyte_name": self.analyte_name,
            "parent_pesticide": self.parent_pesticide,
            "metabolite_class": self.metabolite_class,
            "cas_rn": self.cas_rn,
            "parent_cas_rn": self.parent_cas_rn,
            "epa_pc_code": self.epa_pc_code,
            "pubchem_cid": self.pubchem_cid,
            "typical_matrix": self.typical_matrix,
            "unit": self.unit,
            "nhanes_lod": self.nhanes_lod,
            "first_cycle_measured": self.first_cycle_measured,
            "last_cycle_measured": self.last_cycle_measured,
            "current_measurement_flag": self.current_measurement_flag,
            "notes": self.notes,
        }


def _normalize(s: str) -> str:
    """Normalize strings for loose matching.

    Previous implementation only removed hyphens/underscores which failed a test
    expecting partial matches for names containing commas/apostrophes (e.g., "p,p'-DDE").
    We now collapse to lowercase alphanumerics to make substring suggestion logic
    more robust for metabolite names.
    """
    import re  # local import to avoid global cost

    return re.sub(r"[^a-z0-9]", "", s.lower())


def load_analyte_reference(path: Path = REFERENCE_CSV) -> list[PesticideAnalyte]:
    if not path.exists():  # pragma: no cover
        raise FileNotFoundError(f"Reference CSV not found: {path}")
    records: list[PesticideAnalyte] = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            records.append(
                PesticideAnalyte(
                    analyte_name=row.get("analyte_name", ""),
                    parent_pesticide=row.get("parent_pesticide", ""),
                    metabolite_class=row.get("metabolite_class", ""),
                    cas_rn=row.get("cas_rn", ""),
                    parent_cas_rn=row.get("parent_cas_rn") or None,
                    epa_pc_code=row.get("epa_pc_code") or None,
                    pubchem_cid=row.get("pubchem_cid") or None,
                    typical_matrix=row.get("typical_matrix") or None,
                    unit=row.get("unit") or None,
                    nhanes_lod=row.get("nhanes_lod") or None,
                    first_cycle_measured=row.get("first_cycle_measured") or None,
                    last_cycle_measured=row.get("last_cycle_measured") or None,
                    current_measurement_flag=(
                        row.get("current_measurement_flag", "").strip().lower() == "true"
                    ),
                    notes=row.get("notes") or None,
                )
            )
    return records


def load_source_registry(path: Path = SOURCES_YAML) -> list[dict[str, Any]]:
    if not path.exists():  # pragma: no cover
        raise FileNotFoundError(f"Sources YAML not found: {path}")
    if yaml is None:  # pragma: no cover
        raise RuntimeError("pyyaml not installed; add to extras to use source registry")
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data if isinstance(data, list) else []


def find_analyte(query: str, analytes: list[PesticideAnalyte]) -> PesticideAnalyte | None:
    qn = _normalize(query)
    # Direct cas or name match
    for a in analytes:
        if qn in {_normalize(a.analyte_name), _normalize(a.cas_rn)}:
            return a
    # Parent pesticide match
    for a in analytes:
        if qn == _normalize(a.parent_pesticide):
            return a
    return None


def suggest_analytes(partial: str, analytes: list[PesticideAnalyte], limit: int = 5) -> list[str]:
    p = _normalize(partial)
    scored = []
    for a in analytes:
        name_n = _normalize(a.analyte_name)
        if p in name_n:
            scored.append((len(name_n) - len(p), a.analyte_name))
    scored.sort(key=lambda x: x[0])
    return [s for _, s in scored[:limit]]


def get_pesticide_info(query: str) -> dict[str, Any]:
    """Lookup helper returning analyte metadata + suggestions if not found."""
    analytes = load_analyte_reference()
    match = find_analyte(query, analytes)
    if match:
        return {"match": match.to_dict(), "suggestions": [], "count": 1}
    suggestions = suggest_analytes(query, analytes)
    return {"match": None, "suggestions": suggestions, "count": 0}


def as_json(obj: dict[str, Any]) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


if __name__ == "__main__":  # manual quick test
    info = get_pesticide_info("3-PBA")
    print(as_json(info))
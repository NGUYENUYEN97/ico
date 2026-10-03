"""Cau hinh chung cho quy trinh RAW -> AUDIT -> CLEAN -> VERIFY (ICO 2026, chau A)."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

PKG = Path(__file__).resolve().parent.parent          # lam_sach_du_lieu_ico/
ROOT = PKG.parent                                      # goc repo
SRC = ROOT / "ico26_publicdata"                        # RAW nguon (parquet, Git LFS)
RAW_DIR = PKG / "01_RAW_DATA_UNCHANGED"
CLEAN_DIR = PKG / "02_CLEAN_DATA_CANDIDATE"
QC_DIR = PKG / "06_QC"

SOURCE_FILES = ["capabilities", "densities", "field_complexities", "field_proximities",
                "fields", "outputs", "potentials", "unit_complexities",
                "unit_proximities", "units"]

ASIA_CONTINENTS = ["East Asia", "West and Central Asia"]
BASE_YEAR, LAST_YEAR = 2013, 2023
YEARS = list(range(2001, 2024))

# Nguon: ASEAN Secretariat. Ngay gia nhap: 5 nuoc sang lap 1967, BN 1984, VN 1995,
# LA & MM 1997, KH 1999, TL 26/10/2025.
ASEAN_JOIN_YEAR = {"ID": 1967, "MY": 1967, "PH": 1967, "SG": 1967, "TH": 1967,
                   "BN": 1984, "VN": 1995, "LA": 1997, "MM": 1997, "KH": 1999, "TL": 2025}
ASEAN = sorted(ASEAN_JOIN_YEAR)

# Nguon: UN M49 Standard country or area codes (tieu vung dia ly).
SUBREGION = {
    "Dong A": ["CN", "JP", "KR", "KP", "MN"],
    "Dong Nam A": ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"],
    "Nam A": ["AF", "BD", "BT", "IN", "IR", "LK", "MV", "NP", "PK"],
    "Trung A": ["KZ", "KG", "TJ", "TM", "UZ"],
    "Tay A": ["AE", "AM", "AZ", "BH", "CY", "GE", "IL", "IQ", "JO", "KW",
              "LB", "OM", "QA", "SA", "SY", "TR", "YE"],
}
SUBREGION_OF = {u: r for r, us in SUBREGION.items() for u in us}

# Thu tu bac cua phan loai thu nhap World Bank (thu tu do WB quy dinh).
INCOME_ORDER = {"Low income": 1, "Lower middle income": 2,
                "Upper middle income": 3, "High income": 4}

DIM_CODE = {"T": "cong_nghe", "S": "khoa_hoc", "P": "san_xuat", "E": "khoi_nghiep"}


def read_raw(name, filters=None, columns=None):
    """Doc parquet nguyen trang: giu moi cot (ke ca __index_level_0__), khong ap metadata pandas."""
    return pq.read_table(SRC / f"{name}.parquet", filters=filters, columns=columns) \
             .to_pandas(ignore_metadata=True)


def asia_units():
    u = read_raw("units", columns=["Unit", "Continent"])
    return sorted(u.loc[u["Continent"].isin(ASIA_CONTINENTS), "Unit"].unique())


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def write_csv(df, path):
    """CSV UTF-8, o trong = missing, so thuc ghi day du (repr, khong lam tron)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8", na_rep="")


def write_json(obj, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=_json_default))


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return str(o)


def md_table(df, floatfmt="{:.4g}"):
    """Bang markdown don gian (khong phu thuoc 'tabulate')."""
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        cells = []
        for v in r.values:
            if isinstance(v, (float, np.floating)):
                cells.append("" if pd.isna(v) else floatfmt.format(v))
            else:
                cells.append("" if v is None or (not isinstance(v, str) and pd.isna(v)) else str(v))
        out.append("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")
    return "\n".join(out)

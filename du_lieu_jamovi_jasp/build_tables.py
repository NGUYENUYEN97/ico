"""Tao cac bang du lieu tho (CSV) cho jamovi / JASP tu bo ICO 2026.

Pham vi: Viet Nam, cac nuoc ASEAN va cac nuoc chau A (47 quoc gia).
Chay tu thu muc goc cua repo:  python3 du_lieu_jamovi_jasp/build_tables.py
"""
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "ico26_publicdata"
OUT = Path(__file__).resolve().parent

BASE_YEAR, LAST_YEAR = 2013, 2023

# ASEAN: 11 thanh vien (Timor-Leste gia nhap 10/2025)
ASEAN = ["BN", "KH", "ID", "LA", "MY", "MM", "PH", "SG", "TH", "VN", "TL"]

# Tieu vung theo phan loai M49 cua Lien Hop Quoc
SUBREGION = {
    "Dong A": ["CN", "JP", "KR", "KP", "MN"],
    "Dong Nam A": ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"],
    "Nam A": ["AF", "BD", "BT", "IN", "IR", "LK", "MV", "NP", "PK"],
    "Trung A": ["KZ", "KG", "TJ", "TM", "UZ"],
    "Tay A": ["AE", "AM", "AZ", "BH", "CY", "GE", "IL", "IQ", "JO", "KW",
              "LB", "OM", "QA", "SA", "SY", "TR", "YE"],
}
SUBREGION_OF = {u: r for r, units in SUBREGION.items() for u in units}

INCOME_ORDER = {"Low income": 1, "Lower middle income": 2,
                "Upper middle income": 3, "High income": 4}

DIM = {"T": "cong_nghe", "S": "khoa_hoc", "P": "san_xuat", "E": "khoi_nghiep"}


def read(name, **kw):
    return pd.read_parquet(SRC / f"{name}.parquet", **kw)


def group_label(u):
    if u == "VN":
        return "Viet Nam"
    return "ASEAN khac" if u in ASEAN else "Chau A khac"


# ---------------------------------------------------------------- don vi
units = read("units").drop(columns="__index_level_0__", errors="ignore")
units = units[units["Continent"].isin(["East Asia", "West and Central Asia"])]
ASIA = sorted(units["Unit"].unique())
assert set(ASIA) == set(SUBREGION_OF), set(ASIA) ^ set(SUBREGION_OF)

panel = pd.DataFrame({
    "nam": units["Period"],
    "ma_qg": units["Unit"],
    "ten_qg": units["Unit Name"],
    "tieu_vung": units["Unit"].map(SUBREGION_OF),
    "nhom": units["Unit"].map(group_label),
    "asean": units["Unit"].isin(ASEAN).astype(int),
    "viet_nam": (units["Unit"] == "VN").astype(int),
    "nhom_thu_nhap": units["Income Group"],
    "bac_thu_nhap": units["Income Group"].map(INCOME_ORDER),
    "gdp_ppp_ty_usd": units["GDP PPP"] / 1e9,
    "dan_so_trieu": units["Population"] / 1e6,
    "gdp_dau_nguoi": units["GDP PC"],
})
panel["ln_gdp_dau_nguoi"] = np.log(panel["gdp_dau_nguoi"])

# ---------------------------------------------------------- do phuc tap
uc = read("unit_complexities").rename(columns={
    "Period": "nam", "Unit": "ma_qg",
    "Diversity Share": "do_da_dang",
    "Ecosystem Complexity Index": "eci",
    "Complexity Outlook Index": "coi",
    "Growth Outlook Index": "goi",
})
uc["hang_eci_the_gioi"] = uc.groupby("nam")["eci"].rank(ascending=False, method="min")
panel = panel.merge(uc, on=["nam", "ma_qg"], how="left")
panel["hang_eci_chau_a"] = panel.groupby("nam")["eci"].rank(ascending=False, method="min")

# ------------------------------------------------------- san luong
out = read("outputs", columns=["Period", "Unit", "Dimension", "Outputs (Fractional)"],
           filters=[("Unit", "in", ASIA)])
tot = (out.groupby(["Period", "Unit", "Dimension"])["Outputs (Fractional)"].sum()
          .unstack("Dimension").reindex(columns=list(DIM)).fillna(0))
tot = pd.DataFrame({
    "sang_che": tot["T"],
    "bai_bao_kh": tot["S"],
    "nhan_hieu": tot["E"],
    "xuat_khau_ty_usd": tot["P"] / 1e9,
}).rename_axis(["nam", "ma_qg"]).reset_index()
panel = panel.merge(tot, on=["nam", "ma_qg"], how="left")
for col in ["sang_che", "bai_bao_kh", "nhan_hieu", "xuat_khau_ty_usd"]:
    panel[col] = panel[col].fillna(0)
    panel[f"{col}_tren_trieu_dan"] = panel[col] / panel["dan_so_trieu"]
    panel[f"ln_{col}"] = np.log1p(panel[col])

# ------------------------------------------------------- nang luc
cap = read("capabilities", filters=[("Unit", "in", ASIA)])
cap["dim"] = cap["Field ID"].str[0]
cnt = (cap.groupby(["Period", "Unit", "dim"])["Innovation Capability (Binary)"].sum()
          .unstack("dim").reindex(columns=list(DIM)).fillna(0).astype(int))
cnt.columns = [f"so_nang_luc_{DIM[d]}" for d in cnt.columns]
cnt["so_nang_luc_tong"] = cnt.sum(axis=1)
extra = cap.groupby(["Period", "Unit"]).agg(
    so_nang_luc_tuong_doi=("Relative Capability (Binary)", "sum"),
    so_nang_luc_tuyet_doi=("Absolute Capability (Binary)", "sum"),
)
cnt = cnt.join(extra).rename_axis(["nam", "ma_qg"]).reset_index()
panel = panel.merge(cnt, on=["nam", "ma_qg"], how="left")

panel = panel.sort_values(["ma_qg", "nam"]).reset_index(drop=True)
# Tang truong GDP/nguoi so voi nam truoc (%)
panel["tang_truong_gdp_dau_nguoi"] = panel.groupby("ma_qg")["gdp_dau_nguoi"].pct_change(fill_method=None) * 100

# ---------------------------------------------------- bang cat ngang 2023
last = panel[panel["nam"] == LAST_YEAR].copy()
base = panel[panel["nam"] == BASE_YEAR].set_index("ma_qg")
for col in ["eci", "do_da_dang", "so_nang_luc_tong", "gdp_dau_nguoi"]:
    last[f"{col}_{BASE_YEAR}"] = last["ma_qg"].map(base[col])
last["thay_doi_eci_10_nam"] = last["eci"] - last[f"eci_{BASE_YEAR}"]
last["thay_doi_do_da_dang_10_nam"] = last["do_da_dang"] - last[f"do_da_dang_{BASE_YEAR}"]
last["thay_doi_so_nang_luc_10_nam"] = last["so_nang_luc_tong"] - last[f"so_nang_luc_tong_{BASE_YEAR}"]
last["tang_truong_gdp_dau_nguoi_bq_10_nam"] = (
    (last["gdp_dau_nguoi"] / last[f"gdp_dau_nguoi_{BASE_YEAR}"]) ** (1 / 10) - 1) * 100

prox = read("unit_proximities")
prox = prox[(prox["Unit 1"] == "VN") | (prox["Unit 2"] == "VN")]
prox_vn = pd.concat([
    prox.set_index("Unit 2")["Proximity"], prox.set_index("Unit 1")["Proximity"]
]).drop("VN", errors="ignore")
last["tuong_dong_voi_viet_nam"] = last["ma_qg"].map(prox_vn)
cross = last.drop(columns=["nam", "tang_truong_gdp_dau_nguoi"])

# ------------------------------------- bang linh vuc ASEAN 2013 -> 2023
fields = read("fields").drop(columns="__index_level_0__", errors="ignore")
flt = [("Unit", "in", ASEAN), ("Period", "in", [BASE_YEAR, LAST_YEAR])]
c = read("capabilities", filters=flt)
d = read("densities", filters=flt).drop(columns="__index_level_0__", errors="ignore")
p = read("potentials", filters=flt)
o = read("outputs", columns=["Period", "Unit", "Field ID", "Outputs", "Outputs (Fractional)"],
         filters=flt)
key = ["Period", "Unit", "Field ID"]
fv = c.merge(d, on=key, how="left").merge(p, on=key, how="left").merge(o, on=key, how="left")
fv[["Outputs", "Outputs (Fractional)"]] = fv[["Outputs", "Outputs (Fractional)"]].fillna(0)
wide = fv.pivot(index=["Unit", "Field ID"], columns="Period")
wide.columns = [f"{a}|{b}" for a, b in wide.columns]
wide = wide.reset_index()

fc = read("field_complexities")
fc = fc[fc["Period"] == LAST_YEAR].set_index("Field ID")


def w(col, year):
    return wide[f"{col}|{year}"]


def as_int(s):
    return s.astype("float").astype("Int64")


cap0 = as_int(w("Innovation Capability (Binary)", BASE_YEAR))
cap1 = as_int(w("Innovation Capability (Binary)", LAST_YEAR))
fv_tab = pd.DataFrame({
    "ma_qg": wide["Unit"],
    "ma_linh_vuc": wide["Field ID"],
})
fv_tab = fv_tab.merge(units.loc[units["Period"] == LAST_YEAR, ["Unit", "Unit Name"]]
                      .rename(columns={"Unit": "ma_qg", "Unit Name": "ten_qg"}), on="ma_qg")
fmeta = fields.set_index("Field ID")
fv_tab["ten_linh_vuc"] = fv_tab["ma_linh_vuc"].map(fmeta["Field Name"])
fv_tab["ma_nhom_linh_vuc"] = fv_tab["ma_linh_vuc"].map(fmeta["Domain ID"])
fv_tab["nhom_linh_vuc"] = fv_tab["ma_linh_vuc"].map(fmeta["Domain Name"])
fv_tab["chieu"] = fv_tab["ma_linh_vuc"].map(fmeta["Dimension Name"])
fv_tab = fv_tab.set_index(["ma_qg", "ma_linh_vuc"])
wide = wide.set_index(["Unit", "Field ID"])
wide.index.names = ["ma_qg", "ma_linh_vuc"]
cap0.index = cap1.index = wide.index

fv_tab[f"san_luong_{BASE_YEAR}"] = w("Outputs", BASE_YEAR)
fv_tab[f"san_luong_{LAST_YEAR}"] = w("Outputs", LAST_YEAR)
fv_tab[f"san_luong_phan_so_{LAST_YEAR}"] = w("Outputs (Fractional)", LAST_YEAR)
fv_tab[f"nang_luc_chuan_hoa_{BASE_YEAR}"] = w("Innovation Capability (Normalized)", BASE_YEAR)
fv_tab[f"nang_luc_chuan_hoa_{LAST_YEAR}"] = w("Innovation Capability (Normalized)", LAST_YEAR)
fv_tab[f"co_nang_luc_{BASE_YEAR}"] = cap0
fv_tab[f"co_nang_luc_{LAST_YEAR}"] = cap1
fv_tab[f"nang_luc_tuong_doi_{LAST_YEAR}"] = as_int(w("Relative Capability (Binary)", LAST_YEAR))
fv_tab[f"nang_luc_tuyet_doi_{LAST_YEAR}"] = as_int(w("Absolute Capability (Binary)", LAST_YEAR))
# Gia nhap: chua co nang luc nam goc -> co nang luc nam cuoi. Trong neu da co tu nam goc.
fv_tab["gia_nhap_moi"] = cap1.where(cap0 == 0)
# Roi bo: da co nang luc nam goc -> mat nang luc nam cuoi. Trong neu chua co tu nam goc.
fv_tab["roi_bo"] = (1 - cap1).where(cap0 == 1)
fv_tab[f"mat_do_lien_quan_{BASE_YEAR}"] = w("Relatedness Density", BASE_YEAR)
fv_tab[f"mat_do_lien_quan_{LAST_YEAR}"] = w("Relatedness Density", LAST_YEAR)
fv_tab[f"tiem_nang_{LAST_YEAR}"] = w("Potential", LAST_YEAR)
fv_tab[f"ln_tiem_nang_{LAST_YEAR}"] = np.log1p(fv_tab[f"tiem_nang_{LAST_YEAR}"])
fv_tab[f"ln_san_luong_{LAST_YEAR}"] = np.log1p(fv_tab[f"san_luong_{LAST_YEAR}"])
fv_tab["chenh_lech_tiem_nang"] = fv_tab[f"ln_san_luong_{LAST_YEAR}"] - fv_tab[f"ln_tiem_nang_{LAST_YEAR}"]
mlv = fv_tab.index.get_level_values("ma_linh_vuc")
fv_tab[f"do_phuc_tap_linh_vuc_{LAST_YEAR}"] = mlv.map(fc["Capability Complexity Index"])
fv_tab[f"do_pho_bien_linh_vuc_{LAST_YEAR}"] = mlv.map(fc["Ubiquity Share"])
fv_tab = fv_tab.reset_index()
lead = ["ma_qg", "ten_qg", "ma_linh_vuc", "ten_linh_vuc", "ma_nhom_linh_vuc", "nhom_linh_vuc", "chieu"]
fv_tab = fv_tab[lead + [c for c in fv_tab.columns if c not in lead]]
fv_tab = fv_tab.sort_values(["ma_qg", "chieu", "ma_linh_vuc"])


# ------------------------------------------------------------- ghi file
def to_ascii(text):
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()


def save(df, name):
    df = df.copy()
    for col in df.select_dtypes("float").columns:
        s = df[col].dropna()
        if col.startswith(("hang_", "gia_nhap", "roi_bo")) and (s == s.round()).all():
            df[col] = df[col].astype("Int64")
        else:
            df[col] = df[col].round(6)
    for col in df.select_dtypes(["object", "string"]).columns:
        df[col] = df[col].map(to_ascii, na_action="ignore")
    df.to_csv(OUT / name, index=False, encoding="utf-8", na_rep="")
    print(f"{name}: {len(df):,} dong x {df.shape[1]} cot")


save(panel, "1_panel_chau_a_2001_2023.csv")
save(cross, "2_chau_a_cat_ngang_2023.csv")
save(fv_tab, "3_asean_linh_vuc_2013_2023.csv")
save(fv_tab[fv_tab["ma_qg"] == "VN"], "4_viet_nam_linh_vuc_2013_2023.csv")

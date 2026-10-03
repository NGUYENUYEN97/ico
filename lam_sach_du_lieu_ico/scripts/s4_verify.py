"""BUOC VERIFY + POST-CLEANING QC.

Doc lai moi thu tu DIA (khong dung bien trong bo nho cua s3) va kiem tra:
 1. RAW bat bien (SHA-256 parquet = Git LFS oid; SHA-256 ban trich = MANIFEST)
 2. Cau truc CLEAN (so dong, khoa trung, cot rong)
 3. Range / category / missing (truoc-sau)
 4. Bien dan xuat: tinh lai DOC LAP (pyarrow cho tong hop; cong thuc viet lai)
 5. RAW <-> CLEAN: diff lai doc lap; moi o thay doi phai co trong CLEANING_LOG
 6. Gia tri ky vong de doi chieu tren JASP va jamovi
Ket qua: 06_QC/post/*, cap nhat cot 'verified' trong 04_CLEANING_LOG.csv.
"""
import json

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from common import (CLEAN_DIR, PKG, QC_DIR, RAW_DIR, SOURCE_FILES, SRC, md_table, sha256,
                    write_csv, write_json)

POST = QC_DIR / "post"
NA = dict(keep_default_na=False, na_values=[""], float_precision="round_trip")
checks = []


def check(cid, desc, ok, detail=""):
    checks.append({"check_id": cid, "description": desc, "passed": bool(ok), "detail": str(detail)})
    return ok


def load():
    c = {n: pd.read_csv(CLEAN_DIR / f, **NA) for n, f in [
        ("panel", "1_panel_chau_a_2001_2023.csv"), ("cross", "2_chau_a_cat_ngang_2023.csv"),
        ("field", "3_asean_linh_vuc_2013_2023.csv"), ("vn", "4_viet_nam_linh_vuc_2013_2023.csv")]}
    return c


# 1 ------------------------------------------------------------------------------
def raw_preserved():
    man = json.loads((RAW_DIR / "MANIFEST.json").read_text())
    for f in man["source_files"]:
        h = sha256(PKG.parent / f["file"])
        check("V01", f"RAW nguon bat bien: {f['file']}", h == f["sha256"] == f["git_lfs_oid"], h[:16])
    for e in man["extracts"]:
        h = sha256(RAW_DIR / e["extract"])
        check("V02", f"Ban trich RAW khong doi: {e['extract']}", h == e["sha256"], h[:16])
    return man


# 2 ------------------------------------------------------------------------------
def structure(c):
    spec = {"panel": (["nam", "ma_qg"], 47 * 23), "cross": (["ma_qg"], 47),
            "field": (["ma_qg", "ma_linh_vuc"], 11 * 2508), "vn": (["ma_qg", "ma_linh_vuc"], 2508)}
    rows = []
    for n, (key, expected) in spec.items():
        df = c[n]
        r = {"dataset": n, "rows": len(df), "expected_rows": expected, "columns": df.shape[1],
             "duplicate_keys": int(df.duplicated(key).sum()), "exact_duplicate_rows": int(df.duplicated().sum()),
             "empty_columns": int(df.isna().all().sum()), "missing_ids": int(df[key].isna().any(axis=1).sum())}
        rows.append(r)
        check("V03", f"{n}: so dong = {expected}, khong trung khoa, khong cot rong",
              r["rows"] == expected and r["duplicate_keys"] == 0 and r["empty_columns"] == 0, r)
    return pd.DataFrame(rows)


# 3 ------------------------------------------------------------------------------
ALLOWED = {
    "tieu_vung": {"Dong A", "Dong Nam A", "Nam A", "Trung A", "Tay A"},
    "nhom": {"Viet Nam", "ASEAN khac", "Chau A khac"},
    "chau_luc_nguon": {"East Asia", "West and Central Asia"},
    "nhom_thu_nhap_hien_hanh": {"Low income", "Lower middle income", "Upper middle income", "High income"},
    "chieu": {"Technology", "Science", "Production", "Entrepreneurial"},
}


def categories(c):
    rows = []
    for n, df in c.items():
        for col, allowed in ALLOWED.items():
            if col in df:
                vals = set(df[col].dropna().unique())
                bad = vals - allowed
                ws = int((df[col].dropna() != df[col].dropna().str.strip()).sum())
                rows.append({"dataset": n, "variable": col, "values": "; ".join(sorted(vals)),
                             "outside_allowed": "; ".join(sorted(bad)), "whitespace_issues": ws})
                check("V04", f"{n}.{col}: chi gom gia tri cho phep", not bad and ws == 0, bad)
    return pd.DataFrame(rows)


def ranges():
    dd = pd.read_csv(PKG / "03_DATA_DICTIONARY.csv", **NA)
    oor = pd.to_numeric(dd["n_out_of_range"], errors="coerce").fillna(0)
    check("V05", "Khong con gia tri ngoai mien hop le da xac lap (03_DATA_DICTIONARY)", (oor == 0).all(),
          dd.loc[oor > 0, ["dataset", "variable"]].values.tolist())
    return dd


MISSING_TYPE = {
    "gdp_ppp_usd": ("system missing", "KP, YE: nguon khong co GDP (CL009)"),
    "gdp_dau_nguoi": ("system missing", "KP, YE (CL009)"),
    "gdp_ppp_ty_usd": ("dan xuat tu system missing", "KP, YE"),
    "ln_gdp_dau_nguoi": ("dan xuat tu system missing", "KP, YE"),
    "gdp_dau_nguoi_2013": ("dan xuat tu system missing", "KP, YE"),
    "tang_truong_gdp_dau_nguoi": ("structural + system", "Nam 2001 khong co nam truoc (47) + KP, YE (44)"),
    "tang_truong_gdp_dau_nguoi_bq_10_nam": ("dan xuat tu system missing", "KP, YE"),
    "sang_che": ("no coverage (khong phai 0)", "Khong co ban ghi T cho quoc gia-nam (CL002)"),
    "bai_bao_kh": ("no coverage (khong phai 0)", "Khong co ban ghi S (CL002)"),
    "nhan_hieu": ("no coverage (khong phai 0)", "Khong co ban ghi E (CL002)"),
    "ty_le_bat_thuong_sang_che": ("dan xuat tu no coverage", "CL002"),
    "ty_le_bat_thuong_nhan_hieu": ("dan xuat tu no coverage", "CL002"),
    "tuong_dong_voi_viet_nam": ("structural missing", "Dong Viet Nam (CL015)"),
    "gia_nhap_moi": ("structural missing", "Da co nang luc nam 2013 -> khong thuoc tap nguy co gia nhap"),
    "roi_bo": ("structural missing", "Chua co nang luc nam 2013 -> khong the roi bo"),
    "san_luong_2013": ("no coverage (khong phai 0)", "TL: chieu T va E khong co ban ghi (CL002)"),
    "san_luong_2023": ("no coverage (khong phai 0)", "TL: chieu T va E (CL002)"),
    "san_luong_phan_so_2013": ("no coverage (khong phai 0)", "TL: T va E (CL002)"),
    "san_luong_phan_so_2023": ("no coverage (khong phai 0)", "TL: T va E (CL002)"),
    "ln_san_luong_2023": ("dan xuat tu no coverage", "CL002"),
    "chenh_lech_tiem_nang": ("dan xuat tu no coverage", "CL002"),
    "mat_do_lien_quan_2013": ("structural missing", "Field-year khong co complexity (CL008)"),
    "mat_do_lien_quan_2023": ("structural missing", "CL008"),
    "do_phuc_tap_linh_vuc_2023": ("structural missing", "CL008"),
    "do_pho_bien_linh_vuc_2023": ("structural missing", "CL008"),
}


def missing(c):
    rows = []
    for n, df in c.items():
        for col in df.columns:
            m = int(df[col].isna().sum())
            if m == 0:
                continue
            base = col.replace("_tren_trieu_dan", "").replace("ln_", "") if col.startswith(("ln_s", "ln_b", "ln_n")) \
                else col.replace("_tren_trieu_dan", "")
            t, interp = MISSING_TYPE.get(col, MISSING_TYPE.get(base, ("CHUA PHAN LOAI", "")))
            rows.append({"dataset": n, "variable": col, "N": len(df), "valid_N": len(df) - m, "missing_N": m,
                         "missing_pct": round(100 * m / len(df), 2), "type_of_missing": t, "interpretation": interp})
    out = pd.DataFrame(rows)
    check("V06", "Moi bien co missing deu da duoc phan loai loai missing",
          (out["type_of_missing"] != "CHUA PHAN LOAI").all(),
          out.loc[out["type_of_missing"] == "CHUA PHAN LOAI", "variable"].tolist())
    p = c["panel"]
    diffm = pd.concat({
        "tieu_vung": p.groupby("tieu_vung")[["sang_che", "bai_bao_kh", "nhan_hieu"]].apply(lambda d: d.isna().mean() * 100),
        "bac_thu_nhap": p.groupby("bac_thu_nhap")[["sang_che", "bai_bao_kh", "nhan_hieu"]].apply(lambda d: d.isna().mean() * 100),
    }).round(1)
    diffm.index = [f"{a}={b}" for a, b in diffm.index]
    return out, diffm.reset_index(names="nhom")


# 4 ------------------------------------------------------------------------------
def close(a, b, tol=1e-9):
    a, b = np.asarray(a, float), np.asarray(b, float)
    both_na = np.isnan(a) & np.isnan(b)
    diff = np.where(both_na, 0, np.abs(a - b) / np.maximum(1, np.abs(b)))
    return bool(np.nan_to_num(diff, nan=np.inf).max() <= tol), float(np.nan_to_num(diff, nan=np.inf).max())


def derived(c, man):
    p, x, f = c["panel"], c["cross"], c["field"]
    asia = man["asia_units"]
    res = []

    def rec(name, a, b, tol=1e-9):
        ok, mx = close(a, b, tol)
        res.append({"derived_variable": name, "max_rel_diff": mx, "passed": ok})
        check("V07", f"Tinh lai doc lap: {name}", ok, mx)

    # Tong hop tu parquet bang pyarrow (doc lap voi pandas groupby o s3)
    t = pq.read_table(SRC / "outputs.parquet", columns=["Period", "Unit", "Dimension", "Outputs (Fractional)"],
                      filters=[("Unit", "in", asia)])
    g = t.group_by(["Period", "Unit", "Dimension"]).aggregate([("Outputs (Fractional)", "sum")]).to_pandas()
    g = g.pivot_table(index=["Period", "Unit"], columns="Dimension", values="Outputs (Fractional)_sum", aggfunc="first")
    key = pd.MultiIndex.from_frame(p[["nam", "ma_qg"]])
    g = g.reindex(key)
    rec("sang_che", p["sang_che"], g["T"].values)
    rec("bai_bao_kh", p["bai_bao_kh"], g["S"].values)
    rec("nhan_hieu", p["nhan_hieu"], g["E"].values)
    rec("xuat_khau_ty_usd", p["xuat_khau_ty_usd"], g["P"].values / 1e9)

    tc = pq.read_table(SRC / "capabilities.parquet", columns=["Period", "Unit", "Field ID",
                       "Innovation Capability (Binary)", "Relative Capability (Binary)", "Absolute Capability (Binary)"],
                       filters=[("Unit", "in", asia)])
    tc = tc.append_column("dim", pc.utf8_slice_codeunits(tc["Field ID"], 0, 1))
    for colname in ["Innovation Capability (Binary)", "Relative Capability (Binary)", "Absolute Capability (Binary)"]:
        tc = tc.set_column(tc.schema.get_field_index(colname), colname, pc.cast(tc[colname], pa.int64()))
    gc = tc.group_by(["Period", "Unit", "dim"]).aggregate([("Innovation Capability (Binary)", "sum")]).to_pandas()
    gc = gc.pivot_table(index=["Period", "Unit"], columns="dim", values="Innovation Capability (Binary)_sum").reindex(key)
    for d, name in {"T": "cong_nghe", "S": "khoa_hoc", "P": "san_xuat", "E": "khoi_nghiep"}.items():
        rec(f"so_nang_luc_{name}", p[f"so_nang_luc_{name}"], gc[d].values)
    gt = tc.group_by(["Period", "Unit"]).aggregate([("Relative Capability (Binary)", "sum"),
                                                     ("Absolute Capability (Binary)", "sum"),
                                                     ("Innovation Capability (Binary)", "sum")]).to_pandas() \
           .set_index(["Period", "Unit"]).reindex(key)
    rec("so_nang_luc_tong", p["so_nang_luc_tong"], gt["Innovation Capability (Binary)_sum"].values)
    rec("so_nang_luc_tuong_doi", p["so_nang_luc_tuong_doi"], gt["Relative Capability (Binary)_sum"].values)
    rec("so_nang_luc_tuyet_doi", p["so_nang_luc_tuyet_doi"], gt["Absolute Capability (Binary)_sum"].values)

    # Cong thuc viet lai
    rec("gdp_ppp_ty_usd", p["gdp_ppp_ty_usd"], p["gdp_ppp_usd"] / 1e9)
    rec("dan_so_trieu", p["dan_so_trieu"], p["dan_so"] / 1e6)
    rec("ln_gdp_dau_nguoi", p["ln_gdp_dau_nguoi"], np.log(p["gdp_dau_nguoi"]))
    rec("gdp_dau_nguoi = gdp_ppp_usd / dan_so", p["gdp_dau_nguoi"], p["gdp_ppp_usd"] / p["dan_so"])
    gr = []
    for _, r in p.iterrows():
        prev = p[(p["ma_qg"] == r["ma_qg"]) & (p["nam"] == r["nam"] - 1)]["gdp_dau_nguoi"]
        gr.append(100 * (r["gdp_dau_nguoi"] / prev.iloc[0] - 1) if len(prev) else np.nan)
    rec("tang_truong_gdp_dau_nguoi", p["tang_truong_gdp_dau_nguoi"], gr)
    for base in ["sang_che", "bai_bao_kh", "nhan_hieu", "xuat_khau_ty_usd"]:
        rec(f"{base}_tren_trieu_dan", p[f"{base}_tren_trieu_dan"], p[base] * 1e6 / p["dan_so"])
        rec(f"ln_{base}", p[f"ln_{base}"], np.log(1 + p[base]))
    rank_asia = p.groupby("nam")["eci"].transform(lambda s: s.apply(lambda v: (s > v).sum() + 1))
    rec("hang_eci_chau_a", p["hang_eci_chau_a"], rank_asia)
    uc = pd.read_csv(RAW_DIR / "raw_unit_complexities_all_193.csv", **NA)
    world = uc.groupby("Period")["Ecosystem Complexity Index"].transform(lambda s: s.apply(lambda v: (s > v).sum() + 1))
    wmap = dict(zip(zip(uc["Period"], uc["Unit"]), world))
    rec("hang_eci_the_gioi", p["hang_eci_the_gioi"], [wmap[(a, b)] for a, b in zip(p["nam"], p["ma_qg"])])
    rec("flag_dan_so_lap_lai", p["flag_dan_so_lap_lai"],
        [int(any((p["ma_qg"] == u) & (p["nam"] == y - 1) & (p["dan_so"] == d))) for u, y, d in zip(p["ma_qg"], p["nam"], p["dan_so"])])

    # Cross-section
    p13 = p[p["nam"] == 2013].set_index("ma_qg")
    rec("thay_doi_eci_10_nam", x["thay_doi_eci_10_nam"], x["eci"] - x["ma_qg"].map(p13["eci"]))
    rec("thay_doi_so_nang_luc_10_nam", x["thay_doi_so_nang_luc_10_nam"], x["so_nang_luc_tong"] - x["ma_qg"].map(p13["so_nang_luc_tong"]))
    rec("tang_truong_gdp_dau_nguoi_bq_10_nam", x["tang_truong_gdp_dau_nguoi_bq_10_nam"],
        100 * (np.exp(np.log(x["gdp_dau_nguoi"] / x["ma_qg"].map(p13["gdp_dau_nguoi"])) / 10) - 1))
    p23 = p[p["nam"] == 2023].set_index("ma_qg")
    for col in ["eci", "sang_che", "so_nang_luc_tong", "gdp_dau_nguoi"]:
        rec(f"cross.{col} = panel 2023", x[col], x["ma_qg"].map(p23[col]))

    # Field level
    g_new = np.where(f["co_nang_luc_2013"] == 0, f["co_nang_luc_2023"], np.nan)
    rec("gia_nhap_moi", f["gia_nhap_moi"], g_new)
    rec("roi_bo", f["roi_bo"], np.where(f["co_nang_luc_2013"] == 1, 1 - f["co_nang_luc_2023"], np.nan))
    rec("ln_tiem_nang_2023", f["ln_tiem_nang_2023"], np.log(1 + f["tiem_nang_2023"]))
    rec("ln_san_luong_2023", f["ln_san_luong_2023"], np.log(1 + f["san_luong_2023"]))
    rec("chenh_lech_tiem_nang", f["chenh_lech_tiem_nang"], np.log(1 + f["san_luong_2023"]) - np.log(1 + f["tiem_nang_2023"]))
    for y in (2013, 2023):
        rec(f"flag_phan_so_vuot_toan_phan_{y}", f[f"flag_phan_so_vuot_toan_phan_{y}"],
            (f[f"san_luong_phan_so_{y}"] - f[f"san_luong_{y}"] > 1e-9).astype(int))
    vn_from_field = f[f["ma_qg"] == "VN"].reset_index(drop=True)
    eq = vn_from_field.equals(c["vn"])
    check("V07", "4_viet_nam = loc ma_qg == VN tu file 3", eq)
    return pd.DataFrame(res)


# 5 ------------------------------------------------------------------------------
def diff_verify(c):
    """Diff doc lap: dinh dang long, doi chieu raw CSV voi clean CSV cho moi cot nguon."""
    raw = {
        "Outputs": pd.read_csv(RAW_DIR / "raw_outputs_asean_2013_2023.csv", **NA),
        "cap": pd.read_csv(RAW_DIR / "raw_capabilities_asean_2013_2023.csv", **NA),
        "den": pd.read_csv(RAW_DIR / "raw_densities_asean_2013_2023.csv", **NA),
        "pot": pd.read_csv(RAW_DIR / "raw_potentials_asean_2013_2023.csv", **NA),
    }
    f = c["field"]
    k = ["Period", "Unit", "Field ID"]
    long = []
    spec = [("Outputs", "Outputs", "san_luong"), ("Outputs", "Outputs (Fractional)", "san_luong_phan_so"),
            ("cap", "Innovation Capability (Normalized)", "nang_luc_chuan_hoa"),
            ("cap", "Innovation Capability (Binary)", "co_nang_luc"),
            ("cap", "Relative Capability (Binary)", "nang_luc_tuong_doi"),
            ("cap", "Absolute Capability (Binary)", "nang_luc_tuyet_doi"),
            ("den", "Relatedness Density", "mat_do_lien_quan"), ("pot", "Potential", "tiem_nang")]
    grid = raw["cap"][k]
    for tab, rc, cc in spec:
        r = grid.merge(raw[tab][k + [rc]], on=k, how="left")
        for y in (2013, 2023):
            ry = r[r["Period"] == y].rename(columns={"Unit": "ma_qg", "Field ID": "ma_linh_vuc"})
            m = ry.merge(f[["ma_qg", "ma_linh_vuc", f"{cc}_{y}"]], on=["ma_qg", "ma_linh_vuc"], how="outer", indicator=True)
            assert (m["_merge"] == "both").all()
            a = m[rc].map(lambda v: float(v) if not pd.isna(v) else np.nan)
            b = m[f"{cc}_{y}"].astype(float)
            changed = ~((a == b) | (a.isna() & b.isna()))
            for _, row in m[changed].iterrows():
                long.append(("3_asean_linh_vuc", f"{row['ma_qg']}|{row['ma_linh_vuc']}", f"{cc}_{y}"))
    p = c["panel"]
    u = pd.read_csv(RAW_DIR / "raw_units_asia.csv", **NA).merge(
        pd.read_csv(RAW_DIR / "raw_unit_complexities_all_193.csv", **NA), on=["Period", "Unit"])
    pm = {"Unit Name": "ten_qg", "Continent": "chau_luc_nguon", "Income Group": "nhom_thu_nhap_hien_hanh",
          "GDP PPP": "gdp_ppp_usd", "Population": "dan_so", "GDP PC": "gdp_dau_nguoi",
          "Diversity Share": "do_da_dang", "Ecosystem Complexity Index": "eci",
          "Complexity Outlook Index": "coi", "Growth Outlook Index": "goi"}
    m = u.rename(columns={"Period": "nam", "Unit": "ma_qg"}).merge(p, on=["nam", "ma_qg"], how="outer", indicator=True)
    assert (m["_merge"] == "both").all()
    for rc, cc in pm.items():
        a, b = m[rc], m[cc]
        changed = ~((a == b) | (a.isna() & b.isna()))
        for _, row in m[changed].iterrows():
            long.append(("1_panel", f"{row['nam']}|{row['ma_qg']}", cc))
    mine = pd.DataFrame(long, columns=["dataset", "case", "variable"])
    d = pd.read_csv(PKG / "05_RAW_CLEAN_DIFF.csv", **NA)
    log = pd.read_csv(PKG / "04_CLEANING_LOG.csv", **NA)
    dd = d[d["dataset"].isin(["3_asean_linh_vuc", "1_panel"])][["dataset", "case", "variable"]]
    same = set(map(tuple, mine.values)) == set(map(tuple, dd.values))
    check("V08", "Diff doc lap trung khop 05_RAW_CLEAN_DIFF (panel + field)", same,
          f"doc lap {len(mine)} o; file diff {len(dd)} o")
    check("V09", "Moi o thay doi deu co log_id ton tai trong CLEANING_LOG",
          d["log_id"].isin(log["log_id"]).all() and (d["log_id"] != "UNLOGGED").all(),
          d.loc[~d["log_id"].isin(log["log_id"]), "log_id"].unique().tolist())
    # Dieu kien cua quy tac CL001 dung voi tung o
    cl = d[d["log_id"] == "CL001"]
    cap = raw["cap"].set_index(["Unit", "Field ID", "Period"])["Innovation Capability (Normalized)"]
    ok = all(cap[(cs.split("|")[0], cs.split("|")[1], int(v[-4:]))] == 0 and pd.isna(rv) and float(cv) == 0
             for cs, v, rv, cv in zip(cl["case"], cl["variable"], cl["raw_value"], cl["clean_value"]))
    check("V10", "CL001: moi o doi NA->0 deu co Normalized Capability = 0 (bang chung cua quy tac)", ok, len(cl))
    summary = {
        "RAW rows (field grid / panel)": f"{len(grid)} / {len(u)}",
        "CLEAN rows (panel, cross, field, vn)": f"{len(c['panel'])}, {len(c['cross'])}, {len(c['field'])}, {len(c['vn'])}",
        "changed_cells_total (moi dataset)": len(d),
        "changed_cells_unique (khong dem trung file 4 = tap con file 3)": int((d["dataset"] != "4_viet_nam_linh_vuc").sum()),
        "corrected (C)": int((d["log_id"].map(log.set_index("log_id")["decision_code"]) == "C").sum()),
        "recoded (R)": int((d["log_id"].map(log.set_index("log_id")["decision_code"]) == "R").sum()),
        "set_missing (M)": int((d["log_id"].map(log.set_index("log_id")["decision_code"]) == "M").sum()),
        "deleted rows (D)": 0,
        "retained_after_review (K/F)": int(log["decision_code"].isin(["K", "F"]).sum()),
        "unresolved (U)": int((log["decision_code"] == "U").sum()),
    }
    return summary, mine


# 6 ------------------------------------------------------------------------------
def expected(c):
    rows = []
    spec = {"cross": ["eci", "do_da_dang", "gdp_dau_nguoi", "ln_gdp_dau_nguoi", "thay_doi_eci_10_nam",
                      "tuong_dong_voi_viet_nam", "sang_che", "nhan_hieu"],
            "panel": ["eci", "do_da_dang", "ln_gdp_dau_nguoi", "sang_che", "nhan_hieu", "so_nang_luc_tong"],
            "vn": ["mat_do_lien_quan_2013", "do_phuc_tap_linh_vuc_2023", "san_luong_2023"]}
    for n, cols in spec.items():
        for col in cols:
            s = c[n][col]
            rows.append({"dataset": n, "variable": col, "N_valid": int(s.notna().sum()), "Missing": int(s.isna().sum()),
                         "Mean": s.mean(), "SD (n-1)": s.std(ddof=1), "Median": s.median(),
                         "Min": s.min(), "Max": s.max()})
    desc = pd.DataFrame(rows)
    freq = []
    for n, col in [("cross", "tieu_vung"), ("cross", "nhom"), ("cross", "asean_thoi_diem"),
                   ("cross", "nhom_thu_nhap_hien_hanh"), ("vn", "gia_nhap_moi"), ("vn", "chieu"),
                   ("panel", "flag_dan_so_lap_lai")]:
        vc = c[n][col].value_counts(dropna=False).sort_index()
        for k, v in vc.items():
            freq.append({"dataset": n, "variable": col, "level": "Missing" if pd.isna(k) else k, "count": int(v)})
    by = c["vn"].groupby("gia_nhap_moi")["mat_do_lien_quan_2013"].agg(["count", "mean", "std"]).reset_index()
    by.insert(0, "dataset", "vn")
    return desc, pd.DataFrame(freq), by


def main():
    man = raw_preserved()
    c = load()
    st = structure(c)
    cat = categories(c)
    ranges()
    mis, diffm = missing(c)
    der = derived(c, man)
    diff_summary, _ = diff_verify(c)
    desc, freq, by = expected(c)

    POST.mkdir(parents=True, exist_ok=True)
    write_csv(st, POST / "structure_post.csv")
    write_csv(cat, POST / "category_post.csv")
    write_csv(mis, POST / "missing_report.csv")
    write_csv(diffm, POST / "differential_missingness.csv")
    write_csv(der, POST / "derived_recompute.csv")
    write_csv(desc, PKG / "09_JASP_JAMOVI_EXPECTED_DESCRIPTIVES.csv")
    write_csv(freq, PKG / "09_JASP_JAMOVI_EXPECTED_FREQUENCIES.csv")
    write_csv(by, POST / "vn_density_by_entry.csv")
    ch = pd.DataFrame(checks)
    write_csv(ch, POST / "verification_checks.csv")
    write_json({"diff_summary": diff_summary, "n_checks": len(ch), "n_passed": int(ch["passed"].sum())},
               POST / "verify_summary.json")
    (POST / "tables.md").write_text(
        "## Missing report\n\n" + md_table(mis) + "\n\n## Differential missingness (% missing)\n\n" + md_table(diffm)
        + "\n\n## Expected descriptives\n\n" + md_table(desc) + "\n\n## Expected frequencies\n\n" + md_table(freq)
        + "\n\n## Derived recompute\n\n" + md_table(der, "{:.2e}") + "\n", encoding="utf-8")

    # Cap nhat 'verified' trong CLEANING_LOG
    log = pd.read_csv(PKG / "04_CLEANING_LOG.csv", **NA)
    passed = ch["passed"].all()
    log["verified"] = "YES" if passed else "NO - xem 06_QC/post/verification_checks.csv"
    write_csv(log, PKG / "04_CLEANING_LOG.csv")

    print(f"Checks: {int(ch['passed'].sum())}/{len(ch)} passed")
    print(ch[~ch["passed"]].to_string() if not passed else "ALL PASSED")
    print(json.dumps(diff_summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

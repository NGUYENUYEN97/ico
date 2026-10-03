"""BUOC CLEAN: RAW -> CLEAN_DATA_CANDIDATE + CLEANING_LOG + RAW_CLEAN_DIFF + UNRESOLVED + DICTIONARY.

Nguyen tac: cot nguon duoc sao chep nguyen gia tri; thay doi gia tri chi theo quy tac co
log_id; bien dan xuat duoc tinh lai tu cot nguon da lam sach.
"""
import numpy as np
import pandas as pd

import meta
from common import (ASEAN, ASEAN_JOIN_YEAR, BASE_YEAR, CLEAN_DIR, DIM_CODE, INCOME_ORDER,
                    LAST_YEAR, PKG, RAW_DIR, SUBREGION_OF, asia_units, read_raw, write_csv)

YRS = (BASE_YEAR, LAST_YEAR)


def raw_csv(name):
    # keep_default_na=False: tranh doc ma "NA" (Namibia) thanh missing; chi o trong = missing.
    return pd.read_csv(RAW_DIR / name, keep_default_na=False, na_values=[""], float_precision="round_trip")


# ------------------------------------------------------------------ PANEL
def build_panel():
    u = raw_csv("raw_units_asia.csv")
    uc_all = raw_csv("raw_unit_complexities_all_193.csv")
    asia = sorted(u["Unit"].unique())
    uc_all["hang_eci_the_gioi"] = uc_all.groupby("Period")["Ecosystem Complexity Index"] \
        .rank(ascending=False, method="min").astype(int)
    src = u.merge(uc_all, on=["Period", "Unit"], how="left", validate="1:1")

    p = pd.DataFrame({
        "nam": src["Period"], "ma_qg": src["Unit"], "ten_qg": src["Unit Name"],
        "chau_luc_nguon": src["Continent"],
    })
    p["tieu_vung"] = p["ma_qg"].map(SUBREGION_OF)
    p["asean_hien_nay"] = p["ma_qg"].isin(ASEAN).astype(int)
    p["asean_thoi_diem"] = (p["ma_qg"].map(ASEAN_JOIN_YEAR) <= p["nam"]).astype(int)
    p["nhom"] = np.select([p["ma_qg"] == "VN", p["asean_hien_nay"] == 1],
                          ["Viet Nam", "ASEAN khac"], "Chau A khac")
    p["viet_nam"] = (p["ma_qg"] == "VN").astype(int)
    p["nhom_thu_nhap_hien_hanh"] = src["Income Group"]
    p["bac_thu_nhap"] = src["Income Group"].map(INCOME_ORDER).astype("Int64")
    p["gdp_ppp_usd"] = src["GDP PPP"]
    p["dan_so"] = src["Population"]
    p["gdp_dau_nguoi"] = src["GDP PC"]
    p["do_da_dang"] = src["Diversity Share"]
    p["eci"] = src["Ecosystem Complexity Index"]
    p["coi"] = src["Complexity Outlook Index"]
    p["goi"] = src["Growth Outlook Index"]
    p["hang_eci_the_gioi"] = src["hang_eci_the_gioi"]

    # --- tong san luong tu outputs (tham chieu parquet theo MANIFEST)
    o = read_raw("outputs", filters=[("Unit", "in", asia)],
                 columns=["Period", "Unit", "Dimension", "Outputs", "Outputs (Fractional)"])
    o["frac_anom"] = np.where(o["Outputs (Fractional)"] > o["Outputs"] + 1e-9, o["Outputs (Fractional)"], 0.0)
    g = o.groupby(["Period", "Unit", "Dimension"])
    tot = g["Outputs (Fractional)"].sum().unstack("Dimension")       # khong co ban ghi -> NaN (CL002)
    anom = g["frac_anom"].sum().unstack("Dimension")
    agg = pd.DataFrame({
        "sang_che": tot["T"], "bai_bao_kh": tot["S"], "nhan_hieu": tot["E"],
        "xuat_khau_ty_usd": tot["P"] / 1e9,
        "ty_le_bat_thuong_sang_che": (anom["T"] / tot["T"]).where(tot["T"] > 0, 0.0).where(tot["T"].notna()),
        "ty_le_bat_thuong_nhan_hieu": (anom["E"] / tot["E"]).where(tot["E"] > 0, 0.0).where(tot["E"].notna()),
    }).rename_axis(["nam", "ma_qg"]).reset_index()
    p = p.merge(agg, on=["nam", "ma_qg"], how="left", validate="1:1")

    c = read_raw("capabilities", filters=[("Unit", "in", asia)])
    c["dim"] = c["Field ID"].str[0]
    cnt = c.groupby(["Period", "Unit", "dim"])["Innovation Capability (Binary)"].sum().unstack("dim")
    cnt = cnt.rename(columns={k: f"so_nang_luc_{v}" for k, v in DIM_CODE.items()})
    cnt = cnt[[f"so_nang_luc_{v}" for v in DIM_CODE.values()]]
    cnt["so_nang_luc_tong"] = cnt.sum(axis=1)
    cnt["so_nang_luc_tuong_doi"] = c.groupby(["Period", "Unit"])["Relative Capability (Binary)"].sum()
    cnt["so_nang_luc_tuyet_doi"] = c.groupby(["Period", "Unit"])["Absolute Capability (Binary)"].sum()
    cnt = cnt.astype(int).rename_axis(["nam", "ma_qg"]).reset_index()
    p = p.merge(cnt, on=["nam", "ma_qg"], how="left", validate="1:1")

    p = derive_panel(p)
    raw_view = pd.DataFrame({
        "nam": src["Period"], "ma_qg": src["Unit"], "ten_qg": src["Unit Name"],
        "chau_luc_nguon": src["Continent"], "nhom_thu_nhap_hien_hanh": src["Income Group"],
        "gdp_ppp_usd": src["GDP PPP"], "dan_so": src["Population"], "gdp_dau_nguoi": src["GDP PC"],
        "do_da_dang": src["Diversity Share"], "eci": src["Ecosystem Complexity Index"],
        "coi": src["Complexity Outlook Index"], "goi": src["Growth Outlook Index"],
    })
    return p, raw_view, asia


def derive_panel(p):
    p = p.sort_values(["ma_qg", "nam"]).reset_index(drop=True)
    p["gdp_ppp_ty_usd"] = p["gdp_ppp_usd"] / 1e9
    p["dan_so_trieu"] = p["dan_so"] / 1e6
    p["ln_gdp_dau_nguoi"] = np.log(p["gdp_dau_nguoi"])
    prev = p.groupby("ma_qg")["gdp_dau_nguoi"].shift(1)
    p["tang_truong_gdp_dau_nguoi"] = (p["gdp_dau_nguoi"] / prev - 1) * 100
    p["hang_eci_chau_a"] = p.groupby("nam")["eci"].rank(ascending=False, method="min").astype(int)
    for col in ["sang_che", "bai_bao_kh", "nhan_hieu", "xuat_khau_ty_usd"]:
        p[f"{col}_tren_trieu_dan"] = p[col] / p["dan_so_trieu"]
        p[f"ln_{col}"] = np.log1p(p[col])
    p["flag_dan_so_lap_lai"] = (p["dan_so"] == p.groupby("ma_qg")["dan_so"].shift(1)).astype(int)
    order = ["nam", "ma_qg", "ten_qg", "chau_luc_nguon", "tieu_vung", "nhom", "asean_hien_nay",
             "asean_thoi_diem", "viet_nam", "nhom_thu_nhap_hien_hanh", "bac_thu_nhap",
             "gdp_ppp_usd", "dan_so", "gdp_dau_nguoi", "gdp_ppp_ty_usd", "dan_so_trieu",
             "ln_gdp_dau_nguoi", "tang_truong_gdp_dau_nguoi", "do_da_dang", "eci", "coi", "goi",
             "hang_eci_the_gioi", "hang_eci_chau_a"]
    for col in ["sang_che", "bai_bao_kh", "nhan_hieu", "xuat_khau_ty_usd"]:
        order += [col, f"{col}_tren_trieu_dan", f"ln_{col}"]
    order += [f"so_nang_luc_{v}" for v in DIM_CODE.values()]
    order += ["so_nang_luc_tong", "so_nang_luc_tuong_doi", "so_nang_luc_tuyet_doi",
              "flag_dan_so_lap_lai", "ty_le_bat_thuong_sang_che", "ty_le_bat_thuong_nhan_hieu"]
    assert set(order) == set(p.columns), set(order) ^ set(p.columns)
    return p[order]


OUTLIER_VARS = ["eci", "do_da_dang", "coi", "goi", "ln_gdp_dau_nguoi", "thay_doi_eci_10_nam",
                "ln_sang_che_tren_trieu_dan", "ln_bai_bao_kh_tren_trieu_dan",
                "ln_nhan_hieu_tren_trieu_dan", "ln_xuat_khau_ty_usd_tren_trieu_dan"]


def build_cross(panel):
    last = panel[panel["nam"] == LAST_YEAR].drop(columns=["nam", "tang_truong_gdp_dau_nguoi"]).copy()
    base = panel[panel["nam"] == BASE_YEAR].set_index("ma_qg")
    for col in ["eci", "do_da_dang", "so_nang_luc_tong", "gdp_dau_nguoi"]:
        last[f"{col}_2013"] = last["ma_qg"].map(base[col])
    last["thay_doi_eci_10_nam"] = last["eci"] - last["eci_2013"]
    last["thay_doi_do_da_dang_10_nam"] = last["do_da_dang"] - last["do_da_dang_2013"]
    last["thay_doi_so_nang_luc_10_nam"] = last["so_nang_luc_tong"] - last["so_nang_luc_tong_2013"]
    last["tang_truong_gdp_dau_nguoi_bq_10_nam"] = (
        (last["gdp_dau_nguoi"] / last["gdp_dau_nguoi_2013"]) ** (1 / 10) - 1) * 100

    pr = raw_csv("raw_unit_proximities_vn.csv")
    pr = pr[pr["Period"] == LAST_YEAR]
    other = np.where(pr["Unit 1"] == "VN", pr["Unit 2"], pr["Unit 1"])
    prox = pd.Series(pr["Proximity"].values, index=other)
    prox = prox[prox.index != "VN"]                       # bo cap VN-VN (CL015)
    assert not prox.index.duplicated().any()
    last["tuong_dong_voi_viet_nam"] = last["ma_qg"].map(prox)

    # FLAG ngoai lai (khong sua, khong xoa) - CL016
    tmp = last.copy()
    for col in ["sang_che", "bai_bao_kh", "nhan_hieu", "xuat_khau_ty_usd"]:
        tmp[f"ln_{col}_tren_trieu_dan"] = np.log1p(tmp[f"{col}_tren_trieu_dan"])
    flagged = {i: [] for i in tmp.index}
    for col in OUTLIER_VARS:
        s = tmp[col]
        med = s.median()
        mad = (s - med).abs().median()
        z = 0.6745 * (s - med) / mad
        for i in z[z.abs() > 3.5].index:
            flagged[i].append(col)
    last["flag_ngoai_lai"] = [int(bool(flagged[i])) for i in last.index]
    last["bien_ngoai_lai"] = ["; ".join(flagged[i]) if flagged[i] else "khong" for i in last.index]
    return last.reset_index(drop=True)


# ------------------------------------------------------------------ FIELD LEVEL
def build_field():
    cap = raw_csv("raw_capabilities_asean_2013_2023.csv")
    den = raw_csv("raw_densities_asean_2013_2023.csv").drop(columns="__index_level_0__")
    pot = raw_csv("raw_potentials_asean_2013_2023.csv")
    out = raw_csv("raw_outputs_asean_2013_2023.csv").drop(columns=["__index_level_0__", "Population"])
    fc = raw_csv("raw_field_complexities_2013_2023.csv")
    fields = raw_csv("raw_fields.csv").set_index("Field ID")
    units = raw_csv("raw_units_asia.csv")
    names = units[units["Period"] == LAST_YEAR].set_index("Unit")["Unit Name"]

    k = ["Period", "Unit", "Field ID"]
    m = cap.merge(den, on=k, how="left", validate="1:1").merge(pot, on=k, how="left", validate="1:1") \
           .merge(out.drop(columns="Dimension"), on=k, how="left", validate="1:1")
    m["dim"] = m["Field ID"].str[0]
    covered = set(map(tuple, out[["Unit", "Period", "Dimension"]].drop_duplicates().values))
    m["covered"] = [(u_, p_, d_) in covered for u_, p_, d_ in zip(m["Unit"], m["Period"], m["dim"])]

    cols = {"Outputs": "san_luong", "Outputs (Fractional)": "san_luong_phan_so",
            "Innovation Capability (Normalized)": "nang_luc_chuan_hoa",
            "Innovation Capability (Binary)": "co_nang_luc",
            "Relative Capability (Binary)": "nang_luc_tuong_doi",
            "Absolute Capability (Binary)": "nang_luc_tuyet_doi",
            "Relatedness Density": "mat_do_lien_quan", "Potential": "tiem_nang"}
    w = m.pivot(index=["Unit", "Field ID"], columns="Period", values=list(cols) + ["covered"])
    raw_view = pd.DataFrame(index=w.index)
    bool_src = {"Innovation Capability (Binary)", "Relative Capability (Binary)", "Absolute Capability (Binary)"}
    for src, dst in cols.items():
        for y in YRS:
            s = w[(src, y)]
            # pivot nhieu cot -> dtype object; khoi phuc kieu goc (khong doi gia tri)
            raw_view[f"{dst}_{y}"] = s.astype(bool) if src in bool_src else pd.to_numeric(s)
    covered_w = {y: w[("covered", y)].astype(bool) for y in YRS}

    clean = raw_view.copy()
    # CL001: khong co dong outputs trong quoc gia-nam-chieu CO ban ghi -> 0 (bang chung L06a)
    for y in YRS:
        for base in ["san_luong", "san_luong_phan_so"]:
            col = f"{base}_{y}"
            mask = clean[col].isna() & covered_w[y]
            clean.loc[mask, col] = 0.0
    # CL013: boolean -> 0/1 (bao toan gia tri)
    for base in ["co_nang_luc", "nang_luc_tuong_doi", "nang_luc_tuyet_doi"]:
        for y in YRS:
            clean[f"{base}_{y}"] = clean[f"{base}_{y}"].astype(bool).astype(int)

    fc23 = fc[fc["Period"] == LAST_YEAR].set_index("Field ID")
    idx = clean.index.to_frame(index=False)
    f = pd.DataFrame({
        "ma_qg": idx["Unit"], "ten_qg": idx["Unit"].map(names),
        "ma_linh_vuc": idx["Field ID"],
        "ten_linh_vuc": idx["Field ID"].map(fields["Field Name"]),
        "ma_nhom_linh_vuc": idx["Field ID"].map(fields["Domain ID"]),
        "nhom_linh_vuc": idx["Field ID"].map(fields["Domain Name"]),
        "chieu": idx["Field ID"].map(fields["Dimension Name"]),
    })
    body = clean.reset_index(drop=True)
    f = pd.concat([f, body], axis=1)
    f["do_phuc_tap_linh_vuc_2023"] = f["ma_linh_vuc"].map(fc23["Capability Complexity Index"])
    f["do_pho_bien_linh_vuc_2023"] = f["ma_linh_vuc"].map(fc23["Ubiquity Share"])
    f = derive_field(f)

    rv = raw_view.reset_index().rename(columns={"Unit": "ma_qg", "Field ID": "ma_linh_vuc"})
    rv["do_phuc_tap_linh_vuc_2023"] = rv["ma_linh_vuc"].map(fc23["Capability Complexity Index"])
    rv["do_pho_bien_linh_vuc_2023"] = rv["ma_linh_vuc"].map(fc23["Ubiquity Share"])
    rv["ten_linh_vuc"] = rv["ma_linh_vuc"].map(fields["Field Name"])
    rv["ten_qg"] = rv["ma_qg"].map(names)
    covered_df = pd.DataFrame({f"covered_{y}": covered_w[y].values for y in YRS})
    covered_df[["ma_qg", "ma_linh_vuc"]] = idx[["Unit", "Field ID"]].values
    return f, rv, covered_df


def derive_field(f):
    c0, c1 = f["co_nang_luc_2013"], f["co_nang_luc_2023"]
    f["gia_nhap_moi"] = c1.where(c0 == 0).astype("Int64")
    f["roi_bo"] = (1 - c1).where(c0 == 1).astype("Int64")
    f["ln_tiem_nang_2023"] = np.log1p(f["tiem_nang_2023"])
    f["ln_san_luong_2023"] = np.log1p(f["san_luong_2023"])
    f["chenh_lech_tiem_nang"] = f["ln_san_luong_2023"] - f["ln_tiem_nang_2023"]
    for y in YRS:
        f[f"flag_phan_so_vuot_toan_phan_{y}"] = (
            f[f"san_luong_phan_so_{y}"] > f[f"san_luong_{y}"] + 1e-9).astype(int)
    f["flag_tuyet_doi_khong_nhat_quan_2023"] = (
        (f["nang_luc_tuyet_doi_2023"] == 1) & (f["co_nang_luc_2023"] == 0)).astype(int)
    lead = ["ma_qg", "ten_qg", "ma_linh_vuc", "ten_linh_vuc", "ma_nhom_linh_vuc", "nhom_linh_vuc", "chieu"]
    order = lead.copy()
    for base in ["san_luong", "san_luong_phan_so", "nang_luc_chuan_hoa", "co_nang_luc",
                 "nang_luc_tuong_doi", "nang_luc_tuyet_doi", "mat_do_lien_quan", "tiem_nang"]:
        order += [f"{base}_{y}" for y in YRS]
    order += ["gia_nhap_moi", "roi_bo", "ln_tiem_nang_2023", "ln_san_luong_2023", "chenh_lech_tiem_nang",
              "do_phuc_tap_linh_vuc_2023", "do_pho_bien_linh_vuc_2023",
              "flag_phan_so_vuot_toan_phan_2013", "flag_phan_so_vuot_toan_phan_2023",
              "flag_tuyet_doi_khong_nhat_quan_2023"]
    assert set(order) == set(f.columns), set(order) ^ set(f.columns)
    return f[order].sort_values(["ma_qg", "chieu", "ma_linh_vuc"]).reset_index(drop=True)


# ------------------------------------------------------------------ DIFF
def diff(dataset, clean, raw_view, keys):
    c = clean.set_index(keys)
    r = raw_view.set_index(keys).reindex(c.index)
    rows = []
    for col in r.columns:
        a, b = r[col], c[col]
        same = (a == b) | (a.isna() & b.isna())
        if a.dtype == bool or b.dtype == bool:
            same = (a.astype(float) == b.astype(float)) | (a.isna() & b.isna())
        for key in same[~same.fillna(False)].index:
            rows.append({"dataset": dataset, "case": "|".join(map(str, key if isinstance(key, tuple) else (key,))),
                         "variable": col, "raw_value": a[key], "clean_value": b[key]})
    return pd.DataFrame(rows, columns=["dataset", "case", "variable", "raw_value", "clean_value"])


def assign_log(d):
    out_cols = d["variable"].str.match(r"^san_luong(_phan_so)?_(2013|2023)$")
    rule = out_cols & d["raw_value"].isna() & (d["clean_value"] == 0)
    d["log_id"] = np.where(rule, "CL001", "UNLOGGED")
    d["reason"] = np.where(rule, "vang mat -> 0 (xem CL001)", "")
    d["evidence"] = np.where(rule, "L06a; nang_luc_chuan_hoa = 0", "")
    d["downstream_effect"] = np.select(
        [rule & d["variable"].eq("san_luong_2023"), rule],
        ["ln_san_luong_2023; chenh_lech_tiem_nang; flag_phan_so_2023", "flag_phan_so_vuot_toan_phan"], "")
    return d


# ------------------------------------------------------------------ LOG
def cleaning_log(n_cl001, audit, panel, field):
    n_nocov_field = int(field[["san_luong_2013", "san_luong_2023"]].isna().sum().sum())
    nocov_panel = {c: int(panel[c].isna().sum()) for c in ["sang_che", "bai_bao_kh", "nhan_hieu"]}
    L = []

    def add(**kw):
        base = dict(log_id="", case_id="", variable="", raw_value="", issue_type="", validation_rule="",
                    evidence_source="", review_result="", decision="", clean_value="", decision_code="",
                    rationale="", downstream_variables_affected="", verified="PENDING", notes="", n_cells_changed=0)
        base.update(kw)
        L.append(base)

    add(log_id="CL001", case_id=f"ASEAN x linh vuc x {{2013,2023}}; {n_cl001} o",
        variable="san_luong_{y}, san_luong_phan_so_{y}", raw_value="(khong co dong trong outputs)",
        issue_type="sparse_absence", validation_rule="Quoc gia-nam-chieu co >=1 ban ghi outputs; dong vang mat",
        evidence_source="Kiem tra L06a/L06b (capabilities x outputs); outputs.parquet",
        review_result="Moi dong vang mat deu co Normalized Capability = 0 va Binary = False; khong co ngoai le",
        decision="RECODE", clean_value="0", decision_code="R",
        rationale="Nguon tinh nang luc nhu san luong = 0 cho cac dong nay; README khong viet ro quy tac -> do tin cay MEDIUM",
        downstream_variables_affected="ln_san_luong_2023; chenh_lech_tiem_nang; flag_phan_so_vuot_toan_phan_*",
        notes="Xem UD06 (can xac nhan tu nha san xuat du lieu). Phan tich do nhay: coi cac o nay la missing.",
        n_cells_changed=n_cl001)
    add(log_id="CL002", case_id=f"Panel: sang_che {nocov_panel['sang_che']}, bai_bao_kh {nocov_panel['bai_bao_kh']}, "
                                f"nhan_hieu {nocov_panel['nhan_hieu']} quoc gia-nam; Field: {n_nocov_field} o (TL: T, E)",
        variable="sang_che, bai_bao_kh, nhan_hieu, (*_tren_trieu_dan, ln_*); san_luong_*",
        raw_value="(khong co ban ghi nao cho ca quoc gia-nam-chieu)", issue_type="no_coverage",
        validation_rule="Phan biet 'khong co ban ghi' voi 'san luong = 0'",
        evidence_source="06_QC/pre/outputs_no_record_country_year_dim.csv",
        review_result="Khong the phan biet 'khong phat sinh' voi 'khong duoc bao phu'",
        decision="KEEP AS MISSING", clean_value="NA (o trong)", decision_code="K",
        rationale="MISSING != ZERO. Ban du_lieu_jamovi_jasp truoc day da gan 0 -> da sua o ban nay",
        downstream_variables_affected="*_tren_trieu_dan, ln_*", notes="Missing tap trung o nuoc nho/thu nhap thap -> FLAG do nhay")
    add(log_id="CL003", case_id="47 nuoc, nam 2023", variable="dan_so (Population)",
        raw_value="Population_2023 = Population_2022", issue_type="suspected_carry_forward",
        validation_rule="L08 (soft plausibility)", evidence_source="raw_units_asia.csv",
        review_result="47/47 nuoc trung tuyet doi; nam khac 0 truong hop",
        decision="KEEP + FLAG (UNRESOLVED)", clean_value="giu nguyen", decision_code="U",
        rationale="Khong co source evidence (vd WDI) duoc cung cap de thay the; khong doan",
        downstream_variables_affected="dan_so_trieu, gdp_dau_nguoi (nguon da tinh), *_tren_trieu_dan 2023, "
                                      "tang_truong_gdp_dau_nguoi 2023, tang_truong_gdp_dau_nguoi_bq_10_nam",
        notes="Bien flag_dan_so_lap_lai = 1 o 47 dong 2023. Xem UD01")
    add(log_id="CL004", case_id="47 nuoc x 23 nam", variable="nhom_thu_nhap_hien_hanh (Income Group)",
        raw_value="Hang so qua 23 nam o ca 47 nuoc", issue_type="time_invariant_attribute",
        validation_rule="Phan loai WB thay doi theo nam", evidence_source="06_QC/pre/category_audit.csv",
        review_result="Gia tri hop le nhung la phan loai hien hanh gan nguoc cho moi nam",
        decision="KEEP; doi ten bien de khong hieu nham", clean_value="giu nguyen gia tri", decision_code="F",
        rationale="Dung lam bien thoi gian se sai thoi diem (anachronism)", downstream_variables_affected="bac_thu_nhap",
        notes="Xem UD07")
    add(log_id="CL005", case_id=f"{audit['L04']} dong (chau A, moi nam); T {audit['L04_by_dim'].get('T', 0)}, E {audit['L04_by_dim'].get('E', 0)}",
        variable="Outputs (Fractional) vs Outputs", raw_value="Fractional > Full (toi 8 lan)",
        issue_type="cross_variable_logic", validation_rule="L04: Fractional <= Full (suy ra tu README)",
        evidence_source="06_QC/pre/violations_L04.csv; fractional_anomaly_share.csv",
        review_result=f"{audit['share10']} quoc gia-nam-chieu co >10% tong phan so den tu cac dong nay",
        decision="KEEP + FLAG (UNRESOLVED)", clean_value="giu nguyen", decision_code="U",
        rationale="Quy tac khong duoc README neu tuong minh; khong xac dinh duoc gia tri dung",
        downstream_variables_affected="sang_che, nhan_hieu va bien dan xuat; san_luong_phan_so_*",
        notes="Bien ty_le_bat_thuong_sang_che/_nhan_hieu (panel) va flag_phan_so_vuot_toan_phan_* (field). Xem UD02")
    add(log_id="CL006", case_id=f"{audit['L05']} dong E (chu yeu CN 2019)", variable="Outputs (E)",
        raw_value="so khong nguyen (vd 1308.4)", issue_type="non_integer_count", validation_rule="L05",
        evidence_source="06_QC/pre/violations_L05.csv", review_result="Co the la dem da nguon/da lop; khong xac minh duoc",
        decision="KEEP + FLAG (UNRESOLVED)", clean_value="giu nguyen", decision_code="U",
        rationale="Khong lam tron, khong doan", downstream_variables_affected="san_luong_* (E)", notes="Xem UD03")
    add(log_id="CL007", case_id=f"{audit['L03']} dong 2023: OM P-8906, IR P-8406, IN P-1001, QA E-37_1, QA E-43_10, MY P-6215",
        variable="Absolute/Innovation Capability (Binary)", raw_value="Absolute=True, Innovation=False",
        issue_type="cross_variable_logic", validation_rule="L03: Innovation = Absolute OR Relative (thuc nghiem 99,9998%)",
        evidence_source="06_QC/pre/violations_L03.csv", review_result="Quy tac khong co trong README",
        decision="KEEP + FLAG (UNRESOLVED)", clean_value="giu nguyen", decision_code="U",
        rationale="RULE NOT ESTABLISHED - DO NOT AUTO-CORRECT", downstream_variables_affected="so_nang_luc_tuyet_doi; flag_tuyet_doi_khong_nhat_quan_2023",
        notes="Xem UD04")
    add(log_id="CL008", case_id=f"{audit['fc_missing']} field-year; {audit['dens_missing']} dong density (chau A)",
        variable="mat_do_lien_quan_*, do_phuc_tap_linh_vuc_2023, do_pho_bien_linh_vuc_2023",
        raw_value="(khong co dong)", issue_type="structural_missing",
        validation_rule="L09: thieu density <=> field-year khong co complexity", evidence_source="06_QC/pre/range_logic_audit.csv",
        review_result="100% trung khop", decision="KEEP AS STRUCTURAL MISSING", clean_value="NA", decision_code="K",
        rationale="Linh vuc khong duoc tinh do phuc tap trong nam do", downstream_variables_affected="khong")
    add(log_id="CL009", case_id="KP, YE (23 nam)", variable="gdp_ppp_usd, gdp_dau_nguoi", raw_value="NA",
        issue_type="system_missing", validation_rule="", evidence_source="raw_units_asia.csv",
        review_result="Nguon khong co GDP", decision="KEEP MISSING", clean_value="NA", decision_code="K",
        rationale="Khong impute", downstream_variables_affected="gdp_ppp_ty_usd, ln_gdp_dau_nguoi, tang_truong_*")
    add(log_id="CL010", case_id="Toan chau A 2022-2023", variable="nhan_hieu", raw_value="Tong E: -21,7% (2022), -44,2% (2023); CN -55% (2023)",
        issue_type="possible_recency_truncation", validation_rule="Soft plausibility (dut gay chuoi)",
        evidence_source="06_QC/pre/outputs_yoy_change_pct_asia.csv; trademarks_top10_2020_2023.csv",
        review_result="Khong xac minh duoc la thay doi thuc hay do do tre/thay doi nguon",
        decision="KEEP + FLAG", clean_value="giu nguyen", decision_code="F",
        rationale="Khong cat bo; can phan tich do nhay loai 2022-2023 cho chieu E", downstream_variables_affected="nhan_hieu va dan xuat",
        notes="Xem UD05")
    add(log_id="CL011", case_id=f"{audit['dupnames']} dong fields", variable="ten_linh_vuc", raw_value="Ten trung giua cac Field ID khac nhau",
        issue_type="duplicate_label", validation_rule="Field ID la khoa duy nhat", evidence_source="06_QC/pre/duplicate_field_names.csv",
        review_result="Khac Field ID va/hoac Domain -> la cac linh vuc khac nhau", decision="KEEP", clean_value="giu nguyen",
        decision_code="K", rationale="Khong gop; dung ma_linh_vuc de nhan dien")
    add(log_id="CL012", case_id="Turkiye (23 dong), 1 ten linh vuc co dau nhay cong", variable="ten_qg, ten_linh_vuc",
        raw_value="ky tu Unicode", issue_type="encoding", validation_rule="UTF-8 hop le",
        evidence_source="06_QC/pre/structural_audit.csv", review_result="Ma hoa hop le", decision="KEEP", clean_value="giu nguyen (UTF-8)",
        decision_code="K", rationale="Ban du_lieu_jamovi_jasp truoc day da bo dau (ASCII) -> hoan nguyen")
    add(log_id="CL013", case_id="Toan bo field-level", variable="co_nang_luc_*, nang_luc_tuong_doi_*, nang_luc_tuyet_doi_*",
        raw_value="True/False", issue_type="type_conversion", validation_rule="Bao toan gia tri: True=1, False=0",
        evidence_source="README", review_result="Khong mat thong tin", decision="RECODE (dinh dang)", clean_value="1/0",
        decision_code="R", rationale="jamovi/JASP doc 0/1 on dinh hon", downstream_variables_affected="gia_nhap_moi, roi_bo",
        notes="Thay doi bieu dien, khong thay doi gia tri -> khong tinh la changed cell trong diff")
    add(log_id="CL014", case_id="Moi bien", variable="Ten bien", raw_value="Ten tieng Anh co khoang trang",
        issue_type="rename", validation_rule="Anh xa 1-1 trong 03_DATA_DICTIONARY (cot raw_source)",
        evidence_source="03_DATA_DICTIONARY.csv", review_result="", decision="RENAME", clean_value="snake_case",
        decision_code="R", rationale="Tranh loi ten bien trong jamovi/JASP")
    add(log_id="CL015", case_id="VN", variable="tuong_dong_voi_viet_nam", raw_value="cap VN-VN", issue_type="structural_missing",
        validation_rule="Proximity voi chinh minh khong co nghia", evidence_source="raw_unit_proximities_vn.csv",
        review_result="", decision="NA o dong VN", clean_value="NA", decision_code="K", rationale="Missing cau truc")
    add(log_id="CL016", case_id="Cross-section 2023", variable=", ".join(OUTLIER_VARS),
        raw_value="", issue_type="outlier", validation_rule="|robust z| > 3.5 (Iglewicz & Hoaglin 1993)",
        evidence_source="02_CLEAN/.../2_chau_a_cat_ngang_2023.csv (flag_ngoai_lai)", review_result="",
        decision="KEEP + FLAG", clean_value="giu nguyen", decision_code="F",
        rationale="OUTLIER != ERROR; dung cho phan tich do nhay", downstream_variables_affected="flag_ngoai_lai, bien_ngoai_lai")
    add(log_id="CL017", case_id="47 nuoc", variable="tieu_vung, asean_hien_nay, asean_thoi_diem, nhom",
        raw_value="(bien moi)", issue_type="derived_classification",
        validation_rule="UN M49; ASEAN Secretariat (nam gia nhap)", evidence_source="scripts/common.py",
        review_result="TL gia nhap 2025 -> asean_thoi_diem = 0 cho 2001-2023", decision="DERIVE", clean_value="",
        decision_code="R", rationale="Phan loai co nguon ben ngoai, khong tu dat")
    add(log_id="CL018", case_id="coi, goi", variable="coi, goi", raw_value="thang do -22..498 / 4..675",
        issue_type="documentation_mismatch", validation_rule="README vi du 0.75 / 0.82", evidence_source="README.md",
        review_result="Vi du README khong khop thang do du lieu", decision="KEEP", clean_value="giu nguyen", decision_code="K",
        rationale="RULE NOT ESTABLISHED - DO NOT AUTO-CORRECT; can than khi dien giai do lon")
    return pd.DataFrame(L)


UNRESOLVED = [
    dict(ud_id="UD01", case_id="47 nuoc, 2023", variable="dan_so (-> gdp_dau_nguoi 2023)", raw_value="= gia tri 2022",
         missing_evidence="Dan so 2023 tu WDI/UN WPP; xac nhan cua nha san xuat ICO",
         question="Co thay dan so 2023 bang nguon chinh thuc khong, hay giu va bao cao?",
         recommended_options="(a) Giu + bao cao (mac dinh hien tai); (b) Thay bang WDI 2023 va tinh lai GDP/nguoi, ghi log C; (c) Dat missing cho bien theo dau nguoi 2023"),
    dict(ud_id="UD02", case_id="10.052 dong T/E chau A", variable="Outputs (Fractional)", raw_value="> Outputs",
         missing_evidence="Tai lieu phuong phap dem phan so cua ICO",
         question="Fractional > Full la dung theo phuong phap (vd dem theo don khac nhau) hay loi?",
         recommended_options="(a) Giu (mac dinh); (b) Do nhay: loai quoc gia-nam co ty_le_bat_thuong > 0,10; (c) Neu xac nhan loi: dat missing cac dong do"),
    dict(ud_id="UD03", case_id="134 dong E", variable="Outputs (E)", raw_value="so khong nguyen",
         missing_evidence="Phuong phap dem nhan hieu", question="Dem toan phan nhan hieu co the khong nguyen?",
         recommended_options="(a) Giu; (b) Dung dem phan so cho chieu E (da la mac dinh o panel)"),
    dict(ud_id="UD04", case_id="6 dong 2023", variable="Innovation/Absolute Capability (Binary)", raw_value="Abs=1, Inn=0",
         missing_evidence="Quy tac xac dinh Innovation Capability (Binary)", question="Innovation co phai = Absolute OR Relative?",
         recommended_options="(a) Giu (mac dinh); (b) Neu nguon xac nhan quy tac: sua Innovation = 1, ghi log C"),
    dict(ud_id="UD05", case_id="Chieu E 2022-2023", variable="nhan_hieu", raw_value="giam 22% va 44%",
         missing_evidence="Thong tin do tre/do bao phu du lieu nhan hieu", question="Co loai 2022-2023 cho chieu E khoi phan tich xu huong?",
         recommended_options="(a) Giu + do nhay; (b) Gioi han phan tich E den 2021"),
    dict(ud_id="UD06", case_id=f"CL001", variable="san_luong_*", raw_value="dong vang mat",
         missing_evidence="Xac nhan tu ICO rang dong vang mat = 0", question="Chap nhan quy tac vang mat = 0?",
         recommended_options="(a) Chap nhan (mac dinh, co bang chung L06a); (b) Do nhay: coi la missing"),
    dict(ud_id="UD07", case_id="47 nuoc", variable="nhom_thu_nhap_hien_hanh", raw_value="hang so theo thoi gian",
         missing_evidence="Lich su phan loai WB theo nam (FY)", question="Can bien thu nhap theo tung nam khong?",
         recommended_options="(a) Chi dung cho phan tich cat ngang (mac dinh); (b) Bo sung bang lich su WB, ghi log"),
]


# ------------------------------------------------------------------ DICTIONARY
def check_valid(s, valid):
    s = pd.to_numeric(s, errors="coerce").dropna()
    if valid.startswith("[0,1]"):
        return int((~s.between(0, 1)).sum())
    if valid.startswith(">= 0"):
        return int((s < 0).sum())
    if valid.startswith("> 0"):
        return int((s <= 0).sum())
    if valid.startswith("0/1"):
        return int((~s.isin([0, 1])).sum())
    if valid == "1-4":
        return int((~s.isin([1, 2, 3, 4])).sum())
    if valid == "1-193":
        return int((~s.between(1, 193)).sum())
    if valid == "1-47":
        return int((~s.between(1, 47)).sum())
    if valid == "0-2508":
        return int((~s.between(0, 2508)).sum())
    if valid == "2001-2023":
        return int((~s.between(2001, 2023)).sum())
    return None


def dictionary(datasets):
    rows = []
    for dname, (df, metas) in datasets.items():
        for col in df.columns:
            m = metas[col]
            s = df[col]
            num = pd.api.types.is_numeric_dtype(s)
            nv = int(s.notna().sum())
            rows.append({
                "dataset": dname, "variable": col, "label": m["label"], "role": m["role"],
                "data_type": m["data_type"], "measurement_level": m["measure"],
                "valid_values_range": m["valid"], "missing_code": "o trong",
                "n_valid": nv, "n_missing": int(len(s) - nv), "n_unique": int(s.nunique()),
                "min": s.min() if num and nv else "", "max": s.max() if num and nv else "",
                "n_out_of_range": check_valid(s, m["valid"]) if num else "",
                "raw_source": m["raw_source"], "source_of_rule": m["source_of_rule"],
                "confidence": m["confidence"], "cleaning_log_ref": m["cleaning_rule"],
            })
    return pd.DataFrame(rows)


def main():
    import json
    audit = json.loads((PKG / "06_QC/pre/audit_summary.json").read_text())
    rl = {r["check_id"]: r["n_violations"] for r in audit["range_logic"]}

    panel, panel_raw, asia = build_panel()
    cross = build_cross(panel)
    field, field_raw, covered = build_field()
    vn = field[field["ma_qg"] == "VN"].reset_index(drop=True)

    d_panel = diff("1_panel", panel, panel_raw, ["nam", "ma_qg"])
    cross_raw = panel_raw[panel_raw["nam"] == LAST_YEAR].drop(columns="nam")
    d_cross = diff("2_cat_ngang", cross, cross_raw, ["ma_qg"])
    d_field = diff("3_asean_linh_vuc", field, field_raw, ["ma_qg", "ma_linh_vuc"])
    d_vn = diff("4_viet_nam_linh_vuc", vn, field_raw[field_raw["ma_qg"] == "VN"], ["ma_qg", "ma_linh_vuc"])
    d = assign_log(pd.concat([d_panel, d_cross, d_field, d_vn], ignore_index=True))

    n_cl001 = int(((d["dataset"] == "3_asean_linh_vuc") & (d["log_id"] == "CL001")).sum())
    log = cleaning_log(n_cl001, {
        "L03": rl["L03"], "L04": rl["L04"], "L05": rl["L05"], "L04_by_dim": audit["L04_by_dim"],
        "share10": audit["frac_anomaly_share_gt10pct"], "fc_missing": audit["fc_missing_field_years"],
        "dens_missing": audit["density_rows_missing_asia"], "dupnames": audit["duplicate_field_name_rows"],
    }, panel, field)

    cd = CLEAN_DIR
    write_csv(panel, cd / "1_panel_chau_a_2001_2023.csv")
    write_csv(cross, cd / "2_chau_a_cat_ngang_2023.csv")
    write_csv(field, cd / "3_asean_linh_vuc_2013_2023.csv")
    write_csv(vn, cd / "4_viet_nam_linh_vuc_2013_2023.csv")
    write_csv(log, PKG / "04_CLEANING_LOG.csv")
    write_csv(d, PKG / "05_RAW_CLEAN_DIFF.csv")
    write_csv(pd.DataFrame(UNRESOLVED), PKG / "08_UNRESOLVED_DECISIONS.csv")

    cross_meta = {**meta.UNIT, **meta.CROSS_EXTRA}
    dd = dictionary({"1_panel": (panel, meta.UNIT), "2_cat_ngang": (cross, cross_meta),
                     "3_asean_linh_vuc": (field, meta.FIELD), "4_viet_nam_linh_vuc": (vn, meta.FIELD)})
    write_csv(dd, PKG / "03_DATA_DICTIONARY.csv")

    print(f"panel {panel.shape}, cross {cross.shape}, field {field.shape}, vn {vn.shape}")
    print("diff by dataset/log_id:\n", d.groupby(["dataset", "log_id"]).size())
    print("dictionary out-of-range:", dd.loc[dd["n_out_of_range"].replace("", 0).astype(float) > 0,
                                              ["dataset", "variable", "n_out_of_range"]].to_string())


if __name__ == "__main__":
    main()

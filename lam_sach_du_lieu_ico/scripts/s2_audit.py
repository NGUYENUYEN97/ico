"""BUOC AUDIT (truoc lam sach): kiem tra cau truc, category, range/logic, missing, duplicate
tren du lieu nguon trong pham vi nghien cuu. Chi DOC va BAO CAO, khong sua gi.
"""
import re

import numpy as np
import pandas as pd

from common import (ASEAN, BASE_YEAR, LAST_YEAR, QC_DIR, YEARS, asia_units, read_raw,
                    write_csv, write_json)

OUT = QC_DIR / "pre"
KEYS = {
    "units": ["Period", "Unit"], "unit_complexities": ["Period", "Unit"],
    "fields": ["Field ID"], "field_complexities": ["Period", "Field ID"],
    "outputs": ["Period", "Unit", "Field ID"], "capabilities": ["Period", "Unit", "Field ID"],
    "densities": ["Period", "Unit", "Field ID"], "potentials": ["Period", "Unit", "Field ID"],
    "unit_proximities": ["Period", "Unit 1", "Unit 2"],
}
ID_PATTERN = {"Unit": r"^[A-Z]{2}$", "Unit 1": r"^[A-Z]{2}$", "Unit 2": r"^[A-Z]{2}$",
              "Field ID": r"^[TSPE] - \S+$"}


def load(asia):
    t = {
        "units": read_raw("units", filters=[("Unit", "in", asia)]),
        "unit_complexities": read_raw("unit_complexities", filters=[("Unit", "in", asia)]),
        "fields": read_raw("fields"),
        "field_complexities": read_raw("field_complexities"),
        "outputs": read_raw("outputs", filters=[("Unit", "in", asia)]),
        "capabilities": read_raw("capabilities", filters=[("Unit", "in", asia)]),
        "densities": read_raw("densities", filters=[("Unit", "in", asia)]),
        "potentials": read_raw("potentials", filters=[("Unit", "in", asia)]),
        "unit_proximities": read_raw("unit_proximities"),
    }
    return t


def structural(t):
    rows = []
    for name, df in t.items():
        key = KEYS[name]
        non_ascii = sum(df[c].astype(str).str.contains(r"[^\x00-\x7F]", regex=True).sum()
                        for c in df.columns if df[c].dtype == object or str(df[c].dtype).startswith("str"))
        malformed = 0
        for c in key:
            if c in ID_PATTERN:
                malformed += (~df[c].astype(str).str.match(ID_PATTERN[c])).sum()
        data_cols = [c for c in df.columns if c != "__index_level_0__"]
        rows.append({
            "table": name, "rows": len(df), "columns": df.shape[1], "key": " + ".join(key),
            "duplicate_column_names": int(pd.Index(df.columns).duplicated().sum()),
            "empty_columns": int((df.isna().all()).sum()),
            "exact_duplicate_rows": int(df[data_cols].duplicated().sum()),
            "duplicate_keys": int(df.duplicated(key).sum()),
            "missing_ids": int(df[key].isna().any(axis=1).sum()),
            "malformed_ids": int(malformed),
            "cells_non_ascii": int(non_ascii),
            "unit_of_analysis": " x ".join(key),
            "structure": "long",
        })
    return pd.DataFrame(rows)


def categories(t):
    rows = []
    spec = {"units": ["Unit", "Unit Name", "Continent", "Income Group"],
            "fields": ["Dimension Name", "Domain ID", "Domain Name"],
            "outputs": ["Dimension"]}
    for name, cols in spec.items():
        for c in cols:
            s = t[name][c].astype(str)
            vc = s.value_counts()
            lower = s.str.strip().str.lower()
            rows.append({
                "table": name, "variable": c, "n_unique": int(s.nunique()),
                "values": "; ".join(f"{k} ({v})" for k, v in vc.head(12).items())
                          + (" ..." if len(vc) > 12 else ""),
                "leading_trailing_space": int((s != s.str.strip()).sum()),
                "case_only_variants": int(s.nunique() - lower.nunique()),
                "numeric_text_mixed": int(s.str.fullmatch(r"\d+(\.\d+)?").sum()),
            })
    # Gia tri hang so theo thoi gian (thuoc tinh dang le phai bien thien)
    u = t["units"]
    for c in ["Unit Name", "Continent", "Income Group"]:
        changes = int((u.groupby("Unit")[c].nunique() > 1).sum())
        rows.append({"table": "units", "variable": f"{c} [so nuoc thay doi qua 23 nam]",
                     "n_unique": changes, "values": "", "leading_trailing_space": 0,
                     "case_only_variants": 0, "numeric_text_mixed": 0})
    # Ten linh vuc trung nhau giua cac Field ID khac nhau
    f = t["fields"]
    dup = f[f.duplicated(["Dimension Name", "Field Name"], keep=False)].sort_values("Field Name")
    return pd.DataFrame(rows), dup


def range_logic(t):
    rows, ex = [], {}

    def add(cid, table, rule, source, conf, mask, df, cols, kind):
        n_bad = int(mask.sum())
        rows.append({"check_id": cid, "table": table, "kind": kind, "rule": rule,
                     "source_of_rule": source, "confidence": conf,
                     "n_checked": int(len(mask)), "n_violations": n_bad})
        if n_bad:
            ex[cid] = df.loc[mask, cols]

    u, uc, o, c = t["units"], t["unit_complexities"], t["outputs"], t["capabilities"]
    d, p, fc, f = t["densities"], t["potentials"], t["field_complexities"], t["fields"]
    up = t["unit_proximities"]
    uk = ["Period", "Unit"]
    add("R01", "units", "Period trong 2001-2023", "README (Period = nam) + pham vi quan sat", "HIGH",
        ~u["Period"].isin(YEARS), u, uk, "hard_range")
    for col in ["GDP PPP", "Population", "GDP PC"]:
        add(f"R02_{col}", "units", f"{col} > 0 (khi khong missing)", "Dinh nghia bien (README)", "HIGH",
            u[col].notna() & (u[col] <= 0), u, uk + [col], "hard_range")
    add("R03", "unit_complexities", "Diversity Share trong [0,1]", "README: 'Fraction of fields'", "HIGH",
        ~uc["Diversity Share"].between(0, 1), uc, uk + ["Diversity Share"], "hard_range")
    add("R04", "outputs", "Outputs >= 0 va Outputs (Fractional) >= 0", "README: so luong san pham", "HIGH",
        (o["Outputs"] < 0) | (o["Outputs (Fractional)"] < 0), o, ["Period", "Unit", "Field ID"], "hard_range")
    add("R05", "capabilities", "Innovation Capability (Normalized) trong [0,1]", "README: Range [0,1]", "HIGH",
        ~c["Innovation Capability (Normalized)"].between(0, 1), c, ["Period", "Unit", "Field ID"], "hard_range")
    add("R06", "densities", "Relatedness Density trong [0,1]", "README: ti le linh vuc lien quan", "HIGH",
        ~d["Relatedness Density"].between(0, 1), d, ["Period", "Unit", "Field ID"], "hard_range")
    add("R07", "potentials", "Potential >= 0", "README: so san pham ky vong", "HIGH",
        p["Potential"] < 0, p, ["Period", "Unit", "Field ID"], "hard_range")
    add("R08", "field_complexities", "Ubiquity Share trong [0,1]", "README: 'Fraction of places'", "HIGH",
        ~fc["Ubiquity Share"].between(0, 1), fc, ["Period", "Field ID"], "hard_range")
    add("R09", "unit_proximities", "Proximity trong [0,1]", "README: xac suat", "HIGH",
        ~up["Proximity"].between(0, 1), up, ["Unit 1", "Unit 2", "Proximity"], "hard_range")

    # --- Logic giua cac bien / giua cac file
    gdp = u.dropna(subset=["GDP PPP", "GDP PC"])
    rel = (gdp["GDP PPP"] / gdp["Population"] / gdp["GDP PC"] - 1).abs()
    add("L01", "units", "GDP PC = GDP PPP / Population", "Dinh nghia GDP binh quan dau nguoi", "HIGH",
        rel > 1e-9, gdp, uk, "cross_variable")
    m = c.groupby(uk)["Innovation Capability (Normalized)"].mean().rename("mean_norm").reset_index().merge(uc, on=uk)
    add("L02", "unit_complexities x capabilities", "Diversity Share = trung binh Normalized Capability tren 2.508 linh vuc",
        "Kiem tra thuc nghiem (README khong neu cong thuc)", "MEDIUM",
        (m["mean_norm"] - m["Diversity Share"]).abs() > 1e-12, m, uk, "derived_consistency")
    I, A, R = (c["Innovation Capability (Binary)"], c["Absolute Capability (Binary)"],
               c["Relative Capability (Binary)"])
    add("L03", "capabilities", "Innovation (Binary) = Absolute OR Relative",
        "Suy ra tu README (Innovation = 'basic presence'); khong co cong thuc chinh thuc", "LOW",
        I != (A | R), c, ["Period", "Unit", "Field ID", "Innovation Capability (Normalized)",
                          "Innovation Capability (Binary)", "Absolute Capability (Binary)",
                          "Relative Capability (Binary)"], "cross_variable")
    add("L04", "outputs", "Outputs (Fractional) <= Outputs",
        "Suy ra tu README: fractional = 'adjusted count ... 0.33 if shared across 3 fields'", "MEDIUM",
        o["Outputs (Fractional)"] > o["Outputs"] + 1e-9, o,
        ["Period", "Unit", "Dimension", "Field ID", "Outputs", "Outputs (Fractional)"], "cross_variable")
    tse = o["Dimension"].isin(["T", "S", "E"])
    add("L05", "outputs", "Outputs (dem toan phan) la so nguyen voi T, S, E",
        "Suy ra: bang sang che / bai bao / nhan hieu la don vi dem", "MEDIUM",
        tse & (o["Outputs"] % 1 != 0), o, ["Period", "Unit", "Dimension", "Field ID", "Outputs"], "cross_variable")
    k3 = ["Period", "Unit", "Field ID"]
    mo = c[k3 + ["Innovation Capability (Normalized)"]].merge(o[k3 + ["Outputs"]], on=k3, how="left")
    add("L06a", "capabilities x outputs", "Khong co dong outputs => Normalized Capability = 0",
        "Kiem tra thuc nghiem giua 2 file", "MEDIUM",
        mo["Outputs"].isna() & (mo["Innovation Capability (Normalized)"] > 0), mo, k3, "cross_file")
    add("L06b", "capabilities x outputs", "Outputs > 0 => Normalized Capability > 0",
        "Kiem tra thuc nghiem giua 2 file", "MEDIUM",
        (mo["Outputs"] > 0) & (mo["Innovation Capability (Normalized)"] == 0), mo, k3, "cross_file")
    pm = o[["Period", "Unit", "Population"]].drop_duplicates().merge(
        u[uk + ["Population"]], on=uk, suffixes=("", "_units"))
    add("L07", "outputs x units", "Population trong outputs = Population trong units",
        "Hai file cung mo ta dan so", "HIGH", pm["Population"] != pm["Population_units"], pm, uk, "cross_file")
    pop = u.pivot(index="Unit", columns="Period", values="Population")
    same = (pop.diff(axis=1) == 0).stack().rename("same").reset_index()
    add("L08", "units", "Population khong trung khop tuyet doi voi nam truoc",
        "Soft check: dan so quoc gia hau nhu khong bao gio dung yen chinh xac", "MEDIUM",
        same["same"], same, ["Unit", "Period"], "soft_plausibility")
    dk = c[k3].merge(d[k3], on=k3, how="left", indicator=True)
    dmiss = dk[dk["_merge"] == "left_only"]
    fcmiss = set(map(tuple, pd.MultiIndex.from_product([YEARS, f["Field ID"]]).difference(
        pd.MultiIndex.from_frame(fc[["Period", "Field ID"]]))))
    explained = dmiss.apply(lambda r: (r["Period"], r["Field ID"]) in fcmiss, axis=1)
    add("L09", "densities x field_complexities", "Thieu Relatedness Density chi xay ra o field-year khong co Field Complexity",
        "Kiem tra thuc nghiem (missing cau truc)", "MEDIUM", ~explained, dmiss, k3, "structural_missing")
    add("L10", "outputs x fields", "Dimension = tien to Field ID", "README (T/S/P/E)", "HIGH",
        o["Dimension"] != o["Field ID"].str[0], o, k3, "cross_variable")
    add("L11", "fields", "Domain ID cung tien to voi Field ID", "README", "HIGH",
        f["Domain ID"].str[0] != f["Field ID"].str[0], f, ["Field ID", "Domain ID"], "cross_variable")

    # Thong tin tong hop cho bao cao
    info = {
        "fc_missing_field_years": len(fcmiss),
        "density_rows_missing_asia": int(len(dmiss)),
        "L04_by_dim": o.loc[o["Outputs (Fractional)"] > o["Outputs"] + 1e-9, "Dimension"].value_counts().to_dict(),
    }
    return pd.DataFrame(rows), ex, info


def coverage(t, asia):
    o = t["outputs"]
    cov = o.groupby(["Unit", "Period", "Dimension"]).size().unstack("Dimension")
    full = pd.MultiIndex.from_product([asia, YEARS], names=["Unit", "Period"])
    cov = cov.reindex(full)
    rows = []
    for dim in ["T", "S", "E", "P"]:
        miss = cov[dim].isna()
        for unit, g in miss[miss].reset_index().groupby("Unit"):
            rows.append({"Dimension": dim, "Unit": unit, "n_years_no_record": len(g),
                         "years": ",".join(map(str, g["Period"]))})
    return pd.DataFrame(rows)


def missing(t):
    rows = []
    for name, df in t.items():
        for col in df.columns:
            n_miss = int(df[col].isna().sum())
            rows.append({"table": name, "variable": col, "N": len(df), "valid_N": len(df) - n_miss,
                         "missing_N": n_miss, "missing_pct": round(100 * n_miss / len(df), 3)})
    return pd.DataFrame(rows)


def recency(t):
    o = t["outputs"]
    tot = o.groupby(["Period", "Dimension"])["Outputs (Fractional)"].sum().unstack()
    chg = (tot / tot.shift(1) - 1) * 100
    top = o[o["Dimension"] == "E"].groupby(["Unit", "Period"])["Outputs (Fractional)"].sum().unstack()
    return tot, chg, top[[2020, 2021, 2022, 2023]].sort_values(2022, ascending=False).head(10)


def frac_impact(t):
    o = t["outputs"]
    o = o[o["Dimension"].isin(["T", "E"])].copy()
    o["bad"] = o["Outputs (Fractional)"] > o["Outputs"] + 1e-9
    g = o.groupby(["Unit", "Period", "Dimension"])
    share = (g.apply(lambda x: x.loc[x["bad"], "Outputs (Fractional)"].sum(), include_groups=False)
             / g["Outputs (Fractional)"].sum()).fillna(0).rename("share_from_anomalous_rows").reset_index()
    return share


def outliers_2023(t):
    """Robust z (Iglewicz & Hoaglin 1993): |0.6745*(x - median)/MAD| > 3.5. Chi FLAG."""
    uc = t["unit_complexities"]
    u = t["units"]
    x = uc[uc["Period"] == LAST_YEAR].merge(u[["Period", "Unit", "GDP PC"]], on=["Period", "Unit"])
    x["ln GDP PC"] = np.log(x["GDP PC"])
    rows = []
    for col in ["Ecosystem Complexity Index", "Diversity Share", "Complexity Outlook Index",
                "Growth Outlook Index", "ln GDP PC"]:
        s = x[col]
        med, mad = s.median(), (s - s.median()).abs().median()
        z = 0.6745 * (s - med) / mad
        for i in z[z.abs() > 3.5].index:
            rows.append({"Unit": x.at[i, "Unit"], "variable": col, "value": s[i], "robust_z": z[i]})
    return pd.DataFrame(rows, columns=["Unit", "variable", "value", "robust_z"])


def main():
    asia = asia_units()
    t = load(asia)
    st = structural(t)
    cat, dupnames = categories(t)
    rl, examples, info = range_logic(t)
    cov = coverage(t, asia)
    mis = missing(t)
    tot, chg, etop = recency(t)
    fr = frac_impact(t)
    outl = outliers_2023(t)

    write_csv(st, OUT / "structural_audit.csv")
    write_csv(cat, OUT / "category_audit.csv")
    write_csv(dupnames, OUT / "duplicate_field_names.csv")
    write_csv(rl, OUT / "range_logic_audit.csv")
    for cid, df in examples.items():
        write_csv(df, OUT / f"violations_{cid}.csv")
    write_csv(cov, OUT / "outputs_no_record_country_year_dim.csv")
    write_csv(mis, OUT / "missing_audit_source.csv")
    write_csv(chg.round(2).reset_index(), OUT / "outputs_yoy_change_pct_asia.csv")
    write_csv(etop.reset_index(), OUT / "trademarks_top10_2020_2023.csv")
    write_csv(fr, OUT / "fractional_anomaly_share.csv")
    write_csv(outl, OUT / "outliers_2023_robust_z.csv")

    summary = {
        "n_asia_units": len(asia),
        "structural": st.to_dict("records"),
        "range_logic": rl[["check_id", "n_checked", "n_violations"]].to_dict("records"),
        "coverage_no_record_country_years": cov.groupby("Dimension")["n_years_no_record"].sum().to_dict(),
        "frac_anomaly_share_gt10pct": int((fr["share_from_anomalous_rows"] > 0.10).sum()),
        "frac_anomaly_share_gt1pct": int((fr["share_from_anomalous_rows"] > 0.01).sum()),
        "frac_anomaly_country_year_dims": int(len(fr)),
        "duplicate_field_name_rows": int(len(dupnames)),
        "n_outlier_flags_2023": int(len(outl)),
        **info,
    }
    write_json(summary, OUT / "audit_summary.json")
    print(st.to_string(index=False))
    print(rl[["check_id", "rule", "n_checked", "n_violations"]].to_string(index=False))
    print("coverage:", summary["coverage_no_record_country_years"])
    print("outliers:", outl.to_string(index=False))


if __name__ == "__main__":
    main()

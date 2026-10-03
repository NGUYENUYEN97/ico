"""BUOC RAW: xac minh file nguon bat bien va trich RAW nguyen trang (khong bien doi gia tri).

- Tinh SHA-256 cua 10 file parquet va doi chieu voi oid trong con tro Git LFS da commit.
- Trich cac dong trong pham vi nghien cuu ra CSV, giu nguyen moi cot va moi gia tri.
- Cac bang qua lon de sao chep (outputs/capabilities toan chau A, 23 nam) duoc tham chieu
  bang ten file + bo loc + SHA-256 trong MANIFEST thay vi sao chep.
"""
import os
import stat
import subprocess

from common import (ASEAN, BASE_YEAR, LAST_YEAR, RAW_DIR, ROOT, SOURCE_FILES, SRC,
                    asia_units, read_raw, sha256, write_csv, write_json)


def lfs_oid(name):
    rel = f"ico26_publicdata/{name}.parquet"
    ptr = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"],
                         capture_output=True, text=True, check=True).stdout
    for line in ptr.splitlines():
        if line.startswith("oid sha256:"):
            return line.split(":", 1)[1].strip()
    return None


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for p in RAW_DIR.glob("*.csv"):
        os.chmod(p, stat.S_IWUSR | stat.S_IRUSR)

    files = []
    for name in SOURCE_FILES:
        path = SRC / f"{name}.parquet"
        digest, oid = sha256(path), lfs_oid(name)
        files.append({"file": f"ico26_publicdata/{name}.parquet", "bytes": path.stat().st_size,
                      "sha256": digest, "git_lfs_oid": oid, "match": digest == oid})

    asia = asia_units()
    yrs = [BASE_YEAR, LAST_YEAR]
    extracts = {
        "raw_units_asia.csv": ("units", [("Unit", "in", asia)]),
        "raw_unit_complexities_all_193.csv": ("unit_complexities", None),
        "raw_fields.csv": ("fields", None),
        "raw_field_complexities_2013_2023.csv": ("field_complexities", [("Period", "in", yrs)]),
        "raw_capabilities_asean_2013_2023.csv": ("capabilities", [("Unit", "in", ASEAN), ("Period", "in", yrs)]),
        "raw_densities_asean_2013_2023.csv": ("densities", [("Unit", "in", ASEAN), ("Period", "in", yrs)]),
        "raw_potentials_asean_2013_2023.csv": ("potentials", [("Unit", "in", ASEAN), ("Period", "in", yrs)]),
        "raw_outputs_asean_2013_2023.csv": ("outputs", [("Unit", "in", ASEAN), ("Period", "in", yrs)]),
        "raw_unit_proximities_vn.csv": ("unit_proximities", None),
    }
    out = []
    for fname, (src, flt) in extracts.items():
        df = read_raw(src, filters=flt)
        if fname == "raw_unit_proximities_vn.csv":
            df = df[(df["Unit 1"] == "VN") | (df["Unit 2"] == "VN")]
        write_csv(df, RAW_DIR / fname)
        os.chmod(RAW_DIR / fname, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)   # chi doc
        out.append({"extract": fname, "source": f"{src}.parquet", "filter": str(flt),
                    "rows": len(df), "columns": list(df.columns),
                    "sha256": sha256(RAW_DIR / fname)})

    referenced = [
        {"source": "outputs.parquet", "filter": f"Unit in {len(asia)} nuoc chau A, moi nam",
         "used_for": "tong san luong quoc gia-nam (panel)"},
        {"source": "capabilities.parquet", "filter": f"Unit in {len(asia)} nuoc chau A, moi nam",
         "used_for": "so linh vuc co nang luc quoc gia-nam (panel)"},
    ]
    manifest = {"source_files": files, "extracts": out, "referenced_not_copied": referenced,
                "asia_units": asia, "asean_units": ASEAN}
    write_json(manifest, RAW_DIR / "MANIFEST.json")
    bad = [f["file"] for f in files if not f["match"]]
    print(f"RAW: {len(files)} file nguon, khop LFS oid: {len(files) - len(bad)}/{len(files)}")
    for e in out:
        print(f"  {e['extract']}: {e['rows']:,} dong")
    if bad:
        raise SystemExit(f"File nguon khong khop LFS oid: {bad}")


if __name__ == "__main__":
    main()

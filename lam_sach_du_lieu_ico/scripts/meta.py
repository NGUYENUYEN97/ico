"""Metadata cho DATA DICTIONARY: nhan, vai tro, kieu, thang do, mien gia tri hop le, nguon quy tac.

measure dung thuat ngu jamovi/JASP: ID | Nominal | Ordinal | Continuous.
Bien nhi phan 0/1 la Nominal (khong phai Continuous).
"""
NR = "RULE NOT ESTABLISHED - DO NOT AUTO-CORRECT"


def v(label, role, dtype, measure, valid, rule_src, conf, raw="", rule=""):
    return dict(label=label, role=role, data_type=dtype, measure=measure, valid=valid,
                source_of_rule=rule_src, confidence=conf, raw_source=raw, cleaning_rule=rule)


UNIT = {
    "nam": v("Nam quan sat", "ID (thoi gian)", "integer", "ID", "2001-2023", "README (Period)", "HIGH", "units.Period"),
    "ma_qg": v("Ma quoc gia ISO 3166-1 alpha-2", "ID", "text", "ID", "2 chu in hoa", "Quy uoc ma ISO", "HIGH", "units.Unit"),
    "ten_qg": v("Ten quoc gia (nguyen ban nguon, UTF-8)", "Nhan", "text", "Nominal", "Khong rong", "units.parquet", "HIGH", "units.Unit Name", "CL012"),
    "chau_luc_nguon": v("Vung theo phan loai cua nguon", "Nhom", "text", "Nominal", "East Asia; West and Central Asia", "units.parquet", "HIGH", "units.Continent"),
    "tieu_vung": v("Tieu vung UN M49", "Nhom (dan xuat)", "text", "Nominal", "Dong A; Dong Nam A; Nam A; Trung A; Tay A", "UN M49", "HIGH", "ma_qg", "CL017"),
    "nhom": v("Nhom so sanh", "Nhom (dan xuat)", "text", "Nominal", "Viet Nam; ASEAN khac; Chau A khac", "Dinh nghia nghien cuu (dua tren asean_hien_nay)", "HIGH", "ma_qg", "CL017"),
    "asean_hien_nay": v("Thanh vien ASEAN tinh den 2025 (11 nuoc, ke ca TL)", "Nhom (dan xuat)", "integer", "Nominal", "0/1", "ASEAN Secretariat", "HIGH", "ma_qg", "CL017"),
    "asean_thoi_diem": v("La thanh vien ASEAN tai nam quan sat", "Nhom (dan xuat)", "integer", "Nominal", "0/1", "ASEAN Secretariat (nam gia nhap)", "HIGH", "ma_qg, nam", "CL017"),
    "viet_nam": v("La Viet Nam", "Nhom (dan xuat)", "integer", "Nominal", "0/1", "Dinh nghia", "HIGH", "ma_qg"),
    "nhom_thu_nhap_hien_hanh": v("Nhom thu nhap WB - phan loai HIEN HANH, nguon gan cho moi nam", "Nhom", "text", "Nominal",
                                  "Low/Lower middle/Upper middle/High income", "units.parquet; WB", "HIGH", "units.Income Group", "CL004"),
    "bac_thu_nhap": v("Bac thu nhap (1=thap ... 4=cao), theo nhom_thu_nhap_hien_hanh", "Dan xuat", "integer", "Ordinal", "1-4", "Thu tu WB", "HIGH", "nhom_thu_nhap_hien_hanh", "CL004"),
    "gdp_ppp_usd": v("GDP PPP (USD, gia tri nguon)", "Nguon", "decimal", "Continuous", "> 0", "README", "HIGH", "units.GDP PPP", "CL009"),
    "dan_so": v("Dan so (nguoi, gia tri nguon)", "Nguon", "decimal", "Continuous", "> 0", "README", "HIGH", "units.Population", "CL003"),
    "gdp_dau_nguoi": v("GDP PPP binh quan dau nguoi (USD, gia tri nguon)", "Nguon", "decimal", "Continuous", "> 0; = gdp_ppp_usd/dan_so", "README + L01", "HIGH", "units.GDP PC", "CL003, CL009"),
    "gdp_ppp_ty_usd": v("GDP PPP (ty USD)", "Dan xuat", "decimal", "Continuous", "> 0", "= gdp_ppp_usd / 1e9", "HIGH", "gdp_ppp_usd"),
    "dan_so_trieu": v("Dan so (trieu nguoi)", "Dan xuat", "decimal", "Continuous", "> 0", "= dan_so / 1e6", "HIGH", "dan_so", "CL003"),
    "ln_gdp_dau_nguoi": v("ln(GDP binh quan dau nguoi)", "Dan xuat", "decimal", "Continuous", "so thuc", "= ln(gdp_dau_nguoi)", "HIGH", "gdp_dau_nguoi"),
    "tang_truong_gdp_dau_nguoi": v("Tang truong GDP/nguoi so voi nam truoc (%)", "Dan xuat", "decimal", "Continuous", "so thuc; trong o nam 2001", "= 100*(x_t/x_{t-1} - 1)", "HIGH", "gdp_dau_nguoi", "CL003"),
    "do_da_dang": v("Diversity Share (trung binh nang luc chuan hoa)", "Nguon", "decimal", "Continuous", "[0,1]", "README + L02", "HIGH", "unit_complexities.Diversity Share"),
    "eci": v("Ecosystem Complexity Index", "Nguon", "decimal", "Continuous", NR, "README (khong co mien)", "LOW", "unit_complexities.Ecosystem Complexity Index"),
    "coi": v("Complexity Outlook Index (quoc gia)", "Nguon", "decimal", "Continuous", NR, "README vi du 0.75 khong khop thang do du lieu", "LOW", "unit_complexities.Complexity Outlook Index", "CL018"),
    "goi": v("Growth Outlook Index (quoc gia)", "Nguon", "decimal", "Continuous", NR, "README vi du 0.82 khong khop thang do du lieu", "LOW", "unit_complexities.Growth Outlook Index", "CL018"),
    "hang_eci_the_gioi": v("Thu hang ECI trong 193 don vi (1 = cao nhat)", "Dan xuat", "integer", "Ordinal", "1-193", "rank(min) tren unit_complexities ca 193 don vi", "HIGH", "eci (toan bo 193)"),
    "hang_eci_chau_a": v("Thu hang ECI trong 47 nuoc chau A", "Dan xuat", "integer", "Ordinal", "1-47", "rank(min)", "HIGH", "eci"),
    "sang_che": v("Bang sang che (tong dem phan so)", "Dan xuat", "decimal", "Continuous", ">= 0; trong = khong co ban ghi", "Tong outputs.Outputs (Fractional), T", "MEDIUM", "outputs (T)", "CL002, CL005"),
    "bai_bao_kh": v("Cong bo khoa hoc (tong dem phan so)", "Dan xuat", "decimal", "Continuous", ">= 0; trong = khong co ban ghi", "Tong outputs.Outputs (Fractional), S", "MEDIUM", "outputs (S)", "CL002"),
    "nhan_hieu": v("Nhan hieu (tong dem phan so)", "Dan xuat", "decimal", "Continuous", ">= 0; trong = khong co ban ghi", "Tong outputs.Outputs (Fractional), E", "MEDIUM", "outputs (E)", "CL002, CL005, CL006, CL010"),
    "xuat_khau_ty_usd": v("Xuat khau (ty USD)", "Dan xuat", "decimal", "Continuous", ">= 0", "Tong outputs.Outputs (Fractional), P / 1e9", "HIGH", "outputs (P)"),
    "flag_dan_so_lap_lai": v("FLAG: dan so dung bang nam truoc (nghi chuyen tiep gia tri)", "Flag", "integer", "Nominal", "0/1", "L08", "MEDIUM", "dan_so", "CL003"),
    "ty_le_bat_thuong_sang_che": v("FLAG: ty trong sang_che den tu dong co Fractional > Full", "Flag", "decimal", "Continuous", "[0,1]", "L04", "MEDIUM", "outputs (T)", "CL005"),
    "ty_le_bat_thuong_nhan_hieu": v("FLAG: ty trong nhan_hieu den tu dong co Fractional > Full", "Flag", "decimal", "Continuous", "[0,1]", "L04", "MEDIUM", "outputs (E)", "CL005"),
}
for base in ["sang_che", "bai_bao_kh", "nhan_hieu", "xuat_khau_ty_usd"]:
    UNIT[f"{base}_tren_trieu_dan"] = v(f"{base} tren 1 trieu dan", "Dan xuat", "decimal", "Continuous", ">= 0", f"= {base} / dan_so_trieu", "HIGH", f"{base}, dan_so_trieu", "CL003")
    UNIT[f"ln_{base}"] = v(f"ln(1 + {base})", "Dan xuat", "decimal", "Continuous", ">= 0", f"= ln(1 + {base})", "HIGH", base)
for d in ["cong_nghe", "khoa_hoc", "san_xuat", "khoi_nghiep"]:
    UNIT[f"so_nang_luc_{d}"] = v(f"So linh vuc co nang luc - {d}", "Dan xuat", "integer", "Continuous", ">= 0", "Dem capabilities.Innovation Capability (Binary)", "HIGH", "capabilities")
UNIT["so_nang_luc_tong"] = v("Tong so linh vuc co nang luc", "Dan xuat", "integer", "Continuous", "0-2508", "Tong 4 chieu", "HIGH", "so_nang_luc_*")
UNIT["so_nang_luc_tuong_doi"] = v("So linh vuc co nang luc tuong doi", "Dan xuat", "integer", "Continuous", "0-2508", "Dem Relative Capability (Binary)", "HIGH", "capabilities")
UNIT["so_nang_luc_tuyet_doi"] = v("So linh vuc co nang luc tuyet doi", "Dan xuat", "integer", "Continuous", "0-2508", "Dem Absolute Capability (Binary)", "HIGH", "capabilities", "CL007")

CROSS_EXTRA = {
    "thay_doi_eci_10_nam": v("ECI 2023 - ECI 2013", "Dan xuat", "decimal", "Continuous", "so thuc", "= eci - eci_2013", "HIGH", "eci"),
    "thay_doi_do_da_dang_10_nam": v("Do da dang 2023 - 2013", "Dan xuat", "decimal", "Continuous", "[-1,1]", "hieu", "HIGH", "do_da_dang"),
    "thay_doi_so_nang_luc_10_nam": v("So nang luc 2023 - 2013", "Dan xuat", "integer", "Continuous", "[-2508,2508]", "hieu", "HIGH", "so_nang_luc_tong"),
    "tang_truong_gdp_dau_nguoi_bq_10_nam": v("Tang truong GDP/nguoi binh quan nam 2013-2023 (%)", "Dan xuat", "decimal", "Continuous", "so thuc", "= 100*((x2023/x2013)^(1/10) - 1)", "HIGH", "gdp_dau_nguoi", "CL003"),
    "tuong_dong_voi_viet_nam": v("Proximity voi Viet Nam (2023)", "Dan xuat", "decimal", "Continuous", "[0,1]; trong o dong VN", "unit_proximities", "HIGH", "unit_proximities.Proximity", "CL015"),
    "flag_ngoai_lai": v("FLAG: co it nhat 1 bien chinh co |robust z| > 3.5", "Flag", "integer", "Nominal", "0/1", "Iglewicz & Hoaglin (1993)", "HIGH", "nhieu bien", "CL016"),
    "bien_ngoai_lai": v("Ten cac bien bi FLAG ngoai lai (khong = khong co)", "Flag", "text", "Nominal", "danh sach hoac 'khong'", "CL016", "HIGH", "", "CL016"),
}
for col in ["eci", "do_da_dang", "so_nang_luc_tong", "gdp_dau_nguoi"]:
    CROSS_EXTRA[f"{col}_2013"] = v(f"{col} nam 2013", "Dan xuat", UNIT[col]["data_type"], "Continuous", UNIT[col]["valid"], "Gia tri nam goc", "HIGH", col)


def _field_meta():
    m = {
        "ma_qg": UNIT["ma_qg"], "ten_qg": UNIT["ten_qg"],
        "ma_linh_vuc": v("Ma linh vuc (tien to T/S/P/E = chieu)", "ID", "text", "ID", "^[TSPE] - ...", "README", "HIGH", "Field ID"),
        "ten_linh_vuc": v("Ten linh vuc (5 ten trung lap tren 11 ma khac nhau)", "Nhan", "text", "Nominal", "Khong rong", "fields.parquet", "HIGH", "fields.Field Name", "CL011, CL012"),
        "ma_nhom_linh_vuc": v("Ma nhom linh vuc", "Nhom", "text", "Nominal", "44 nhom", "fields.parquet", "HIGH", "fields.Domain ID"),
        "nhom_linh_vuc": v("Ten nhom linh vuc", "Nhom", "text", "Nominal", "44 nhom", "fields.parquet", "HIGH", "fields.Domain Name"),
        "chieu": v("Chieu doi moi", "Nhom", "text", "Nominal", "Technology; Science; Production; Entrepreneurial", "README", "HIGH", "fields.Dimension Name"),
        "gia_nhap_moi": v("OUTCOME: 0 nam 2013 -> 1 nam 2023 (trong neu da co nang luc nam 2013)", "Outcome (dan xuat)", "integer", "Nominal", "0/1; trong = cau truc", "= co_nang_luc_2023 khi co_nang_luc_2013 = 0", "HIGH", "co_nang_luc_*"),
        "roi_bo": v("OUTCOME: 1 nam 2013 -> 0 nam 2023 (trong neu chua co nam 2013)", "Outcome (dan xuat)", "integer", "Nominal", "0/1; trong = cau truc", "= 1 - co_nang_luc_2023 khi co_nang_luc_2013 = 1", "HIGH", "co_nang_luc_*"),
        "ln_tiem_nang_2023": v("ln(1 + tiem_nang_2023)", "Dan xuat", "decimal", "Continuous", ">= 0", "ln1p", "HIGH", "tiem_nang_2023"),
        "ln_san_luong_2023": v("ln(1 + san_luong_2023)", "Dan xuat", "decimal", "Continuous", ">= 0", "ln1p", "HIGH", "san_luong_2023", "CL001"),
        "chenh_lech_tiem_nang": v("ln_san_luong_2023 - ln_tiem_nang_2023 (am = duoi tiem nang)", "Dan xuat", "decimal", "Continuous", "so thuc", "hieu", "HIGH", "ln_san_luong_2023, ln_tiem_nang_2023", "CL001"),
        "do_phuc_tap_linh_vuc_2023": v("Capability Complexity Index 2023", "Nguon", "decimal", "Continuous", NR, "README", "LOW", "field_complexities.Capability Complexity Index", "CL008"),
        "do_pho_bien_linh_vuc_2023": v("Ubiquity Share 2023", "Nguon", "decimal", "Continuous", "[0,1]", "README", "HIGH", "field_complexities.Ubiquity Share", "CL008"),
        "flag_tuyet_doi_khong_nhat_quan_2023": v("FLAG: Absolute=1 nhung Innovation=0 (L03)", "Flag", "integer", "Nominal", "0/1", "L03", "LOW", "capabilities", "CL007"),
    }
    for y in (2013, 2023):
        m[f"san_luong_{y}"] = v(f"San luong {y} (dem toan phan; P = USD)", "Nguon", "decimal", "Continuous", ">= 0; trong = khong co ban ghi ca quoc gia-nam-chieu", "README", "HIGH", "outputs.Outputs", "CL001, CL002, CL006")
        m[f"san_luong_phan_so_{y}"] = v(f"San luong {y} (dem phan so)", "Nguon", "decimal", "Continuous", ">= 0; ky vong <= san_luong", "README (suy ra)", "MEDIUM", "outputs.Outputs (Fractional)", "CL001, CL002, CL005")
        m[f"nang_luc_chuan_hoa_{y}"] = v(f"Nang luc chuan hoa {y}", "Nguon", "decimal", "Continuous", "[0,1]", "README", "HIGH", "capabilities.Innovation Capability (Normalized)")
        m[f"co_nang_luc_{y}"] = v(f"Co nang luc {y}", "Nguon", "integer", "Nominal", "0/1", "README", "HIGH", "capabilities.Innovation Capability (Binary)", "CL013")
        m[f"nang_luc_tuong_doi_{y}"] = v(f"Nang luc tuong doi {y}", "Nguon", "integer", "Nominal", "0/1", "README", "HIGH", "capabilities.Relative Capability (Binary)", "CL013")
        m[f"nang_luc_tuyet_doi_{y}"] = v(f"Nang luc tuyet doi {y}", "Nguon", "integer", "Nominal", "0/1", "README", "HIGH", "capabilities.Absolute Capability (Binary)", "CL007, CL013")
        m[f"mat_do_lien_quan_{y}"] = v(f"Relatedness density {y}", "Nguon", "decimal", "Continuous", "[0,1]; trong = cau truc (L09)", "README", "HIGH", "densities.Relatedness Density", "CL008")
        m[f"tiem_nang_{y}"] = v(f"Potential {y}", "Nguon", "decimal", "Continuous", ">= 0", "README", "HIGH", "potentials.Potential")
        m[f"flag_phan_so_vuot_toan_phan_{y}"] = v(f"FLAG: Fractional > Full nam {y} (L04)", "Flag", "integer", "Nominal", "0/1", "L04", "MEDIUM", "outputs", "CL005")
    return m


FIELD = _field_meta()

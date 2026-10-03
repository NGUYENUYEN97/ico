# Báo cáo audit và làm sạch dữ liệu: ICO 2026, Việt Nam – ASEAN – châu Á

Quy trình: RAW → AUDIT → FLAG → REVIEW → DECIDE → LOG → CORRECT/RECODE → RECOMPUTE → VERIFY → CLEAN.
Tái lập toàn bộ: `cd lam_sach_du_lieu_ico/scripts && python3 run_all.py` (cần `pandas`, `pyarrow`, và đã chạy `git lfs pull`).

**Trạng thái: PROVISIONAL — UNRESOLVED ISSUES REMAIN.**

---

## A. EXECUTIVE DATA AUDIT

- **Phạm vi:** 47 quốc gia châu Á (trong đó 11 nước ASEAN) × 23 năm, và 2.508 lĩnh vực. Có 4 file CLEAN: panel quốc gia-năm, cắt ngang 2023, ASEAN × lĩnh vực, Việt Nam × lĩnh vực.
- **Cấu trúc tốt:** 0 khóa trùng, 0 dòng trùng, 0 ID lỗi, 0 vi phạm miền giá trị cứng trên khoảng 9,8 triệu dòng nguồn trong phạm vi.
- **Có 4 vấn đề logic chưa xác minh được, đã giữ nguyên và gắn cờ:**
  - dân số năm 2023 trùng năm 2022 ở cả 47 nước;
  - 10.052 dòng có số đếm phân số lớn hơn số đếm toàn phần;
  - 134 dòng nhãn hiệu có số đếm không nguyên;
  - 6 dòng mâu thuẫn giữa các chỉ báo năng lực nhị phân.
- **Có 2 vấn đề thời gian:** số nhãn hiệu giảm 22% (2022) và 44% (2023), nghi do dữ liệu bị cắt cụt; nhóm thu nhập không đổi trong 23 năm, tức là phân loại hiện hành được gán ngược.
- **Chỉ có 1 quy tắc làm thay đổi giá trị (CL001):** 35.796 ô sản lượng vắng mặt được mã hóa thành 0, có bằng chứng (L06a). Ngoài ra **không có giá trị nào bị sửa, xóa hay impute.**
- **Sửa lỗi của phiên bản trước** (`du_lieu_jamovi_jasp/`): 165 quốc gia-năm-chiều không có bản ghi nào đã bị gán 0, nay được trả về missing. Phiên bản đó cũng đã bỏ dấu tên riêng (đã hoàn nguyên) và làm tròn đến 6 chữ số thập phân (nay không làm tròn).
- **Kiểm chứng:** 80/80 kiểm tra đạt. RAW được bảo toàn (SHA-256 trùng với Git LFS oid). Diff độc lập trùng khớp với file 05. 41 biến dẫn xuất được tính lại và khớp.
- **Mức sẵn sàng:** AMBER cho các phân tích chính. GREEN cho xu hướng ECI và năng lực. RED cho xu hướng nhãn hiệu 2022–2023, cho các chỉ số theo đầu người hoặc tăng trưởng năm 2023, và cho việc dùng nhóm thu nhập như biến thay đổi theo thời gian.

## B. DATA STRUCTURE

**Bước 0: tài liệu dùng để xác minh**

| Tài liệu | Có? | Ghi chú |
|---|---|---|
| RAW data | ✅ | 10 file parquet (`ico26_publicdata/`), SHA-256 trùng với Git LFS oid |
| Questionnaire/instrument | — | Không áp dụng (dữ liệu thứ cấp) |
| Codebook / Data dictionary | ⚠️ một phần | `ico26_publicdata/README.md`: định nghĩa cột, không có mã missing, không có công thức |
| Research protocol, eligibility criteria | ⚠️ | Chỉ có phạm vi do người dùng xác định (Việt Nam, ASEAN, châu Á) |
| Source register | ❌ | Không có. Vì vậy mọi giá trị nghi vấn được ghi U và không được sửa |
| Cleaning rules, scoring rules, missing-data rules | ❌ | Quy tắc tự xác lập được ghi rõ nguồn và độ tin cậy ở `03_DATA_DICTIONARY.csv` |

Biến không có quy tắc được ghi **"RULE NOT ESTABLISHED — DO NOT AUTO-CORRECT"**: `eci`, `coi`, `goi`, `do_phuc_tap_linh_vuc_2023`. Ngoài ra, ví dụ trong README cho COI/GOI (0,75; 0,82) không khớp với thang đo thực của dữ liệu (−22 đến 498; 4 đến 675).

**Cấu trúc:** mọi bảng ở dạng long, khóa tổ hợp. Đơn vị phân tích là quốc gia-năm (panel, cắt ngang) hoặc quốc gia-lĩnh vực với hai năm 2013 và 2023 xoay sang dạng wide. Cấu trúc lồng: lĩnh vực nằm trong quốc gia, năm nằm trong quốc gia. Chi tiết: `06_QC_REPORT.md` §1.

## C. ISSUES DETECTED

| Mã | Vấn đề | Phạm vi | Mức độ | Tự sửa? |
|---|---|---|---|---|
| L08 / CL003 | Dân số 2023 = 2022 (nghi giá trị được chuyển tiếp) | 47/47 nước | Cao (ảnh hưởng mọi chỉ số theo đầu người 2023) | NO |
| L04 / CL005 | Fractional > Full (tới 8 lần) | 10.052 dòng; 683 quốc gia-năm-chiều có > 10% tổng bị ảnh hưởng | Cao | NO |
| CL010 | Nhãn hiệu giảm mạnh 2022–2023 | Toàn châu Á (CN −55%) | Cao cho phân tích xu hướng | NO |
| CL004 | Nhóm thu nhập không đổi theo thời gian | 47 nước | Trung bình | NO |
| CL002 | Quốc gia-năm-chiều không có bản ghi nào | T 53, S 11, E 101 | Trung bình (missing không ngẫu nhiên) | NO (giữ missing) |
| L05 / CL006 | Số đếm toàn phần không nguyên (nhãn hiệu) | 134 dòng | Thấp | NO |
| L03 / CL007 | Absolute = 1, Innovation = 0 | 6 dòng (2023) | Thấp | NO |
| L06a / CL001 | Dòng sản lượng vắng mặt trong quốc gia-năm-chiều có bản ghi | 17.898 dòng lĩnh vực-năm (ASEAN 2013/2023) | Trung bình | Có, theo quy tắc có bằng chứng (R) |
| L09 / CL008 | Density và độ phức tạp thiếu ở 42 field-year | 1.974 dòng (châu Á) | Thấp (missing cấu trúc) | NO |
| CL009 | GDP thiếu ở KP, YE | 46 dòng | Thấp | NO |
| CL011 | 5 tên lĩnh vực trùng nhau trên 11 mã khác nhau | 11 dòng | Thấp | NO |
| CL012 | Ký tự Unicode | 24 ô | Không (UTF-8 hợp lệ) | NO |

## D. CLEANING DECISION TABLE

Đầy đủ: `04_CLEANING_LOG.csv` (18 mục). Các vấn đề quan trọng được trình bày theo chuỗi RAW → RULE → EVIDENCE → DECISION → CLEAN → DOWNSTREAM:

**CL001: sản lượng vắng mặt (R)**
- RAW: không có dòng trong `outputs` cho (nước, năm, lĩnh vực), trong khi cùng nước-năm-chiều đó có bản ghi khác.
- RULE: dòng vắng mặt = sản lượng 0.
- EVIDENCE: L06a cho thấy 0/2.711.148 dòng vắng mặt có Normalized Capability > 0; file nguồn cũng có dòng 0 tường minh.
- DECISION: RECODE, độ tin cậy MEDIUM, vì README không ghi rõ quy tắc này (xem UD06).
- CLEAN: 0, tổng cộng 35.796 ô.
- DOWNSTREAM: `ln_san_luong_2023`, `chenh_lech_tiem_nang`, `flag_phan_so_vuot_toan_phan_*`.

**CL002: không có bản ghi nào (K)**
- RAW: cả quốc gia-năm-chiều không có dòng nào.
- RULE: MISSING ≠ ZERO.
- EVIDENCE: không phân biệt được "không phát sinh" với "không được bao phủ".
- DECISION: giữ missing.
- CLEAN: ô trống.
- DOWNSTREAM: `*_tren_trieu_dan`, `ln_*`. Đây là thay đổi so với phiên bản trước, vốn đã gán 0.

**CL003: dân số 2023 (U)**
- RAW: Population năm 2023 bằng năm 2022.
- RULE: L08, kiểm tra hợp lý mềm.
- EVIDENCE: 47/47 nước trùng; các năm khác 0 trường hợp; không có nguồn đối chứng.
- DECISION: giữ nguyên và gắn cờ `flag_dan_so_lap_lai`.
- CLEAN: giữ nguyên.
- DOWNSTREAM: GDP/người 2023 (đã do nguồn tính sẵn), mọi chỉ số "trên triệu dân" 2023, tăng trưởng 2023, tăng trưởng bình quân 10 năm.

**CL005: fractional > full (U)**
- RAW: ví dụ JO 2005 T-B41J: Full 1, Fractional 8.
- RULE: L04, suy ra từ README.
- EVIDENCE: README không có công thức đếm phân số.
- DECISION: giữ nguyên và gắn cờ `ty_le_bat_thuong_*` (panel), `flag_phan_so_vuot_toan_phan_*` (file lĩnh vực).
- CLEAN: giữ nguyên.
- DOWNSTREAM: `sang_che`, `nhan_hieu`.

**CL007: Absolute = 1 nhưng Innovation = 0 (U)**
- RAW: 6 dòng năm 2023.
- RULE: L03, thực nghiệm (độ tin cậy LOW).
- EVIDENCE: quy tắc không có trong README.
- DECISION: giữ nguyên, không tự đặt Innovation = 1.
- CLEAN: giữ nguyên.
- DOWNSTREAM: `so_nang_luc_tuyet_doi`.

**CL004: nhóm thu nhập (F)**
- RAW: không đổi trong 23 năm.
- RULE: phân loại WB thay đổi theo năm.
- DECISION: giữ giá trị, đổi tên biến thành `nhom_thu_nhap_hien_hanh` để không bị hiểu nhầm.
- CLEAN: giữ nguyên.
- DOWNSTREAM: `bac_thu_nhap`.

**CL017: ASEAN theo thời điểm (R, dẫn xuất)**
- RAW: không có biến này trong nguồn.
- RULE: năm gia nhập ASEAN theo ASEAN Secretariat.
- DECISION: tạo `asean_hien_nay` (11 nước) và `asean_thoi_diem` (Timor-Leste = 0 cho 2001–2023).
- DOWNSTREAM: `nhom`.

Thống kê mã quyết định: C = 0, M = 0, D = 0; R = 4 mục (CL001, CL013, CL014, CL017); K = 7; F = 3; U = 4.

## E. MISSINGNESS REPORT

| Biến | N | Valid | Missing | % | Loại | Diễn giải |
|---|---|---|---|---|---|---|
| gdp_dau_nguoi (panel) | 1.081 | 1.035 | 46 | 4,3 | system | KP, YE |
| sang_che (panel) | 1.081 | 1.028 | 53 | 4,9 | no coverage | Không phải 0 |
| bai_bao_kh (panel) | 1.081 | 1.070 | 11 | 1,0 | no coverage | |
| nhan_hieu (panel) | 1.081 | 980 | 101 | 9,3 | no coverage | Trung Á 27,8%; thu nhập trung bình thấp 20,2% |
| tang_truong_gdp_dau_nguoi | 1.081 | 990 | 91 | 8,4 | structural + system | Năm 2001; KP, YE |
| tuong_dong_voi_viet_nam | 47 | 46 | 1 | 2,1 | structural | Dòng Việt Nam |
| san_luong_2013/2023 (file 3) | 27.588 | 26.570 | 1.018 | 3,7 | no coverage | Timor-Leste, chiều T và E |
| gia_nhap_moi (file 3 / file 4) | 27.588 / 2.508 | 24.334 / 2.321 | 3.254 / 187 | 11,8 / 7,5 | structural | Đã có năng lực năm 2013 |
| mat_do_lien_quan_2023, độ phức tạp lĩnh vực | 27.588 | 27.577 | 11 | 0,04 | structural | Field-year không được tính |

Không impute. Missing khác nhau theo tiểu vùng và nhóm thu nhập, nên đã được **FLAG để phân tích độ nhạy**. Đầy đủ: `06_QC/post/missing_report.csv` và `differential_missingness.csv`.

## F. DERIVED-VARIABLE CHECK

Sơ đồ phụ thuộc giữa biến nguồn, biến dẫn xuất và phân tích:

```
units.GDP PPP, Population ──► gdp_ppp_ty_usd, dan_so_trieu
units.GDP PC ─────────────► ln_gdp_dau_nguoi, tang_truong_gdp_dau_nguoi (t vs t−1), tang_truong_bq_10_nam
                             └► [CL003] năm 2023 phụ thuộc dân số lặp lại
outputs.Outputs (Fractional) ─► sang_che, bai_bao_kh, nhan_hieu, xuat_khau_ty_usd
                             ──► *_tren_trieu_dan (÷ dan_so_trieu), ln_* = ln(1+x)
                             ──► ty_le_bat_thuong_* [CL005]
capabilities.*(Binary) ─────► so_nang_luc_{4 chiều}, _tong, _tuong_doi, _tuyet_doi
unit_complexities.ECI ──────► hang_eci_the_gioi (193 đơn vị), hang_eci_chau_a (47 nước)
panel 2013 & 2023 ──────────► thay_doi_*_10_nam (file 2)
co_nang_luc_2013, _2023 ────► gia_nhap_moi, roi_bo ──► hồi quy logistic
san_luong_2023 [CL001], tiem_nang_2023 ─► ln_san_luong_2023, ln_tiem_nang_2023 ─► chenh_lech_tiem_nang
```

Kết quả: 41/41 biến dẫn xuất được tính lại **độc lập** và khớp với CLEAN; sai lệch tương đối lớn nhất là 6,2·10⁻¹⁵. Tổng hợp từ parquet được tính lại bằng pyarrow; công thức được viết lại riêng. Biến dẫn xuất do nguồn tính sẵn cũng được kiểm tra: `Diversity Share` = trung bình năng lực chuẩn hóa (L02, 0 sai lệch) và `GDP PC` = GDP/dân số (L01, 0 sai lệch). Vì CL001 là thay đổi duy nhất ở biến nguồn, mọi biến dẫn xuất phụ thuộc vào nó đã được tính **sau** khi recode.

## G. RAW ↔ CLEAN DIFF

| Chỉ số | Giá trị |
|---|---|
| RAW rows | panel 1.081; lưới lĩnh vực 55.176 (11 nước × 2.508 × 2 năm) |
| CLEAN rows | 1.081 / 47 / 27.588 / 2.508 |
| RAW columns → CLEAN columns | units 9 + uc 6 → panel 46 (12 cột nguồn + 34 cột dẫn xuất hoặc flag) |
| Số ô thay đổi | **35.796** (file 3); file 4 là tập con của file 3 (2.236 ô) |
| Corrected (C) | 0 |
| Recoded (R) | 35.796 ô (CL001); ngoài ra có thay đổi biểu diễn không làm đổi giá trị (True/False → 1/0; đổi tên biến) |
| Set missing (M) | 0 |
| Deleted (D) | 0 dòng, 0 cột dữ liệu (chỉ bỏ `__index_level_0__`, là chỉ số kỹ thuật) |
| Retained after review (K/F) | 10 mục log |
| Unresolved (U) | 4 mục log; 7 quyết định ở `08_UNRESOLVED_DECISIONS.csv` |

Bảng CASE | VARIABLE | RAW | CLEAN | REASON | EVIDENCE | DOWNSTREAM EFFECT đầy đủ có trong `05_RAW_CLEAN_DIFF.csv`. Kiểm tra V08 cho thấy diff độc lập trùng khớp với file 05. Kiểm tra V09 cho thấy 0 ô thay đổi không có trong Cleaning Log. **Các cột nguồn của panel và file cắt ngang: 0 ô thay đổi.**

## H. JASP VERIFICATION

Xem `09_HUONG_DAN_KIEM_TRA_JASP_JAMOVI.md` §1–2. Tóm tắt các bước:
1. Đặt thang đo: 0/1 là Nominal, `bac_thu_nhap` và các biến thứ hạng là Ordinal, ID là Nominal.
2. Chạy *Descriptives* (Valid, Missing, Mean, SD, Median, Min, Max) và *Frequency tables*.
3. So kết quả với `09_JASP_JAMOVI_EXPECTED_*.csv`.
4. Dùng *Compute column* (R) để tính lại `log(gdp_dau_nguoi)`, `log1p(sang_che)` và `ifelse(co_nang_luc_2013 == 0, co_nang_luc_2023, NA)`; hiệu số với cột có sẵn phải bằng 0.
5. Filter chỉ dùng cho phân tích độ nhạy.

**Chưa chạy thực tế trên JASP.**

## I. jamovi VERIFICATION

Xem `09_HUONG_DAN_KIEM_TRA_JASP_JAMOVI.md` §1, §3. Tóm tắt các bước:
1. Trong *Data → Setup*, đặt Measure type.
2. Chạy *Exploration → Descriptives*.
3. Dùng *Compute* để kiểm tra lại: `LN(gdp_dau_nguoi)`, `LN(1 + sang_che)`, `sang_che / dan_so_trieu`, `gdp_ppp_usd / 1000000000`.
4. Kiểm tra `gia_nhap_moi` bằng Contingency Table `co_nang_luc_2013` × `co_nang_luc_2023`: ô (0,0) = 2151, (0,1) = 170, và hàng 1 có 187 lĩnh vực.
5. Dùng *Transform* để tạo biến mới, không ghi đè biến gốc.

**Chưa chạy thực tế trên jamovi.** Nếu JASP và jamovi cho kết quả khác nhau, dò theo thứ tự trong §5 của hướng dẫn: thang đo, định nghĩa missing, filter, công thức, làm tròn, phạm vi case.

## J. ANALYSIS READINESS

| Mức | Phân tích |
|---|---|
| **GREEN** | Mô tả xu hướng ECI, độ đa dạng, số năng lực (panel) |
| **AMBER** | Tương quan và hồi quy trên file cắt ngang 2023 (N = 47); xu hướng sáng chế và bài báo; logistic gia nhập lĩnh vực (file 3 bắt buộc có hiệu ứng quốc gia; file 4 chỉ có 170 sự kiện); `chenh_lech_tiem_nang` |
| **RED** | Xu hướng nhãn hiệu 2022–2023; tăng trưởng và chỉ số theo đầu người năm 2023; nhóm thu nhập dùng như biến thay đổi theo thời gian |

Năm câu hỏi readiness và năm khía cạnh chất lượng (dữ liệu ≠ đo lường ≠ thiết kế ≠ nhân quả ≠ tuyên bố): xem `07_ANALYSIS_READINESS_REPORT.md`.

## K. METHODS PARAGRAPH (Data Preparation)

**Tiếng Việt (179 từ):**

> Dữ liệu được trích từ Innovation Capabilities Outlook 2026 cho 47 quốc gia châu Á, giai đoạn 2001–2023. Tệp nguồn được giữ nguyên và xác minh bằng mã băm SHA-256. Chúng tôi kiểm tra trùng lặp khóa và dòng, miền giá trị, danh mục phân loại và 11 quy tắc logic giữa các biến và giữa các tệp; không phát hiện trùng lặp hay vi phạm miền giá trị. Ô sản lượng vắng mặt trong quốc gia–năm–chiều đã có bản ghi được mã hóa bằng 0 (35.796 ô) vì mọi ô này có năng lực chuẩn hóa bằng 0; quốc gia–năm–chiều không có bản ghi được giữ là giá trị khuyết. Không giá trị nào bị sửa, xóa hay ước lượng thay thế. Các bất thường không xác minh được (dân số 2023 trùng 2022; 10.052 dòng có số đếm phân số vượt số đếm toàn phần; sáu dòng mâu thuẫn chỉ báo nhị phân) được giữ nguyên và gắn cờ. Biến dẫn xuất được tính lại độc lập; mọi thay đổi được ghi trong nhật ký làm sạch.

**English (134 words):**

> Data were extracted from the Innovation Capabilities Outlook 2026 (updated 4 June 2026) for 47 Asian economies, 2001–2023. Source files were left unmodified and verified by SHA-256 checksums. We checked keys and rows for duplicates, value ranges, category codes and 11 cross-variable and cross-file logic rules; no duplicates or hard range violations were found. Absent output records within country-year-dimensions that had other records were coded as zero (35,796 cells), because every such cell had a normalized capability of zero; country-year-dimensions with no records were kept as missing. No values were corrected, deleted or imputed. Unverifiable anomalies (2023 population identical to 2022; 10,052 rows with fractional counts exceeding full counts; six rows with inconsistent binary capability indicators) were retained and flagged. Derived variables were recomputed independently, and every change is documented in a cleaning log.

*Chỉ thêm câu "Core descriptive statistics were reproduced in JASP and jamovi" sau khi bạn đã chạy và đối chiếu thực tế.*

## L. CLAIM BOUNDARY

1. Dữ liệu là quan sát ở cấp quốc gia. Vì vậy không thể kết luận mật độ liên quan **gây ra** việc gia nhập lĩnh vực mới, hay độ phức tạp **gây ra** thu nhập cao hơn.
2. Chênh lệch mật độ khi gộp ASEAN (0,270 so với 0,110) không phải bằng chứng cho "nguyên lý liên quan" bên trong từng nước. Trong từng nước, khoảng cách gần như bằng không (Việt Nam 0,148 so với 0,141), nên chênh lệch khi gộp chủ yếu phản ánh khác biệt giữa các nước.
3. Khi UD01 và UD05 chưa được giải quyết, không thể tuyên bố về xu hướng nhãn hiệu 2022–2023, về tăng trưởng GDP/người năm 2023, hay về bất kỳ chỉ số theo đầu người nào của năm 2023.
4. Missing không ngẫu nhiên: nó tập trung ở Trung Á, Nam Á và nhóm thu nhập trung bình thấp. Vì vậy kết quả trên các case đầy đủ không đại diện cho các nước nhỏ hoặc thu nhập thấp, và không thể suy kết quả cấp quốc gia xuống doanh nghiệp, ngành hay địa phương (ecological fallacy).
5. Chưa được viết rằng kết quả "đã kiểm chứng trên JASP/jamovi" cho đến khi việc đối chiếu ở mục H–I được thực hiện.

## M. FILES CREATED

| File | Nội dung |
|---|---|
| `01_RAW_DATA_UNCHANGED/` | 9 bản trích nguyên trạng (CSV, chỉ đọc) và `MANIFEST.json` (SHA-256 của 10 file parquet, đối chiếu Git LFS oid; bộ lọc trích). Các bảng quá lớn được tham chiếu qua hash thay vì sao chép |
| `02_CLEAN_DATA_CANDIDATE/` | `1_panel_chau_a_2001_2023.csv`, `2_chau_a_cat_ngang_2023.csv`, `3_asean_linh_vuc_2013_2023.csv`, `4_viet_nam_linh_vuc_2013_2023.csv` |
| `03_DATA_DICTIONARY.csv` | 167 dòng (biến × dataset): nhãn, vai trò, kiểu, thang đo, miền hợp lệ, N valid/missing/unique, min/max, số giá trị ngoài miền, nguồn quy tắc, độ tin cậy, tham chiếu log |
| `04_CLEANING_LOG.csv` | 18 quyết định, đủ các cột bắt buộc cộng `n_cells_changed`; cột `verified` do script kiểm chứng ghi |
| `05_RAW_CLEAN_DIFF.csv` | 38.032 dòng (35.796 ô duy nhất và 2.236 ô của file 4) |
| `06_QC_REPORT.md`, `06_QC/pre/`, `06_QC/post/` | Báo cáo trước và sau làm sạch; danh sách vi phạm; 80 kiểm tra |
| `07_ANALYSIS_READINESS_REPORT.md` | Phân loại GREEN/AMBER/RED và 5 câu hỏi |
| `08_UNRESOLVED_DECISIONS.csv` | 7 quyết định cần người nghiên cứu (UD01–UD07) |
| `09_HUONG_DAN_KIEM_TRA_JASP_JAMOVI.md`, `09_JASP_JAMOVI_EXPECTED_*.csv` | Hướng dẫn và giá trị kỳ vọng |
| `scripts/` | `s1_extract_raw.py` → `s2_audit.py` → `s3_clean.py` → `s4_verify.py` (`run_all.py`) |

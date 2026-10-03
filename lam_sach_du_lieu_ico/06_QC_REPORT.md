# 06 — QC REPORT (trước và sau làm sạch)

Bảng chi tiết nằm ở `06_QC/pre/` (audit trước làm sạch, chạy trên dữ liệu nguồn) và `06_QC/post/` (kiểm tra sau làm sạch, đọc lại CLEAN từ đĩa). Có thể tái lập toàn bộ bằng `python3 scripts/run_all.py`.

## 1. Cấu trúc

| Bảng nguồn (phạm vi 47 nước châu Á) | Dòng | Cột | Khóa | Khóa trùng | Dòng trùng hoàn toàn | ID lỗi định dạng | Cột rỗng |
|---|---|---|---|---|---|---|---|
| units | 1.081 | 9 | Period + Unit | 0 | 0 | 0 | 0 |
| unit_complexities | 1.081 | 6 | Period + Unit | 0 | 0 | 0 | 0 |
| fields | 2.508 | 6 | Field ID | 0 | 0 | 0 | 0 |
| field_complexities | 57.642 | 6 | Period + Field ID | 0 | 0 | 0 | 0 |
| outputs | 1.609.733 | 8 | Period + Unit + Field ID | 0 | 0 | 0 | 0 |
| capabilities | 2.711.148 | 7 | Period + Unit + Field ID | 0 | 0 | 0 | 0 |
| densities | 2.709.174 | 5 | Period + Unit + Field ID | 0 | 0 | 0 | 0 |
| potentials | 2.711.148 | 4 | Period + Unit + Field ID | 0 | 0 | 0 | 0 |
| unit_proximities | 18.721 | 5 | Period + Unit 1 + Unit 2 | 0 | 0 | 0 | 0 |

Tất cả bảng đều ở dạng long. Đơn vị phân tích: quốc gia-năm, hoặc quốc gia-năm-lĩnh vực. Mã hóa UTF-8 hợp lệ; chỉ có 24 ô chứa ký tự ngoài ASCII (Türkiye ×23, một tên lĩnh vực có dấu ’). Cột `__index_level_0__` là chỉ số pandas còn sót lại, không mang dữ liệu; cột này được giữ trong RAW và không đưa vào CLEAN.

| CLEAN | Dòng | Cột | Khóa trùng | Dòng trùng | Cột rỗng |
|---|---|---|---|---|---|
| 1_panel_chau_a_2001_2023 | 1.081 | 46 | 0 | 0 | 0 |
| 2_chau_a_cat_ngang_2023 | 47 | 55 | 0 | 0 | 0 |
| 3_asean_linh_vuc_2013_2023 | 27.588 | 33 | 0 | 0 | 0 |
| 4_viet_nam_linh_vuc_2013_2023 | 2.508 | 33 | 0 | 0 | 0 |

**Số case được giữ nguyên:** không xóa dòng nào. CLEAN có 47 × 23 = 1.081 dòng (bằng RAW units) và 11 × 2.508 = 27.588 dòng (bằng RAW capabilities ASEAN cho mỗi năm).

## 2. Range và category

| Kiểm tra | Trước | Sau |
|---|---|---|
| Vi phạm miền giá trị cứng (R01–R09: năm, GDP > 0, tỷ lệ trong [0,1], số đếm ≥ 0, density, potential, ubiquity, proximity) | 0 | 0 |
| Giá trị category ngoài danh mục, khoảng trắng thừa, biến thể chỉ khác chữ hoa/thường | 0 | 0 (V04, 10 biến) |
| Giá trị ngoài miền đã xác lập trong 03_DATA_DICTIONARY | — | 0 (V05) |
| Biến có quy tắc "RULE NOT ESTABLISHED" (không kiểm tra miền) | eci, coi, goi, do_phuc_tap_linh_vuc | giữ nguyên |

## 3. Logic giữa các biến và giữa các file

| Mã | Quy tắc | Nguồn quy tắc | Số kiểm tra | Vi phạm | Quyết định |
|---|---|---|---|---|---|
| L01 | GDP PC = GDP PPP / Population | định nghĩa | 1.035 | 0 | — |
| L02 | Diversity Share = trung bình Normalized Capability | thực nghiệm | 1.081 | 0 | — |
| L03 | Innovation (Binary) = Absolute OR Relative | suy ra (LOW) | 2.711.148 | **6** | U (CL007) |
| L04 | Fractional ≤ Full | suy ra từ README (MEDIUM) | 1.609.733 | **10.052** (T 7.299; E 2.753) | U (CL005) |
| L05 | Full count là số nguyên (T, S, E) | suy ra (MEDIUM) | 1.609.733 | **134** (E) | U (CL006) |
| L06a | Không có dòng outputs ⇒ Normalized = 0 | thực nghiệm | 2.711.148 | 0 | bằng chứng cho CL001 |
| L06b | Outputs > 0 ⇒ Normalized > 0 | thực nghiệm | 2.711.148 | 0 | — |
| L07 | Population trong outputs = trong units | 2 file | 1.081 | 0 | — |
| L08 | Population khác năm trước (soft) | soft plausibility | 1.081 | **47** (đều là năm 2023) | U + flag (CL003) |
| L09 | Thiếu density ⇔ field-year không có complexity | thực nghiệm | 1.974 | 0 dòng không giải thích được | missing cấu trúc (CL008) |
| L10, L11 | Tiền tố chiều thống nhất | README | — | 0 | — |

Theo L04, có 683/2.008 tổ hợp quốc gia-năm-chiều (T, E) trong đó **hơn 10%** tổng số đếm phân số đến từ các dòng bất thường. Với Việt Nam năm 2023, tỷ lệ này là 6,5% với bằng sáng chế và 1,2% với nhãn hiệu.

## 4. Missing

| Loại missing | Biến (CLEAN) | Số lượng | Diễn giải |
|---|---|---|---|
| System missing | GDP (KP, YE) | 46 dòng panel; 2 dòng cắt ngang | Nguồn không có GDP |
| No coverage (không phải 0) | sang_che / bai_bao_kh / nhan_hieu | 53 / 11 / 101 quốc gia-năm | Không có bản ghi nào trong quốc gia-năm-chiều. **Phiên bản `du_lieu_jamovi_jasp/` trước đây đã gán 0 cho các ô này; đó là lỗi và đã được sửa ở đây** |
| No coverage | san_luong_* (file 3) | 1.018 ô mỗi cột | Timor-Leste, chiều T và E |
| Structural | gia_nhap_moi / roi_bo | 3.254 / 24.334 (file 3) | Không thuộc tập có nguy cơ |
| Structural | mat_do_lien_quan_2023, độ phức tạp lĩnh vực | 11 (file 3) | Field-year không được tính độ phức tạp |
| Structural | tuong_dong_voi_viet_nam | 1 | Dòng Việt Nam |
| Structural | tang_truong_gdp_dau_nguoi | 47 (+44 do KP, YE) | Năm 2001 không có năm trước |

Không giá trị nào được impute; không ô missing nào bị đổi thành 0, mean hay median. Bảng đầy đủ: `06_QC/post/missing_report.csv`.

**Missing khác nhau theo nhóm (FLAG cho phân tích độ nhạy).** Tỷ lệ % quốc gia-năm không có bản ghi:

| Nhóm | Sáng chế | Bài báo | Nhãn hiệu |
|---|---|---|---|
| Đông Á | 0,0 | 0,9 | 0,9 |
| Đông Nam Á | 9,5 | 2,0 | 12,6 |
| Nam Á | 8,2 | 1,0 | 15,9 |
| Tây Á | 0,8 | 0,0 | 0,8 |
| Trung Á | 7,8 | 2,6 | **27,8** |
| Thu nhập trung bình thấp | 8,7 | 1,5 | 20,2 |
| Thu nhập cao | 0,0 | 0,0 | 0,0 |

Missing tập trung ở các nước nhỏ hoặc có thu nhập thấp hơn, nên **không thể coi là MCAR**. Phân tích chỉ dùng các case đầy đủ sẽ nghiêng về những nước có hệ thống báo cáo tốt hơn.

## 5. Trùng lặp

| Loại | Kết quả |
|---|---|
| A. ID trùng | 0 ở mọi bảng (khóa tổ hợp) |
| B. Dòng trùng hoàn toàn | 0 |
| C. Hai quốc gia khác nhau có bộ giá trị trùng nhau (khả năng trùng đối tượng) | 0 (Diversity Share + ECI trong cùng năm) |
| D. Quan sát lặp hợp lệ | Mỗi quốc gia xuất hiện 23 năm, đúng thiết kế panel |
| Tên lĩnh vực trùng nhau | 5 tên, 11 dòng, có Field ID và/hoặc nhóm lĩnh vực khác nhau. **Giữ nguyên** (CL011) và dùng `ma_linh_vuc` để nhận diện |

## 6. Ngoại lai

Dùng robust z với ngưỡng |0,6745·(x − median)/MAD| > 3,5 trên 10 biến chính của file cắt ngang 2023. **Không có nước nào bị gắn cờ** (`flag_ngoai_lai = 0` cho cả 47 nước). Trên toàn thế giới, một số nước rất nhỏ có thứ hạng ECI cao (Marshall Islands hạng 3, Andorra, Monaco); các nước này không thuộc mẫu châu Á. Không có giá trị nào bị winsorize hay cắt bỏ.

## 7. Biến dẫn xuất

Tất cả 41 biến dẫn xuất được tính lại độc lập và khớp với CLEAN; sai lệch tương đối lớn nhất là 6,2·10⁻¹⁵ (sai số dấu phẩy động). Các biến tổng hợp từ parquet được tính lại bằng `pyarrow`, khác với `pandas` dùng ở bước làm sạch. Chi tiết: `06_QC/post/derived_recompute.csv`.

## 8. Checklist sau làm sạch (80/80 kiểm tra đạt, `06_QC/post/verification_checks.csv`)

- [x] Không có thay đổi nào không được ghi lại: diff độc lập trùng khớp với file 05, và mọi ô thay đổi đều có `log_id` (V08, V09)
- [x] Không còn giá trị nằm ngoài miền đã xác lập; các vi phạm logic không xác minh được đã được FLAG (V05; CL003, CL005–CL007)
- [x] Biến dẫn xuất đã được tính lại (V07, 42 kiểm tra)
- [x] Giữ nguyên missing cấu trúc (CL008, CL015; gia_nhap_moi, roi_bo)
- [x] Giữ nguyên giá trị bất thường nhưng hợp lệ (không xóa hay sửa ngoại lai)
- [x] RAW được bảo toàn: SHA-256 của 10 file parquet trùng với Git LFS oid, và 9 bản trích không đổi (V01, V02)
- [x] Cleaning log đầy đủ (18 mục, cột `verified` = YES do s4_verify ghi)

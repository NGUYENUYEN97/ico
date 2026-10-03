# Dữ liệu thô cho jamovi / JASP: Việt Nam – ASEAN – châu Á

Trích từ bộ **Innovation Capabilities Outlook 2026** (`ico26_publicdata/`). Phạm vi 47 quốc gia châu Á (Đông Á + Tây và Trung Á theo phân loại của bộ dữ liệu), trong đó có 11 nước ASEAN (kể cả Timor-Leste, gia nhập 10/2025).

Tạo lại toàn bộ bảng: `python3 du_lieu_jamovi_jasp/build_tables.py` (cần `pandas`, `pyarrow`, và đã `git lfs pull`).

## Các file

| File | Đơn vị quan sát | Số dòng | Dùng để |
|---|---|---|---|
| `1_panel_chau_a_2001_2023.csv` | quốc gia × năm | 1.081 (47 nước × 23 năm) | Xu hướng, so sánh theo thời gian, hồi quy dữ liệu bảng, ANOVA đo lặp |
| `2_chau_a_cat_ngang_2023.csv` | quốc gia (năm 2023) | 47 | Tương quan, hồi quy tuyến tính, ANOVA/Kruskal-Wallis theo tiểu vùng, t-test ASEAN vs. ngoài ASEAN |
| `3_asean_linh_vuc_2013_2023.csv` | nước ASEAN × lĩnh vực | 27.588 (11 × 2.508) | Hồi quy logistic: mật độ liên quan → gia nhập lĩnh vực mới; so sánh cơ cấu năng lực |
| `4_viet_nam_linh_vuc_2013_2023.csv` | lĩnh vực (chỉ Việt Nam) | 2.508 | Như file 3, chỉ riêng Việt Nam |

**Định dạng:** CSV, phân cách bằng dấu phẩy, số thập phân dùng dấu chấm, mã hóa ASCII (tên riêng đã bỏ dấu, ví dụ `Turkiye`). Ô trống là giá trị khuyết (missing). Biến nhị phân được mã hóa 0/1.

## Mở file

- **jamovi:** ☰ → *Open* → *Browse* → chọn file `.csv`.
- **JASP:** *File* → *Open* → *Computer* → *Browse*.

Sau khi mở, kiểm tra loại thang đo của từng biến. Phần mềm có thể nhận nhầm các biến 0/1 (`asean`, `viet_nam`, `co_nang_luc_*`, `gia_nhap_moi`, `roi_bo`…) là biến liên tục. Đổi chúng sang **Nominal**, và đổi `bac_thu_nhap` sang **Ordinal**.

---

## File 1: `1_panel_chau_a_2001_2023.csv`

| Biến | Ý nghĩa |
|---|---|
| `nam` | Năm (2001–2023) |
| `ma_qg`, `ten_qg` | Mã ISO 2 ký tự, tên quốc gia |
| `tieu_vung` | Tiểu vùng theo M49 của LHQ: Dong A, Dong Nam A, Nam A, Trung A, Tay A |
| `nhom` | Viet Nam / ASEAN khac / Chau A khac |
| `asean`, `viet_nam` | 1 = có, 0 = không |
| `nhom_thu_nhap` | Nhóm thu nhập theo Ngân hàng Thế giới |
| `bac_thu_nhap` | 1 = thấp, 2 = trung bình thấp, 3 = trung bình cao, 4 = cao |
| `gdp_ppp_ty_usd` | GDP theo sức mua tương đương (tỷ USD) |
| `dan_so_trieu` | Dân số (triệu người) |
| `gdp_dau_nguoi`, `ln_gdp_dau_nguoi` | GDP bình quân đầu người theo PPP (USD) và logarit của nó |
| `tang_truong_gdp_dau_nguoi` | Tăng trưởng GDP/người so với năm trước (%) |
| `do_da_dang` | Diversity Share: trung bình năng lực chuẩn hóa trên 2.508 lĩnh vực (0–1) |
| `eci` | Ecosystem Complexity Index: độ phức tạp của hệ sinh thái đổi mới |
| `coi` | Complexity Outlook Index: mức thuận lợi khi dịch chuyển sang các lĩnh vực phức tạp |
| `goi` | Growth Outlook Index: mức thuận lợi khi dịch chuyển sang các lĩnh vực tăng trưởng nhanh |
| `hang_eci_the_gioi` | Thứ hạng ECI trong 193 quốc gia (1 = cao nhất) |
| `hang_eci_chau_a` | Thứ hạng ECI trong 47 nước châu Á |
| `sang_che` | Số bằng sáng chế (đếm phân số) |
| `bai_bao_kh` | Số công bố khoa học (đếm phân số) |
| `nhan_hieu` | Số nhãn hiệu thương mại (đếm phân số) |
| `xuat_khau_ty_usd` | Giá trị xuất khẩu (tỷ USD) |
| `*_tren_trieu_dan` | Các chỉ tiêu trên tính trên 1 triệu dân |
| `ln_*` | ln(1 + x) của các chỉ tiêu trên, vì phân phối gốc lệch phải rất mạnh |
| `so_nang_luc_cong_nghe` / `_khoa_hoc` / `_san_xuat` / `_khoi_nghiep` | Số lĩnh vực có năng lực (Innovation Capability = True) trong từng chiều |
| `so_nang_luc_tong` | Tổng số lĩnh vực có năng lực (tối đa 2.508) |
| `so_nang_luc_tuong_doi` | Số lĩnh vực có lợi thế tương đối (chuyên môn hóa) |
| `so_nang_luc_tuyet_doi` | Số lĩnh vực có năng lực tuyệt đối (quy mô lớn trên thế giới) |

**Đếm phân số (fractional counting):** một sản phẩm thuộc nhiều quốc gia hoặc nhiều lĩnh vực chỉ được tính một phần cho mỗi bên. Vì vậy con số nhỏ hơn số đếm toàn phần nhưng cộng gộp được mà không bị trùng lặp.

## File 2: `2_chau_a_cat_ngang_2023.csv`

Gồm tất cả biến của file 1 tại năm 2023 (không có `nam` và tăng trưởng 1 năm), cộng thêm:

| Biến | Ý nghĩa |
|---|---|
| `eci_2013`, `do_da_dang_2013`, `so_nang_luc_tong_2013`, `gdp_dau_nguoi_2013` | Giá trị năm gốc 2013 |
| `thay_doi_eci_10_nam` | ECI 2023 − ECI 2013 |
| `thay_doi_do_da_dang_10_nam` | Mức thay đổi độ đa dạng trong 10 năm |
| `thay_doi_so_nang_luc_10_nam` | Số lĩnh vực có năng lực tăng thêm (hoặc giảm đi) trong 10 năm |
| `tang_truong_gdp_dau_nguoi_bq_10_nam` | Tăng trưởng GDP/người bình quân năm, giai đoạn 2013–2023 (%) |
| `tuong_dong_voi_viet_nam` | Proximity: mức tương đồng về cơ cấu năng lực với Việt Nam (0–1). Để trống ở dòng Việt Nam |

## File 3 và 4: `3_asean_linh_vuc_2013_2023.csv`, `4_viet_nam_linh_vuc_2013_2023.csv`

| Biến | Ý nghĩa |
|---|---|
| `ma_qg`, `ten_qg` | Quốc gia |
| `ma_linh_vuc`, `ten_linh_vuc` | Mã và tên lĩnh vực. Tiền tố cho biết chiều: T = công nghệ, S = khoa học, P = sản xuất, E = khởi nghiệp |
| `ma_nhom_linh_vuc`, `nhom_linh_vuc` | Nhóm lĩnh vực lớn (44 nhóm) |
| `chieu` | Technology / Science / Production / Entrepreneurial |
| `san_luong_2013`, `san_luong_2023` | Sản lượng (đếm toàn phần). Với chiều Production, đơn vị là USD xuất khẩu |
| `san_luong_phan_so_2023` | Sản lượng đếm phân số |
| `nang_luc_chuan_hoa_2013`, `nang_luc_chuan_hoa_2023` | Năng lực chuẩn hóa (0–1) |
| `co_nang_luc_2013`, `co_nang_luc_2023` | 1 = có năng lực trong lĩnh vực |
| `nang_luc_tuong_doi_2023`, `nang_luc_tuyet_doi_2023` | 1 = có lợi thế tương đối / tuyệt đối |
| `gia_nhap_moi` | **Biến phụ thuộc cho hồi quy logistic.** 1 = chưa có năng lực năm 2013 và có năm 2023; 0 = chưa có ở cả hai năm; để trống nếu đã có năng lực từ 2013 |
| `roi_bo` | 1 = có năng lực năm 2013 nhưng mất năm 2023; 0 = vẫn giữ; để trống nếu năm 2013 chưa có |
| `mat_do_lien_quan_2013`, `mat_do_lien_quan_2023` | Relatedness density: lĩnh vực gần với các năng lực sẵn có đến mức nào (0–1) |
| `tiem_nang_2023`, `ln_tiem_nang_2023` | Sản lượng kỳ vọng, suy ra từ năng lực ở các lĩnh vực liên quan |
| `ln_san_luong_2023` | ln(1 + sản lượng 2023) |
| `chenh_lech_tiem_nang` | ln(sản lượng) − ln(tiềm năng). Giá trị âm: sản xuất dưới mức tiềm năng ("dư địa") |
| `do_phuc_tap_linh_vuc_2023` | Capability Complexity Index: độ khó của lĩnh vực |
| `do_pho_bien_linh_vuc_2023` | Ubiquity Share: tỷ lệ quốc gia làm chủ lĩnh vực này |

---

## Gợi ý phân tích

| Câu hỏi nghiên cứu | File | jamovi | JASP |
|---|---|---|---|
| Mô tả xu hướng ECI và số năng lực của Việt Nam so với ASEAN | 1 | Exploration → Descriptives (Split by `nhom`); vẽ bằng module *scatr* hoặc lọc `ma_qg` | Descriptives → Split |
| ECI có liên quan đến GDP/người không? | 2 | Regression → Correlation Matrix; Linear Regression `ln_gdp_dau_nguoi ~ eci` | Regression → Correlation; Linear Regression (có thể dùng Bayesian) |
| Các tiểu vùng châu Á khác nhau về độ phức tạp? | 2 | ANOVA → One-Way ANOVA / Kruskal-Wallis (`eci` theo `tieu_vung`) | ANOVA; Nonparametrics |
| ASEAN và ngoài ASEAN có khác nhau? | 2 | T-Tests → Independent Samples (`asean`) | T-Tests (Welch, Mann-Whitney, Bayesian) |
| Mật độ liên quan năm 2013 có dự báo việc gia nhập lĩnh vực mới đến 2023? (kiểm định "nguyên lý liên quan") | 4 (VN) hoặc 3 (ASEAN) | Regression → 2 Outcomes Binomial: `gia_nhap_moi ~ mat_do_lien_quan_2013 + do_phuc_tap_linh_vuc_2023 + chieu` | Regression → Logistic Regression |
| Lĩnh vực nào Việt Nam có tiềm năng nhưng còn bỏ ngỏ? | 4 | Lọc `co_nang_luc_2023 = 0`, sắp xếp theo `mat_do_lien_quan_2023` hoặc `chenh_lech_tiem_nang` | Filter + Sort |
| Cơ cấu năng lực theo chiều đổi mới | 3 | Frequencies → Contingency Tables (`chieu` × `co_nang_luc_2023`, split `ma_qg`) | Frequencies → Contingency Tables |

**Lưu ý phương pháp**

- Panel có 23 năm và 47 nước, nên các quan sát không độc lập. Khi dùng file 1 cho hồi quy, nên chọn một năm cụ thể hoặc dùng mô hình hỗn hợp (jamovi module *GAMLj*, JASP → *Mixed Models*) với `ma_qg` làm hiệu ứng ngẫu nhiên.
- Một số nước rất nhỏ hoặc có ít dữ liệu (Maldives, Bhutan, Timor-Leste, Triều Tiên…) có thể là ngoại lai. Nên kiểm tra lại kết quả khi loại các nước này hoặc lọc theo dân số.
- Triều Tiên (`KP`) và Yemen (`YE`) không có số liệu GDP ở tất cả các năm.
- Trong file 3, mỗi nước có 2.508 dòng, nên các lĩnh vực trong cùng một nước không độc lập với nhau. Khi gộp nhiều nước, nên đưa `ma_qg` vào mô hình.

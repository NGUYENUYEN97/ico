# Hướng dẫn kiểm tra CLEAN dataset trên JASP và jamovi

Mục đích: mở `02_CLEAN_DATA_CANDIDATE/*.csv` trên cả hai phần mềm và đối chiếu kết quả mô tả cốt lõi với giá trị kỳ vọng ở `09_JASP_JAMOVI_EXPECTED_DESCRIPTIVES.csv` và `09_JASP_JAMOVI_EXPECTED_FREQUENCIES.csv`. Các giá trị kỳ vọng được tính bằng Python với SD chia cho n − 1, giống cách JASP và jamovi tính.

> **Trạng thái:** các giá trị kỳ vọng đã được chuẩn bị, nhưng **chưa ai chạy thực tế trên JASP hoặc jamovi**. Chỉ được ghi "đã kiểm chứng trên JASP/jamovi" trong bài viết sau khi bạn chạy xong và kết quả khớp.

## 0. Định dạng file

- CSV, mã hóa UTF-8, dấu phẩy phân cách, dấu chấm thập phân. Ô trống là missing.
- Hai tên có ký tự Unicode: `Türkiye` và một tên lĩnh vực chứa dấu nháy cong (’). Nếu thấy ký tự lạ thì phần mềm đang không đọc file theo UTF-8.
- Dữ liệu không có chuỗi `NA`, `NaN` hay `.`. Vì vậy quy ước mặc định về missing của JASP không làm mất ô nào.

## 1. Thang đo cần đặt (giống nhau ở cả hai phần mềm)

| Nhóm biến | Biến | jamovi | JASP |
|---|---|---|---|
| Định danh | `ma_qg`, `ma_linh_vuc`, `ten_qg`, `ten_linh_vuc` | ID | Nominal (Text) |
| Thời gian | `nam` | ID, hoặc Nominal nếu dùng để tách nhóm | Nominal |
| Phân loại | `tieu_vung`, `nhom`, `chau_luc_nguon`, `nhom_thu_nhap_hien_hanh`, `chieu`, `nhom_linh_vuc`, `ma_nhom_linh_vuc`, `bien_ngoai_lai` | Nominal | Nominal |
| Nhị phân 0/1 | `asean_hien_nay`, `asean_thoi_diem`, `viet_nam`, `co_nang_luc_*`, `nang_luc_tuong_doi_*`, `nang_luc_tuyet_doi_*`, `gia_nhap_moi`, `roi_bo`, `flag_*` | Nominal (Integer) | Nominal |
| Thứ bậc | `bac_thu_nhap`, `hang_eci_the_gioi`, `hang_eci_chau_a` | Ordinal | Ordinal |
| Liên tục | Các biến còn lại (`eci`, `do_da_dang`, `gdp_*`, `sang_che*`, `mat_do_lien_quan_*`, `ty_le_bat_thuong_*`…) | Continuous | Scale |

Hai phần mềm có thể tự nhận biến 0/1 là Continuous/Scale. Khi đó Descriptives sẽ tính trung bình cho biến nhị phân thay vì bảng tần số. Phải đổi các biến này sang **Nominal** trước khi chạy.

## 2. JASP

1. *File → Open → Computer → Browse* và chọn file CSV.
2. Đặt thang đo theo bảng ở mục 1 (bấm vào biểu tượng cạnh tên cột).
3. *Descriptives → Descriptive Statistics.* Đưa các biến liên tục trong file kỳ vọng vào ô *Variables*. Trong mục *Statistics*, chọn Valid, Missing, Mean, Std. deviation, Median, Minimum, Maximum.
4. Trong cùng phân tích, đưa các biến Nominal vào và chọn *Frequency tables* để so với `09_JASP_JAMOVI_EXPECTED_FREQUENCIES.csv`.
5. Biểu đồ nên xem: *Distribution plots* cho `eci`, `ln_gdp_dau_nguoi`, `ln_sang_che`. Boxplot của `sang_che` sẽ lệch rất mạnh; đó là đặc tính của dữ liệu, không phải lỗi.
6. **Kiểm tra lại biến dẫn xuất.** Thêm cột tính toán (dấu + ở đầu bảng → *Compute column*, chọn R) với công thức `ln_gdp_dau_nguoi - log(gdp_dau_nguoi)`. Chạy Descriptives cho cột này: Min và Max phải bằng 0 (hoặc khoảng 1e-15). Làm tương tự với:
   - `sang_che_tren_trieu_dan - sang_che / dan_so_trieu`
   - `ln_sang_che - log1p(sang_che)`
   - (file 4) `gia_nhap_moi - ifelse(co_nang_luc_2013 == 0, co_nang_luc_2023, NA)`
7. **Filter** (dùng cho kiểm tra và phân tích độ nhạy, không phải để làm sạch):
   - `flag_dan_so_lap_lai == 0`: loại các dòng 2023 có dân số bị lặp lại.
   - `ty_le_bat_thuong_sang_che <= 0.10`: bỏ các quốc gia-năm có nhiều dòng bất thường về đếm phân số.
   - `nam <= 2021`: dùng cho phân tích nhãn hiệu (xem UD05).

## 3. jamovi

1. *☰ → Open → Browse* và chọn file CSV.
2. Trong *Data → Setup*, đặt *Measure type* và *Data type* theo bảng ở mục 1. Biến 0/1 đặt là Nominal, kiểu Integer.
3. *Exploration → Descriptives.* Chọn N, Missing, Mean, Median, Std. deviation, Minimum, Maximum. Bật *Frequency tables* cho biến Nominal.
4. **Kiểm tra lại biến dẫn xuất** bằng *Data → Compute* (Computed variable):
   - `ln_gdp_dau_nguoi - LN(gdp_dau_nguoi)`: Min và Max bằng 0.
   - `sang_che_tren_trieu_dan - sang_che / dan_so_trieu`: bằng 0.
   - `ln_sang_che - LN(1 + sang_che)`: bằng 0.
   - `gdp_ppp_ty_usd - gdp_ppp_usd / 1000000000`: bằng 0.
   - `gia_nhap_moi` (file 4): không cần công thức. Chạy *Frequencies → Contingency Tables* với hàng `co_nang_luc_2013`, cột `co_nang_luc_2023`. Ô (0,0) phải bằng 2151, ô (0,1) bằng 170, và tổng hàng `co_nang_luc_2013 = 1` phải bằng 187. Các số này phải khớp với bảng tần số của `gia_nhap_moi` (0: 2151; 1: 170; Missing: 187).
5. **Transformed variables** (*Data → Transform*): nếu cần biến nhóm, ví dụ cắt `do_da_dang` thành tứ phân vị, hãy tạo biến mới và không ghi đè lên biến gốc.
6. **Filters** (*Data → Filters*) dùng cùng điều kiện như JASP ở mục 2.7, viết theo cú pháp jamovi, ví dụ `flag_dan_so_lap_lai == 0`.

## 4. Giá trị kỳ vọng chính (trích)

| File | Biến | N | Missing | Mean | SD | Median | Min | Max |
|---|---|---|---|---|---|---|---|---|
| 2 (cắt ngang) | eci | 47 | 0 | −0.7155 | 0.8471 | −0.6411 | −2.1016 | 0.9904 |
| 2 | do_da_dang | 47 | 0 | 0.1865 | 0.1463 | 0.1545 | 0.0136 | 0.5003 |
| 2 | ln_gdp_dau_nguoi | 45 | 2 | 9.8040 | 0.9757 | 9.7182 | 7.6007 | 11.8204 |
| 2 | tuong_dong_voi_viet_nam | 46 | 1 | 0.1689 | 0.0803 | 0.2003 | 0.0193 | 0.2980 |
| 2 | thay_doi_eci_10_nam | 47 | 0 | 0.0482 | 0.3566 | 0.0429 | −0.7678 | 0.7088 |
| 1 (panel) | eci | 1081 | 0 | −0.7696 | 0.8613 | −0.6759 | −3.0640 | 1.1059 |
| 1 | sang_che | 1028 | 53 | 10852.72 | 45531.82 | 78.86 | 0.25 | 321984.92 |
| 1 | nhan_hieu | 980 | 101 | 2155.23 | 12996.76 | 108.29 | 0.33 | 249271.37 |
| 4 (VN) | mat_do_lien_quan_2013 | 2508 | 0 | 0.1473 | 0.0489 | 0.1413 | 0.0387 | 0.9214 |

Tần số: `tieu_vung` gồm Đông Á 5, Đông Nam Á 11, Nam Á 9, Tây Á 17, Trung Á 5. `asean_thoi_diem` (2023) có 10 nước mang giá trị 1; Timor-Leste mang giá trị 0 vì gia nhập ASEAN năm 2025.

## 5. Nếu JASP và jamovi cho kết quả khác nhau

**Không chọn phần mềm cho ra kết quả mình thích.** Hãy dò nguyên nhân theo thứ tự sau:

1. **Thang đo:** một biến 0/1 đang đặt là Scale ở phần mềm này nhưng Nominal ở phần mềm kia.
2. **Định nghĩa missing:** một phần mềm đã đổi ô trống thành 0, hoặc có missing value code do người dùng tự đặt.
3. **Filter:** còn một filter đang bật ở một trong hai phần mềm.
4. **Công thức:** ví dụ dùng `LOG10` thay cho `LN`, hoặc `log` thay cho `log1p`.
5. **Làm tròn:** sai khác ở chữ số thập phân thứ 5 trở đi thường là do cách hiển thị.
6. **Phạm vi case:** sai số dòng do mở nhầm file (file 3 so với file 4) hoặc do đọc sai mã hóa ký tự.

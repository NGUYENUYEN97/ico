# 07 — ANALYSIS READINESS REPORT

**Trạng thái chung: `PROVISIONAL — UNRESOLVED ISSUES REMAIN`.** Có 4 vấn đề mã U và 7 quyết định đang chờ người nghiên cứu (xem `08_UNRESOLVED_DECISIONS.csv`).

## Phân loại theo dataset và theo mục đích phân tích

| Dataset / phân tích dự kiến | Mức | Lý do |
|---|---|---|
| **2_cat_ngang_2023**: tương quan, hồi quy giữa `eci`, `do_da_dang`, `ln_gdp_dau_nguoi`; ANOVA theo tiểu vùng | **AMBER** | Dữ liệu sạch về kỹ thuật, nhưng N = 47 (Đông Á và Trung Á mỗi nhóm chỉ 5 nước). GDP/người năm 2023 dùng dân số năm 2022 (UD01). Thiếu GDP của KP, YE |
| **2**: phân tích có dùng `nhan_hieu` năm 2023 | **AMBER/RED** | Nghi dữ liệu nhãn hiệu 2022–2023 bị cắt cụt (UD05: CN −55%). Chưa nên dùng làm biến chính trước khi giải quyết UD05 |
| **1_panel**: mô tả xu hướng ECI, độ đa dạng, số năng lực, 2001–2023 | **GREEN** | Các biến này lấy trực tiếp từ nguồn, không có vi phạm, không có missing |
| **1**: xu hướng sáng chế, bài báo | **AMBER** | Missing do không có bản ghi khác nhau theo nhóm; có dòng bất thường về đếm phân số (UD02) |
| **1**: xu hướng nhãn hiệu, đặc biệt năm 2022–2023 | **RED** | UD05 |
| **1**: tăng trưởng GDP/người năm 2023; mọi chỉ số "trên triệu dân" của năm 2023 | **RED** | Dân số năm 2023 là giá trị lặp lại (UD01); tăng trưởng 2023 bị cộng thêm khoảng bằng tốc độ tăng dân số |
| **1**: hồi quy theo thời gian có dùng nhóm thu nhập | **RED** | `nhom_thu_nhap_hien_hanh` là phân loại hiện hành, được gán ngược cho mọi năm (UD07) |
| **1**: hồi quy panel nói chung | **AMBER** | Các quan sát lặp theo nước nên không độc lập; cần hiệu ứng ngẫu nhiên/cố định theo nước hoặc sai số chuẩn cluster |
| **3_asean_linh_vuc**: logistic `gia_nhap_moi ~ mat_do_lien_quan_2013` | **AMBER** | Cần đưa hiệu ứng quốc gia vào mô hình (xem câu 3). CL001 (vắng mặt = 0) có độ tin cậy MEDIUM |
| **4_viet_nam_linh_vuc**: logistic và mô tả cho Việt Nam | **AMBER** | Dữ liệu sạch; chỉ có 170 trường hợp gia nhập; sản lượng phụ thuộc CL001 |
| `chenh_lech_tiem_nang`, `ln_san_luong_2023` | **AMBER** | Phụ thuộc CL001; với chiều P, đơn vị là USD nên không so sánh trực tiếp được với T, S, E |

## Năm câu hỏi

**1. Dataset đã đủ sạch về mặt kỹ thuật chưa?**
Về kỹ thuật thì đã đủ. Không có khóa trùng, không có giá trị ngoài miền cứng, mọi thay đổi đều được ghi log và kiểm chứng (80/80 kiểm tra), và RAW được bảo toàn. "Sạch về kỹ thuật" không có nghĩa là mọi biến đều dùng được cho mọi câu hỏi; xem bảng phân loại ở trên.

**2. Những vấn đề nào vẫn chưa giải quyết?**
- UD01: dân số năm 2023 lặp lại số của 2022 ở cả 47 nước.
- UD02: 10.052 dòng có số đếm phân số lớn hơn số đếm toàn phần.
- UD03: 134 dòng nhãn hiệu có số đếm không nguyên.
- UD04: 6 dòng Absolute = 1 nhưng Innovation = 0.
- UD05: nhãn hiệu giảm mạnh năm 2022–2023.
- UD06: quy tắc "dòng vắng mặt = 0" cần nhà sản xuất dữ liệu xác nhận.
- UD07: nhóm thu nhập không thay đổi theo thời gian.

**3. Quyết định làm sạch nào có thể làm thay đổi kết quả?**
- *Mẫu phân tích:* CL002 giữ missing thay vì 0 nên mất 53, 11 và 101 quốc gia-năm cho sáng chế, bài báo và nhãn hiệu. Phần mất này rơi chủ yếu vào Trung Á, Nam Á và nhóm thu nhập trung bình thấp. CL001 (vắng mặt = 0) đưa 17.898 dòng lĩnh vực-năm vào mẫu với sản lượng 0.
- *Ước lượng hiệu ứng:* trong file 3, gộp 11 nước cho thấy mật độ năm 2013 trung bình là 0,270 ở các lĩnh vực về sau gia nhập, so với 0,110 ở các lĩnh vực không gia nhập. Nhưng trong từng nước, khoảng cách này rất nhỏ (VN 0,148 so với 0,141; TH 0,256 so với 0,253). Phần lớn chênh lệch khi gộp đến từ **khác biệt giữa các nước** (SG, MY vừa có mật độ cao vừa gia nhập nhiều). Mô hình không có hiệu ứng quốc gia sẽ phóng đại hệ số. Đây là một vấn đề về thiết kế phân tích, không phải lỗi dữ liệu.
- *Độ bất định:* các dòng lĩnh vực lồng trong quốc gia nên cần sai số chuẩn cluster. N = 47 ở file cắt ngang cho khoảng tin cậy rộng.
- *Estimand:* `gia_nhap_moi` chỉ xác định được trong tập lĩnh vực chưa có năng lực năm 2013. Ước lượng là xác suất gia nhập có điều kiện, không phải xác suất "có năng lực".
- *Kết luận thực chất:* UD02 và UD05 có thể đảo chiều xu hướng nhãn hiệu và sáng chế ở cấp quốc gia.

**4. Nên làm những phân tích độ nhạy nào?**
1. Chạy lại khi loại các quốc gia-năm có `ty_le_bat_thuong_sang_che` hoặc `ty_le_bat_thuong_nhan_hieu` > 0,10 (UD02).
2. Chạy lại phân tích nhãn hiệu chỉ đến năm 2021 (UD05).
3. Chạy lại khi loại các dòng có `flag_dan_so_lap_lai = 1`, hoặc khi thay dân số bằng số liệu WDI (UD01).
4. Trong file 3 và 4, coi các ô CL001 là missing thay vì 0 (UD06). Có thể nhận diện các ô này qua `05_RAW_CLEAN_DIFF.csv`.
5. Logistic có hiệu ứng cố định theo quốc gia, so với mô hình gộp (file 3).
6. So sánh các case đầy đủ với các case có missing do không có bản ghi theo tiểu vùng (missing không phải MCAR).
7. Chạy lại khi loại các nước rất nhỏ (Maldives, Bhutan, Timor-Leste) khỏi file cắt ngang.

**5. Những gì KHÔNG THỂ tuyên bố chỉ từ dataset này?** Xem mục L (CLAIM BOUNDARY) trong `00_BAO_CAO_AUDIT_A_M.md`.

## Năm khía cạnh chất lượng khác nhau

| Khía cạnh | Đánh giá hiện tại |
|---|---|
| **Chất lượng dữ liệu** (DATA QUALITY) | Tốt về cấu trúc; còn 4 vấn đề logic chưa giải quyết (U) |
| **Chất lượng đo lường** (MEASUREMENT QUALITY) | Chưa được đánh giá trong bước này. ECI, COI, GOI, density và potential là chỉ số do nhà sản xuất tính, chưa được kiểm định độ giá trị. Thang đo của COI/GOI không khớp với ví dụ trong README |
| **Chất lượng thiết kế nghiên cứu** (RESEARCH DESIGN QUALITY) | Dữ liệu quan sát, thứ cấp và tổng hợp; đơn vị là quốc gia; không có nhóm đối chứng |
| **Nhận diện nhân quả** (CAUSAL IDENTIFICATION) | Không có. Thứ tự thời gian (mật độ 2013 → gia nhập 2023) chưa đủ để nhận diện quan hệ nhân quả |
| **Độ giá trị của tuyên bố** (CLAIM VALIDITY) | Chỉ hỗ trợ tuyên bố mô tả và tương quan, trong giới hạn nêu ở mục L |

Dữ liệu sạch không biến nghiên cứu quan sát này thành nghiên cứu nhân quả.

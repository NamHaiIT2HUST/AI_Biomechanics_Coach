# Mốc 1 — Kiểm kê Multi-View và baseline thăm dò

Ngày 27/11/2026. Đây là phần có thể thực hiện ngay của mốc A trong [kế hoạch ML](25-ke-hoach-ml-va-kiem-chung.md), không phải đánh giá độc lập hoặc huấn luyện model.

## Kiểm kê manifest

Công cụ [audit_multiview.py](../ai/data/audit_multiview.py) kiểm tra metadata, đường dẫn trong thư mục dữ liệu, file tồn tại, path hoặc tổ hợp subject/view/label trùng và subject nằm ở nhiều split. Nó chỉ dùng metadata của test để kiểm tra cấu trúc split; không đọc nội dung video hay fit/tune model. Output nằm ngoài Git.

Kết quả trên dữ liệu hiện có: **150 video, 25 subject, không phát hiện lỗi trong các kiểm tra trên**. Riêng side:

| Split | Subject | Video | Nhãn video good/bad |
| --- | ---: | ---: | --- |
| Train | 17 | 34 | 17 / 17 |
| Validation | 4 | 8 | 4 / 4 |
| Test | 4 | 8 | 4 / 4 |

Metadata và sự tồn tại file không chứng minh clip giải mã được, nội dung chưa thay đổi hay nhãn đúng. Chưa kiểm tra hash từng video trong lượt này; mã subject của các nguồn khác cũng có thể trùng người nhưng chưa xác minh. Quyền và điều kiện sử dụng cần đối chiếu theo từng nguồn trước khi công bố. Số lượng video không phải số lượng người hoặc rep độc lập.

Run lưu tại `data/external/annotation_work/multiview_audit_4044ecf5-daa3-4e11-ae15-895afdf3e960.json`, ghi commit code `0bd4544badc4df824890fc6d1e18378a2f901a2d`, working tree sạch ở thời điểm kiểm kê, Python 3.11.9 và SHA-256:

- Manifest: `8a15aa4093f85444219f2d0c23ad313c78e77f883db666c9f78545b314f95ef3`
- Cấu hình squat tại thời điểm kiểm kê: `c67e85fae2b844ded5110ec81c1a5d2313c16fb9643bd97d089dc7eb4c2c59a8`
- Model pose local: `64437af838a65d18e5ba7a0d39b465540069bc8aae8308de3e318aad31fcbc7b`

Các hash này nhận diện file đã dùng, không chứng minh nội dung chính xác. Hash config và model là snapshot môi trường kiểm kê; **không khẳng định pose cache bên dưới được tạo bằng đúng file model hiện tại**, vì chưa có provenance model gắn với từng cache.

Chạy lại bằng Git Bash (chọn tên output mới, tool không ghi đè):

```bash
cd /d/Project/AI_Biomechanics_Coach
./.venv/Scripts/python.exe ai/data/audit_multiview.py --output data/external/annotation_work/multiview_audit_new.json
```

## Baseline train từ cache

Đã chạy lại [sweep_rep_duration.py](../ai/data/sweep_rep_duration.py) với ngưỡng 0,8 và 1,0 giây trên **6 video train** trong `baseline_20261121`; giữ ngưỡng đáy 150°, đứng 160°, prominence 15°, tolerance 0,2 giây. Không chạy validation hoặc test. Không trích pose mới và không train model. Output là `data/external/annotation_work/baseline_20261121/baseline_train_bdf88c96-ff44-43a5-bdd2-3f2c1840ba21.json`.

Trong 6 video có 2 complete, 4 partial. Với **cả hai ngưỡng**, đối chiếu **2 video complete** với nhãn AI nháp: 26 mốc khớp, 1 mốc dự đoán thừa và 1 mốc nháp không được ghép. Bốn video partial bị loại khỏi các metric gộp; số rep phát hiện của chúng không phải số rep toàn video. Đây là phép so khớp nhãn nháp, **không phải precision/recall đã kiểm chứng**, không suy ra các ngưỡng tương đương trên video khác.

Ví dụ cần rà: `subject_003_squat_good_side` có 32 frame thiếu, 19 khoảng AI nháp và 7 rep phát hiện; không thể khẳng định 12 khoảng còn lại đều là false negative vì dữ liệu partial và nhãn chưa xác nhận. Video cá nhân `test_squat` không thuộc phép so sánh này.

```bash
./.venv/Scripts/python.exe ai/data/sweep_rep_duration.py data/external/annotation_work/baseline_20261121 --durations 0.8 1.0 --output data/external/annotation_work/baseline_20261121/baseline_train_new.json
```

Kiểm thử sau khi thêm tool: **117 test backend pass**. Các test xác minh logic, không đo độ chính xác mô hình.

## Việc còn thiếu để đóng toàn bộ mốc A

- Đề cương/rubric và deadline chưa có, nên phạm vi nghiệm thu chưa chốt.
- Chưa có nhãn rep được người độc lập xác nhận, vì vậy baseline chính thức và so sánh trước/sau chưa thể hoàn thành. AI nháp không được nâng thành nhãn người bằng thay metadata.
- Chưa kiểm tra hash từng video hoặc xác minh provenance gốc của pose cache; cần làm trước các báo cáo đòi hỏi tính tái lập cao. Khi phải đọc/trích xuất hàng loạt tốn lâu, benchmark và báo người dùng trước.
- Tiếp theo chuẩn bị quy trình/task gán nhãn mù, rồi công cụ trích đặc trưng và baseline ML theo đơn vị video. Không chạy train dài tự ý.

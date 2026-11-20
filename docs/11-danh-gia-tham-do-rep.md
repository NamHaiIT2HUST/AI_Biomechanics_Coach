# Đánh giá thăm dò rep và xử lý thiếu pose

Ngày: 21/11/2026. Người dùng đồng ý tiếp tục với nhãn nháp. Nhãn được Codex ước lượng trực quan từ ảnh video lấy mẫu mỗi 2–4 frame; cả 10 video vẫn `needs_review`, có thể thiếu rep, đặc biệt ở các khoảng bị che. **Không coi kết quả dưới đây là độ chính xác đã xác nhận, nhãn chuyên gia hay đánh giá độc lập bởi người.** Video validation không được dùng để chỉnh ngưỡng. Chưa dùng tập test.

## Cấu hình baseline

- Tập gồm 6 video train và 4 validation từ Multi-View, quay bên hông; 15 FPS. Video nhãn good/bad là nhãn toàn video từ dataset.
- MediaPipe Pose Heavy, thuật toán có sẵn, ngưỡng phát hiện chuyển động 150°, đứng 160°, prominence 15°, min duration 1 giây; ghép mốc đáy trong ±0,2 giây. Không huấn luyện model.
- Số rep nháp gồm 145 khoảng; mốc không chắc chắn, không khẳng định là số rep thực.

## Kết quả chế độ nghiêm ngặt

Bộ phân tích từ chối một video nếu có bất kỳ frame không phát hiện pose. Kết quả: **3/10 video xử lý được; 7/10 bị từ chối**. Không biến các video lỗi thành 0 rep để tính precision/recall.

Trên 3 video xử lý được, đối chiếu với nhãn nháp chỉ nhằm kiểm tra pipeline:

| Tập | Video | TP | FP | FN |
| --- | ---: | ---: | ---: | ---: |
| Train | 2 | 26 | 1 | 1 |
| Validation | 1 | 6 | 5 | 7 |

Số liệu này không thể khái quát: nhãn chưa được xác nhận, chỉ ba video, mẫu có chọn lọc và nhiều video không được xử lý. TP/FP/FN dùng mốc đáy, không đánh giá form hay sai số góc.

## Chế độ theo đoạn liên tục

Thêm `analyze_detected_spans`: chia dữ liệu tại frame thiếu pose, chạy bộ phân tích cũ trên từng đoạn liên tục, giữ số frame/timestamp gốc. Không nội suy hoặc nối các rep qua khoảng thiếu. 7 video được trả trạng thái `partial`, 3 video `complete`, 0 lỗi. `partial` nghĩa là số rep tìm được không phải số rep hoàn chỉnh của video; các đoạn ngắn cũng có thể không được phân tích. Chế độ này không sửa được landmark visibility thấp hay bảo đảm chọn đúng người khi nhiều người xuất hiện.

Ví dụ, `subject_003_squat_good_side` có 32 frame không phát hiện pose, nhãn nháp 19 khoảng và chế độ theo đoạn chỉ tìm 7 rep. Không thể suy ra độ chính xác chỉ từ phép so sánh này. `subject_002_squat_bad_side` và `subject_009_squat_bad_side` trả 0 rep trong chế độ partial; không có nghĩa người tập không thực hiện rep.

## Tái lập và lưu trữ

Chạy MediaPipe lại tốn khoảng 5 phút trên máy đã thử, tùy CPU. Lệnh sau tạo thư mục mới, không ghi đè các run cũ:

```powershell
.\.venv\Scripts\python.exe ai/data/exploratory_rep_baseline.py --output-dir data/external/annotation_work/baseline_moi
.\.venv\Scripts\python.exe ai/data/reanalyze_cached_spans.py data/external/annotation_work/baseline_moi --output data/external/annotation_work/baseline_moi/partial_summary.json
```

Run đã thực hiện tại `data/external/annotation_work/baseline_20261121/`, bao gồm snapshot nhãn nháp, cấu hình, pose, lỗi theo video và kết quả; toàn bộ nằm ngoài Git. Có thể chạy CLI chế độ partial trực tiếp:

```powershell
$env:PYTHONPATH='backend'
.\.venv\Scripts\python.exe -m app.core.landmark_analysis data/external/annotation_work/baseline_20261121/subject_003_squat_good_side_pose.json --allow-partial
```

Chế độ nghiêm ngặt vẫn là mặc định. Tùy chọn partial không phải giải pháp quality gate hoàn chỉnh.

## Việc tiếp theo

1. Người kiểm tra độc lập xác nhận nhãn hoặc loại những khoảng không thể quan sát; ghi rõ 003 bad có khoảng bị che chưa gán nhãn. Kiểm tra identity, multiple-person và góc camera.
2. Thiết kế xử lý mất pose ngắn có kiểm soát và quality gate theo khớp/từng rep, phân biệt dữ liệu thiếu, độ tin cậy thấp và kết quả không thể kết luận. Kiểm tra tác động lọc quanh các đoạn mất pose, không tự suy diễn rep.
3. Đánh giá theo số rep, mốc và coverage trên các video được gán nhãn xác nhận, test độc lập theo người; sau đó nối pipeline với evaluator và backend.

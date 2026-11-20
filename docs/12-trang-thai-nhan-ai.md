# Trạng thái nhãn rep do AI gán

## Phạm vi và mức độ tin cậy

Codex đã thực hiện một lượt gán nhãn trực quan trên 10 video development Multi-View góc side và lưu bản nháp cục bộ ở `data/external/annotation_work/tasks.json`. Các khoảng nháp được chọn từ ảnh lấy mẫu mỗi 2–4 frame; lượt rà tiếp dùng thêm các frame lân cận. Đây là nhãn **AI-generated, provisional**, không phải nhãn do người độc lập hoặc chuyên gia xác nhận. Không dùng output bộ đếm để chọn các mốc ban đầu, nhưng Codex đã xem kết quả baseline trước lượt rà sau, nên các nhãn sau rà không còn bảo đảm mù với dự đoán, bao gồm cả validation.

| Video | Khoảng nháp | Trạng thái |
| --- | ---: | --- |
| subject_003_squat_good_side | 19 | needs_review |
| subject_003_squat_bad_side | 20 | needs_review |
| subject_004_squat_good_side | 10 | needs_review |
| subject_004_squat_bad_side | 12 | needs_review |
| subject_005_squat_good_side | 18 | needs_review |
| subject_005_squat_bad_side | 17 | needs_review |
| subject_002_squat_good_side | 13 | needs_review |
| subject_002_squat_bad_side | 9 | needs_review |
| subject_009_squat_good_side | 9 | needs_review |
| subject_009_squat_bad_side | 18 | needs_review |

145 là tổng **khoảng ứng viên**, không phải số rep đã xác minh. Sau lượt rà, 11 mốc đáy đã được điều chỉnh. Vẫn có các vùng mất nét, người đi ngang, clip bắt đầu/kết thúc giữa rep và mốc đứng không rõ. Đặc biệt video subject_003 bad có các khoảng 294–310 và 394–408 bị che chưa gán, có thể thiếu rep; subject_005 có nhiều frame làm mờ và subject_002 bad có tư thế khó xác định. Nhãn của từng video vẫn `needs_review`; script kiểm tra không chấp nhận bộ này là `--require-complete`.

## Các phiên bản và sử dụng

- `tasks_before_20261121_frame_audit.json`: snapshot trước khi sửa mốc theo ảnh lân cận.
- `tasks.json`: bản nháp sau lượt rà, có `review_provenance` mô tả AI, phương pháp và việc đã nhìn baseline. Dữ liệu ngoài Git.
- `baseline_20261121/references_snapshot.json`: bản nhãn được chụp trước khi chạy baseline thăm dò. Không so sánh kết quả baseline cũ với nhãn đã sửa như thể đó là nhãn độc lập.
- `bottom_check/` và `bottom_wide/`: ảnh tổng hợp tạo từ video phục vụ rà thủ công; không đưa vào Git.

Một người gán nhãn độc lập cần xem video gốc, quyết định cách xử lý các khoảng không quan sát được, sửa và xác nhận nhãn, hoặc tạo một bộ nhãn kiểm thử mới độc lập. Nếu dùng các mốc này để phát triển, phải gọi là nhãn nháp AI và báo rõ độ không chắc chắn; không tính là thành quả kiểm chứng khoa học độc lập. Không dùng test đã xem hoặc validation đã bị lộ để tuyên bố khả năng tổng quát.

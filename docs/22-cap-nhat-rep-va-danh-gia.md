# Cập nhật rep ngắn, quản lý dữ liệu và đánh giá

## Rep ngắn cần xem lại

Pipeline bổ sung `coverage.short_motion_candidates`: chuyển động đã đạt ngưỡng độ sâu và prominence nhưng bị loại do thời lượng ngắn. UI cho phép tua tới điểm đáy của ứng viên, nêu rõ đây có thể là nhiễu và không tính là rep. Các ngưỡng và số rep chính thức giữ nguyên, chưa xác nhận độ chính xác của các ứng viên.

Trên video mẫu MediaPipe thực, hệ thống đếm 1 rep và thông báo 2 ứng viên ngắn; có một ứng viên đáy tại frame 133, khoảng 4,43 giây, và một đoạn ngắn ở đầu video. Nút tua tới ứng viên 4,43 giây đã được thử trong trình duyệt. Người quan sát vẫn cần xác nhận đâu là rep và đâu là nhiễu.

## Xóa dữ liệu local

UI có lựa chọn ẩn ID trên trình duyệt hoặc xóa vĩnh viễn video và bản ghi của tác vụ hoàn tất/thất bại sau xác nhận. API từ chối xóa job đang chờ hoặc đang xử lý; nếu file bị khóa và không xóa được thì vẫn giữ bản ghi để thử lại. Không có xóa tự động. Trong trường hợp tiến trình dừng giữa xóa file và ghi SQLite, có thể còn bản ghi thiếu video; chạy lại thao tác xóa để hoàn tất. Xem [API contract](15-api-contract-mvp.md) để biết mã phản hồi và giới hạn local.

## Chuẩn bị đánh giá test độc lập

`evaluate_rep_annotations.py` chỉ xử lý split test khi truyền `--include-test`; nhãn phải được đánh dấu reviewed và prediction test phải có `coverage_status`. Video partial/failed/insufficient được liệt kê riêng và không tính vào metric trên video complete. Công cụ từ chối một subject xuất hiện ở nhiều split trong cùng dataset khi metadata đó hiện diện; không thể phát hiện trùng người giữa các nguồn nếu ID khác/thiếu. `label_reps.py` và lệnh validate chỉ chấp nhận task test khi có `--allow-test` tường minh.

Đây là công cụ chuẩn bị; hiện chưa có nhãn test độc lập được xác nhận, chưa có kết quả benchmark độc lập và chưa train model phân loại form. Nhãn AI nháp không được tự nâng thành nhãn người.

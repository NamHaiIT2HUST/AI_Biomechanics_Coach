# Rà soát logic và giao diện

Ngày 23/11/2026. Các kết quả bên dưới mô tả phạm vi kiểm tra thực hiện, không phải chứng nhận toàn bộ dự án không có lỗi.

## Đã sửa

- Pipeline dùng `MODEL_PATH` trong cấu hình khi khởi tạo PoseEngine; trước đây cấu hình này không có hiệu lực với pipeline.
- Dữ liệu pose thiếu khớp, tọa độ/visibility không hợp lệ hoặc khớp kề trùng nhau bị tách khỏi đoạn hợp lệ. Điều này tránh dùng góc 0° giả từ hàm geometry khi vector có chiều dài bằng 0. Các frame không dùng được làm coverage thành partial.
- Công bố số frame visibility thấp đã phân tích trong `coverage.low_visibility_frames`, kể cả khi không phát hiện rep. Evaluator vẫn trả insufficient data cho rep có chất lượng pose không đủ.
- Frontend giữ kết quả cũ nếu lần upload tiếp theo bị từ chối hoặc lỗi kết nối; cho phép chọn lại cùng một file, giải thích frame thiếu/không hợp lệ và cảnh báo visibility thấp. Giao diện được chỉnh độ tương phản, trạng thái và bố cục hẹp.

## Kiểm tra và giới hạn

- Toàn bộ backend pytest: 91 pass; build frontend thành công sau khi dừng dev server dùng chung thư mục `.next`.
- Trình duyệt: thử video MP4 không giải mã được, nhận lỗi và kết quả cũ vẫn hiển thị; thử video mẫu qua API thật, xem kết quả và tua về 3,0 giây. Kiểm tra không tràn chiều ngang tại viewport 390 px. Đây không phải bộ kiểm thử E2E tự động hay thử hết các codec và trình duyệt.
- Điều tra landmarks mẫu: với min_duration 1,0 giây chỉ phát hiện rep tại frame đáy 90; với 0,8 giây phát hiện thêm đáy frame 133, rep thứ hai có thời lượng 0,93 giây. Không thay đổi ngưỡng dựa trên một mẫu: cần dữ liệu development đa dạng và đánh giá FP/FN trên test độc lập. Nhãn số rep của video mẫu vẫn cần xác nhận bằng người.
- Các frame low visibility vẫn được tính trong phân đoạn và có thể ảnh hưởng đếm rep; cảnh báo không thay thế bộ kiểm chứng chất lượng. Pose detection rate không chứng minh góc chính xác. Camera view vẫn do người dùng cung cấp và chưa được xác minh.
- Trong một số lần tua, Windows ghi log ConnectionResetError khi client đóng luồng video; thao tác trong thử nghiệm vẫn hoàn thành. Chưa khẳng định nguyên nhân hoặc sửa triệt để.

## Tham khảo giao diện

Tham khảo bố cục dashboard, sự phân cấp dữ liệu và tính trực quan của [Volt](https://github.com/M-AlAteegi/volt) và phong cách fitness tối giản của [FitLog](https://github.com/imranonweb/fitlog). Giao diện dự án được tự viết theo luồng phân tích video và không sao chép mã hoặc dữ liệu từ các dự án này.

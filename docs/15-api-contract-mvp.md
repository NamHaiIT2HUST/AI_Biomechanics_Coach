# API phân tích squat — contract MVP local

Base path `/api/v1`. Chạy một process Uvicorn với một worker. Tác vụ pose chạy trong một thread xử lý lần lượt; trạng thái lưu SQLite trong `data/outputs/analyses`.

- `GET /health`: trạng thái API.
- `GET /api/v1/exercises`: danh sách bài tập hỗ trợ; chỉ squat.
- `POST /api/v1/analyses`: multipart form `file` (MP4/MOV), `exercise_id=squat`, `camera_view=side_90deg|front_0deg|unknown`; trả 202 và `{id,status,created_at,updated_at,result,error}`. API kiểm tra kích thước, loại file, video giải mã được và metadata; FPS thấp chỉ là cảnh báo pipeline. Không chấp nhận file lớn hơn cấu hình.
- `GET /api/v1/analyses/{id}`: trạng thái `queued`, `processing`, `completed` hoặc `failed`. `result` chỉ có khi completed; `error` chỉ có khi failed. UUID không hợp lệ → 422; không tìm thấy → 404.
- `GET /api/v1/analyses/{id}/video`: video gốc đã tải lên; 404 nếu không có. Dùng `FileResponse` hỗ trợ phát/tua tùy client.
- `DELETE /api/v1/analyses/{id}`: xóa thủ công video và bản ghi kết quả của tác vụ `completed` hoặc `failed`; trả 204, 404 nếu không có, 409 nếu đang `queued`/`processing`, 503 nếu chưa xóa được file. Đóng video đang phát trước khi xóa. Không xóa tự động. Nếu tiến trình bị dừng đúng giữa thao tác xóa file và commit SQLite, bản ghi có thể còn nhưng video không còn; lặp lại lệnh để hoàn tất.

Lỗi input: 413 quá giới hạn, 415 đuôi không hỗ trợ, 422 tệp video không đọc được hoặc form sai. Trường camera view là do người dùng cung cấp, chưa xác minh. Lỗi phân tích được báo `failed`, không công bố chi tiết nội bộ. Nếu service khởi động lại khi có tác vụ queued/processing, chúng chuyển failed với lý do `interrupted`; người dùng upload lại để chạy tiếp. MVP chưa có hàng đợi phân tán, xác thực tài khoản, tự xóa, hay bảo đảm xử lý đa process. Không dùng `--workers` lớn hơn 1 và không chạy nhiều instance cùng thư mục dữ liệu.

Kết quả phụ thuộc pipeline, mang cảnh báo ngưỡng thử nghiệm, chất lượng và trạng thái partial. `detected_rep_count` không phải số rep chắc chắn; không có rep phát hiện không đồng nghĩa không có rep.

Trong `coverage`, `missing_frames` tính các frame không có pose/khớp cần thiết hoặc có tọa độ, visibility hay hình học khớp không hợp lệ; các frame này tách chuỗi phân tích. `low_visibility_frames` là số frame đã phân tích có ít nhất một khớp cần thiết dưới ngưỡng visibility. Nó không bao gồm đoạn quá ngắn bị bỏ qua, được biểu thị qua trạng thái partial và `coverage.warnings`. Trạng thái complete chỉ nói về phạm vi frame được xử lý, không khẳng định các phép đo chính xác. Kết quả cũ có thể không có trường `low_visibility_frames`.

`coverage.short_motion_candidates` là các đoạn đứng–đứng vượt các ngưỡng độ sâu/prominence nhưng bị loại vì ngắn hơn `min_duration_s`, gồm frame bắt đầu/đáy/kết thúc, thời lượng và thời điểm đáy. Đây là gợi ý để xem video: có thể là rep nhanh hoặc nhiễu, không cộng vào `detected_rep_count`, không có đánh giá form và không chứng minh có rep bị bỏ sót. Kết quả cũ có thể không có trường này.

## Chạy thử bằng Git Bash

```bash
cd /d/Project/AI_Biomechanics_Coach/backend
../.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Mở `http://127.0.0.1:8000/docs`, thử các endpoint theo README. API mặc định giới hạn 100 MiB mỗi video; cấu hình bằng biến môi trường `MAX_UPLOAD_BYTES`. Thư mục lưu dữ liệu có thể đổi qua `ANALYSES_DIR`. Video và SQLite được lưu cục bộ, không đưa vào Git. Cần có model Heavy tại `ai/models/pretrained/pose_landmarker_heavy.task`; thiếu model sẽ khiến tác vụ chuyển `failed` với mã `analysis_failed`.

Đã thử thông qua FastAPI TestClient với video `test_squat.mp4` và MediaPipe thật: POST 202, kết quả completed, coverage complete, một rep phát hiện; request Range trả 206. Đây là thử nghiệm local, không chứng minh chất lượng dự đoán trên các video khác. Pipeline hiện biết có thể bỏ sót rep thứ hai của video mẫu.

Đã kiểm tra thêm Uvicorn qua HTTP localhost với video mẫu: `/docs` 200, POST 202, trạng thái `completed` và video Range 206. Server kiểm thử đã được dừng sau khi thử; để người dùng test cần tự chạy lệnh ở trên.

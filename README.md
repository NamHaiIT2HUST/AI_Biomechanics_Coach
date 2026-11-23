# AI Biomechanics Coach

Đồ án phân tích video squat và gợi ý xem lại chuyển động. MVP local hỗ trợ upload video, chạy pose/đếm rep và xem kết quả trên giao diện web. Các ngưỡng đang thử nghiệm, không phải kết luận y khoa hoặc kết quả đánh giá độ chính xác độc lập.

## Chạy backend trên Windows với Git Bash

Tại thư mục dự án, bảo đảm đã có môi trường `.venv` và model `ai/models/pretrained/pose_landmarker_heavy.task`. Video mẫu và model không nằm trong Git, nên máy clone mới cần tự chuẩn bị chúng.

```bash
cd /d/Project/AI_Biomechanics_Coach/backend
../.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Mở [Swagger UI](http://127.0.0.1:8000/docs). Trong `POST /api/v1/analyses`, chọn **Try it out**, upload MP4/MOV, đặt `camera_view` rồi Execute. Lấy `id` trả về và dùng `GET /api/v1/analyses/{analysis_id}` để theo dõi đến `completed` hoặc `failed`. Tại `completed`, trường `result` có rep, số đo và cảnh báo; video xem tại `GET /api/v1/analyses/{analysis_id}/video`.

Môi trường Python mới có thể cài dependencies bằng `../.venv/Scripts/python.exe -m pip install -r requirements.txt` từ thư mục `backend`. Model không được tải tự động. Chạy một process, không dùng `--workers` lớn hơn 1.

## Chạy giao diện trên Git Bash

Giữ backend chạy ở terminal thứ nhất, mở terminal thứ hai:

```bash
cd /d/Project/AI_Biomechanics_Coach/frontend
npm ci
npm run dev
```

Mở `http://localhost:3000`. Chọn video MP4/MOV không quá 100 MiB, góc quay và chế độ đếm, rồi nhấn **Phân tích video**. Mặc định yêu cầu rep dài tối thiểu 1,0 giây; chế độ nhanh thử nghiệm dùng 0,8 giây và có thể đếm nhầm. Kết quả cho phép nhấn rep hoặc ứng viên ngắn để tua video. Nếu thiếu dữ liệu hoặc góc quay không phù hợp, hệ thống không kết luận theo rule. Dùng nút xóa có xác nhận để xóa một video và kết quả đã xử lý khỏi backend.

Trong kết quả, thời gian hạ/đứng lên đo theo điểm đáy ước lượng; thời gian gần đáy có thể trùng với hai pha này. Nút **Tải báo cáo JSON** lưu số đo, cảnh báo và cấu hình của lần phân tích, không kèm video. File vẫn chứa thông tin chuyển động, nên chỉ chia sẻ với người bro tin tưởng.

Để dừng, nhấn `Ctrl+C` trong từng terminal. Frontend mặc định gọi API tại `http://127.0.0.1:8000`; [hướng dẫn frontend](frontend/README.md) có cấu hình địa chỉ khác. Video/model không được lưu trong Git.

Chi tiết định dạng, trạng thái, giới hạn và cơ chế khi khởi động lại: [API contract](docs/15-api-contract-mvp.md). Core vẫn đang thử nghiệm: góc quay chưa xác minh tự động, số rep có thể bị bỏ sót, ngưỡng đánh giá chưa kiểm chứng độc lập.

Xem [hướng dẫn từng bước và giải thích lệnh](docs/24-huong-dan-chay-va-test.md) nếu cần bắt đầu từ VS Code hoặc xử lý lỗi thường gặp.

Chạy test từ thư mục gốc:

```bash
./.venv/Scripts/python.exe -m pytest backend/tests/ -v
```

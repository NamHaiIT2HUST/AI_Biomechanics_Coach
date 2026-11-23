# Frontend MVP — AI Biomechanics Coach

Giao diện Next.js cho luồng video squat → trạng thái xử lý → kết quả và tua đến đáy rep. Đây là mã nguồn ban đầu, chưa được kiểm thử chạy thật. Các ngưỡng và gợi ý chỉ mang tính thử nghiệm, không phải chẩn đoán y khoa. Số rep có thể bị bỏ sót.

## Chạy local bằng Git Bash

Cần Node.js 20 và backend, môi trường Python, model MediaPipe Heavy đã cài theo tài liệu API. Ở terminal thứ nhất:

```bash
cd /d/Project/AI_Biomechanics_Coach/backend
../.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Ở terminal thứ hai:

```bash
cd /d/Project/AI_Biomechanics_Coach/frontend
npm install
npm run dev
```

Mở `http://localhost:3000`. Frontend mặc định gọi `http://127.0.0.1:8000`; nếu cần đổi, tạo `frontend/.env.local` với `NEXT_PUBLIC_API_BASE_URL` rồi khởi động lại Next.js. CORS backend hiện cho phép các origin local đã cấu hình; cấu hình lại backend khi đổi origin frontend.

Video MP4/MOV mặc định không quá 100 MiB. Camera bên hông mới được evaluator hỗ trợ; góc quay là người dùng tự khai. Video và kết quả được lưu trên máy chạy backend, hiện không có cơ chế tự xóa. Trình duyệt có thể không phát được một số codec MOV mặc dù backend đọc được; MP4 H.264 là lựa chọn phù hợp hơn.

Chưa có lockfile vì cài npm bị treo trong môi trường hiện tại. Sau khi cài được, lưu `package-lock.json` để cố định phiên bản. Chưa chạy build, kiểm thử UI hay end-to-end theo yêu cầu gộp kiểm thử khi hoàn thiện MVP.

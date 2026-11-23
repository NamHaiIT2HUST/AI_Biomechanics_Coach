# Hướng dẫn chạy và test MVP trong VS Code

Tài liệu này dành cho workspace `D:\Project\AI_Biomechanics_Coach`, Windows, Git Bash và môi trường Python `.venv` đã có. Chạy local trên máy tin cậy: hệ thống chưa có đăng nhập hoặc xác thực.

## Chuẩn bị

- Mở thư mục dự án trong VS Code; chọn terminal **Git Bash**.
- Cần Python environment `.venv`, Node.js/npm và model `ai/models/pretrained/pose_landmarker_heavy.task`. Model và video không được đưa vào Git; trên máy mới cần chuẩn bị riêng. Không chạy `npm ci` mỗi lần khởi động nếu dependencies đã được cài và không thay đổi.
- Video MP4/MOV tối đa 100 MiB theo cấu hình mặc định; nên quay một người bên hông, đủ đầu đến bàn chân, máy ổn định và đủ sáng. MP4 H.264 thường tương thích trình duyệt hơn MOV.

## Terminal 1: backend

```bash
cd /d/Project/AI_Biomechanics_Coach/backend
../.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

`cd` chuyển đến thư mục backend; Python trong `.venv` chạy Uvicorn để phục vụ FastAPI tại cổng 8000. Backend nhận video, chạy MediaPipe pose → phân đoạn rep → đánh giá và lưu kết quả. Giữ terminal này mở. Không thêm `--workers` lớn hơn 1. `http://127.0.0.1:8000/docs` là tài liệu API tương tác, không phải giao diện người tập.

## Terminal 2: frontend

Mở terminal Git Bash thứ hai:

```bash
cd /d/Project/AI_Biomechanics_Coach/frontend
npm ci
npm run dev
```

`npm ci` cài đúng phiên bản trong lockfile; cần mạng ở lần cài đầu. `npm run dev` chạy giao diện Next.js tại `http://localhost:3000`; giữ terminal mở. Những lần sau, khi thư viện đã cài, thường chỉ cần `cd` và `npm run dev`.

## Thử phân tích

1. Mở `http://localhost:3000`, chọn video và góc quay. Góc do người dùng khai; hệ thống chưa tự xác minh.
2. Chọn **Mặc định** (rep từ 1,0 giây) hoặc **Nhanh hơn** (0,8 giây, thử nghiệm). Nhanh hơn có thể đếm nhầm; so sánh với video gốc.
3. Nhấn **Phân tích video** và chờ `Phân tích hoàn tất`. Tùy video và CPU, quá trình có thể mất thời gian; backend hiện xử lý lần lượt.
4. Đối chiếu số rep, nhấn từng rep hoặc ứng viên ngắn để tua. Kết quả hiển thị thời gian hạ đến đáy, đứng lên từ đáy và thời gian gần đáy. Khoảng gần đáy có thể chồng lên hai pha còn lại, không cộng thêm vào tổng.
5. Nhấn **Tải báo cáo JSON** để lưu số đo, mốc, chất lượng, cảnh báo và cấu hình. File không chứa video nhưng chứa dữ liệu chuyển động; cân nhắc trước khi chia sẻ.
6. **Ẩn trên trình duyệt** chỉ xóa ID cục bộ khỏi trình duyệt. **Xóa video và kết quả** xóa dữ liệu tác vụ đã hoàn tất/thất bại khỏi backend sau khi xác nhận; hành động này không thể hoàn tác. Không xóa được tác vụ đang chạy.

Video mẫu từng cho 1 rep ở chế độ mặc định và 2 rep ở chế độ nhanh, nhưng đó không phải bằng chứng độ chính xác chung. Chỉ số và ngưỡng là thử nghiệm, không phải chẩn đoán hay kết luận form an toàn.

## Kiểm thử và xử lý lỗi

```bash
cd /d/Project/AI_Biomechanics_Coach
./.venv/Scripts/python.exe -m pytest backend/tests/ -v
```

Lệnh pytest chạy các kiểm thử tự động của backend; không thay thế việc xem video thực và đánh giá nhãn độc lập. Nếu Windows từ chối thư mục Temp mặc định, xem lệnh dùng thư mục tạm riêng trong [báo cáo smoke test](17-kiem-thu-mvp-va-training.md).

- Nếu trình duyệt báo không kết nối được backend, kiểm tra terminal 1 còn chạy và `http://127.0.0.1:8000/docs` mở được.
- Nếu báo thiếu model, kiểm tra đúng đường dẫn model trong phần chuẩn bị. Nếu báo file không đọc được, thử MP4 khác; nếu vượt kích thước, chọn video nhỏ hơn.
- Nếu không tìm thấy kết quả cũ sau khi thay backend hoặc thư mục lưu, khôi phục cấu hình backend cũ và tải lại trang. Video/kết quả được lưu tại `data/outputs/analyses` mặc định, không tự xóa.
- Nếu gặp lỗi, gửi thông báo lỗi, thao tác vừa làm, chế độ đếm, số rep thực tế và JSON báo cáo nếu có thể chia sẻ. Không cần gửi video riêng tư nếu không muốn.

Nhấn `Ctrl+C` trong từng terminal để dừng hai server.

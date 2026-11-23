# Kiểm thử luồng MVP và kế hoạch huấn luyện

Ngày 23/11/2026. Đây là smoke test local, chưa phải đánh giá độ chính xác trên tập kiểm thử độc lập.

## Kết quả chạy thực tế

- Frontend `npm run build` thành công với Next.js 15.5.29; có cảnh báo CSS autoprefixer về tương thích giá trị `start`/`end`.
- Backend: 86 test pytest pass khi dùng một thư mục tạm mới trong workspace. Lần chạy đầu gặp lỗi quyền thư mục Temp mặc định của Windows; đây là lỗi fixture môi trường.
- Chạy frontend và backend local, tải `test_squat.mp4` qua trình duyệt, tác vụ đi qua queued → processing → completed. Pose detection rate 100%, phát hiện 1 rep, góc gối ở đáy 62.2°, thân 19.3°; đây là số đo thử nghiệm, không phải kết luận chất lượng động tác.
- Nhấn rep đưa video tới 3.0 giây và tải lại trang khôi phục kết quả. Kết quả video qua endpoint trả HTTP 206.
- Khi trình duyệt đổi/yêu cầu lại luồng video, log Uvicorn trên Windows có `ConnectionResetError` khi kết nối cũ bị ngắt; video và tua vẫn hoạt động trong thử nghiệm này. Cần theo dõi thêm, chưa kết luận nguyên nhân.
- Video mẫu được mô tả có 2 rep, trong khi hệ thống chỉ phát hiện 1. Nhãn này chưa phải ground truth độc lập; cần rà lại video và nguyên nhân bỏ sót trước khi đánh giá độ chính xác. Chưa kiểm thử toàn bộ trình duyệt, codec, thiết bị, tình huống biên hay video mới.

Lệnh pytest với thư mục tạm mới trên PowerShell:

```powershell
$testRunDir = Join-Path (Get-Location) ('data/outputs/pytest-' + [guid]::NewGuid().ToString())
.\.venv\Scripts\python.exe -m pytest backend/tests/ -q --basetemp $testRunDir
```

## Có cần train không?

MVP hiện dùng model MediaPipe Pose Landmarker Heavy đã được huấn luyện trước để trích khớp. Bộ lọc, phân đoạn rep, hai luật đánh giá và gợi ý là thuật toán/quy tắc cấu hình, không có model phân loại tự train. Vì vậy MVP có thể chạy mà không train thêm, nhưng không thể trình bày là đã huấn luyện một model đánh giá form riêng.

Nếu đề cương hoặc giảng viên yêu cầu huấn luyện model thì cần bổ sung một mốc ML; kiểm tra yêu cầu đó trước khi chốt phạm vi đồ án. Dù có train hay không, vẫn cần đánh giá định lượng trên nhãn độc lập và video chưa dùng để điều chỉnh.

Đề xuất khi làm ML:

1. Rà giấy phép, thống nhất nhãn theo từng rep và lỗi; nhãn AI v1 chỉ là nháp phát triển, không làm ground truth độc lập. Chia tập theo người, giữ riêng test chưa dùng trong phát triển.
2. Trích đặc trưng đã có như góc gối, góc thân, thời gian pha và chất lượng pose; xác định rõ bài toán và xử lý thiếu dữ liệu. Không đồng nhất nhãn tốt/xấu cấp video với nhãn lỗi từng rep.
3. Train baseline nhẹ trên train, chọn cấu hình trên validation, so sánh công bằng với bộ luật hiện tại; báo số lượng mẫu, phân bố nhãn, precision/recall/F1, ma trận nhầm lẫn và coverage trên test độc lập.
4. Chỉ tích hợp model nếu dữ liệu và kết quả chứng minh được giá trị; giữ lựa chọn không kết luận khi đầu vào không đủ. Việc fine-tune pose model nặng không phải điều kiện tiên quyết.

Lượt train dài chỉ tiến hành sau khi thống nhất dữ liệu và bài toán; chuẩn bị lệnh và báo người dùng tự chạy theo yêu cầu. Hiện chưa có số liệu đáng tin để ước lượng thời gian train.

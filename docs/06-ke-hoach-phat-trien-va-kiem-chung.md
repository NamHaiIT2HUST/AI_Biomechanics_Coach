# Kế hoạch phát triển từ baseline phân đoạn squat

Tài liệu này bổ sung lộ trình 12 tuần, dựa trên trạng thái mã và dữ liệu hiện có. Không coi các ngưỡng hoặc kết quả mẫu là độ chính xác đã kiểm chứng.

## Hiện trạng và quyết định

- `test_squat.json`: cấu hình 1,0 giây đếm 1 rep (đáy 90); cấu hình thử nghiệm 0,9 giây đếm 2 rep (đáy 90, 133). Các mốc này chưa được xác nhận bằng nhãn frame độc lập. Khoảng rep thứ hai là 118–146, tức 0,933 giây theo định nghĩa giao ngưỡng gối 160°.
- `sample_squat.json`: cấu hình hiện tại đếm 0; cần xem video và gán nhãn trước khi kết luận đúng hay sai.
- Landmark visibility < 0,5: 17/178 frame test và 52/180 frame sample. Baseline vẫn tính số đo từ điểm yếu và phát cảnh báo; chưa có cơ chế tự đánh giá hoặc loại số đo không tin cậy.
- Bộ đếm nay dùng ngưỡng thử nghiệm dưới 150° để nhận chuyển động, tách khỏi quy tắc đánh giá độ sâu 100°. Ngưỡng cũ 105° vẫn chọn được qua tham số; file cấu hình squat cũ vẫn khai báo 105° và chưa được nối với CLI. Ngưỡng 150° chỉ mới kiểm thử tổng hợp, cần kiểm chứng bằng nhãn video độc lập.
- Tín hiệu 2D phải tính theo pixel (x nhân width, y nhân height), vì khung hình không vuông. Góc 3D MediaPipe và góc ảnh 2D là các đại lượng khác nhau.

## Mốc 1 — Nhãn và kiểm chứng baseline

1. Xem lại video gốc; ghi cho từng video số rep, các frame bắt đầu/đáy/kết thúc, người tập, góc quay và dạng squat. Nhãn phải độc lập với output máy; ghi rõ các đoạn khó quan sát.
2. Tạo danh sách video và bộ nhãn riêng, không giả định tên thư mục good/bad là nhãn chuẩn. Ưu tiên nhiều người, chuyển động nông, nhanh, chậm, rep dở dang và góc quay sai.
3. Đánh giá số rep và sai lệch mốc theo từng video và người tập, kèm ví dụ sai. Không điều chỉnh ngưỡng bằng dữ liệu kiểm thử cuối cùng; tách tập phát triển và kiểm thử theo người tập.
4. Kiểm tra trực quan landmark ở những đoạn visibility thấp và ở đáy; quyết định các khoảng tín hiệu được nội suy ngắn, đánh dấu không chắc chắn hoặc từ chối xử lý. Không nội suy khoảng dài như dữ liệu thật.

**Hoàn thành khi:** có nhãn thủ công, báo cáo baseline tái lập và phân loại các lỗi chính; không đặt trước kết quả phải đạt.

## Mốc 2 — Phân đoạn và chất lượng đo

1. Thử ngưỡng thời lượng, biên độ chuyển động, prominence và các cách xác định đầu/cuối trên tập phát triển; so sánh với nhãn và báo cáo nhạy cảm tham số. Không chốt 0,9 giây dựa trên một video.
2. Tách phát hiện rep khỏi đánh giá độ sâu để rep nông có thể được nhận diện, đồng thời kiểm tra chống rung và nhấp nhổm. Xử lý các rep cắt ở đầu/cuối video và trường hợp không trở lại tư thế đứng.
3. Xây dựng quality gate: theo dõi visibility theo từng khớp và từng pha, cảnh báo phép lọc có thể bị ảnh hưởng bởi điểm kém tin cậy, quyết định lúc nào kết quả phải là không đủ dữ liệu. Kiểm thử frame thiếu, góc quay và các tín hiệu hỏng.
4. Đo sai số góc trên frame được đo tay bằng cùng quy ước tọa độ, ghi rõ phương pháp đo, góc quay, sai số theo video và thống kê tổng hợp; MAE < 5° là mục tiêu cần kiểm chứng, không phải kết quả đảm bảo.

**Hoàn thành khi:** đếm và mốc rep được đánh giá độc lập, có cơ chế báo không đủ tin cậy và test hồi quy cho các lỗi đã gặp.

## Mốc 3 — MVP phân tích offline

Nối pose → đo góc → kiểm tra chất lượng → tách rep → đánh giá bằng cấu hình → JSON và frame bằng chứng; bổ sung API và giao diện đơn giản. Cho phép xem lại video, số đo và cảnh báo. Kiểm thử đầu-cuối với video mới và các trường hợp đầu vào lỗi. Quy tắc 100°/45° là giá trị thử nghiệm, không kết luận về nguy cơ chấn thương cá nhân.

## Mốc 4 — ML, AI coach và mở rộng

- Chỉ huấn luyện ML khi có đủ nhãn, nhiều người tập và tập kiểm thử độc lập theo người. So sánh baseline luật với mô hình, báo cáo cả dữ liệu, sai số và giới hạn. Thông báo người dùng trước khi chạy train lâu; hiện chưa cần train.
- Bắt đầu coaching bằng thông điệp dựa trên kết quả xác định được; chỉ thêm RAG/LLM sau khi có nguồn, quy trình kiểm tra trích dẫn và kiểm thử nội dung. Không cho AI tự bịa số đo hoặc kết luận y khoa.
- 3D viewer và webcam là mở rộng sau khi pipeline offline và đánh giá cơ bản ổn định.

## Chạy baseline hiện tại trên Windows

```powershell
$env:PYTHONPATH = 'backend'
.\.venv\Scripts\python.exe -m app.core.landmark_analysis data/processed/landmarks/test_squat.json
.\.venv\Scripts\python.exe -m app.core.landmark_analysis data/processed/landmarks/test_squat.json --min-duration 0.9
.\.venv\Scripts\python.exe -m pytest backend/tests/ -v
```

CLI báo số frame độ tin cậy thấp toàn video, trong từng rep và gần frame đáy (cửa sổ ±5 frame của bộ lọc). Nó yêu cầu frame liên tục và từ chối dữ liệu thiếu pose; đây là baseline khảo sát, chưa thay cho quality gate.

## Ghi chú phân đoạn hiện tại

- Phát hiện cực tiểu trong từng khoảng đứng–đứng để hai rep sát nhau không loại lẫn nhau. Đoạn chuyển động bị loại hoặc chưa kết thúc mang nhãn `unknown`.
- Ngưỡng mặc định 150°, prominence 15° và 1 giây là các tham số thử nghiệm; độ sâu 100° thuộc đánh giá form, chưa được triển khai trong baseline.
- Notebook 03 cố định ngưỡng 105° để tái lập số liệu baseline cũ. Trên CLI, dùng `--bottom-threshold 105` để so sánh.

- CLI hiện đánh dấu từng rep `needs_review` khi có landmark visibility thấp trong khoảng rep hoặc vùng lân cận ±5 frame dùng bởi Savitzky–Golay. `no_low_visibility_detected` chỉ nói không phát hiện visibility thấp, không chứng minh góc đúng hoặc góc quay phù hợp. Đây là cảnh báo sơ bộ, chưa phải quality gate hoàn chỉnh.

## Đánh giá rep theo nhãn thủ công

Chọn đáy từng rep bằng cách xem video gốc trước khi xem output máy. Lưu kết quả riêng cùng tên video, người tập, FPS, các frame bắt đầu/đáy/kết thúc, góc quay và ghi chú frame khó nhìn. File dưới đây chỉ minh họa định dạng, **không phải nhãn thật**; thay danh sách bằng số liệu thực tế sau khi gán nhãn. Frame đánh số từ 0.

```json
{
  "videos": [
    {
      "id": "video-id",
      "fps": 30,
      "reference_bottom_frames": [10, 50],
      "predicted_bottom_frames": [11, 51]
    }
  ]
}
```

Chạy `python -m app.core.rep_validation <duong-dan-json> --tolerance 0.2` với `PYTHONPATH=backend`. Công cụ ghép một–một trong khoảng sai lệch cho phép, báo precision/recall, chênh lệch số rep và sai lệch thời gian đáy. Nó chỉ đánh giá mốc đáy, không đánh giá đầu/cuối, chất lượng form hay sai số góc. Ngưỡng tolerance 0,2 giây là tham số thử nghiệm. Không lấy danh sách dự đoán làm nhãn tham chiếu.

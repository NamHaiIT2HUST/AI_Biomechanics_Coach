# Nhãn AI v1 và evaluator squat thử nghiệm

## Đóng băng nhãn để phát triển

Theo quyết định của người dùng, bản nhãn nháp AI cho 10 video development được đóng băng ở `data/external/annotation_work/ai_provisional_v1.json`: 145 khoảng ứng viên, kèm SHA-256 của file nguồn và metadata `development_only`, `unverified`, `independent_benchmark=false`. Các trạng thái `needs_review` và ghi chú về vùng bị che vẫn được giữ nguyên. Đây là nhãn tham khảo để phát triển, không phải số rep đã xác nhận hoặc nhãn người đánh giá. Bản snapshot này đã được rà sau khi người gán nhãn AI thấy kết quả baseline, nên validation không còn mù. File gốc và nhãn nằm ngoài Git.

Có thể tạo một snapshot tại đường dẫn mới, không ghi đè bản trước:

```powershell
.\.venv\Scripts\python.exe ai/data/freeze_ai_annotations.py data/external/annotation_work/tasks.json data/external/annotation_work/ai_provisional_v2.json
```

Script chỉ chấp nhận bộ task hợp lệ đã ghi provenance AI, không cho nhãn nháp trở thành nhãn người đã xác nhận. Việc kiểm chứng độc lập có thể thực hiện ở giai đoạn đánh giá, không chặn phát triển MVP.

## Evaluator

`backend/app/core/evaluator.py` đọc các luật từ cấu hình squat, không để LLM xác định lỗi hoặc thêm số đo. `evaluate_squat` xử lý một rep; `evaluate_squat_analysis` nhận kết quả từ phân tích theo đoạn và giữ trạng thái video complete/partial.

- Trả `finding`, `within_threshold` hoặc `insufficient_data` theo từng luật, cùng số đo, ngưỡng, đơn vị và frame đáy. `within_threshold` chỉ nghĩa là không vượt ngưỡng cấu hình, không khẳng định động tác an toàn hoặc đúng kỹ thuật toàn diện.
- Rep có quality status không rõ/thấp, giá trị không hợp lệ hoặc không có góc, hay góc quay không được hỗ trợ → `insufficient_data`.
- `camera_view` do người dùng cung cấp; evaluator **không xác minh** góc quay tự động. Visibility đủ cao không chứng minh chọn đúng người hoặc phép đo chính xác. Những ngưỡng 100°/45° là thử nghiệm, không đưa ra kết luận y khoa.
- Với video partial, có thể đánh giá những rep được phát hiện nhưng phải giữ cảnh báo số rep toàn video không đầy đủ.

Smoke test trên pose đã lưu của `subject_004_squat_good_side`: kết quả complete, 10 rep, 18 lượt kiểm tra trong ngưỡng và 2 lượt kích hoạt luật. Đây chỉ cho thấy mã chạy trên dữ liệu thực; chưa xác nhận hai nhận xét đúng vì không có nhãn lỗi cụ thể độc lập.

## Tiếp theo

Nối video → pose → phân tích theo đoạn → evaluator thành một pipeline thống nhất, làm rõ cấu hình ngưỡng đếm 105°/150°, xử lý video/pose thiếu và chuẩn hóa schema. Sau đó xây API upload/trạng thái/kết quả và giao diện. Không cần train dài cho bước này.

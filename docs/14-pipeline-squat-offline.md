# Pipeline squat offline v1

Pipeline thực thi video → MediaPipe Pose → góc 2D theo pixel → lọc → phân đoạn rep theo đoạn pose liên tục → đánh giá bằng `squat.json`. Đây là core thử nghiệm, chưa phải API hay ứng dụng hoàn chỉnh. Góc quay là lựa chọn do người dùng cung cấp và chưa được hệ thống xác minh. Không diễn giải ngưỡng thành chẩn đoán hoặc kết luận an toàn.

## Chạy trên Windows

Mô hình MediaPipe Heavy phải tồn tại tại `ai/models/pretrained/pose_landmarker_heavy.task` và môi trường `.venv` phải cài dependencies. Từ PowerShell:

```powershell
$env:PYTHONPATH = 'backend'
.\.venv\Scripts\python.exe -m app.core.pipeline data/raw/squats_bad/test_squat.mp4 --camera-view side_90deg --output data/outputs/pipeline/test_squat.json
```

Git Bash:

```bash
PYTHONPATH=backend ./.venv/Scripts/python.exe -m app.core.pipeline data/raw/squats_bad/test_squat.mp4 --camera-view side_90deg --output data/outputs/pipeline/test_squat.json
```

Không truyền `--output` để in JSON ra terminal. Khi có output, lệnh chỉ tạo file mới và từ chối ghi đè. Các lựa chọn góc quay: `side_90deg`, `front_0deg`, `unknown`; hai góc không phải side sẽ trả `insufficient_data` cho các luật 2D side-view. Có thể chỉ định `--config` tới một JSON hợp lệ khác.

## Đầu ra

- `outcome`: `reps_detected`, `no_reps_detected`, hoặc `insufficient_data`. Không có rep được phát hiện không đồng nghĩa video không có rep.
- `video`, `pose`, `coverage`: metadata, số frame phát hiện pose và đoạn dữ liệu quan sát được. `coverage.status = partial` nghĩa là có frame thiếu hoặc đoạn quá ngắn; có thể bỏ lỡ rep, không coi số rep phát hiện là đầy đủ.
- `config`: tham số đã dùng và SHA-256 của JSON cấu hình đã chuẩn hóa. Mốc thời gian dùng FPS danh nghĩa; chưa xử lý video frame-rate biến thiên hoặc xác thực metadata bằng decoder khác.
- `reps`: mốc bắt đầu/đáy/kết thúc, góc, chất lượng và `assessment` cho từng luật với frame bằng chứng. Chất lượng kém, view không phù hợp hoặc số đo thiếu → `insufficient_data`; `within_threshold` chỉ là trong ngưỡng thử nghiệm, không chứng minh form chuẩn.
- `warnings`: giới hạn của phân tích, góc quay do người dùng chọn, và cảnh báo FPS dưới mức khuyến nghị (không tự động từ chối).

Mốc rep có pose bị mất trong vùng ảnh hưởng của bộ lọc được đánh dấu `needs_review` thay vì đánh giá bình thường. Không nội suy qua gap hoặc khẳng định số rep toàn video khi coverage partial.

## Cấu hình và kiểm thử thực tế

`backend/app/exercises/squat.json` là nguồn tham số pipeline: ngưỡng phát hiện chuyển động 150°, trở về đứng 160°, prominence 15°, tối thiểu 1,0 giây, visibility 0,5; ngưỡng đánh giá độ sâu 100° và thân 45°. Đây đều là cấu hình thử nghiệm, chưa kiểm chứng độc lập; ngưỡng nhận chuyển động và ngưỡng đánh giá độ sâu là hai mục đích riêng.

Đã chạy trên `test_squat.mp4`: 178 frame, 30 FPS, coverage complete, 1 rep phát hiện, đáy frame 90; cả hai phép đo của rep này trong ngưỡng cấu hình. Dữ liệu thực có thể chứa rep thứ hai (bản thử trước đếm 2 khi giảm min duration xuống 0,9 giây); vì vậy **mặc định 1,0 giây có thể bỏ sót rep**. Không dùng kết quả này để tuyên bố độ chính xác hoặc form an toàn. File kết quả thực nằm ngoài Git tại `data/outputs/pipeline/test_squat_pipeline_v1.json`.

Tiếp theo: cải thiện tách rep và quality gate trên dữ liệu có nhãn; xây API xử lý video và frontend. Chưa có xác thực danh tính người tập khi nhiều người trong khung hình, cơ chế kiểm tra góc quay tự động, overlay, hoặc đánh giá thực nghiệm độc lập.

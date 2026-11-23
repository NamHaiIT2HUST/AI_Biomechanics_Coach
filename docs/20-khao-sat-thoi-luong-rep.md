# Khảo sát thời lượng rep trên dữ liệu train nháp

Ngày 23/11/2026. Đây là thí nghiệm phát triển, **không phải đánh giá độ chính xác độc lập** và không phải huấn luyện model.

## Mục đích và phương pháp

So sánh ngưỡng thời lượng tối thiểu 0,7 / 0,8 / 0,9 / 1,0 / 1,2 giây trên pose đã lưu từ `baseline_20261121`. Dùng riêng 6 video split train, không chạy trên validation hay test. Giữ nguyên các ngưỡng đáy 150°, đứng 160°, prominence 15°; ghép mốc đáy với sai lệch tối đa 0,2 giây.

Các mốc tham chiếu là bản nháp do AI ước lượng, chưa được người rà độc lập, và có thể thiếu rep. Trong 6 video, 2 video coverage complete, 4 partial; chỉ tính TP/FP/FN cho 2 video complete. Partial không có nghĩa không có rep: các rep qua frame thiếu có thể bị bỏ qua. Pose cache và nhãn dùng trong phép thử chưa xác minh độc lập tính chính xác.

## Kết quả

| Ngưỡng | Video complete | TP | FP | FN | Rep phát hiện trong 4 video partial (chỉ tham khảo) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0,7 s | 2 | 26 | 1 | 1 | 46 |
| 0,8 s | 2 | 26 | 1 | 1 | 46 |
| 0,9 s | 2 | 26 | 1 | 1 | 46 |
| 1,0 s | 2 | 26 | 1 | 1 | 46 |
| 1,2 s | 2 | 26 | 1 | 1 | 44 |

TP/FP/FN ở đây chỉ so khớp mốc đáy với nhãn nháp, không phản ánh lỗi kỹ thuật hoặc chất lượng tư thế. Việc tất cả ngưỡng cho cùng kết quả trên 2 video complete không chứng minh các ngưỡng tương đương trên video khác. Các tổng partial cũng không được dùng làm precision/recall toàn video.

Video người dùng `test_squat` không thuộc phép sweep trên: với cấu hình hiện tại 1,0 giây có 1 rep, còn 0,8 giây có thêm ứng viên rep tại frame 133 dài khoảng 0,93 giây. Số rep của video này cần người xem xác nhận; không điều chỉnh ngưỡng sản phẩm từ một mẫu. Giữ nguyên 1,0 giây cho đến khi có thêm video nhanh, nhãn kiểm chứng và phép đo false positive.

## Tái lập

Tool [sweep_rep_duration.py](../ai/data/sweep_rep_duration.py) đọc các tệp pose đã cache, không chạy lại MediaPipe, không sửa nhãn hoặc thay cấu hình ứng dụng. Nó chỉ sử dụng video train; kiểm tra FPS/số frame, ghi SHA-256 của snapshot và pose, báo lỗi file thiếu và loại video partial khỏi metric tổng hợp. Snapshot dùng trong run này có SHA-256 `b23899fb8a1d1cc8e2d1315ceb6a5819343ab19c5a0cb739fb2e8008c17f02cc`. Các đường dẫn cache và output ở `data/external` nằm ngoài Git.

Git Bash, từ thư mục dự án (đổi tên output nếu đã tồn tại):

```bash
./.venv/Scripts/python.exe ai/data/sweep_rep_duration.py \
  data/external/annotation_work/baseline_20261121 \
  --output data/external/annotation_work/baseline_20261121/duration_sweep_new.json
```

Output của run hiện tại là `duration_sweep_28a2e22e-1063-4690-b572-e63e85bb36ff.json` trong thư mục baseline; tool không ghi đè file đã có. Chạy test backend sau thay đổi: 97 pass.

## Cần làm tiếp

- Người xem độc lập rà `test_squat` và các video rep nhanh; chuẩn hóa các tình huống đứng chưa khóa, rep nông, rung và clip bị cắt.
- Chuẩn bị thêm dữ liệu train có tốc độ khác nhau; dùng validation để chọn phương án sau khi lập quy trình, sau cùng đo trên test độc lập chia theo người.
- So sánh false positive, false negative, coverage và vị trí đáy; nếu không đủ bằng chứng, giữ ngưỡng và nêu rõ rep nhanh có thể bị bỏ sót.

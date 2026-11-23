# Mốc 1: Gán nhãn rep độc lập và đánh giá baseline

Bộ tác vụ phát triển gồm 10 video Multi-View góc side: subject_003/004/005 thuộc train và subject_002/009 thuộc validation, mỗi người một video good và một video bad. Không chọn hoặc xem nhãn từ tập test. Các nhãn good/bad là của nguồn ở mức video; không suy ra nhãn cho mỗi rep.

Danh sách tác vụ được tạo tại `data/external/annotation_work/tasks.json` từ manifest và hash SHA-256 của từng video. Các file video, ảnh liên hệ, dữ liệu nhãn cá nhân nằm ngoài Git. `unreviewed` không đồng nghĩa với video có 0 rep. Kết quả gán nhãn phải được một người kiểm tra trên video gốc trước khi coi là nhãn tham chiếu.

## Giao thức gán nhãn độc lập

- Xem video gốc trước khi xem dự đoán của detector. Bắt đầu/đáy/kết thúc là frame 0-based; bắt đầu là lúc rời tư thế đứng, đáy là tư thế thấp nhất quan sát được và kết thúc là khi trở lại đứng.
- Không ép các rep bị cắt đầu/cuối thành rep hoàn chỉnh. Nếu video bị che, pha không quan sát được hoặc không thể quyết định, lưu `needs_review` và ghi chú; không biến khoảng đó thành nhãn chuẩn. Các định nghĩa này là quy ước đánh giá, không chứng minh form an toàn.
- Ứng dụng chỉ hiển thị video gốc, không hiển thị kết quả detector; nhãn video good/bad không được dùng như nhãn lỗi riêng cho mỗi rep. Không gán nhãn từ tín hiệu MediaPipe.
- Trong clip có dừng ở đáy, chọn một frame theo quan sát và ghi chú sự không chắc chắn. Sai lệch 0,2 giây là ngưỡng thử nghiệm cho đánh giá đáy, không phải tuyên bố độ chính xác.

## Tạo danh sách và đánh dấu

Sau khi chạy script chuẩn bị dataset nếu cần, tạo một lần:

```bash
cd /d/Project/AI_Biomechanics_Coach
./.venv/Scripts/python.exe ai/data/rep_annotation_tasks.py create
```

Script từ chối ghi đè `tasks.json` đã tồn tại. Tác vụ hiện có đã được tạo và gồm 10 video chưa xem. Xem ID trong `tasks.json`; chạy trên Git Bash với một ID và tên người gán nhãn, ví dụ:

```bash
./.venv/Scripts/python.exe ai/data/label_reps.py --id subject_004_squat_good_side --annotator "ten-nguoi-gan-nhan"
```

Trong cửa sổ: `A/D` lùi/tiến một frame, `J/L` lùi/tiến 15 frame; `S/B/E` đánh dấu start/bottom/end theo thứ tự; `U` bỏ rep vừa hoàn thành, `C` xóa nhãn đang dở. `R` lưu reviewed, `N` lưu needs-review, `Q` thoát không lưu. Dùng `N` khi clip bị che hoặc chưa xác định; ghi thêm `notes` trong JSON. Chỉ dùng `R` khi đã xem hết video và kiểm tra mọi mốc, kể cả quyết định video có 0 rep. Có thể chạy lại lệnh để chỉnh nhãn đã lưu. Đóng cửa sổ bằng `Q` để thoát không lưu. Cần môi trường OpenCV có hỗ trợ cửa sổ đồ họa.

Kiểm tra cấu trúc và tiến độ:

```bash
./.venv/Scripts/python.exe ai/data/rep_annotation_tasks.py validate data/external/annotation_work/tasks.json
./.venv/Scripts/python.exe ai/data/rep_annotation_tasks.py validate data/external/annotation_work/tasks.json --require-complete
```

Lệnh thứ hai chỉ thành công khi mọi video reviewed và có người gán nhãn. Nó kiểm tra cấu trúc, không thay thế việc kiểm tra trực quan. Nếu `needs_review`, tiếp tục xử lý thủ công hoặc quyết định loại video theo tiêu chí được ghi lại trước khi đánh giá.

## Đánh giá dự đoán

Chỉ sau khi chốt nhãn độc lập, tạo một JSON dự đoán với ID trùng tuyệt đối, chẳng hạn định dạng:

```json
{"videos": [{"id": "video_id", "bottom_frames": [20, 50], "coverage_status": "complete"}]}
```

Ví dụ minh họa định dạng, không phải kết quả thực. Cần liệt kê mọi video trong file nhãn. Dùng `coverage_status` là `complete`, `partial`, `failed` hoặc `insufficient_data`; những video không complete được báo riêng và loại khỏi các metric mốc đáy. `bottom_frames: []` chỉ có nghĩa là không phát hiện rep, không tự thể hiện lỗi xử lý. Vì tương thích dữ liệu cũ, train/validation thiếu `coverage_status` được coi là complete; cần điền rõ trường này khi chạy mới.

```bash
./.venv/Scripts/python.exe ai/data/evaluate_rep_annotations.py data/external/annotation_work/tasks.json data/external/annotation_work/predictions.json --tolerance 0.2
```

Công cụ từ chối nhãn chưa hoàn chỉnh và ID thiếu/trùng, tách kết quả theo split và báo TP/FP/FN, precision/recall, sai số số rep, sai lệch frame đáy ghép được. Các tác vụ test chỉ được bật tường minh bằng `--include-test` khi đánh giá; mỗi dự đoán test bắt buộc có `coverage_status`. Công cụ phát hiện trùng subject giữa các split khi có `dataset`/`subject`, nhưng không thể phát hiện trùng người giữa các nguồn nếu ID khác hoặc thiếu. Chỉ đánh giá mốc đáy và count; chưa đánh giá mốc đầu/cuối, góc hay chất lượng form. Không chọn ngưỡng theo tập test.

## Trạng thái

Đã chọn và khóa danh sách development, tạo công cụ gán nhãn/kiểm tra/đánh giá và test. **10/10 video vẫn chưa được gán nhãn độc lập**; chưa có kết quả precision/recall thực nghiệm. Cần người gán nhãn xem video để hoàn tất mốc, sau đó mới tạo và đánh giá dự đoán baseline. CFRep không dùng cho mốc này do giấy phép và mã người chưa rõ. Không train.

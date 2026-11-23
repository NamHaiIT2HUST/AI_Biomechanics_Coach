# Ưu tiên phát triển tiếp theo

Cập nhật 23/11/2026. Đây là kế hoạch sau [rà soát logic/UI](19-ra-soat-logic-va-giao-dien.md) và [khảo sát ngưỡng rep](20-khao-sat-thoi-luong-rep.md). Thời gian thực hiện phụ thuộc dữ liệu, yêu cầu học phần và nguồn lực; không coi các khoảng thời gian dự kiến là cam kết.

## Hiện trạng

- Pipeline squat local đã nối video → MediaPipe Pose Heavy có sẵn → động học → phân đoạn rep → hai luật đánh giá → API → UI. Video mẫu đã được thử thực tế qua trình duyệt; giao diện có cảnh báo và tua đến rep.
- 97 test backend pass ở lượt gần nhất; frontend đã build thành công trước lần bổ sung công cụ khảo sát, không có thay đổi frontend sau lượt build đó. Đây không phải kiểm thử toàn diện mọi trường hợp.
- Còn lỗi bỏ sót rep nhanh: video mẫu được mô tả có 2 rep nhưng cấu hình 1 giây chỉ phát hiện 1. Ngưỡng 0,8 giây phát hiện thêm một ứng viên dài 0,93 giây, chưa đủ bằng chứng để đổi mặc định.
- Thử nghiệm trên 6 video train có 2 complete, 4 partial và nhãn AI chưa xác minh. Không dùng kết quả này để tuyên bố độ chính xác độc lập. Model pose là pretrained, chưa có model tự train đánh giá form.

## P0 — Tăng chất lượng bộ đếm và quality gate

1. Rà lại video mẫu cùng các trường hợp rep nhanh, nông, dừng ở đáy, chưa đứng hẳn, bị cắt và rung; ghi frame đáy/bắt đầu/kết thúc, trường hợp mơ hồ và provenance. Người rà độc lập không xem dự đoán trước khi gán nhãn đánh giá.
2. Đo baseline, phân tích từng nguyên nhân bỏ sót/đếm nhầm trên dữ liệu development. Chọn ngưỡng hoặc thuật toán bằng train/validation, theo dõi FP/FN, sai lệch đáy và coverage, không điều chỉnh theo tập test.
3. Bổ sung hoặc sửa thuật toán dựa trên kết quả, kèm test hồi quy cho nguyên nhân đã tái hiện. Rà logic khi visibility thấp, người bị che, khớp lỗi, rep cắt qua gap hoặc có nhiều người; trả không đủ dữ liệu khi chưa đáng tin.

**Xong khi:** có bảng trước/sau, test hồi quy pass, trường hợp video mẫu được giải thích, và quyết định ngưỡng có căn cứ; nếu chưa đủ nhãn thì giữ ngưỡng hiện tại và ghi giới hạn.

## P1 — Hoàn thiện MVP local

1. Kiểm thử end-to-end và sửa lỗi: upload hợp lệ/không hợp lệ/quá lớn, no reps, partial, góc không hỗ trợ, backend offline, job failed/restart, reload, tua và codec. Thử responsive, bàn phím và ít nhất hai trình duyệt sẵn có.
2. Cải thiện luồng quản lý dữ liệu: chỉ rõ thư mục lưu, thời gian lưu và cách xóa; nếu thêm xóa trong UI/API, quy định tác vụ đang chạy và kiểm thử, không xóa dữ liệu cũ tự động. Điều tra log `ConnectionResetError` khi tua trên Windows.
3. Chuẩn hóa hợp đồng API và hướng dẫn cài/chạy từ máy mới, bao gồm model, một worker, CORS, giới hạn upload và dọn dữ liệu theo lựa chọn người dùng.

**Xong khi:** các luồng và lỗi chính có bằng chứng thử nghiệm, có thể tái lập demo trên máy được hỗ trợ và giới hạn vận hành được ghi rõ.

## P2 — Dữ liệu và kiểm chứng cho báo cáo

1. Kiểm kê nguồn video, điều kiện sử dụng, người tập, góc quay và nhãn; xác minh quyền trước khi dùng hoặc công bố. Không đưa video, model hoặc dữ liệu cá nhân lên Git.
2. Xây nhãn độc lập cho số rep và frame đáy; nếu đánh giá lỗi form, có nhãn lỗi cấp rep và định nghĩa thống nhất. Nhãn tốt/xấu cấp video và nhãn AI nháp không tự trở thành nhãn lỗi.
3. Chia theo người, giữ test chưa dùng để điều chỉnh; ghi số người/video/rep, coverage, TP/FP/FN, precision/recall, sai số đếm và thời gian đáy. Với góc, cần phép đo tham chiếu phù hợp mới báo MAE.
4. Viết phương pháp, baseline, kết quả, giới hạn và chuẩn bị video demo, slide, kịch bản phản biện.

**Xong khi:** kết quả trên test độc lập có thể tái lập, báo cả trường hợp không phân tích được và không nhầm với đánh giá dựa trên nhãn AI nháp.

## P3 — Model ML riêng khi yêu cầu hoặc dữ liệu cho phép

Chốt yêu cầu giảng viên và bài toán cụ thể trước; ví dụ phân loại một lỗi có nhãn cấp rep, sử dụng đặc trưng góc và thời gian pha. So sánh baseline nhẹ với bộ luật hiện tại trên cùng phân chia theo người; chỉ tích hợp khi dữ liệu, kết quả và hành vi với đầu vào thiếu đủ thuyết phục. MediaPipe pose đã pretrained; hiện chưa có model đánh giá form tự train.

Trước lượt train dài: chuẩn bị lệnh, cấu hình, dữ liệu, yêu cầu CPU/GPU/RAM, ước lượng từ thử nghiệm ngắn, đường dẫn output và cách gửi kết quả; báo người dùng tự chạy. Chưa ước lượng thời gian khi chưa biết model, dữ liệu và phần cứng.

## Cần người dùng chuẩn bị

| Thông tin hoặc dữ liệu | Vì sao cần | Có chặn công việc ngay? |
| --- | --- | --- |
| Đề cương/rubric, yêu cầu thầy, hạn nộp | Xác định model tự train, số bài tập và hình thức nghiệm thu có bắt buộc không | Không chặn rà core/UI; cần để chốt phạm vi học phần |
| Video squat mới có sự đồng ý sử dụng, gồm rep tốc độ khác nhau | Làm dữ liệu development và giữ một phần chưa xem cho test | Không chặn sửa lỗi tái hiện; cần để đánh giá rộng |
| Người rà nhãn độc lập | Xác nhận rep/đáy và lỗi có thể quan sát | Cần trước báo cáo độ chính xác độc lập |
| Thông số CPU/GPU/RAM/dung lượng | Chọn cấu hình và ước lượng lượt train | Chỉ cần trước thử nghiệm hoặc train dài |

Thứ tự mặc định: P0 và P1 trước; chuẩn bị P2 song song; P3 theo yêu cầu và điều kiện dữ liệu. Mỗi phần có kiểm thử phù hợp và commit riêng.

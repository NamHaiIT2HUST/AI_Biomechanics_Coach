# Kế hoạch hoàn thiện core và MVP v1

Cập nhật theo mã nguồn ngày 19/11/2026. MVP là bản phân tích squat từ video quay bên hông, chạy được đầu cuối và hiển thị giới hạn độ tin cậy; không coi là sản phẩm đã xác nhận độ chính xác lâm sàng.

## Đầu ra MVP v1

Người dùng tải lên một video squat bên hông → theo dõi trạng thái → xem video và các rep phát hiện được, góc gối/thân tại đáy, điểm thời gian bằng chứng, nhận xét theo quy tắc thử nghiệm và cảnh báo dữ liệu không đủ. Tối thiểu có hướng dẫn ngắn cố định gắn với lỗi thực sự được phát hiện. Khi không đủ dữ liệu, phải hiển thị lý do, không hiển thị kết luận đạt form.

Không bắt buộc cho MVP kỹ thuật: model phân loại được train, LLM/RAG, 3D viewer, webcam trực tiếp, tài khoản người dùng. Nếu giáo viên yêu cầu các chức năng này trong nghiệm thu đồ án, bổ sung như điều kiện riêng trước bảo vệ; MVP không thay thế yêu cầu đồ án.

## Hiện trạng theo lớp

| Lớp | Đã có | Còn thiếu |
| --- | --- | --- |
| Pose | MediaPipe PoseEngine, model Heavy trên máy, dữ liệu và notebook mẫu | Nối thành pipeline ổn định; xử lý video hỏng và frame thiếu; đánh giá thực tế |
| Động học | Góc, lọc, đếm rep baseline; CLI phân tích landmarks | Chất lượng đầu vào, xử lý tín hiệu thiếu có kiểm soát; thử nghiệm độ chính xác và thống nhất cấu hình |
| Đánh giá | Cấu hình hai luật squat; công cụ so sánh mốc đáy với nhãn | Evaluator thật, kết quả theo rep và khung hình; không khẳng định chẩn đoán hay tính chính xác lâm sàng |
| Coaching | Có ý tưởng trong tài liệu | Gợi ý mẫu cho kết quả xác định được; LLM/RAG là mở rộng |
| Backend | FastAPI `/` và `/health` | Upload, công việc phân tích, lưu kết quả, báo lỗi, cung cấp video/bằng chứng và API contract |
| Frontend | Mới có thư mục trống | Upload, trạng thái, màn hình kết quả và xử lý lỗi |
| Kiểm chứng | 43 test hiện có; công cụ so sánh mốc đáy | Nhãn độc lập, dữ liệu người tập đa dạng, đo sai số góc và đánh giá end-to-end |

## Lộ trình và điều kiện hoàn thành

### Mốc 1 — Chốt hợp đồng đầu ra và pipeline core

- Thống nhất schema cho metadata, chất lượng, rep, phép đo, nhận xét, thời gian/frame; đặt trạng thái có kết quả, không đủ dữ liệu, thất bại và lý do.
- Nối video → PoseEngine → tín hiệu 2D có tỉ lệ pixel → lọc → rep; giữ timestamp và frame. Tách thuật toán khỏi lưu trữ và API, xử lý thiếu pose có giới hạn hoặc trả không đủ dữ liệu.
- Thống nhất nguồn cấu hình squat; file JSON đang khai báo ngưỡng nhận rep 105° trong khi code baseline dùng 150°. Không tự coi ngưỡng nào đã được xác nhận. Thời lượng tối thiểu 1 giây hiện bỏ sót rep thứ hai trong video mẫu.
- Dùng video mẫu sẵn có, test đơn vị và test tích hợp; mô hình Heavy phải có hướng dẫn cài riêng vì không nằm trong Git.
- Hoàn thành khi một lệnh chạy video mẫu tạo kết quả có schema, cảnh báo phù hợp và test lỗi video/thiếu pose, không tự bịa số liệu.

### Mốc 2 — Evaluator, bằng chứng và lời nhắc

- Thực thi hai luật squat trong JSON với góc gối và thân tại đáy; trả số đo, ngưỡng, frame/timestamp, nhãn và nguồn cấu hình. Các ngưỡng chỉ là giá trị thử nghiệm, không suy diễn chấn thương hay chẩn đoán.
- Không đưa kết luận khi góc quay không phù hợp hoặc dữ liệu không đủ; nếu chưa xác thực góc quay tự động thì yêu cầu người dùng chọn góc và nêu rõ hệ thống chưa xác minh.
- Ghép gợi ý mẫu ngắn với rule ID; không đưa gợi ý cho lỗi chưa phát hiện. Tạo ảnh bằng chứng hoặc hỗ trợ nhảy video tới timestamp; overlay là tùy chọn nếu đủ thời gian.
- Hoàn thành khi rep đạt, vi phạm, thiếu chất lượng và video không có rep đều được xử lý và test.

### Mốc 3 — API và giao diện tối thiểu

- Backend: `POST /api/v1/analyses` upload; `GET /api/v1/analyses/{id}` trả trạng thái và kết quả; endpoint phục vụ video/bằng chứng. Có giới hạn kích thước, kiểm tra file, lỗi rõ ràng, dọn file và cấu hình CORS phù hợp.
- Chạy tác vụ nền và lưu trạng thái/kết quả cục bộ; phải xử lý lỗi và nhận biết tác vụ gián đoạn sau restart. MVP local có thể dùng lưu trữ đơn giản; không giả định BackgroundTasks là hàng đợi bền vững.
- Frontend: upload, hướng dẫn quay, tiến độ, video/rep, số đo, cảnh báo, trạng thái không có rep và lỗi. Làm UI với contract/mock trong khi core đang nối; sau đó test với backend thật.
- Hoàn thành khi người dùng upload video mẫu và xem được kết quả thực qua trình duyệt; test case video lỗi, thiếu model và xử lý thất bại.

### Mốc 4 — Đánh giá, demo và chốt MVP

- Gán nhãn độc lập cho tập video nhỏ sẵn có trước; sau khi mạng khỏe, tải dataset và kiểm tra quyền/nhãn. Chia theo người khi điều chỉnh và đánh giá. Không dùng output hệ thống làm ground truth.
- Báo đếm rep, mốc đáy, các lỗi thường gặp; kiểm chứng góc nếu có đo tay. Báo giới hạn và kết quả thực, không hứa MAE hoặc accuracy chưa đo.
- Viết hướng dẫn cài/chạy từ máy mới, chạy test end-to-end, chuẩn bị hai video demo và nêu các trường hợp không hỗ trợ.
- Chốt MVP khi luồng đầu-cuối và trường hợp lỗi hoạt động; có báo cáo đánh giá thực tế và giới hạn. MVP kỹ thuật có thể demo sớm trên video mẫu, nhưng không được trình bày là đã kiểm chứng rộng.

## Cách triển khai và phụ thuộc

Thứ tự ưu tiên: Mốc 1 → Mốc 2; thiết kế API/UI có thể tiến hành song song với Mốc 1–2 khi contract ổn định → Mốc 3 → Mốc 4. Dữ liệu mẫu cho phép phát triển ngay; kết luận độ chính xác, huấn luyện ML và nghiệm thu rộng phụ thuộc dữ liệu có nhãn. Tải dataset đang hoãn đến khi người dùng báo mạng khỏe.

Sau mỗi mốc chạy test phù hợp và commit riêng. Không push khi chưa có yêu cầu. Huấn luyện dài chỉ chuẩn bị khi đủ dữ liệu; thông báo người dùng để tự chạy và gửi lại kết quả.

## Mở rộng sau MVP

- ML nhẹ dựa trên đặc trưng rep, so sánh với baseline và chia tập theo người.
- AI coach / RAG có nguồn trích dẫn và giới hạn đầu vào, không tự thêm lỗi hoặc số đo.
- Hỗ trợ thêm góc chính diện, deadlift/lunge, overlay hoàn chỉnh, 3D và webcam sau khi có tiêu chí đánh giá riêng.

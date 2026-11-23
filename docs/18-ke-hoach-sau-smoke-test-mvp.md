# Kế hoạch phát triển sau smoke test MVP

Cập nhật 23/11/2026. Tài liệu này là kế hoạch ưu tiên hiện tại, bổ sung cho [lộ trình sau backend](16-lo-trinh-sau-backend.md) và [kết quả smoke test](17-kiem-thu-mvp-va-training.md).

## 1. Điểm xuất phát và mục tiêu

Đã có pipeline video squat → MediaPipe Pose Heavy có sẵn → phân tích động học và rep → evaluator hai luật → API → giao diện. Một video mẫu đã đi hết luồng trên trình duyệt, có thể tua về đáy rep và khôi phục kết quả sau reload; 86 test backend pass và frontend build thành công. Đây là smoke test, chưa chứng minh độ chính xác, khả năng hoạt động với nhiều người dùng hay sẵn sàng triển khai công khai.

Vấn đề ưu tiên: video `test_squat.mp4` được mô tả có 2 rep nhưng pipeline phát hiện 1. Nhãn 2 rep cần được rà độc lập trước khi dùng làm chuẩn. Nhãn AI hiện tại là nháp phát triển, không phải ground truth; các ngưỡng evaluator và coaching là thử nghiệm.

**MVP v1 hoàn chỉnh**: chạy local từ video squat bên hông đến kết quả và bằng chứng, có cảnh báo dữ liệu không đủ, xử lý được các tình huống lỗi chính, có báo cáo kiểm chứng trên dữ liệu độc lập và hướng dẫn demo. Khả năng train một model riêng phụ thuộc yêu cầu học phần và dữ liệu nhãn, không phải điều kiện kỹ thuật để chạy pipeline hiện nay.

## 2. Thứ tự thực hiện

### Mốc 1 — Rà lỗi bỏ sót rep và chất lượng đầu vào (ưu tiên cao nhất)

1. Xem lại video mẫu, xác nhận bằng người quan sát số rep và frame bắt đầu/đáy/kết thúc; ghi quy ước frame và trường hợp không rõ. Lưu video và nhãn ngoài Git.
2. Tái hiện trên tín hiệu góc đã lưu: xem smoothing, độ sâu, prominence, điều kiện lockout, thời lượng và chất lượng pose. Xác định điều kiện nào làm rep bị bỏ trước khi đổi code.
3. Thu thập thêm các video development có rep nhanh, nông, tạm dừng ở đáy và bị cắt; so sánh trước/sau trên cùng dữ liệu. Điều chỉnh trên development, không dùng tập test độc lập để chọn ngưỡng.
4. Sửa có kiểm soát, thêm test hồi quy cho nguyên nhân cụ thể và các tình huống dễ đếm nhầm, đồng thời giữ cảnh báo khi không đủ pose hoặc chuỗi bị đứt.

**Hoàn thành khi:** có nguyên nhân được chứng minh hoặc giới hạn được xác định rõ; kết quả trước/sau được ghi lại; bộ test hồi quy pass. Không lấy riêng một video làm bằng chứng cải thiện tổng quát.

### Mốc 2 — Ổn định trải nghiệm và vận hành local

1. Kiểm tra frontend với video hợp lệ, file rỗng/sai định dạng/vượt giới hạn, góc không hỗ trợ, không có rep, dữ liệu thiếu, backend offline, job thất bại hoặc gián đoạn, tải lại trang và tua video. Thử cả màn hình nhỏ và codec phổ biến.
2. Cải thiện thông báo nếu phát hiện sai lệch; xử lý hoặc ghi nhận cảnh báo CSS và log `ConnectionResetError` khi stream video trên Windows. Không báo phần trăm xử lý khi backend chưa có số đo tiến độ.
3. Thiết kế quản lý video/kết quả local: liệt kê vị trí lưu, cách người dùng xóa dữ liệu; nếu thêm chức năng xóa trong ứng dụng, định nghĩa hành vi an toàn đối với job đang xử lý và bổ sung kiểm thử. Không tự động xóa dữ liệu hiện có.
4. Hoàn thiện hướng dẫn cài mới, khởi động hai service, yêu cầu model, cấu hình API/CORS và xử lý lỗi. API hiện chỉ dành cho một worker local; chưa có đăng nhập hoặc hàng đợi phân tán.

**Hoàn thành khi:** các luồng chính và lỗi được kiểm tra có kết quả ghi lại; người dùng biết dữ liệu nằm ở đâu và chạy được theo hướng dẫn trên môi trường phù hợp.

### Mốc 3 — Chuẩn bị dữ liệu và nhãn đánh giá độc lập

1. Kiểm kê dataset đang có: nguồn, giấy phép/quyền sử dụng, số video, người tập, góc quay, bài tập, nhãn và mức độ phù hợp. CFRep hoặc nguồn nào chưa xác minh danh tính/giấy phép vẫn được đánh dấu chưa dùng cho đánh giá hoặc công bố.
2. Thiết lập quy trình gán nhãn độc lập cho số rep và thời điểm đáy; ghi người gán, phương pháp, nguồn video, trạng thái không chắc chắn. Nếu đánh giá lỗi kỹ thuật cần thêm định nghĩa cụ thể và nhãn lỗi ở cấp rep; nhãn tốt/xấu cấp video không tự suy ra được nhãn lỗi.
3. Chia theo người thành train/development, validation và test độc lập; giữ test chưa dùng để điều chỉnh thuật toán hoặc lựa chọn model. Ghi số người, video và rep thực tế theo từng tập; ưu tiên đa dạng tốc độ, ánh sáng, trang phục, che khuất và bodyweight/barbell nếu có.
4. Tạo bảng dự đoán và nhãn đối chiếu có phiên bản, không đưa video nhạy cảm, model lớn hay dữ liệu cá nhân vào Git. Nếu nhiều nguồn trùng người/video, tránh rò rỉ giữa các tập.

**Hoàn thành khi:** có manifest và nhãn được rà độc lập, có chia tập tái lập được và thống kê phân bố thực tế. Quy mô tập phụ thuộc dữ liệu và nguồn lực; không đặt số lượng tối thiểu như thể bảo đảm chất lượng.

### Mốc 4 — Đánh giá định lượng core và hoàn thiện demo

1. Đo coverage/số video không phân tích được; sai số đếm rep; TP, FP, FN và precision/recall cho rep theo quy tắc ghép đã công bố; sai lệch thời gian đáy. Công bố số mẫu và các trường hợp bất định, không chỉ báo accuracy.
2. Đánh giá từng luật chỉ khi có nhãn lỗi tương ứng và định nghĩa phù hợp. MAE góc chỉ tính khi có góc tham chiếu hoặc phép đo thủ công đáng tin cậy với cùng quy ước. Không dùng detection rate 100% như bằng chứng góc hoặc form chính xác.
3. Thử ít nhất một video chưa dùng điều chỉnh qua trình duyệt, ghi kết quả thực và lỗi. Chuẩn bị video demo, ảnh bằng chứng, sơ đồ kiến trúc, cách tái lập, hạn chế và nội dung báo cáo/bảo vệ.

**Hoàn thành khi:** có báo cáo số liệu trên test độc lập, phạm vi và giới hạn rõ ràng, demo chạy được và các kết quả có thể tái lập theo môi trường đã mô tả.

### Mốc 5 — Model ML riêng nếu đồ án yêu cầu hoặc dữ liệu đủ

1. Xác định câu hỏi cụ thể: phân loại lỗi nào, ở cấp rep hay cấp video, nhãn nào có thể xác nhận và metric cần so sánh. Tránh hứa model nhận biết mọi lỗi kỹ thuật từ một góc quay.
2. Trích đặc trưng trên các rep đủ chất lượng; thử baseline ML nhẹ, ví dụ logistic regression hoặc random forest nếu phù hợp với dữ liệu. Chọn model và tham số chỉ trên train/validation; so sánh với rule baseline trên cùng tập test độc lập.
3. Báo số mẫu, phân bố lớp, coverage, precision/recall/F1 theo lớp, ma trận nhầm lẫn và sai lệch do dữ liệu ít. Chỉ tích hợp model khi chứng minh được giá trị và có cách trả `insufficient_data` khi đầu vào không tin cậy.
4. Fine-tune pose model nặng, LLM/RAG, camera trực tiếp và bài tập khác là các hướng mở rộng riêng; không cần chờ chúng để vận hành MVP squat.

**Điều kiện chạy train dài:** trước khi chạy, chuẩn bị và gửi người dùng lệnh, dữ liệu đầu vào, yêu cầu phần cứng, thời gian ước tính dựa trên thử nghiệm ngắn, vị trí output và cách gửi lại kết quả. Người dùng tự chạy theo thỏa thuận; chưa có ước tính thời gian đáng tin cậy.

## 3. Những thứ cần chuẩn bị

| Cần chuẩn bị | Người/phụ thuộc | Mục đích và thời điểm |
| --- | --- | --- |
| Đề cương, rubric, yêu cầu giảng viên và hạn nộp | Người dùng cung cấp khi có | Xác định training, số bài tập, ngôn ngữ, báo cáo và deployment có bắt buộc không; cần trước khi chốt phạm vi. |
| Video squat mới có sự đồng ý sử dụng | Người dùng hỗ trợ quay/thu thập | Ưu tiên quay bên hông, trọn người, đủ sáng; thêm tình huống tốc độ và che khuất khác nhau. Dành một phần chưa dùng cho test. |
| Người rà nhãn độc lập và quy ước nhãn | Người dùng/nhóm dự án; có thể nhờ người hiểu kỹ thuật tập | Xác nhận số rep, frame đáy và lỗi quan sát được; không dựa hoàn toàn vào output của hệ thống. |
| Quyền dùng dataset và danh sách nguồn | Nhóm dự án kiểm tra theo từng nguồn | Bảo đảm phạm vi dùng, chia sẻ, trích dẫn và công bố phù hợp; chưa giả định nguồn nào đã được cấp phép. |
| Thông số máy, CPU/GPU, RAM, dung lượng trống | Người dùng cung cấp trước lượt train hoặc benchmark dài | Ước lượng lựa chọn model, thời gian và dung lượng; MVP hiện dùng model pose có sẵn. |
| Model Heavy và môi trường Python/Node | Đã có trên máy hiện tại; cần hướng dẫn tái lập | Model không nằm trong Git; cần có khi chạy trên máy khác. |

Không cần chuẩn bị GPU hoặc train ngay để xử lý mốc 1–4. Nếu chưa có video mới hay người gán nhãn độc lập, vẫn có thể tái hiện lỗi trên dữ liệu development và hoàn thiện trải nghiệm, nhưng chưa thể hoàn tất đánh giá độc lập.

## 4. Nguyên tắc triển khai

- Thứ tự mặc định: 1 → 2 → 3 → 4; chuẩn bị dữ liệu có thể làm đồng thời. Mốc 5 phụ thuộc yêu cầu và điều kiện nhãn.
- Mỗi thay đổi có kiểm thử phù hợp và commit riêng theo mốc; push khi người dùng yêu cầu. Không tự thay đổi hoặc xóa video và nhãn gốc.
- Thời gian chưa ước lượng chắc chắn vì phụ thuộc số video, người rà nhãn, tài nguyên máy và yêu cầu học phần; cập nhật sau khi rà lỗi và kiểm kê dữ liệu.

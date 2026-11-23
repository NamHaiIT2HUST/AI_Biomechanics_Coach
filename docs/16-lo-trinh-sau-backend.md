# Lộ trình sau backend API — MVP v1 và hoàn thiện đồ án

Cập nhật 23/11/2026 theo mã nguồn. Mục tiêu: một người dùng có thể tải video squat, theo dõi xử lý và xem kết quả có bằng chứng cùng giới hạn độ tin cậy. Bản MVP là sản phẩm nghiên cứu thử nghiệm, chưa khẳng định độ chính xác y khoa.

## 1. Những gì đã có

- MediaPipe Pose Heavy, tính góc 2D đã tính tỉ lệ ảnh, lọc, phân đoạn rep và evaluator 2 luật squat; kết nối qua pipeline offline.
- API local FastAPI: `/health`, danh sách bài tập, upload, trạng thái, JSON kết quả và stream video. SQLite lưu trạng thái, một worker xử lý tuần tự; restart đánh dấu job chưa xong là `interrupted`. Giới hạn upload mặc định 100 MiB.
- Dữ liệu squat Multi-View/UI-PRMD đã chuẩn bị; CFRep chờ xác minh giấy phép/định danh. Có snapshot nhãn AI sơ bộ cho phát triển nhưng chưa phải nhãn kiểm chứng độc lập.
- Test suite gần nhất 86 pass; đã thử Uvicorn và MediaPipe với video mẫu. Video mẫu có rep thứ hai có thể bị bỏ sót; đây là vấn đề còn mở.
- Frontend chưa có ứng dụng. Overlay hoàn chỉnh, chat/RAG và model ML chưa được triển khai.

## 2. Phạm vi MVP v1

Video squat quay bên hông → upload → theo dõi trạng thái → xem video, rep phát hiện, số đo, kết quả hai luật và cảnh báo. Người dùng nhấn vào rep để tua video tới thời gian đáy. Cần có thông báo rõ khi không đủ dữ liệu, không phát hiện rep, lỗi xử lý hoặc video chỉ phân tích được một phần. Có thể đưa gợi ý cố định, ngắn, gắn với rule thực sự được kích hoạt.

MVP kỹ thuật không yêu cầu 3D, live webcam, đăng nhập, train model riêng hay RAG; nếu giảng viên yêu cầu các mục đó để nghiệm thu đồ án thì giữ làm mốc bắt buộc trước bảo vệ.

## 3. Mốc A — Kiểm tra backend và làm ổn định hợp đồng

1. Người dùng thử upload qua Swagger với video mẫu và ít nhất một video tự quay mới; ghi trạng thái, thời gian, lỗi và các trường hợp chưa dễ hiểu. Dùng dữ liệu thực để xác định lỗi, không điều chỉnh ngưỡng chỉ theo một video.
2. Hoàn thiện contract phục vụ frontend: version schema kết quả, ví dụ `completed`, `partial`, `no_reps_detected`, `insufficient_data`, `failed`; quy định frame 0-based, `bottom_time_s` theo FPS danh nghĩa, camera view do người dùng chọn.
3. Rà giới hạn vận hành local: một process/worker, kích thước/duration và video sai, lỗi thiếu model, restart giữa chừng, thư mục lưu và quy trình xóa video. Bổ sung chức năng xóa có kiểm thử nếu cần cho sản phẩm; không tự xóa dữ liệu của người dùng.
4. Kiểm thử API: file rỗng/sai định dạng/vượt mức, góc quay không hỗ trợ, job không tồn tại, job lỗi, stream/tua video, reload và restart. Cân nhắc giới hạn hàng đợi và kích thước/duration trước khi dùng ngoài demo local.

**Xong khi:** luồng API có thể tái lập trên máy mới có model, mô tả lỗi hữu ích và test các tình huống trên; API vẫn hoạt động với một worker.

## 4. Mốc B — Frontend kết nối API

1. Khởi tạo Next.js/TypeScript trong `frontend`, cấu hình địa chỉ backend và lệnh chạy; không hard-code đường dẫn máy người dùng.
2. Màn hình upload: bài squat, góc quay side/front/unknown, giới hạn file, hướng dẫn camera và trạng thái upload; hiển thị thông báo lỗi từ API.
3. Theo dõi `queued → processing → completed/failed`: polling có khoảng dừng hợp lý, dừng khi kết thúc hoặc rời trang, tránh gửi upload hai lần. Không hứa phần trăm tiến độ nếu API chưa cung cấp.
4. Màn hình kết quả: video gốc, danh sách rep, góc gối/thân, trạng thái rule và cảnh báo coverage/visibility. Nhấn rep tua tới `bottom_time_s`; phân biệt `finding`, `within_threshold`, `insufficient_data`. Không hiển thị `within_threshold` thành kết luận động tác an toàn hay hoàn toàn chuẩn.
5. Trường hợp biên: chưa có rep, video partial, camera không hỗ trợ, API offline, trạng thái failed/interrupted, dữ liệu thiếu hoặc model chưa có. Bố cục dùng được trên điện thoại lẫn desktop.
6. Trước khi nối thật có thể dùng fixture/mock cục bộ dựa trên API contract; nghiệm thu phải thử backend và video thật, không chỉ mock.

**Xong khi:** trên trình duyệt tải video, theo dõi, xem kết quả và tua đúng rep; các trường hợp lỗi không hiển thị sai ý nghĩa. Có kiểm tra UI và ít nhất một luồng end-to-end thật.

## 5. Mốc C — Bằng chứng và hướng dẫn sửa form

1. Gắn thời gian/frame bằng chứng của từng luật với video gốc; kiểm tra quy đổi frame/FPS và tua theo codec. Nếu cần ảnh, trích frame bằng chứng có metadata và đường dẫn riêng; overlay màu là phần mở rộng, không giả định đã có.
2. Thêm bảng coaching cố định theo rule ID, chỉ hiển thị khi `finding`; thiếu dữ liệu hoặc trong ngưỡng không tạo thêm lỗi/cue suy diễn. Nội dung là hướng dẫn tập luyện tổng quát, không suy đoán bệnh, nguyên nhân hay nguy cơ cá nhân từ góc đơn lẻ.
3. Kiểm tra góc quay và độ tin cậy: view không phải side phải cho trạng thái chưa đủ; cảnh báo video partial và landmark thấp; xác thực tự động góc quay và người chính là việc tiếp theo, không giả định đã có.

**Xong khi:** mỗi nhận xét có số đo và vị trí xem lại, gợi ý khớp đúng rule, trường hợp không đủ dữ liệu không được kết luận form.

## 6. Mốc D — Cải thiện chất lượng core, song song frontend

1. Đo baseline trên video train có nhãn sơ bộ; tách rõ kết quả thăm dò AI và đánh giá độc lập. Rà trường hợp nhiều người và landmark mất, phân biệt mất pose thật với visibility thấp.
2. Sửa lỗi đếm rep nhanh và rep nông bằng thí nghiệm có kiểm soát: so sánh ngưỡng duration, prominence và cách tìm điểm bắt đầu/kết thúc trên train; không chỉnh dựa trên test. Lưu cấu hình/phiên bản đi kèm kết quả.
3. Cải thiện quality gate: tránh nối rep xuyên gap, xem xét nội suy chỉ khoảng ngắn và kiểm tra sai số, gắn mức độ tin cậy theo rep; xử lý khớp thiếu, rung, ảnh bị che và thời gian video không đều. Nếu chưa đủ tin cậy, trả partial/insufficient.
4. Đảm bảo test hồi quy có các video/tín hiệu cho rep nông, nhanh, bị cắt, pose chập chờn, camera sai và nhiều người. Test tự động cần tránh lưu video nặng/nhạy cảm trong Git.

**Xong khi:** lỗi đã biết được tái hiện và đo trước/sau, các trường hợp bất định không bị báo sai là đạt; không hứa sửa hết lỗi trên mọi góc quay.

## 7. Mốc E — Kiểm chứng, báo cáo và demo

1. Chuẩn bị nhãn độc lập để đánh giá số rep, frame đáy và sai số góc; ghi giao thức đo, người gán, trường hợp không quan sát được. Snapshot AI hiện tại chỉ là phát triển, đã lộ baseline; không báo là ground truth độc lập.
2. Chia theo người và giữ test riêng; lưu số video/rep thực tế, coverage, TP/FP/FN, precision/recall, sai số đếm và thời gian đáy; kèm sai số và trường hợp không phân tích được. MAE góc cần đo tay hoặc hệ tham chiếu phù hợp và quy ước góc tương ứng.
3. Chạy full end-to-end từ trình duyệt trên video mẫu, video chưa thấy và các trường hợp lỗi; chuẩn bị video demo, hướng dẫn cài mới, nhật ký hạn chế và nội dung báo cáo.
4. Mốc giao MVP: cả luồng thực chạy; kết quả có bằng chứng, cảnh báo đúng; có báo cáo coverage và kết quả thực nghiệm, không tuyên bố mục tiêu MAE/accuracy nếu chưa đo.

## 8. ML và tính năng nâng cao

- Khi nhãn đủ và điều kiện giấy phép được xác minh, trích đặc trưng từ tập train rồi thử baseline ML nhẹ; so sánh với luật, chia theo người và đánh giá trên test chưa dùng để điều chỉnh. Phân biệt nhãn video tốt/xấu với nhãn lỗi theo rep. Trước bất kỳ lượt train dài, báo người dùng lệnh, dữ liệu, ước lượng thời gian, cách lưu và cách gửi kết quả; không tự chạy khi người dùng muốn tự thực hiện.
- Coach AI/RAG cần nguồn tài liệu được phép sử dụng, trích dẫn và kiểm thử không tự sinh số đo/lỗi. Chưa cần để demo MVP kỹ thuật.
- 3D viewer, live webcam, deadlift/lunge, auth, deployment và hàng đợi bền vững là các mốc riêng sau khi offline ổn định hoặc theo yêu cầu giảng viên.

## 9. Thứ tự thực hiện và quản lý

A → B, trong lúc đó làm D trên nhánh công việc riêng nếu phù hợp; C tích hợp cùng B khi UI có video; E sau khi các luồng ổn định. Không đợi dataset Fit3D hay train ML mới dựng UI. Ước lượng tương đối cho một người: A 1–3 ngày, B 4–7 ngày, C 1–3 ngày, D 3–7 ngày, E 3–7 ngày; phụ thuộc thời gian thực tế, mức độ che khuất và phản hồi, không cộng máy móc vì có việc song song.

Commit theo mốc có thể chạy/test; không đưa video, nhãn người dùng, model hoặc database lên Git. Push theo yêu cầu người dùng. Cập nhật tài liệu nếu phạm vi thay đổi.

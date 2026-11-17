# Báo cáo hiện trạng dự án và dữ liệu

Ngày kiểm tra: 17/11/2026. Đánh giá dưới đây dựa trên mã và kiểm thử hiện có; các chỉ tiêu trong lộ trình cũ là mục tiêu, không phải kết quả đã đạt.

## Các mốc đã có

1. **Thiết kế và môi trường:** tài liệu kiến trúc, dữ liệu và lộ trình; FastAPI có `/` và `/health`; môi trường Python và pytest chạy được.
2. **Pose và thử nghiệm:** `PoseEngine` đọc video và trích xuất landmark MediaPipe; model Heavy và ba video mẫu hiện có tại máy. Hai file landmark và ba notebook thử nghiệm đã có. Tỷ lệ bắt khớp cao trên một video không chứng minh độ chính xác trên dữ liệu đa dạng.
3. **Hình học và lọc:** hàm tính góc 2D/3D, góc thân, các chỉ số khác và lọc Savitzky–Golay. Góc 2D từ landmark chuẩn hóa cần đổi về tỉ lệ pixel theo chiều rộng và cao.
4. **Tách rep baseline:** `phases.py` nhận chuyển động, đánh dấu pha và xuất mốc rep; ngưỡng nhận chuyển động hiện mặc định 150° để có thể nhận rep nông, ngưỡng đánh giá độ sâu 100° chưa được dùng làm bộ phân loại form. Cả ngưỡng và độ chính xác chưa được kiểm chứng độc lập.
5. **Chất lượng và đánh giá baseline:** CLI `landmark_analysis` cảnh báo visibility thấp theo rep; `rep_validation` so sánh mốc đáy với nhãn độc lập. Chưa có quality gate hoàn chỉnh hoặc báo cáo MAE thực nghiệm. `test_squat` nhận 2 rep với ngưỡng 0,9 giây, mặc định 1 giây chỉ nhận 1 rep; `sample_squat` chưa nhận được rep.
6. **Kiểm thử:** 43 test pass ngày kiểm tra. Test phần lớn dùng dữ liệu tổng hợp, không chứng minh độ chính xác trong thực tế.

## Các mốc còn lại

1. Hoàn tất tải, kiểm tra checksum và kiểm kê từng dataset; đọc giấy phép, xác định danh tính người tập, góc quay và định nghĩa nhãn. Không commit dữ liệu nặng vào Git.
2. Tạo bộ nhãn tham chiếu độc lập: số rep, mốc bắt đầu/đáy/kết thúc; chia train/validation/test theo người tập. Đánh giá cả rep nông, nhanh, video thiếu pose và góc quay không phù hợp.
3. Điều chỉnh và đánh giá bộ đếm rep trên tập phát triển, báo precision/recall, sai lệch mốc và các lỗi; sau đó kiểm thử trên người chưa thấy. Thêm xử lý thiếu dữ liệu có giới hạn và quality gate.
4. Thực hiện kiểm chứng góc với nhãn đo tay hoặc hệ tham chiếu phù hợp, báo MAE và điều kiện đo. Chưa có bằng chứng đạt MAE < 5°.
5. Viết evaluator đọc cấu hình squat, chỉ trả các phép đo phù hợp góc quay và độ tin cậy; nối pose → tín hiệu → rep → đánh giá và bằng chứng. Video overlay hoàn chỉnh, API phân tích và frontend vẫn chưa có.
6. Khi đủ dữ liệu và nhãn, huấn luyện ML và đánh giá theo người tập, so với baseline luật. Chưa train lúc này; cần thông báo cho người dùng trước khi có tác vụ train dài.
7. Triển khai coaching dựa trên kết quả đã xác định, RAG nếu cần; sau đó xem xét 3D viewer và webcam. Hoàn thiện đánh giá cuối kỳ, báo cáo và demo.

## Nguồn dữ liệu ngoài

- **Multi-View Fitness Exercises v3:** https://data.mendeley.com/datasets/kgbb3yn47p/3 — 26 người, bảy bài gồm bodyweight squat; video MP4 và nhãn good/bad theo video. CC BY 4.0; trích dẫn theo trang nguồn. Ba archive là ba cách sắp xếp của cùng video, chỉ cần một bản. Dự kiến `data/external/multiview_fitness/`.
- **CFRep:** https://github.com/lc-leonardo/CFRep — video và nhãn hợp lệ/không hợp lệ theo rep; chưa xác minh giấy phép từ repository. Không suy diễn nhãn hợp lệ là nhãn y khoa. Dự kiến `data/external/cfrep/`.
- **UI-PRMD:** https://zenodo.org/records/23104965 và https://www.idahofallshighered.org/vakanski/ui-prmd.html — dữ liệu Vicon/Kinect; PDDL 1.0 theo trang tác giả. Dự kiến `data/external/ui_prmd/`; các file Zenodo được đối chiếu checksum MD5 do nguồn công bố.
- **Fit3D:** https://fit3d.imar.ro/fit3d — cần đăng ký và được cấp quyền; giấy phép nghiên cứu phi thương mại https://fit3d.imar.ro/legal, có hạn chế chia sẻ. Không tự tạo tài khoản hoặc chấp thuận điều khoản thay người dùng. Dự kiến `data/external/fit3d/` sau khi được cấp quyền.

Chỉ tính dataset đã sẵn sàng khi file tải hoàn chỉnh và checksum/khả năng đọc được kiểm tra; xem trạng thái từng lần tải trong đầu ra quá trình tải. Không dùng file `.zip` tải dở.

# Khảo sát kỹ thuật: đếm rep và chất lượng phân tích squat

Ngày 23/11/2026. Phạm vi là squat offline một người với video RGB một camera, không phải đánh giá y khoa. Các nguồn dưới đây không xác nhận độ chính xác của chính dự án này.

## Nguồn và kết luận áp dụng

1. [MediaPipe Pose Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker) mô tả 33 landmark và tọa độ theo ảnh/world; visibility và tọa độ model không đảm bảo khớp được đo đúng. Dự án dùng vị trí 2D theo ảnh, nhân theo kích thước ảnh trước khi tính góc. Điểm thiếu, visibility thấp hoặc điểm nằm ngoài ảnh cần được báo; camera một phía không tự xác minh được đúng người hoặc góc quay.
2. [SciPy `find_peaks`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html) mô tả prominence và khoảng cách giữa đỉnh; chúng là điều kiện xử lý tín hiệu chứ không phải bằng chứng một đỉnh là rep thật. Bộ đếm vẫn yêu cầu chu kỳ đứng–hạ–đứng, ngưỡng chuyển động, prominence và thời lượng tối thiểu; không điền dữ liệu qua gap pose.
3. [Nghiên cứu ảnh hưởng góc camera tới OpenPose](https://pubmed.ncbi.nlm.nih.gov/39943438/) ghi nhận sai lệch phụ thuộc góc quay so với motion capture; kết quả đó không phải sai số đo được cho MediaPipe hoặc video của dự án. Hệ thống yêu cầu người dùng khai góc và không đưa đánh giá hai luật từ video khai góc chính diện/không rõ; vẫn chưa tự xác thực góc.
4. [So sánh squat với vị trí tải khác nhau](https://pubmed.ncbi.nlm.nih.gov/33161870/) nghiên cứu các kiểu squat và cơ học thân/chi dưới. Không suy ra một ngưỡng ngả thân duy nhất là sai cho mọi người hoặc mọi kiểu tập. UI dùng ngôn ngữ “vượt ngưỡng tham khảo”, kèm vị trí video và cảnh báo ngưỡng thử nghiệm thay cho kết luận an toàn hay kỹ thuật đúng/sai.
5. [Nghiên cứu tính hợp lệ 2D pose trong single-leg squat](https://pubmed.ncbi.nlm.nih.gov/36198251/) so sánh một mô hình 2D với motion capture và cho thấy khác biệt thay đổi theo khớp/mặt phẳng. Không thể chuyển các kết quả single-leg hoặc mô hình khác thành sai số cho bilateral squat của ứng dụng. Cần đo góc tham chiếu độc lập trước khi báo MAE.

## Cải tiến trong dự án

- Giữ mặc định `standard`: thời lượng rep tối thiểu 1,0 giây. Thêm tùy chọn `fast` 0,8 giây để người dùng thử video có rep nhanh. Cả hai đều thử nghiệm, ngưỡng này không được rút ra như một chuẩn sinh cơ học. Fast có thể tăng đếm nhầm; luôn cần đối chiếu video và đánh giá FP/FN độc lập.
- `count_mode` được gửi cùng upload; `config.count_mode`, các tham số thực tế và SHA-256 của cấu hình xuất hiện trong kết quả. Với tác vụ bị gián đoạn khi server khởi động lại, cần upload lại video.
- Landmarks của các khớp cần dùng nằm ngoài khung ảnh sẽ làm các rep bị ảnh hưởng chuyển `needs_review` và các luật thành `insufficient_data`. Frame vẫn có thể tham gia đếm rep; tỷ lệ pose và số rep không được coi là xác nhận chất lượng. Cảnh báo theo video ghi tổng frame ngoài ảnh.
- Điều chỉnh cách xác định vùng frame ảnh hưởng tới bộ lọc Savitzky–Golay ở biên chuỗi: khi nội suy biên, một output có thể phụ thuộc toàn bộ cửa sổ đầu/cuối thay vì chỉ bán kính 5 frame. Low visibility hoặc điểm ngoài khung trong vùng ảnh hưởng làm rep cần xem lại. Ngưỡng visibility vẫn là ngưỡng kỹ thuật thử nghiệm; visibility cao không xác nhận độ chính xác.
- Tên hai rule và cue nhấn mạnh đây là so sánh với ngưỡng tham khảo, không suy luận chấn thương hoặc kiểu squat lý tưởng. Kết quả cũ vẫn giữ số đo và ngưỡng lịch sử.

## Bằng chứng và giới hạn

So sánh trước đó trên cache 6 video train chỉ có 2 video complete và nhãn AI chưa xác nhận: các ngưỡng 0,7–1,0 giây cho cùng số TP/FP/FN so với nhãn nháp; không đủ để kết luận chế độ nhanh tốt hơn. Video `test_squat` có một ứng viên dài khoảng 0,93 giây, được phát hiện ở ngưỡng 0,8 giây; vẫn cần người xác nhận rep và thử trên nhiều người, tốc độ, loại squat, ánh sáng và che khuất. [Chi tiết thí nghiệm](20-khao-sat-thoi-luong-rep.md).

Thử trên trình duyệt với backend và MediaPipe thật: cùng video mẫu, standard phát hiện 1 rep (đáy frame 90), fast phát hiện 2 rep (frame 90 và 133); nút rep hai tua đến 4,43 giây. Có 17 frame low visibility toàn video; cả hai rep tìm được không có frame low visibility trong vùng ảnh hưởng bộ lọc. Chuyển động ngắn ở frame 11 vẫn bị loại và được gợi ý xem lại. Đây là kết quả của một video, chưa xác nhận 2 ứng viên là rep đúng hay đo được sai số tổng quát.

Các unit/integration test xác minh logic, không đo độ đúng trên quần thể. Không có nhãn người độc lập, nhãn lỗi theo rep, benchmark góc hay model phân loại tự train trong kết quả này. Không sử dụng các ngưỡng để đưa khuyến cáo y khoa.

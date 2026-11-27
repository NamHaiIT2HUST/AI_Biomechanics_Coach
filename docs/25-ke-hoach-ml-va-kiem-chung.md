# Kế hoạch phát triển, huấn luyện ML và kiểm chứng

Cập nhật 27/11/2026. Mục tiêu là một sản phẩm squat offline dùng được và một đồ án có phương pháp, baseline, thực nghiệm tái lập, giới hạn và kết quả được báo trung thực. Cần đối chiếu đề cương/rubric với giảng viên trước khi chốt điều kiện nghiệm thu.

## 1. Hiện trạng và vấn đề

- Pipeline video → MediaPipe Pose Heavy pretrained → góc/lọc/FSM → hai rule thử nghiệm → API → UI; có rep nhanh thử nghiệm 0,8 giây, kết quả JSON và thời gian pha. Test backend gần nhất 113 pass, frontend build và video mẫu đã chạy qua trình duyệt. Đây là bằng chứng hoạt động kỹ thuật, không phải độ chính xác độc lập.
- Video mẫu được mô tả có 2 rep: chế độ 1,0 giây phát hiện 1, chế độ 0,8 giây phát hiện 2. Chưa có kiểm chứng độc lập để khẳng định 0,8 giây tốt hơn trên dữ liệu đa dạng. Detector có thể bỏ sót các rep không trở về ngưỡng đứng hoặc cắt qua gap.
- Có Multi-View squat 150 video/25 subject, gồm 50 side, 50 front, 50 diagonal; good/bad là nhãn nguồn cấp video, không phải nhãn lỗi theo rep. Tập dự kiến side có 34 video train/17 subject, 8 validation/4 subject, 8 test/4 subject. Xác nhận bằng manifest trước chạy; các góc khác cùng người/sự kiện không được rò qua split. Đây là quy mô nhỏ, kết quả sẽ bất định.
- UI-PRMD có 800 file dữ liệu cảm biến cho 10 subject nhưng nhiều bản sensor/representation của cùng lần thực hiện, không phải 800 rep/video độc lập và khác miền video gym. CFRep đã tải nhưng quyền sử dụng và định danh chưa xác minh; không dùng để train/công bố cho đến khi làm rõ.
- 145 khoảng nhãn AI là nháp trên 10 video development, không phải ground truth người độc lập. Các nhãn đã lộ baseline; không dùng làm test mù hay đổi thành nhãn người.

## 2. Định hướng ML: ba bài toán khác nhau

| Bài toán | Đầu ra và nhãn cần | Lựa chọn ban đầu | Giới hạn |
| --- | --- | --- | --- |
| A. Phân loại video theo nhãn nguồn | Một nhãn good/bad **cho cả video**; Multi-View có nhãn nguồn | Đặc trưng thống kê từ pose + logistic regression/Random Forest, so sánh baseline đơn giản | Không dự đoán lỗi riêng của từng rep, không chứng minh form an toàn; số subject ít, có nguy cơ học môi trường hoặc cách quay |
| B. Đếm rep/điểm đáy | Các mốc start/bottom/end hoặc chuỗi pha được người rà độc lập | Giữ FSM làm baseline, so sánh model chuỗi nhẹ (1D-CNN/TCN) sau khi có đủ nhãn | Nhãn good/bad cấp video không dạy được mốc rep; cần đánh giá FP/FN và gap |
| C. Nhận xét lỗi cụ thể | Nhãn theo rep cho từng lỗi, định nghĩa và người đánh giá | Model ML theo đặc trưng rep, chỉ thử sau khi nhãn đủ | Không suy lỗi từ good/bad của video; chưa có nhãn xác nhận nên chưa train/đánh giá chính thức |

**Ưu tiên:** làm A để xây một baseline ML có thể giải thích và báo cáo, đồng thời làm B với nhãn độc lập để cải thiện core. Không thay bộ đếm bằng A, không gắn nhãn tốt/xấu của A cho từng rep. Giữ rule/quality gate và khả năng từ chối kết luận khi thông tin không đủ. Nếu rubric bắt buộc đúng lỗi theo rep, đổi thứ tự ưu tiên sang chuẩn bị nhãn C.

## 3. Mốc A — Khóa phạm vi và tái lập baseline

1. Thu thập đề cương/rubric, deadline và yêu cầu model, số động tác, demo, báo cáo; ghi quyết định phạm vi.
2. Ghi phiên bản code, cấu hình, model pose, manifest, kiểm tra hash/số file và quyền sử dụng. Lưu snapshot config theo run; không đưa video/model/nhãn cá nhân vào Git.
3. Khóa test theo subject trước mọi điều chỉnh; các clip khác góc của cùng người giữ cùng split. Kiểm tra trùng clip/subject theo thông tin sẵn có; không thể bảo đảm khác nguồn không trùng người nếu không có định danh.
4. Chạy baseline FSM 1,0 và 0,8 giây trên development có nhãn người; ghi coverage, đếm, đáy và tình huống không phân tích được. Không dùng test để chọn ngưỡng. Chưa có nhãn người thì chỉ báo thăm dò và không gọi đó là accuracy.

**Đầu ra:** manifest/snapshot có phiên bản, báo cáo baseline và danh sách lỗi kèm ví dụ. **Xong khi:** người khác có thể chạy lại trên cùng tập và biết chính xác mẫu nào thiếu/không dùng được.

## 4. Mốc B — Nhãn và dữ liệu

1. Tạo task mù từ video gốc, không cho người gán xem dự đoán; quy định frame 0-based, rep hoàn chỉnh, đáy, clip bị cắt, người bị che và `needs_review`. Không ép nhãn khi không quan sát được. Ghi annotator, thời điểm, phiên bản và sự đồng ý sử dụng video.
2. Rà độc lập số rep và đáy cho tập development/test; dành một nhóm được hai người rà nếu có để đo mức bất đồng. Với lỗi form, trước hết thống nhất mô tả, ví dụ minh họa và tiêu chí; phân biệt “không quan sát được” với “không có lỗi”.
3. Báo số subject/video/rep theo split, class và góc quay, coverage, thiếu nhãn; không coi nhiều frame của cùng video là mẫu độc lập. Không cần định ra số mẫu tối thiểu giả; một tập nhỏ có thể đủ chạy thử nhưng không đủ chứng minh tổng quát.
4. Khóa nhãn test trước khi đánh giá cuối; giữ riêng test mới nếu nhãn đã xem dự đoán hoặc dùng để chọn cấu hình. Kết quả AI nháp chỉ dùng để hỗ trợ rà development, ghi rõ không mù.

**Đầu ra:** manifest, nhãn, quy trình và thống kê được rà. **Phụ thuộc:** cần người xem/rá nhãn độc lập; có thể chuẩn bị công cụ và task trước, không thể tự tạo đánh giá độc lập bằng cách đổi metadata AI.

## 5. Mốc C — Baseline ML A: phân loại video

1. Lọc side view Multi-View từ manifest, kiểm tra nhãn, pose và thông tin cá nhân/giấy phép. Cache pose train/validation, ghi phiên bản model và hash; việc trích pose lâu phải báo người dùng trước.
2. Xác định đơn vị dự đoán là video. Trích đặc trưng tổng hợp như phân vị góc gối/thân, biên độ, thời gian rep, số candidate và chỉ số coverage/visibility; theo dõi thiếu rep. Không dùng tên file, ID, nhãn nguồn, split, đường dẫn hay thông tin hậu nghiệm làm đặc trưng. Chỉ được dùng thông tin có ở thời điểm dự đoán.
3. So sánh dự đoán lớp đa số và rule video được định nghĩa trước với logistic regression (chuẩn hóa/điền thiếu trong pipeline) và Random Forest. Chia theo subject; nếu ít subject không đủ cho stratified group CV thì báo, giảm số fold hoặc dùng validation nhóm cố định, không tách ngẫu nhiên từng frame.
4. Fit preprocessing/chọn đặc trưng/hyperparameter chỉ trên train (mỗi fold riêng), chọn cấu hình bằng validation/group CV, không chọn theo test. Khóa mô hình, sau đó chạy một lần trên test chưa dùng để điều chỉnh.
5. Báo số subject/video, accuracy, balanced accuracy, macro F1, precision/recall theo lớp, confusion matrix, coverage/không xử lý và kết quả theo subject. Với mẫu nhỏ báo số đếm thô và khoảng bất định phù hợp; không thổi phồng vài phần trăm thành cải thiện chắc chắn. So sánh same-split/same-coverage với baseline.

**Đầu ra:** script trích đặc trưng, training/evaluation có cấu hình và seed, model artifact ngoài Git, báo cáo và lệnh tái lập. **Xong khi:** chạy được và có kết quả trung thực; nếu không tốt hơn baseline thì báo kết quả âm, không tự tích hợp thành kết luận chất lượng.

## 6. Mốc D — Cải thiện đếm rep B

1. Trên train có nhãn người: phân loại nguyên nhân FP/FN theo rep nhanh/nông, chưa đứng hẳn, tạm dừng, mất pose, nhiều người và clip cắt. Giữ nguyên trường hợp `partial` và các khoảng không quan sát được.
2. Cải thiện FSM/quality gate có kiểm thử hồi quy. Thử tiêu chí độ nổi bật/thời lượng và các đặc trưng thời gian một cách có kiểm soát, không tinh chỉnh chỉ theo video mẫu.
3. Nếu nhãn thời gian đủ đa dạng, thử model 1D-CNN/TCN nhỏ nhận chuỗi góc, velocity và visibility/mask để phát hiện pha hoặc đáy; không coi các window từ cùng người là độc lập. Cần xử lý FPS, gap, pose lỗi và trường hợp không đủ dữ liệu, đo inference CPU.
4. Trên cùng test độc lập và cùng điều kiện: video complete báo MAE đếm, rep TP/FP/FN theo quy tắc ghép, precision/recall và sai số thời gian đáy; báo coverage và partial riêng. Bổ sung ablation: FSM 1,0 / FSM 0,8 / phiên bản mới / ML nếu đủ dữ liệu.

**Xong khi:** có so sánh trước/sau và test hồi quy; chỉ đổi mặc định khi có bằng chứng phù hợp. Nếu model không cải thiện hoặc dữ liệu thiếu, giữ baseline và nêu rõ giới hạn.

## 7. Mốc E — Tích hợp, demo và báo cáo Project 3

- Chỉ nối model đã đánh giá vào pipeline/API/UI khi output, lớp nhãn, điều kiện dữ liệu và ngưỡng tin cậy được định nghĩa rõ; hiển thị phiên bản, mức độ không đủ dữ liệu và tách nhận xét cấp video/rep. Kiểm thử upload, lỗi, restart, xóa, tua, xuất JSON và tính tương thích dữ liệu cũ.
- Kiểm thử thật với video chưa dùng phát triển trên máy mục tiêu; ghi thời gian xử lý, phần cứng, cảnh báo và tình huống thất bại. Chuẩn bị demo, slide, sơ đồ, mô tả dữ liệu, baseline, bảng số liệu và giới hạn/đạo đức dữ liệu.
- Đối chiếu với rubric trước khi tuyên bố hoàn thành Project 3; MVP chạy được không tự đồng nghĩa hoàn thành học phần.

## 8. Tài nguyên, thời gian và người dùng cần chuẩn bị

- Không cần train MediaPipe Heavy từ đầu để bắt đầu. Baseline logistic/Random Forest thường nhẹ hơn model video lớn, nhưng thời gian thực tế phụ thuộc dữ liệu và máy; chưa có benchmark nên không hứa số phút. Trích pose hàng loạt có thể là phần tốn thời gian nhất.
- Trước mỗi lượt trích pose/train dài: đo thử trên mẫu nhỏ và báo người dùng mục tiêu, lệnh Git Bash, tập dữ liệu, CPU/GPU/RAM/dung lượng, thời gian dự kiến từ benchmark, vị trí artifact/log và cách gửi kết quả. Người dùng tự chạy theo thỏa thuận; không khởi chạy tác vụ train dài tự ý.
- Cần người dùng cung cấp khi có: rubric/đề cương và deadline; thông số phần cứng; video squat có sự đồng ý sử dụng nếu muốn kiểm thử dữ liệu mới; người rà nhãn độc lập. Không bắt buộc có GPU để xây baseline kỹ thuật; mức sử dụng thực tế cần benchmark.
- Ước lượng lập kế hoạch, không phải cam kết: A 1–2 ngày làm việc, B 3–10+ ngày phụ thuộc số video/người rà, C 2–5 ngày sau khi có dữ liệu, D 3–10+ ngày tùy kết quả và nhãn, E 3–7 ngày. Có thể làm B song song A/C; tổng không cộng máy móc và thời gian chạy máy/đợi người rà chưa chắc chắn.

## 9. Nguồn kỹ thuật

- [scikit-learn: cross-validation theo nhóm](https://scikit-learn.org/stable/modules/cross_validation.html) và [tránh data leakage](https://scikit-learn.org/stable/common_pitfalls.html): tách theo người và fit preprocessing chỉ trên train.
- [RepNet, CVPR 2020](https://openaccess.thecvf.com/content_CVPR_2020/html/Dwibedi_Counting_Out_Time_Class_Agnostic_Video_Repetition_Counting_in_the_CVPR_2020_paper.html): ví dụ học tín hiệu lặp từ video; không chứng minh RepNet tốt hơn FSM cho dataset này và không mặc định cần huấn luyện lại model lớn.
- [Pose Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker): model hiện dùng để trích landmark; output pose không đồng nghĩa nhãn kỹ thuật hay ground truth.

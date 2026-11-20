# Chuẩn bị dữ liệu squat cho MVP

Ngày chuẩn bị: 20/11/2026. Chạy từ thư mục dự án:

```powershell
.\.venv\Scripts\python.exe ai/data/prepare_squat_datasets.py
```

Script kiểm tra SHA-256 Multi-View, MD5 hai archive UI-PRMD sử dụng, giải nén có chọn lọc, kiểm tra video đọc được và tạo manifest JSONL tại `data/external/prepared_squat/`. File đã tồn tại được đối chiếu CRC/kích thước; nếu khác script dừng để bảo vệ dữ liệu, không ghi đè. Dataset và manifest nằm ngoài Git. Không có tác vụ huấn luyện trong bước này.

## Multi-View Fitness v3

Nguồn https://data.mendeley.com/datasets/kgbb3yn47p/3 — CC BY 4.0. Cần trích dẫn tác giả và DOI 10.17632/kgbb3yn47p.3 khi sử dụng. Chỉ giải nén phần squat từ archive exercise-wise; các archive alternative là cùng dữ liệu được sắp xếp lại.

- 150 video từ 25 mã người trong phần squat: good/bad mỗi loại 75; side/front/diagonal mỗi góc 50. Đây là nhãn **cấp video** do nguồn cung cấp, không phải nhãn frame hay loại lỗi.
- 17 người / 102 video train, 4 / 24 validation, 4 / 24 test, chia cố định theo mã người với seed 20261120. Mỗi bên/nhãn đều có mặt trong từng split. Chia theo người chỉ được bảo đảm trong nguồn này; không có bằng chứng người tập không xuất hiện trong dataset khác.
- File `multiview_manifest.jsonl` chứa đường dẫn tương đối với `prepared_squat`, subject, split, view, nhãn video và metadata video. MVP quay bên hông lọc `view == "side"`, nhưng không tự loại góc khác khỏi kho gốc.

## CFRep

Nguồn https://github.com/lc-leonardo/CFRep. ZIP đã kiểm tra CRC; chưa tìm thấy file giấy phép rõ ràng nên **cần xác minh quyền sử dụng trước khi train hoặc phân phối**. 22 video squat và một file JSON annotation nguồn cho mỗi video được giải nén để kiểm tra nội bộ. Các pose trong JSON là ước lượng của model nguồn, không phải ground truth MediaPipe. Nhãn `rep`/`no-rep` là nhãn hợp lệ theo quy tắc nguồn, không phải nhãn frame đáy hoặc chẩn đoán lâm sàng.

Manifest `cfrep_manifest.jsonl` giữ mã người, góc, số rep theo tên file và đường dẫn tới JSON. Mã `m32` chưa rõ có liên quan `m3` hay không; do chưa xác minh danh tính và giấy phép, tất cả CFRep có split `unassigned` và không được tự động nhập vào tập train/test. Script kiểm tra số nhãn `rep`/`no-rep` khớp với số trong tên video.

## UI-PRMD

Nguồn https://zenodo.org/records/23104965 và https://www.idahofallshighered.org/vakanski/ui-prmd.html — PDDL 1.0 theo trang tác giả; cần trích dẫn Vakanski và cộng sự (2018). Đã chọn các file movement `m01` (deep squat) từ hai archive segmented correct/incorrect: 800 file, gồm 400 correct và 400 incorrect, từ 10 mã người.

Mỗi lần thực hiện được lưu nhiều bản theo hệ cảm biến Kinect/Vicon và dữ liệu angles/positions; **800 là số file, không phải 800 rep độc lập**. Manifest `ui_prmd_manifest.jsonl` giữ nguồn, sensor, loại phép đo, nhãn và split theo người. Split: 6 người / 480 file train, 2 / 160 validation, 2 / 160 test; cùng một người không qua nhiều split. Đây là dữ liệu phục hồi chức năng, không phải video gym hay nhãn form theo từng lỗi.

## Kiểm tra ban đầu

- OpenCV đọc được frame đầu, FPS và frame count của cả 172 video trong hai nguồn.
- Smoke test MediaPipe Heavy trên **60 frame đầu** của hai video Multi-View side train của subject_003: video nhãn good phát hiện 56/60 frame, video nhãn bad 55/60 frame. Đây chỉ kiểm tra chạy kỹ thuật, không phải thước đo sai số góc, độ đúng form hay đại diện toàn bộ tập.
- Fit3D chưa tải: phải đăng ký và được cấp quyền tại https://fit3d.imar.ro/; tuân thủ https://fit3d.imar.ro/legal. Không nhập nó vào các manifest đã chuẩn bị.

## Việc tiếp theo

Kiểm tra thủ công nhãn và góc quay, tạo nhãn mốc bắt đầu/đáy/kết thúc độc lập cho tập phát triển và test, rồi thử pipeline pose → chất lượng → rep trên một nhóm nhỏ. Đo precision/recall đếm rep và sai số mốc. Trước khi trích xuất hàng loạt/train, tính thời gian và báo người dùng nếu là tác vụ dài; không dùng test để điều chỉnh tham số. Cần tránh trộn dữ liệu giữa các nguồn khi chưa biết danh tính trùng lặp.

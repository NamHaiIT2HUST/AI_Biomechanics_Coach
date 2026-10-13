# KẾ HOẠCH & LỘ TRÌNH TRIỂN KHAI CHI TIẾT DỰ ÁN (12 TUẦN)



---

## MỤC LỤC
1. [Tổng quan Hai Cột mốc Đánh giá SoICT](#1-tổng-quan-hai-cột-mốc-đánh-giá-soict)
2. [Lộ trình Chi tiết Từng tuần (Tuần 1 - 12)](#2-lộ-trình-chi-tiết-từng-tuần-tuần-1---12)
3. [Phân chia Trách nhiệm & Ma trận Deliverables](#3-phân-chia-trách-nhiệm--ma-trận-deliverables)
4. [Quản lý Rủi ro & Kế hoạch Dự phòng](#4-quản-lý-rủi-ro--kế-hoạch-dự-phòng)
5. [Checklist Hồ sơ Nghiệm thu Đồ án 3](#5-checklist-hồ-sơ-nghiệm-thu-đồ-án-3)

---

## 1. TỔNG QUAN HAI CỘT MỐC ĐÁNH GIÁ SOICT

Trong quy trình làm Đồ án 3 tại SoICT - HUST, giảng viên hướng dẫn và hội đồng bộ môn sẽ đánh giá theo 2 mốc quan trọng:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ CỘT MỐC 1: ĐÁNH GIÁ GIỮA KỲ (Tuần 6 - 7)                               │
│ Yêu cầu bắt buộc:                                                      │
│ • Có dữ liệu video thô và dữ liệu gán nhãn đo tay (Ground Truth).      │
│ • Hoàn thiện thuật toán CV trích xuất 33 khớp và tính góc sinh cơ học. │
│ • Có kết quả đo kiểm chứng sai số sơ bộ (MAE < 5°).                    │
│ • Xuất được video overlay khung xương đổi màu (chứng minh thuật toán). │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ CỘT MỐC 2: BẢO VỆ CUỐI KỲ (Tuần 12)                                    │
│ Yêu cầu bắt buộc:                                                      │
│ • Sản phẩm Web hoàn chỉnh chạy end-to-end (Frontend Next.js + Backend).│
│ • Tích hợp Mô hình Học máy nhẹ (Tầng 2) & Multi-Agent RAG (Tầng 3).    │
│ • Trình diễn 3D Digital Twin xoay 360 độ và Chat tư vấn HLV AI.       │
│ • Cuốn Báo cáo thuyết minh Đồ án 3 chuẩn format Bách Khoa.             │
│ • Video Demo 3–5 phút và Slide bảo vệ sẵn sàng.                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. LỘ TRÌNH CHI TIẾT TỪNG TUẦN (TUẦN 1 - 12)

---

### TUẦN 1: KHỞI TẠO NỀN TẢNG & MÔI TRƯỜNG DỰ ÁN
* **Mục tiêu:** Thiết lập toàn bộ hạ tầng mã nguồn, môi trường ảo và quy chuẩn kỹ thuật.
* **Các đầu việc cụ thể (Tasks):**
  - [x] Tạo cấu trúc thư mục chuẩn: `docs/`, `data/`, `ai/`, `backend/`, `frontend/`.
  - [x] Cấu hình file `.gitignore` thông minh (bỏ qua video nặng, model weights, `.venv`).
  - [x] Khởi tạo môi trường ảo Python 3.11 (`.venv`) và cài đặt `requirements.txt`.
  - [x] Tạo file cấu hình tiêu chuẩn ban đầu: `backend/app/exercises/squat.json`.
  - [x] Viết khung ứng dụng `backend/app/main.py` với endpoint `/health`.
* **Kết quả bàn giao (Deliverables):**
  - Git repository sạch, cấu trúc thư mục hoàn chỉnh trên GitHub.
  - Môi trường ảo import thành công 100% các thư viện CV, ML và FastAPI.

---

### TUẦN 2: THU THẬP DỮ LIỆU & POSE BASELINE (EXPERIMENTS)
* **Mục tiêu:** Thu thập tập video thực tế đầu tiên và chạy thử nghiệm bóc tách khung xương.
* **Các đầu việc cụ thể (Tasks):**
  - [ ] **Thu thập video:** Nhờ 3–4 bạn sinh viên quay 20–30 video bài Squat từ góc nghiêng $90^\circ$:
    - 10 video tập chuẩn form (Full depth, lưng thẳng).
    - 10 video cố tình xuống nông (Half squat).
    - 10 video cố tình ngả lưng nhiều về trước hoặc nhấc gót.
  - [ ] Đưa video vào thư mục `data/raw/squats_good/` và `data/raw/squats_bad/`.
  - [ ] **Viết Notebook `ai/notebooks/01_pose_extraction.ipynb`:**
    - Dùng OpenCV đọc video và chạy MediaPipe Pose Heavy trích xuất 33 landmarks.
    - Trực quan hóa khung xương lên các frame để đánh giá độ bám khớp.
* **Đầu vào $\rightarrow$ Đầu ra:**
  - *Input:* 30 video `.mp4` $\rightarrow$ *Output:* File JSON lưu chuỗi tọa độ 33 khớp cho từng video trong `data/processed/landmarks/`.
* **Tiêu chí nghiệm thu (DoD):** Trích xuất được tọa độ 33 khớp từ video với tỷ lệ phát hiện $\ge 90\%$ số frame.

---

### TUẦN 3: LÕI TOÁN HỌC SINH CƠ HỌC & LỌC TÍN HIỆU
* **Mục tiêu:** Xây dựng module tính góc động học và thuật toán lọc khử rung lắc.
* **Các đầu việc cụ thể (Tasks):**
  - [ ] **Viết `backend/app/core/geometry.py`:**
    - Hàm tính góc 3 điểm: $\theta_{\text{knee}}$ (Hông - Gối - Cổ chân), $\theta_{\text{hip}}$ (Vai - Hông - Gối).
    - Hàm tính độ nghiêng thân trên: $\theta_{\text{trunk}}$ so với phương thẳng đứng.
  - [ ] **Viết `backend/app/core/smoothing.py`:**
    - Cài đặt bộ lọc Savitzky-Golay (`window_length=11`, `polyorder=2`).
  - [ ] **Viết Notebook `ai/notebooks/02_signal_filtering.ipynb`:**
    - Vẽ đồ thị so sánh tín hiệu góc thô (Raw) vs Tín hiệu sau khi lọc Savitzky-Golay.
    - Chứng minh Savitzky-Golay không làm cụt độ sâu ở đáy (so với Moving Average).
  - [ ] **Viết Unit Test:** Tạo `backend/tests/test_geometry.py` kiểm thử các hàm tính góc với dữ liệu mẫu (tam giác vuông, góc $90^\circ$, $180^\circ$).
* **Đầu vào $\rightarrow$ Đầu ra:**
  - *Input:* Mảng tọa độ khớp thô $\rightarrow$ *Output:* Chuỗi góc khớp đã làm mượt.
* **Tiêu chí nghiệm thu (DoD):** Unit test góc hình học pass 100%; đồ thị góc mượt mà không còn gai nhọn (jitter).

---

### TUẦN 4: THUẬT TOÁN TÁCH PHA & ĐẾM REPS
* **Mục tiêu:** Tự động phát hiện điểm bắt đầu, điểm đáy (Bottom), điểm kết thúc và đếm số rep.
* **Các đầu việc cụ thể (Tasks):**
  - [ ] **Viết `backend/app/core/phases.py`:**
    - Sử dụng hàm `scipy.signal.find_peaks` trên đồ thị nghịch đảo $-\theta_{\text{knee}}$ để tìm frame đáy cực tiểu.
    - Cài đặt cơ chế ngưỡng trễ (Hysteresis): Xuống dưới $105^\circ$ và trở về trên $160^\circ$ mới được ghi nhận là 1 Rep hoàn chỉnh.
  - [ ] **Viết Notebook `ai/notebooks/03_rep_segmentation.ipynb`:**
    - Chạy thử nghiệm thuật toán tách rep trên 20 video thu thập ở Tuần 2.
    - Vẽ đồ thị đánh dấu vị trí các điểm đáy (Bottom Peaks) trên timeline.
  - [ ] **Viết Unit Test:** Tạo `backend/tests/test_phases.py` kiểm tra độ chính xác của hàm đếm rep.
* **Đầu vào $\rightarrow$ Đầu ra:**
  - *Input:* Chuỗi góc gối $\theta_{\text{knee}}(t) \rightarrow$ *Output:* Danh sách các đối tượng `RepData` (`[rep_id, start_frame, bottom_frame, end_frame, min_knee_angle]`).
* **Tiêu chí nghiệm thu (DoD):** Đếm chính xác số rep trên $\ge 95\%$ video thử nghiệm, không đếm trùng lặp.

---

### TUẦN 5: BỘ SO SÁNH TIÊU CHUẨN & RENDER VIDEO OVERLAY
* **Mục tiêu:** Hoàn thiện bộ luật bắt lỗi và xuất video có khung xương trực quan đổi màu.
* **Các đầu việc cụ thể (Tasks):**
  - [ ] **Viết `backend/app/core/evaluator.py`:**
    - Đọc file cấu hình `exercises/squat.json`.
    - Kiểm tra lỗi từng rep:
      - Nếu $\min(\theta_{\text{knee}}) > 100^\circ \rightarrow$ Ghi nhận lỗi `insufficient_depth`.
      - Nếu $\theta_{\text{trunk\_at\_bottom}} > 45^\circ \rightarrow$ Ghi nhận lỗi `excessive_trunk_lean`.
  - [ ] **Viết `backend/app/core/overlay.py`:**
    - Dùng OpenCV vẽ khung xương lên từng frame video:
      - Xương màu **Xanh lá cây** khi góc đạt chuẩn.
      - Xương đổi sang màu **Đỏ** khi vi phạm lỗi.
      - Vẽ bảng text hiển thị số đo góc và pha động tác ở góc màn hình.
    - Đóng gói chuỗi frame thành video MP4 hoàn chỉnh.
* **Đầu vào $\rightarrow$ Đầu ra:**
  - *Input:* Video gốc + Danh sách góc $\rightarrow$ *Output:* Video MP4 có overlay khung xương + JSON danh sách lỗi.
* **Tiêu chí nghiệm thu (DoD):** Chạy 1 lệnh xuất ra được file video overlay xem trực quan mượt mà bằng VLC/Windows Media Player.

---

### TUẦN 6: HUẤN LUYỆN MÔ HÌNH HỌC MÁY NHẸ (LIGHT ML)
* **Mục tiêu:** Cung cấp thành phần Machine Learning thực thụ để phân loại chất lượng form rep (Tầng 2).
* **Các đầu việc cụ thể (Tasks):**
  - [ ] **Viết `ai/training/extract_features.py`:**
    - Duyệt qua toàn bộ video trong `data/raw/` để bóc tách các đặc trưng của từng rep:
      - $\min(\text{góc gối})$, $\max(\text{độ ngả thân})$, thời gian pha hạ/đẩy (tempo), góc gập hông.
    - Lưu thành file `data/processed/angle_features.csv`.
  - [ ] **Viết Notebook `ai/notebooks/04_train_form_classifier.ipynb`:**
    - Huấn luyện mô hình **XGBoost / Random Forest** phân loại Form (Good Form vs Bad Form).
    - Phân chia tập dữ liệu: 80% Train, 20% Test (Stratified K-Fold).
    - Đánh giá mô hình: Độ chính xác (Accuracy), F1-Score, vẽ ma trận nhầm lẫn (Confusion Matrix).
  - [ ] Đóng gói mô hình đã huấn luyện thành file `ai/models/trained/squat_classifier.joblib`.
* **Đầu vào $\rightarrow$ Đầu ra:**
  - *Input:* File CSV đặc trưng $\rightarrow$ *Output:* File model `.joblib` đạt $\text{Accuracy} \ge 88\%$.
* **Tiêu chí nghiệm thu (DoD):** Có mô hình ML chạy suy luận (predict) độc lập trong 5 mili-giây cho 1 rep.

---

### TUẦN 7: ĐO KIỂM CHỨNG SAI SỐ THỰC NGHIỆM (VALIDATION MAE) — *[MỐC GIỮA KỲ]*
* **Mục tiêu:** Hoàn thiện chương quan trọng nhất trong đồ án: Đo sai số MAE so với đo tay thủ công.
* **Các đầu việc cụ thể (Tasks):**
  - [ ] **Tạo Ground Truth:**
    - Trích xuất 50–100 frame ngẫu nhiên từ các video thử nghiệm.
    - Dùng phần mềm đo góc chuyên dụng (Kinovea) đo tay góc gối và góc thân trên từng ảnh.
    - Lưu kết quả vào `data/ground_truth/manual_annotations.csv`.
  - [ ] **Viết Notebook `ai/notebooks/05_validation_mae.ipynb`:**
    - Chạy thuật toán tự động của hệ thống trên đúng 50–100 frame đó.
    - Tính sai số tuyệt đối trung bình (MAE) và độ lệch chuẩn (Std):
      $$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |\theta_{\text{system}}^{(i)} - \theta_{\text{manual}}^{(i)}|$$
    - Vẽ biểu đồ phân tán (Scatter Plot) và biểu đồ tương quan Bland-Altman.
  - [ ] Soạn tài liệu `docs/validation-report.md` tổng kết kết quả thực nghiệm.
* **Đầu vào $\rightarrow$ Đầu ra:**
  - *Input:* 100 frame gán nhãn Kinovea $\rightarrow$ *Output:* Báo cáo kiểm chứng đạt **$\text{MAE} < 5^\circ$**.
* **Tiêu chí nghiệm thu (DoD):** Có bảng số liệu và đồ thị so sánh chứng minh hệ thống đo đạc chính xác khoa học để báo cáo giữa kỳ với thầy.

---

### TUẦN 8: XÂY DỰNG REST API BACKEND (FASTAPI)
* **Mục tiêu:** Đóng gói toàn bộ logic CV và ML thành dịch vụ web hoàn chỉnh.
* **Các đầu việc cụ thể (Tasks):**
  - [ ] Xây dựng các Pydantic Schemas trong `backend/app/models/domain.py`: `AnalysisRequest`, `AnalysisResponse`, `RepDetail`, `FaultItem`.
  - [ ] Cài đặt các API endpoints trong `backend/app/api/v1/analyses.py`:
    - `POST /api/v1/analyses`: Tiếp nhận file video upload, kiểm tra độ phân giải $\ge 720p$, FPS $\ge 30$, lưu file vào `data/raw/`.
    - `GET /api/v1/analyses/{id}`: Trả về trạng thái xử lý (`PROCESSING`, `COMPLETED`) và toàn bộ kết quả phân tích.
    - `GET /api/v1/analyses/{id}/overlay`: Trả về file video overlay MP4.
  - [ ] Tích hợp xử lý ngầm (Background Worker) qua `FastAPI.BackgroundTasks` để không làm treo API khi xử lý video dài.
  - [ ] Viết API lấy thông tin bài tập `GET /api/v1/exercises`.
* **Đầu vào $\rightarrow$ Đầu ra:**
  - *Input:* HTTP Requests $\rightarrow$ *Output:* OpenAPI Documentation tại `http://localhost:8000/docs`.
* **Tiêu chí nghiệm thu (DoD):** Dùng Swagger UI upload thử 1 video và nhận lại JSON kết quả phân tích chuẩn schema.

---

### TUẦN 9: XÂY DỰNG RAG Y VĂN THỂ HÌNH (KNOWLEDGE BASE)
* **Mục tiêu:** Tạo cơ sở tri thức y học vận động và sinh cơ học cho AI Agent.
* **Các đầu việc cụ thể (Tasks):**
  - [ ] Thu thập tài liệu chuyên ngành:
    - Giáo trình *Essentials of Strength Training and Conditioning* (NSCA).
    - Các bài báo Open-Access trên PubMed về sinh cơ học bài Squat.
    - Lưu vào thư mục `data/knowledge_base/`.
  - [ ] **Viết `backend/app/agent/rag.py`:**
    - Cắt đoạn văn bản (Chunking) 400–600 tokens kèm metadata (`exercise`, `fault_type`).
    - Tạo embedding vector và lưu trữ vào ChromaDB cục bộ tại `data/vector_db/`.
    - Cài đặt hàm tìm kiếm: `search_knowledge(query, tags)`.
  - [ ] Viết script test truy vấn: Hỏi về *"lumbar shear stress squat trunk lean"* $\rightarrow$ trả về đoạn y văn chuẩn xác kèm trích dẫn.
* **Đầu vào $\rightarrow$ Đầu ra:**
  - *Input:* Tài liệu PDF/Markdown $\rightarrow$ *Output:* ChromaDB Vector Store sẵn sàng truy vấn trong $< 50\text{ ms}$.
* **Tiêu chí nghiệm thu (DoD):** Truy vấn các lỗi squat trả về đúng đoạn trích dẫn khoa học.

---

### TUẦN 10: TRIỂN KHAI HỆ THỐNG ĐA TÁC TỬ AI (MULTI-AGENT COACH)
* **Mục tiêu:** Tích hợp AI Agent đóng vai trò PT ảo phân tích lỗi và lập giáo án sửa form.
* **Các đầu việc cụ thể (Tasks):**
  - [ ] **Viết `backend/app/agent/prompts.py`:** Thiết lập System Prompt chuyên sâu cho 3 tác tử:
    - `AnalysisAgent`: Chuyên gia thống kê số liệu rep.
    - `BiomechanicsAgent`: Chuyên gia đối chiếu y văn RAG.
    - `CoachingAgent`: HLV trưởng đưa ra khẩu lệnh Cues & Bài tập phục hồi.
  - [ ] **Viết `backend/app/agent/coordinator.py`:**
    - Lắp ráp luồng điều phối Multi-Agent bằng LangChain / Tool-calling.
    - Đầu ra báo cáo chuẩn 4 phần: *[Nhận định]* $\rightarrow$ *[Cơ chế áp lực]* $\rightarrow$ *[Khẩu lệnh Cues]* $\rightarrow$ *[Bài tập bổ trợ]*.
  - [ ] Cài đặt API Chat trong `backend/app/api/v1/chat.py`:
    - Cho phép người dùng hỏi đáp trực tiếp theo ngữ cảnh video đã phân tích.
* **Đầu vào $\rightarrow$ Đầu ra:**
  - *Input:* Danh sách lỗi của video $\rightarrow$ *Output:* Báo cáo phân tích hoàn chỉnh và Chatbot trả lời thông minh.
* **Tiêu chí nghiệm thu (DoD):** AI Agent trả lời đúng 100% các lỗi từ Detector, tuyệt đối không tự bịa lỗi mới (không hallucination).

---

### TUẦN 11: PHÁT TRIỂN GIAO DIỆN CLIENT (NEXT.JS & 3D DIGITAL TWIN)
* **Mục tiêu:** Xây dựng giao diện web hoàn chỉnh, hiện đại và trực quan.
* **Các đầu việc cụ thể (Tasks):**
  - [ ] Dựng trang chủ và trang tải video: Form upload kéo thả có hướng dẫn góc quay chuẩn.
  - [ ] **Dựng Component `Viewer3D.tsx` (Plotly.js):**
    - Hiển thị khung xương 3D tái tạo từ tọa độ `world_landmarks`.
    - Cho phép xoay chuột 360 độ (Orbit Camera) như công cụ Robotics.
  - [ ] **Dựng Component `VideoOverlay.tsx`:**
    - Phát video gốc song song video overlay có thanh trượt timeline tua theo từng frame.
  - [ ] **Dựng Component `MetricsDashboard.tsx`:**
    - Vẽ đồ thị biến thiên góc khớp theo rep bằng Recharts.
    - Thẻ chấm điểm bài tập (Score 0–100) và danh sách các lỗi vi phạm.
  - [ ] **Dựng Component `ChatPanel.tsx`:**
    - Khung chat nhắn tin với AI Coach để hỏi đáp kỹ thuật.
* **Đầu vào $\rightarrow$ Đầu ra:**
  - *Input:* REST API Backend $\rightarrow$ *Output:* Ứng dụng Web chạy trên `http://localhost:3000`.
* **Tiêu chí nghiệm thu (DoD):** Người dùng có thể upload video và xem toàn bộ kết quả mượt mà trên trình duyệt.

---

### TUẦN 12: ĐÁNH GIÁ TOÀN DIỆN, VIẾT BÁO CÁO & ĐÓNG GÓI BẢO VỆ
* **Mục tiêu:** Hoàn thiện toàn bộ hồ sơ nghiệm thu Đồ án 3 để bảo vệ điểm A/A+.
* **Các đầu việc cụ thể (Tasks):**
  - [ ] Kiểm thử toàn diện hệ thống (End-to-End Testing): Chạy thử trên 10 video mới để kiểm tra các trường hợp biên.
  - [ ] Thử nghiệm chế độ Gương tập luyện trực tiếp webcam (`LiveMirror.tsx`) với Web Worker (nếu kịp tiến độ).
  - [ ] **Viết Báo cáo Thuyết minh Đồ án 3 (40–50 trang theo format SoICT):**
    - Chương 1: Đặt vấn đề & Khảo sát bài toán.
    - Chương 2: Cơ sở lý thuyết (Sinh cơ học, MediaPipe, XGBoost, RAG, Multi-Agent).
    - Chương 3: Phân tích thiết kế hệ thống (Kiến trúc, UML, Database).
    - Chương 4: Cài đặt và Thực nghiệm (Kết quả đo sai số MAE, độ chính xác ML, giao diện).
    - Chương 5: Kết luận và Hướng phát triển.
  - [ ] Thiết kế Slide thuyết trình PowerPoint / Canva (15–20 slides).
  - [ ] Quay 1 Video Demo giới thiệu sản phẩm (3–5 phút).
* **Tiêu chí nghiệm thu (DoD):** Bộ hồ sơ hoàn chỉnh sẵn sàng nộp cho Giảng viên hướng dẫn và Hội đồng chấm đồ án.

---

## 3. PHÂN CHIA TRÁCH NHIỆM & MA TRẬN DELIVERABLES

| Phân hệ chức năng | Tuần hoàn thành | Module mã nguồn chính | Người kiểm tra (Reviewer) |
|---|:---:|---|---|
| **Cấu trúc & Môi trường** | Tuần 1 | `backend/requirements.txt`, `.gitignore` | Bản thân & GVHD |
| **Dữ liệu & Pose Baseline** | Tuần 2 | `data/raw/`, `01_pose_extraction.ipynb` | GVHD |
| **Toán học & Lọc tín hiệu** | Tuần 3 | `backend/app/core/geometry.py`, `smoothing.py` | Unit Test tự động |
| **Tách Pha & Đếm Reps** | Tuần 4 | `backend/app/core/phases.py` | Unit Test tự động |
| **Bắt lỗi & Video Overlay** | Tuần 5 | `backend/app/core/evaluator.py`, `overlay.py` | Bản thân |
| **Huấn luyện Mô hình ML** | Tuần 6 | `ai/training/`, `ai/models/trained/` | Bản thân |
| **Đo Kiểm chứng MAE** | Tuần 7 | `ai/notebooks/05_validation_mae.ipynb` | **Báo cáo Giữa kỳ GVHD** |
| **FastAPI REST API** | Tuần 8 | `backend/app/api/v1/` | Swagger Docs |
| **ChromaDB RAG** | Tuần 9 | `backend/app/agent/rag.py` | Bản thân |
| **Multi-Agent Coaching** | Tuần 10 | `backend/app/agent/coordinator.py` | Bản thân |
| **Next.js Frontend & 3D** | Tuần 11 | `frontend/src/` | Bản thân |
| **Báo cáo & Slide bảo vệ** | Tuần 12 | Cuốn báo cáo PDF + Slide + Video Demo | **Hội đồng Bảo vệ SoICT** |

---

## 4. QUẢN LÝ RỦI RO & KẾ HOẠCH DỰ PHÒNG

| # | Rủi ro tiềm ẩn | Mức độ | Kế hoạch dự phòng (Contingency Plan) |
|---|---|:---:|---|
| **R1** | Không quay đủ video đa dạng thể trạng | Trung bình | Tải thêm các tập dữ liệu mở (Fit3D, RepCount) và áp dụng các phép Data Augmentation (lật gương, time-warping). |
| **R2** | Sai số trục Z (độ sâu) làm méo góc | Cao | **Không tính góc dựa vào trục Z**. Quy định chặt chẽ góc quay bên hông $90^\circ$ để chỉ tính toán trên mặt phẳng XY 2D. Trục Z chỉ dùng minh họa cho 3D Viewer. |
| **R3** | AI Agent bị quá tải hoặc hallucination | Cao | Ràng buộc chặt bằng System Prompt: Agent chỉ được diễn giải các lỗi nằm trong danh sách trả về của hàm `evaluator.py`. |
| **R4** | Không kịp thời gian làm chế độ Live Webcam | Trung bình | **Chiến lược cắt giảm an toàn:** Ưu tiên hoàn thiện 100% chế độ Offline (Upload Video + 3D Viewer + Báo cáo MAE). Đây là phần cốt lõi để đạt điểm tuyệt đối. Chế độ Live coi là tính năng nâng cao (Bonus). |

---

## 5. CHECKLIST HỒ SƠ NGHIỆM THU ĐỒ ÁN 3

Trước ngày bảo vệ chính thức, hãy kiểm tra danh sách này để đảm bảo không thiếu sót bất kỳ tài liệu nào:

- [ ] **Mã nguồn (Source Code):**
  - [ ] GitHub repo công khai hoặc cấp quyền cho thầy cô.
  - [ ] File `README.md` có hướng dẫn cài đặt và chạy thử bằng 2–3 câu lệnh.
- [ ] **Báo cáo Thuyết minh (Project Thesis):**
  - [ ] Định dạng chuẩn theo quy định SoICT (Bìa, Lời cảm ơn, Mục lục, Danh mục hình vẽ/bảng biểu).
  - [ ] Chương 4 có biểu đồ thực nghiệm so sánh MAE và Confusion Matrix của mô hình ML.
  - [ ] Đã kiểm tra đạo văn và lỗi chính tả.
- [ ] **Tài liệu Thuyết trình:**
  - [ ] Slide thuyết trình 15–20 trang (tập trung vào Bài toán $\rightarrow$ Giải pháp $\rightarrow$ Kiến trúc $\rightarrow$ Kết quả thực nghiệm $\rightarrow$ Demo).
  - [ ] Video Demo quay màn hình chất lượng cao (phòng trường hợp mất mạng khi bảo vệ trực tiếp).
- [ ] **Chạy Demo trực tiếp:**
  - [ ] Chuẩn bị sẵn 2 video test trong máy: 1 video form chuẩn và 1 video form cố tình mắc lỗi để trình diễn trước hội đồng.

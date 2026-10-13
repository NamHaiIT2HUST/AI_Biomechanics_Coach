# ĐẶC TẢ CHI TIẾT: PHÂN TÍCH THIẾT KẾ HỆ THỐNG (UML & DATABASE)


---

## 1. BIỂU ĐỒ USE CASE (USE CASE DIAGRAM)

Biểu đồ Use Case mô tả trực quan các tác nhân (Actors) và các chức năng mà hệ thống cung cấp.

### 1.1. Các Tác nhân trong Hệ thống (Actors)
1. **Người tập Gym (Primary Actor):** Người trực tiếp sử dụng ứng dụng để phân tích động tác, tập luyện với gương thông minh và nhận lời khuyên từ HLV AI.
2. **Huấn luyện viên / Quản trị viên (Secondary Actor):** Quản lý bộ quy tắc tiêu chuẩn bài tập, giám sát hệ thống và xem báo cáo thống kê.
3. **Hệ thống AI / Agent (System Actor):** Thực hiện tự động các tác vụ nặng: xử lý video, tính toán sinh cơ học, tra cứu y văn RAG và sinh lời khuyên.

### 1.2. Sơ đồ Use Case Tổng thể

```mermaid
flowchart LR
    USER(["👤 Người tập Gym"])
    ADMIN(["👔 HLV / Quản trị viên"])
    AI_ACTOR(["🤖 Hệ thống AI / Agent"])

    subgraph SYSTEM_BOUNDARY ["HỆ THỐNG PHÂN TÍCH & GỢI Ý CHỈNH SỬA ĐỘNG TÁC GYM"]
        UC_AUTH["1. Đăng ký / Đăng nhập"]
        UC_PROFILE["2. Cập nhật thể trạng & Chiều cao"]
        UC_SELECT_EX["3. Chọn bài tập (Squat, Deadlift)"]
        UC_UPLOAD["4. Tải lên Video / Ảnh động tác"]
        UC_PROCESS["5. Xử lý khung xương & Đánh giá Form"]
        UC_VIEW_RESULT["6. Xem Dashboard & Video Overlay"]
        UC_VIEW_3D["7. Tương tác mô hình 3D xoay 360°"]
        UC_AI_REPORT["8. Nhận báo cáo phân tích & Bài tập"]
        UC_AI_CHAT["9. Chat hỏi đáp với AI Coach"]
        UC_LIVE_MIRROR["10. Gương tập luyện trực tiếp qua Webcam"]
        UC_CONFIG_RULES["11. Quản trị luật & Tiêu chuẩn góc"]
    end

    USER --- UC_AUTH
    USER --- UC_PROFILE
    USER --- UC_SELECT_EX
    USER --- UC_UPLOAD
    USER --- UC_VIEW_RESULT
    USER --- UC_VIEW_3D
    USER --- UC_AI_REPORT
    USER --- UC_AI_CHAT
    USER --- UC_LIVE_MIRROR

    ADMIN --- UC_CONFIG_RULES

    UC_UPLOAD -.->|Kích hoạt| UC_PROCESS
    UC_PROCESS --- AI_ACTOR
    UC_AI_REPORT --- AI_ACTOR
    UC_AI_CHAT --- AI_ACTOR
```

### 1.3. Đặc tả Use Case Tiêu biểu (Use Case Specification)

* **Tên Use Case:** `Phân tích Video Động tác (Analyze Exercise Video)`
* **Mã số:** `UC-02`
* **Tác nhân chính:** Người tập Gym.
* **Tác nhân hỗ trợ:** Hệ thống AI / Background Worker.
* **Tiền điều kiện:** Người dùng đã đăng nhập và chọn một bài tập hợp lệ (ví dụ: Squat).
* **Luồng sự kiện chính (Basic Flow):**
  1. Người dùng chọn file video (.mp4) từ máy tính/điện thoại và nhấn "Bắt đầu phân tích".
  2. Hệ thống kiểm tra điều kiện kỹ thuật của video (độ phân giải $\ge 720p$, FPS $\ge 30$, thời lượng $3 - 60$ giây).
  3. Hệ thống lưu video, tạo mã phiên phân tích (`analysis_id`), và hiển thị màn hình chờ xử lý.
  4. Hệ thống chạy tiến trình ngầm: trích xuất 33 khớp, làm mượt, tính góc, tách rep, đối chiếu tiêu chuẩn và kích hoạt Multi-Agent.
  5. Hệ thống hoàn tất và điều hướng người dùng tới trang kết quả trực quan (Video Overlay + 3D Viewer + Lời khuyên HLV).
* **Luồng ngoại lệ (Alternative Flow):**
  * *2a. Video không đạt chuẩn (FPS quá thấp hoặc không nhận diện được người):* Hệ thống hiển thị cảnh báo lỗi cụ thể bằng tiếng Việt và yêu cầu người dùng tải lại video đúng hướng dẫn.

---

## 2. THIẾT KẾ CƠ SỞ DỮ LIỆU (DATABASE ERD SCHEMA)

Cơ sở dữ liệu được thiết kế theo chuẩn hóa dạng chuẩn 3 (3NF), đảm bảo tính toàn vẹn dữ liệu và hỗ trợ tốt cho việc lưu trữ chuỗi thời gian phân tích thể thao.

### 2.1. Sơ đồ Thực thể - Mối quan hệ (ERD Diagram)

```mermaid
erDiagram
    USERS ||--o{ ANALYSES : "thực hiện"
    EXERCISES ||--o{ ANALYSES : "áp dụng cho"
    ANALYSES ||--o{ REPS : "chứa các hiệp lặp"
    REPS ||--o{ FAULTS : "phát hiện lỗi tại"
    ANALYSES ||--o{ CHAT_MESSAGES : "lịch sử trao đổi"

    USERS {
        uuid id PK "Khóa chính"
        string email UK "Địa chỉ email (duy nhất)"
        string password_hash "Mật khẩu mã hóa bcrypt"
        string full_name "Họ và tên người tập"
        float height_cm "Chiều cao (hiệu chuẩn tỉ lệ m/px)"
        string fitness_level "Trình độ: BEGINNER, INTERMEDIATE, ADVANCED"
        timestamp created_at "Thời điểm tạo tài khoản"
    }

    EXERCISES {
        string code PK "Mã bài tập: squat, deadlift, lunge"
        string name "Tên bài: Barbell Back Squat"
        string category "Phân loại: LOWER_BODY, UPPER_BODY"
        string target_muscles "Nhóm cơ tác động chính (Quadriceps, Glutes)"
        jsonb config_rules "Cấu hình chuẩn góc và ngưỡng lỗi (JSON)"
        string description "Mô tả kỹ thuật chuẩn chỉ"
    }

    ANALYSES {
        uuid id PK "Mã phiên phân tích"
        uuid user_id FK "Liên kết người dùng"
        string exercise_code FK "Liên kết bài tập"
        string raw_video_url "Đường dẫn file video gốc"
        string overlay_video_url "Đường dẫn video đã vẽ khung xương"
        float fps "Tốc độ khung hình (khuyến nghị >= 30)"
        int total_frames "Tổng số khung hình video"
        float duration_seconds "Thời lượng video (giây)"
        int total_reps "Tổng số lần lặp phát hiện được"
        int valid_reps "Số lần lặp đạt chuẩn form"
        float overall_score "Điểm đánh giá tổng thể (thang điểm 100)"
        text ai_summary_report "Báo cáo tổng kết do AI Coach soạn"
        string status "Trạng thái: PENDING, PROCESSING, COMPLETED, FAILED"
        timestamp created_at "Thời điểm tạo"
    }

    REPS {
        uuid id PK "Khóa chính cho mỗi rep"
        uuid analysis_id FK "Thuộc phiên phân tích nào"
        int rep_number "Số thứ tự rep (1, 2, 3...)"
        int start_frame "Frame bắt đầu xuống"
        int bottom_frame "Frame tại điểm đáy (cực tiểu góc gối)"
        int end_frame "Frame đứng thẳng hoàn thành rep"
        float duration_seconds "Thời gian thực hiện rep"
        float min_knee_angle "Góc gối nhỏ nhất đạt được (độ)"
        float max_trunk_lean "Độ nghiêng thân lớn nhất (độ)"
        boolean is_valid "Rep đạt chuẩn (true) hay mắc lỗi (false)"
    }

    FAULTS {
        uuid id PK "Khóa chính lỗi"
        uuid rep_id FK "Lỗi xảy ra ở rep nào"
        string fault_code "Mã lỗi: insufficient_depth, excessive_trunk_lean..."
        string fault_name "Tên lỗi: Chưa xuống đủ sâu, Võng lưng..."
        string severity "Mức độ nghiêm trọng: LOW, MEDIUM, HIGH"
        float measured_value "Giá trị đo được thực tế (ví dụ: 112.5°)"
        float benchmark_value "Giá trị tiêu chuẩn quy định (ví dụ: 100.0°)"
        int evidence_frame "Frame video bằng chứng chụp khoảnh khắc lỗi"
        string corrective_cue "Khẩu lệnh sửa tức thì từ HLV"
    }

    CHAT_MESSAGES {
        uuid id PK "Mã tin nhắn"
        uuid analysis_id FK "Tin nhắn gắn liền ngữ cảnh video nào"
        string sender "Người gửi: user hoặc ai_coach"
        text content "Nội dung trao đổi"
        jsonb tool_calls_data "Log các tool mà AI Agent đã gọi (RAG, metrics)"
        timestamp created_at "Thời điểm gửi"
    }
```

---

## 3. BIỂU ĐỒ TUẦN TỰ (SEQUENCE DIAGRAM)

Mô tả sự tương tác động giữa các thành phần phần mềm theo dòng thời gian.

### 3.1. Luồng 1: Phân tích Video Bài tập (Tải lên $\rightarrow$ Xử lý CV $\rightarrow$ AI Báo cáo)

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 Người dùng
    participant Web as 💻 Next.js Frontend
    participant API as 🚀 FastAPI Gateway
    participant Worker as ⚙️ Core CV Pipeline
    participant DB as 🗄️ PostgreSQL
    participant MultiAgent as 🤖 Multi-Agent System

    User->>Web: 1. Chọn bài Squat & Upload video (.mp4)
    Web->>API: 2. POST /api/analyses (Multipart Form)
    API->>API: 3. Kiểm tra chất lượng (FPS >= 30, Format)
    API->>DB: 4. Tạo bản ghi Analysis (status='PROCESSING')
    API-->>Web: 5. Trả về analysis_id ngay lập tức (HTTP 202 Accepted)
    Web-->>User: 6. Hiển thị màn hình tiến trình phân tích

    API->>Worker: 7. Đẩy tác vụ xử lý video vào tiến trình nền
    Note over Worker: • OpenCV đọc từng khung hình<br/>• MediaPipe trích xuất 33 khớp 3D<br/>• Savitzky-Golay làm mượt chuỗi tọa độ<br/>• Tính góc gối, hông, độ nghiêng thân<br/>• Tách pha Reps & Chạy mô hình Light ML + Rules<br/>• Vẽ video overlay đổi màu khung xương

    Worker->>DB: 8. Lưu thông tin Reps, Faults & Video Overlay URL
    Worker->>MultiAgent: 9. Kích hoạt phân tích AI (truyền danh sách lỗi)

    Note over MultiAgent: • Analysis Agent tổng hợp thống kê lỗi<br/>• Biomechanics Agent tra cứu Y văn RAG (ChromaDB)<br/>• Coaching Agent soạn bài tập phục hồi & Cues

    MultiAgent->>DB: 10. Lưu Báo cáo HLV AI & Cập nhật Analysis (status='COMPLETED')

    loop Polling trạng thái mỗi 2 giây
        Web->>API: 11. GET /api/analyses/{id}
        API->>DB: 12. Truy vấn trạng thái
        DB-->>API: 13. Trả về kết quả hoàn tất
        API-->>Web: 14. Trả về đầy đủ dữ liệu JSON
    end

    Web-->>User: 15. Hiển thị Dashboard hoàn chỉnh:<br/>Video Overlay, Đồ thị góc, 3D Plotly & Báo cáo HLV AI
```

### 3.2. Luồng 2: Chat Hỏi đáp Chuyên sâu với Huấn luyện viên AI

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 Người dùng
    participant Web as 💻 Giao diện Chat
    participant API as 🚀 Chat API Router
    participant Agent as 🤖 Coaching Agent
    participant RAG as 📚 Vector DB (ChromaDB)
    participant DB as 🗄️ Database

    User->>Web: 1. Nhập câu hỏi: "Vì sao rep 2 của tôi lại bị cảnh báo đau lưng?"
    Web->>API: 2. POST /api/analyses/{id}/chat (message, analysis_id)
    API->>Agent: 3. Điều phối câu hỏi kèm ngữ cảnh bài tập
    
    Agent->>DB: 4. Gọi tool `get_rep_details(rep_id=2)`
    DB-->>Agent: 5. Trả về: Lưng ngả 52.8° tại đáy, lỗi excessive_trunk_lean
    
    Agent->>RAG: 6. Gọi tool `search_knowledge("lumbar shear stress squat trunk lean")`
    RAG-->>Agent: 7. Trả về đoạn trích y văn: Ngả lưng quá mức dồn áp lực cắt lên đĩa đệm L4-L5
    
    Note over Agent: Tổng hợp câu trả lời:<br/>1. Chỉ rõ con số góc ngả lưng ở rep 2<br/>2. Giải thích cơ chế áp lực lên cột sống<br/>3. Gợi ý cách khắc phục: Gồng core, bài tập Goblet Squat

    Agent->>DB: 8. Lưu tin nhắn vào bảng CHAT_MESSAGES
    Agent-->>API: 9. Trả về phản hồi dạng văn bản
    API-->>Web: 10. Trả về kết quả cho Frontend
    Web-->>User: 11. Hiển thị câu trả lời tận tình của HLV AI
```

---

## 4. BIỂU ĐỒ HOẠT ĐỘNG (ACTIVITY DIAGRAM)

Biểu đồ hoạt động mô tả luồng công việc logic từ đầu đến cuối của toàn bộ quy trình phân tích:

```mermaid
flowchart TD
    START([Bắt đầu]) --> A1[Người dùng đăng nhập & Chọn bài tập]
    A1 --> A2[Tải lên video thực hiện động tác]
    A2 --> C1{Video có đạt chuẩn không?<br/>FPS >= 30, Rõ người}
    
    C1 -- Không đạt --> E1[Thông báo lỗi & Hướng dẫn quay lại góc chuẩn]
    E1 --> A2
    
    C1 -- Đạt chuẩn --> A3[Trích xuất 33 điểm mốc khớp bằng MediaPipe]
    A3 --> A4[Làm mượt tọa độ bằng bộ lọc Savitzky-Golay]
    A4 --> A5[Tính toán chuỗi góc sinh cơ học theo thời gian]
    A5 --> A6[Nhận diện các pha chuyển động & Tách các Reps]
    
    A6 --> A7[Đánh giá từng Rep bằng Mô hình Light ML & Đối chiếu Tiêu chuẩn]
    A7 --> A8[Tạo Video Overlay có khung xương đổi màu]
    
    A8 --> A9[Multi-Agent truy vấn Y văn RAG & Soạn thảo Báo cáo HLV]
    A9 --> A10[Lưu toàn bộ kết quả vào Cơ sở Dữ liệu]
    A10 --> A11[Hiển thị Dashboard trực quan cho người dùng]
    
    A11 --> C2{Người dùng có câu hỏi thắc mắc?}
    C2 -- Có --> A12[Người dùng chat hỏi đáp chuyên sâu với AI Coach]
    A12 --> END([Kết thúc phiên])
    C2 -- Không --> END
```

---

## 5. BIỂU ĐỒ LỚP (CLASS DIAGRAM) — LÕI XỬ LÝ SINH CƠ HỌC

Thiết kế hướng đối tượng (OOP) cho các mô-đun cốt lõi trong thư mục `backend/app/core/`:

```mermaid
classDiagram
    %% LỚP TỌA ĐỘ VÀ KHUNG HÌNH
    class Landmark {
        +float x
        +float y
        +float z
        +float visibility
    }

    class FramePose {
        +int frame_idx
        +float timestamp
        +List~Landmark~ landmarks
        +List~Landmark~ world_landmarks
        +get_joint(name: str) Landmark
    }

    %% BỘ LỌC TÍN HIỆU
    class SignalFilter {
        <<interface>>
        +apply(series: List~float~) List~float~
    }

    class SavitzkyGolayFilter {
        +int window_length
        +int polyorder
        +apply(series: List~float~) List~float~
    }

    class OneEuroFilter {
        +float min_cutoff
        +float beta
        +filter_stream(val: float, t: float) float
    }

    %% TÍNH TOÁN SINH CƠ HỌC
    class KinematicsEngine {
        +calculate_3point_angle(a: Landmark, b: Landmark, c: Landmark) float
        +calculate_vertical_angle(a: Landmark, b: Landmark) float
        +calculate_knee_valgus_ratio(left_knee, right_knee, left_ankle, right_ankle) float
    }

    %% PHÂN TÁCH PHA VÀ ĐẾM REP
    class RepData {
        +int rep_id
        +int start_frame
        +int bottom_frame
        +int end_frame
        +float duration_s
        +float min_knee_angle
        +float max_trunk_lean
    }

    class RepSegmenter {
        +int min_rep_duration_frames
        +detect_reps(knee_angles: List~float~, fps: float) List~RepData~
    }

    %% ĐÁNH GIÁ VÀ BẮT LỖI
    class BenchmarkRule {
        +str rule_id
        +str metric_name
        +str operator
        +float threshold
        +str severity
        +evaluate(measured_value: float) bool
    }

    class FormEvaluator {
        +List~BenchmarkRule~ rules
        +LightMLModel ml_classifier
        +evaluate_rep(rep: RepData) List~FaultItem~
    }

    %% MỐI QUAN HỆ KẾ THỪA VÀ KẾT TẬP
    SignalFilter <|.. SavitzkyGolayFilter
    SignalFilter <|.. OneEuroFilter
    FramePose *-- Landmark
    KinematicsEngine ..> FramePose
    RepSegmenter ..> RepData
    FormEvaluator o-- BenchmarkRule
    FormEvaluator ..> RepData
```

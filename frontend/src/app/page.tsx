"use client";

import { useEffect, useRef, useState } from "react";

type Rule = { rule_id: string; name: string; status: "finding" | "within_threshold" | "insufficient_data"; measured_value: number | null; benchmark_value: number; operator: string; reason: string | null; evidence_frame: number };
type Rep = { rep_id: number; bottom_time_s: number; start_time_s: number; end_time_s: number; min_knee_angle: number | null; trunk_lean_at_bottom: number | null; assessment: Rule[] };
type Result = { outcome: "reps_detected" | "no_reps_detected" | "insufficient_data"; detected_rep_count: number; reps: Rep[]; coverage: { status: "complete" | "partial"; missing_frames: number; low_visibility_frames?: number }; pose: { detection_rate: number }; video: { duration_s: number; fps: number; camera_view: string }; warnings: (string | null)[] };
type Job = { id: string; status: "queued" | "processing" | "completed" | "failed"; result: Result | null; error: string | null };

const API = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const LIMIT = 100 * 1024 * 1024;
const cues: Record<string, string> = {
  insufficient_depth: "Thử hạ sâu hơn trong biên độ bạn kiểm soát được, giữ chuyển động ổn định.",
  excessive_trunk_lean: "Thử giữ thân ổn định hơn, điều chỉnh tư thế hoặc giảm tải nếu cần.",
};
const statusText = { queued: "Đang chờ xử lý", processing: "Đang phân tích video", completed: "Phân tích hoàn tất", failed: "Phân tích chưa thành công" };
const fmt = (n: number | null | undefined, suffix = "") => typeof n === "number" && Number.isFinite(n) ? `${n.toFixed(1)}${suffix}` : "—";
const time = (n: number) => `${Math.floor(n / 60)}:${String(Math.floor(n % 60)).padStart(2, "0")}`;

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [view, setView] = useState("side_90deg");
  const [job, setJob] = useState<Job | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [connectionError, setConnectionError] = useState(false);
  const [restoring, setRestoring] = useState(true);
  const [selected, setSelected] = useState<number | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const requestRef = useRef(false);

  useEffect(() => {
    const controller = new AbortController();
    let id: string | null = null;
    try { id = localStorage.getItem("biomechanics:last-analysis"); } catch { /* Storage is optional. */ }
    if (!id) { setRestoring(false); return () => controller.abort(); }
    const restore = async () => {
      try {
        const response = await fetch(`${API}/api/v1/analyses/${id}`, { signal: controller.signal, cache: "no-store" });
        if (response.status === 404 || response.status === 422) {
          try { localStorage.removeItem("biomechanics:last-analysis"); } catch { /* Storage is optional. */ }
          if (!controller.signal.aborted) setError("Không tìm thấy lần phân tích trước trên backend hiện tại.");
        } else if (!response.ok) throw new Error("restore failed");
        else { const restored: Job = await response.json(); if (!controller.signal.aborted) setJob(restored); }
      } catch {
        if (!controller.signal.aborted) setError("Chưa thể khôi phục lần phân tích trước. Kiểm tra backend rồi tải lại trang.");
      } finally { if (!controller.signal.aborted) setRestoring(false); }
    };
    void restore();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!job || (job.status !== "queued" && job.status !== "processing")) return;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const response = await fetch(`${API}/api/v1/analyses/${job.id}`, { signal: controller.signal, cache: "no-store" });
        if (response.status === 404 || response.status === 422) {
          try { localStorage.removeItem("biomechanics:last-analysis"); } catch { /* Storage is optional. */ }
          if (!controller.signal.aborted) { setJob(null); setError("Không tìm thấy tác vụ trên backend. Hãy gửi lại video."); }
          return;
        }
        if (!response.ok) throw new Error("poll failed");
        const next: Job = await response.json();
        if (controller.signal.aborted) return;
        setConnectionError(false);
        setJob(next);
        if (next.status === "queued" || next.status === "processing") timer = setTimeout(poll, 2500);
      } catch {
        if (!controller.signal.aborted) { setConnectionError(true); timer = setTimeout(poll, 5000); }
      }
    };
    timer = setTimeout(poll, 1500);
    return () => { controller.abort(); clearTimeout(timer); };
  }, [job?.id, job?.status]);

  function chooseFile(next: File | null) {
    setError("");
    if (next && !/\.(mp4|mov)$/i.test(next.name)) { setError("Vui lòng chọn video MP4 hoặc MOV."); setFile(null); return; }
    if (next && (next.size === 0 || next.size > LIMIT)) { setError("Video phải có dữ liệu và không vượt quá 100 MiB."); setFile(null); return; }
    setFile(next);
  }

  async function submit() {
    if (!file || requestRef.current) return;
    requestRef.current = true;
    setUploading(true); setError(""); setConnectionError(false);
    const form = new FormData();
    form.append("file", file); form.append("exercise_id", "squat"); form.append("camera_view", view);
    try {
      const response = await fetch(`${API}/api/v1/analyses`, { method: "POST", body: form });
      if (!response.ok) {
        const message: Record<number, string> = { 413: "Video vượt quá giới hạn của máy chủ.", 415: "Định dạng video không được hỗ trợ.", 422: "Không đọc được video hoặc thông tin gửi lên không hợp lệ.", 503: "Bộ xử lý hiện chưa sẵn sàng." };
        throw new Error(message[response.status] || `Không thể gửi video (lỗi ${response.status}).`);
      }
      const created: Job = await response.json();
      try { localStorage.setItem("biomechanics:last-analysis", created.id); } catch { /* Storage is optional. */ }
      setSelected(null);
      setJob(created);
    } catch (e) { setError(e instanceof TypeError ? "Mất kết nối khi gửi video. Tác vụ có thể đã được tạo; hãy kiểm tra backend trước khi gửi lại." : e instanceof Error ? e.message : "Có lỗi khi gửi video."); }
    finally { requestRef.current = false; setUploading(false); }
  }

  function selectRep(rep: Rep) {
    setSelected(rep.rep_id);
    if (videoRef.current) { videoRef.current.currentTime = rep.bottom_time_s; videoRef.current.focus(); }
  }
  function forgetLastAnalysis() {
    try { localStorage.removeItem("biomechanics:last-analysis"); } catch { /* Storage is optional. */ }
    setJob(null); setSelected(null); setError(""); setConnectionError(false);
  }
  const busy = restoring || uploading || job?.status === "queued" || job?.status === "processing";
  const result = job?.status === "completed" ? job.result : null;

  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">B<span>.</span></span><div><strong>BIOMECHANICS</strong><small>COACH / PROJECT 3</small></div></div>
      <div className="side-label">KHÔNG GIAN TẬP LUYỆN</div>
      <div className="nav-active"><span className="nav-icon">◫</span> Phân tích động tác <span className="nav-dot" /></div>
      <div className="side-bottom"><span className="side-badge">BẢN THỬ NGHIỆM</span><p>Công cụ hỗ trợ quan sát chuyển động khi tập luyện.</p><div className="side-line" />SOICT · HUST</div>
    </aside>
    <main>
      <header className="topbar"><span>WORKSPACE <b>/</b> PHÂN TÍCH</span><span className="top-right"><i /> MVP V1</span></header>
      <div className="content">
        <div className="heading"><div><div className="eyebrow"><span /> AI BIOMECHANICS COACH</div><h1>Hiểu chuyển động.<br/><em>Tập tốt hơn.</em></h1><p>Tải video squat lên để xem từng rep, số đo và những điểm cần chú ý.</p></div><div className="heading-tag"><div>SQUAT<br/><small>PHÂN TÍCH VIDEO</small></div></div></div>
        <div className="workspace">
          <section className="card upload-card"><div className="card-heading"><div><span className="overline">BẮT ĐẦU TẠI ĐÂY</span><h2>Video của bạn</h2></div><span className="pill">SQUAT</span></div>
            <p className="muted">Một góc quay rõ ràng giúp phân tích hữu ích hơn.</p>
            <input ref={inputRef} id="video-file" type="file" accept=".mp4,.mov,video/mp4,video/quicktime" onChange={e => { chooseFile(e.target.files?.[0] || null); e.target.value = ""; }} disabled={!!busy} className="file-input" />
            <label htmlFor="video-file" className={`dropzone ${busy ? "disabled" : ""}`} onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); if (!busy) chooseFile(e.dataTransfer.files[0] || null); }}>
              <span className="upload-icon" aria-hidden="true">▣</span><strong>{file ? file.name : "Chọn video để phân tích"}</strong><span>{file ? `${(file.size / 1024 / 1024).toFixed(1)} MiB · Chọn lại video` : "hoặc kéo và thả vào đây"}</span><small>MP4 hoặc MOV · tối đa 100 MiB</small>
            </label>
            <label className="field-label" htmlFor="camera">Góc quay của video</label>
            <div className="select-wrap"><select id="camera" value={view} onChange={e => setView(e.target.value)} disabled={!!busy}><option value="side_90deg">Nhìn từ bên hông (khuyến nghị)</option><option value="front_0deg">Nhìn từ phía trước</option><option value="unknown">Không chắc chắn</option></select></div>
            <p className="field-hint">Các số đo hiện hỗ trợ góc quay bên hông; lựa chọn của bạn chưa được xác minh tự động.</p>
            <button className="primary" type="button" onClick={submit} disabled={!file || !!busy}>{restoring ? "Đang khôi phục tác vụ..." : uploading ? "Đang tải video lên..." : busy ? "Đang xử lý..." : "Phân tích video"}</button>
            {error && <p className="message error" role="alert">{error}</p>}
            {job && <div className={`job-status ${job.status}`} role="status"><span className="status-dot"/><div><strong>{statusText[job.status]}</strong><p>{job.status === "queued" ? "Video đã được đưa vào hàng đợi." : job.status === "processing" ? "Đang trích xuất chuyển động và đánh giá từng rep." : job.status === "failed" ? job.error === "interrupted" ? "Tác vụ bị gián đoạn do backend khởi động lại. Hãy tải lại video." : "Hãy kiểm tra backend và model pose, rồi thử lại." : "Bạn có thể xem kết quả bên cạnh."}</p>{connectionError && <p>Đang mất kết nối; hệ thống sẽ tự thử lại.</p>}{!busy && <button type="button" className="forget" onClick={forgetLastAnalysis}>Ẩn kết quả trên trình duyệt</button>}</div></div>}
          </section>
          <section className="card results-card"><div className="card-heading"><div><span className="overline">KẾT QUẢ PHÂN TÍCH</span><h2>{result ? "Xem lại chuyển động" : "Góc nhìn của bạn"}</h2></div><span className="result-index">SQUAT</span></div>
            {!result ? <div className="empty"><div className="empty-symbol" aria-hidden="true"><svg viewBox="0 0 150 150" fill="none"><circle cx="75" cy="75" r="63" stroke="currentColor" strokeDasharray="4 7"/><circle cx="75" cy="75" r="46" stroke="currentColor" opacity=".25"/><circle cx="72" cy="35" r="8" fill="currentColor"/><path d="M72 47 L64 70 L91 77 M64 70 L48 91 L31 99 M91 77 L96 101 L116 106 M66 57 L89 61 L105 52" stroke="currentColor" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"/><circle cx="64" cy="70" r="5" fill="#d8f370"/><circle cx="91" cy="77" r="5" fill="#d8f370"/></svg></div><h3>Mỗi rep đều có câu chuyện.</h3><p>Tải video lên để xem các rep được phát hiện, số đo và thời điểm cần xem lại.</p><div className="empty-tags"><span>VIDEO GỐC</span><span>PHÂN ĐOẠN REP</span><span>GÓC CHUYỂN ĐỘNG</span></div></div> : <div className="results">
              <div className="video-wrap"><video ref={videoRef} controls preload="metadata" src={`${API}/api/v1/analyses/${job?.id}/video`}>Trình duyệt không hỗ trợ phát video.</video></div>
              <div className="result-meta"><div><span>REP ĐƯỢC PHÁT HIỆN</span><strong>{result.detected_rep_count}</strong></div><div><span>THỜI LƯỢNG</span><strong>{fmt(result.video.duration_s, "s")}</strong></div><div><span>NHẬN DIỆN POSE</span><strong>{fmt(result.pose.detection_rate * 100, "%")}</strong></div></div>
              {result.coverage.status === "partial" && <p className="message caution">Video chỉ được phân tích một phần ({result.coverage.missing_frames} frame thiếu hoặc không hợp lệ; một số đoạn ngắn cũng có thể bị bỏ qua). Kết quả có thể chưa đầy đủ.</p>}
              {!!result.coverage.low_visibility_frames && <p className="message caution">Có {result.coverage.low_visibility_frames} frame với điểm khớp quan sát kém; kết quả có thể không đáng tin cậy.</p>}
              {result.video.camera_view !== "side_90deg" && <p className="message caution">Góc quay đã chọn chưa hỗ trợ đánh giá các số đo bên hông.</p>}
              {result.video.fps < 30 && <p className="message caution">Video có {fmt(result.video.fps)} FPS, thấp hơn mức khuyến nghị 30 FPS.</p>}
              {result.outcome === "no_reps_detected" && <p className="message caution">Không phát hiện rep trong dữ liệu phân tích. Điều này không khẳng định video không có rep.</p>}
              {result.outcome === "insufficient_data" && <p className="message caution">Không đủ dữ liệu để phân tích. Hãy thử video có đủ cơ thể và ánh sáng rõ hơn.</p>}
              {result.reps.length > 0 && <><div className="section-title"><div><span className="overline">CHI TIẾT</span><h3>Các rep phát hiện</h3></div><span>Nhấn để tua đến đáy</span></div><div className="reps">{result.reps.map(rep => <article className={`rep ${selected === rep.rep_id ? "selected" : ""}`} key={rep.rep_id}><button type="button" className="rep-header" onClick={() => selectRep(rep)}><span className="rep-number">{String(rep.rep_id).padStart(2, "0")}</span><span><strong>Rep {rep.rep_id}</strong><small>Điểm đáy · {time(rep.bottom_time_s)}</small></span><span className="seek">Xem video</span></button><div className="measurements"><span>Góc gối ở đáy <b>{fmt(rep.assessment.find(r => r.rule_id === "insufficient_depth")?.measured_value, "°")}</b></span><span>Độ ngả thân ở đáy <b>{fmt(rep.assessment.find(r => r.rule_id === "excessive_trunk_lean")?.measured_value, "°")}</b></span></div><div className="rules">{rep.assessment.map(rule => <div className="rule" key={rule.rule_id}><div className="rule-title"><strong>{rule.name}</strong><span className={`rule-status ${rule.status}`}>{rule.status === "finding" ? "Cần chú ý" : rule.status === "within_threshold" ? "Trong ngưỡng thử nghiệm" : "Chưa đủ dữ liệu"}</span></div>{rule.measured_value !== null && <p>Số đo {fmt(rule.measured_value, "°")} · Ngưỡng so sánh {fmt(rule.benchmark_value, "°")}</p>}{rule.status === "finding" && cues[rule.rule_id] && <p className="cue">{cues[rule.rule_id]}</p>}{rule.status === "insufficient_data" && <p>Chưa thể đánh giá quy tắc này từ góc quay hoặc chất lượng pose hiện tại.</p>}</div>)}</div></article>)}</div></>}
              <p className="disclaimer">Các ngưỡng đang trong giai đoạn thử nghiệm; kết quả chỉ hỗ trợ tham khảo, không phải chẩn đoán y khoa. Số rep có thể bị bỏ sót. Mốc thời gian được tính theo FPS danh nghĩa và có thể lệch trên một số video.</p>
            </div>}
          </section>
        </div>
        <section className="guide"><div><span className="overline">TRƯỚC KHI BẮT ĐẦU</span><h2>Quay đúng, nhìn rõ hơn.</h2><p>Chuẩn bị video đơn giản để hệ thống quan sát được chuyển động của bạn.</p></div><div className="guide-item"><span>◉</span><strong>Chọn góc bên hông</strong><p>Đặt camera ngang hông, cách khoảng 2–3 m.</p></div><div className="guide-item"><span>▣</span><strong>Giữ trọn cơ thể</strong><p>Đảm bảo đầu và bàn chân đều nằm trong khung hình.</p></div><div className="guide-item"><span>◷</span><strong>Giữ khung hình ổn định</strong><p>Đủ sáng, tránh che khuất; nên quay từ 30 FPS.</p></div></section>
        <footer><span>BIOMECHANICS COACH <b>·</b> PROJECT 3</span><span>Video lưu trên máy chạy backend, chưa tự động xóa. Trình duyệt lưu ID tác vụ gần nhất.</span></footer>
      </div>
    </main>
  </div>;
}

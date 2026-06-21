import { useState, useEffect, useRef, useCallback } from "react";
import { useQuery, useMutation, useQueryClient, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  Upload, FileText, Cpu, Trophy, MessageSquare,
  CheckCircle, XCircle, Loader2, ChevronRight,
  Zap, BarChart3, Send, Bot, User, AlertCircle
} from "lucide-react";

const API = "http://localhost:8000";
const WS  = "ws://localhost:8000";

const queryClient = new QueryClient();
export default function AppWrapper() {
  return <QueryClientProvider client={queryClient}><App /></QueryClientProvider>;
}

// ─── API helpers ────────────────────────────────────────────────────────────

async function uploadPDF(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API}/api/upload`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

async function fetchStatus() {
  const res = await fetch(`${API}/api/status`);
  if (!res.ok) throw new Error("Status fetch failed");
  return res.json();
}

async function fetchResults() {
  const res = await fetch(`${API}/api/results`);
  if (!res.ok) throw new Error("Results fetch failed");
  return res.json();
}

// ─── Main App ───────────────────────────────────────────────────────────────

function App() {
  const [phase, setPhase] = useState("upload"); // upload | optimizing | complete
  const [docId, setDocId]   = useState(null);
  const [fileName, setFileName] = useState("");
  const qc = useQueryClient();

  // Poll /api/status while optimizing
  const { data: status } = useQuery({
    queryKey: ["status"],
    queryFn: fetchStatus,
    refetchInterval: (data) => {
      if (!docId) return false;
      if (data?.status === "complete" || data?.status === "failed") return false;
      return 2000;
    },
    enabled: !!docId,
  });

  // Fetch results once complete
  const { data: results } = useQuery({
    queryKey: ["results"],
    queryFn: fetchResults,
    enabled: phase === "complete",
  });

  // Watch status transitions
  useEffect(() => {
    if (!status) return;
    if (status.status === "complete" && phase === "optimizing") setPhase("complete");
    if (status.status === "failed"   && phase === "optimizing") setPhase("failed");
  }, [status, phase]);

  const uploadMutation = useMutation({
    mutationFn: uploadPDF,
    onSuccess: (data) => {
      setDocId(data.doc_id);
      setPhase("optimizing");
      qc.invalidateQueries(["status"]);
    },
  });

  const handleFile = (file) => {
    if (!file || !file.name.endsWith(".pdf")) return;
    setFileName(file.name);
    uploadMutation.mutate(file);
  };

  return (
    <div className="app-root">
      <Header phase={phase} />
      <main className="main-content">
        {phase === "upload"      && <UploadZone onFile={handleFile} mutation={uploadMutation} />}
        {phase === "optimizing"  && <OptimizingView status={status} fileName={fileName} />}
        {phase === "complete"    && <CompleteView results={results} fileName={fileName} />}
        {phase === "failed"      && <FailedView status={status} onReset={() => { setPhase("upload"); setDocId(null); }} />}
      </main>
    </div>
  );
}

// ─── Header ─────────────────────────────────────────────────────────────────

function Header({ phase }) {
  const steps = [
    { id: "upload",      label: "Upload",    icon: Upload },
    { id: "optimizing",  label: "Optimizing",icon: Cpu },
    { id: "complete",    label: "Chat",      icon: MessageSquare },
  ];
  const idx = steps.findIndex(s => s.id === phase);

  return (
    <header className="header">
      <div className="header-inner">
        <div className="logo" onClick={() => navigate("/")} style={{ cursor: "pointer" }}>
          <Zap size={20} className="logo-icon" />
          <span className="logo-text">RAG Optimizer</span>
        </div>
        <nav className="stepper">
          {steps.map((step, i) => {
            const Icon = step.icon;
            const state = i < idx ? "done" : i === idx ? "active" : "pending";
            return (
              <div key={step.id} className="step-item">
                <div className={`step-dot step-dot--${state}`}>
                  {state === "done" ? <CheckCircle size={14} /> : <Icon size={14} />}
                </div>
                <span className={`step-label step-label--${state}`}>{step.label}</span>
                {i < steps.length - 1 && <ChevronRight size={14} className="step-arrow" />}
              </div>
            );
          })}
        </nav>
      </div>
    </header>
  );
}

// ─── Upload Zone ─────────────────────────────────────────────────────────────

function UploadZone({ onFile, mutation }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef();

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) onFile(file);
  };

  return (
    <div className="upload-page">
      <div className="upload-hero">
        <h1 className="upload-title">Drop your document.<br />We'll find the best way to read it.</h1>
        <p className="upload-sub">
          The optimizer tests multiple retrieval configurations against your PDF
          and automatically selects the one that answers questions most accurately.
        </p>
      </div>

      <div
        className={`upload-zone ${dragging ? "upload-zone--drag" : ""} ${mutation.isPending ? "upload-zone--loading" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !mutation.isPending && inputRef.current?.click()}
      >
        <input
          ref={inputRef} type="file" accept=".pdf"
          style={{ display: "none" }}
          onChange={(e) => onFile(e.target.files[0])}
        />
        {mutation.isPending ? (
          <div className="upload-zone-inner">
            <Loader2 size={40} className="spin upload-zone-icon" />
            <p className="upload-zone-label">Uploading…</p>
          </div>
        ) : (
          <div className="upload-zone-inner">
            <FileText size={40} className="upload-zone-icon" />
            <p className="upload-zone-label">Drag a PDF here or <span className="upload-link">browse</span></p>
            <p className="upload-zone-hint">Legal contracts, research papers, manuals — any text PDF</p>
          </div>
        )}
      </div>

      {mutation.isError && (
        <div className="error-banner">
          <AlertCircle size={16} />
          <span>{mutation.error?.message}</span>
        </div>
      )}

      <div className="feature-row">
        {[
          { icon: Cpu,      label: "4–8 variants tested",     sub: "Different chunk sizes and retrieval depths" },
          { icon: BarChart3, label: "LLM-graded evaluation",  sub: "Judge scores faithfulness, completeness, conciseness" },
          { icon: Trophy,   label: "Winner auto-promoted",    sub: "Best config locked in before you chat" },
        ].map(({ icon: Icon, label, sub }) => (
          <div key={label} className="feature-card">
            <Icon size={20} className="feature-icon" />
            <p className="feature-label">{label}</p>
            <p className="feature-sub">{sub}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Optimizing View ─────────────────────────────────────────────────────────

const STAGES = [
  { key: "ingesting",   label: "Extracting & chunking document",  match: /ingesting|extracting|chunking/i },
  { key: "building",    label: "Building variant configurations",  match: /building|variants/i },
  { key: "evaluating",  label: "Evaluating with LLM judge",        match: /evaluat|scoring/i },
  { key: "complete",    label: "Selecting winner",                  match: /complete|winner|selecting/i },
];

function OptimizingView({ status, fileName }) {
  const message = status?.message || "";

  const activeIdx = (() => {
    if (status?.status === "complete") return STAGES.length;
    for (let i = STAGES.length - 1; i >= 0; i--) {
      if (STAGES[i].match.test(message)) return i;
    }
    return 0;
  })();

  const pct = Math.min(100, Math.round((activeIdx / STAGES.length) * 100));

  return (
    <div className="opt-page">
      <div className="opt-header">
        <Cpu size={32} className="opt-icon spin-slow" />
        <div>
          <h2 className="opt-title">Optimizing for your document</h2>
          <p className="opt-file">{fileName}</p>
        </div>
      </div>

      <div className="progress-track">
        <div className="progress-bar" style={{ width: `${pct}%` }} />
      </div>
      <p className="progress-pct">{pct}%</p>

      <div className="stages">
        {STAGES.map((stage, i) => {
          const state = i < activeIdx ? "done" : i === activeIdx ? "active" : "pending";
          return (
            <div key={stage.key} className={`stage stage--${state}`}>
              <div className="stage-dot">
                {state === "done"   ? <CheckCircle size={16} /> :
                 state === "active" ? <Loader2 size={16} className="spin" /> :
                                      <div className="stage-empty" />}
              </div>
              <span className="stage-label">{stage.label}</span>
            </div>
          );
        })}
      </div>

      {message && (
        <div className="opt-message">
          <span className="opt-message-dot" />
          {message}
        </div>
      )}

      <p className="opt-note">This takes 2–5 minutes. You can leave this tab open.</p>
    </div>
  );
}

// ─── Complete View ────────────────────────────────────────────────────────────

function CompleteView({ results }) {
  const [tab, setTab] = useState("chat");

  return (
    <div className="complete-page">
      <div className="complete-banner">
        <CheckCircle size={20} className="banner-check" />
        <div>
          <p className="banner-title">Optimization complete</p>
          {results?.winner_config && (
            <p className="banner-sub">
              Winner: <strong>{results.winner_config.variant_id}</strong> — score {results.winner_config.final_score?.toFixed(1)}/10
            </p>
          )}
        </div>
      </div>

      <div className="tabs">
        <button className={`tab ${tab === "chat" ? "tab--active" : ""}`} onClick={() => setTab("chat")}>
          <MessageSquare size={15} /> Chat
        </button>
        <button className={`tab ${tab === "scores" ? "tab--active" : ""}`} onClick={() => setTab("scores")}>
          <BarChart3 size={15} /> Scoreboard
        </button>
        <button className={`tab ${tab === "config" ? "tab--active" : ""}`} onClick={() => setTab("config")}>
          <Trophy size={15} /> Winning config
        </button>
      </div>

      <div className="tab-panel">
        {tab === "chat"   && <ChatPanel />}
        {tab === "scores" && <ScoreboardPanel results={results} />}
        {tab === "config" && <ConfigPanel config={results?.winner_config} />}
      </div>
    </div>
  );
}

// ─── Chat Panel ───────────────────────────────────────────────────────────────

function ChatPanel() {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "I've been optimized for your document. Ask me anything about it." }
  ]);
  const [input, setInput]       = useState("");
  const [streaming, setStreaming] = useState(false);
  const wsRef   = useRef(null);
  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  // Auto-scroll on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Connect WebSocket once
  useEffect(() => {
    const ws = new WebSocket(`${WS}/ws/chat`);
    wsRef.current = ws;

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === "token") {
        setMessages(prev => {
          const last = prev[prev.length - 1];
          if (last?.role === "assistant" && last?.streaming) {
            return [...prev.slice(0, -1), { ...last, content: last.content + data.content }];
          }
          return [...prev, { role: "assistant", content: data.content, streaming: true }];
        });
      } else if (data.type === "done") {
        setMessages(prev => {
          const last = prev[prev.length - 1];
          if (last?.streaming) return [...prev.slice(0, -1), { ...last, streaming: false }];
          return prev;
        });
        setStreaming(false);
        setTimeout(() => inputRef.current?.focus(), 50);
      } else if (data.type === "error") {
        setMessages(prev => [...prev, { role: "error", content: data.content }]);
        setStreaming(false);
      }
    };

    ws.onerror = () => {
      setMessages(prev => [...prev, { role: "error", content: "WebSocket connection failed. Is the backend running?" }]);
    };

    return () => ws.close();
  }, []);

  const send = () => {
    const q = input.trim();
    if (!q || streaming || wsRef.current?.readyState !== WebSocket.OPEN) return;
    setMessages(prev => [...prev, { role: "user", content: q }]);
    setInput("");
    setStreaming(true);
    wsRef.current.send(JSON.stringify({ question: q }));
  };

  const onKey = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } };

  return (
    <div className="chat-wrap">
      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`msg msg--${msg.role}`}>
            <div className="msg-avatar">
              {msg.role === "user"      ? <User size={14} /> :
               msg.role === "assistant" ? <Bot  size={14} /> :
                                          <AlertCircle size={14} />}
            </div>
            <div className="msg-bubble">
              <p className="msg-text">{msg.content}</p>
              {msg.streaming && <span className="cursor" />}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-row">
        <textarea
          ref={inputRef}
          className="chat-input"
          placeholder="Ask about your document…"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={onKey}
          rows={1}
          disabled={streaming}
        />
        <button
          className={`chat-send ${streaming || !input.trim() ? "chat-send--disabled" : ""}`}
          onClick={send}
          disabled={streaming || !input.trim()}
        >
          {streaming ? <Loader2 size={18} className="spin" /> : <Send size={18} />}
        </button>
      </div>
    </div>
  );
}

// ─── Scoreboard Panel ─────────────────────────────────────────────────────────

function ScoreboardPanel({ results }) {
  if (!results?.scoreboard) {
    return <p className="empty-note">Scoreboard data not available.</p>;
  }

  // Compute per-variant averages
  const rows = Object.entries(results.scoreboard).map(([variant_id, questions]) => {
    const avg = (key) => (questions.reduce((s, q) => s + (q[key] || 0), 0) / questions.length).toFixed(1);
    return {
      variant_id,
      faithfulness: avg("faithfulness"),
      completeness: avg("completeness"),
      conciseness:  avg("conciseness"),
      average:      avg("average"),
    };
  }).sort((a, b) => b.average - a.average);

  const winner = results?.winner_config?.variant_id;

  return (
    <div className="scoreboard">
      <table className="score-table">
        <thead>
          <tr>
            <th>Variant</th>
            <th>Faithfulness</th>
            <th>Completeness</th>
            <th>Conciseness</th>
            <th>Average</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={row.variant_id} className={row.variant_id === winner ? "score-row--winner" : ""}>
              <td className="variant-cell">
                {i === 0 && <Trophy size={13} className="trophy-icon" />}
                <span className="variant-name">{row.variant_id}</span>
              </td>
              <td><ScorePill value={row.faithfulness} /></td>
              <td><ScorePill value={row.completeness} /></td>
              <td><ScorePill value={row.conciseness}  /></td>
              <td><ScorePill value={row.average} bold /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ScorePill({ value, bold }) {
  const v = parseFloat(value);
  const cls = v >= 8 ? "pill--high" : v >= 6 ? "pill--mid" : "pill--low";
  return <span className={`pill ${cls} ${bold ? "pill--bold" : ""}`}>{value}</span>;
}

// ─── Config Panel ─────────────────────────────────────────────────────────────

function ConfigPanel({ config }) {
  if (!config) return <p className="empty-note">No config data available.</p>;

  const fields = [
    { label: "Variant ID",      value: config.variant_id },
    { label: "Chunk size",      value: `${config.chunk_size} tokens` },
    { label: "Chunk overlap",   value: `${config.chunk_overlap} tokens` },
    { label: "Top-K retrieved", value: config.top_k },
    { label: "Collection",      value: config.collection_name },
    { label: "Final score",     value: `${config.final_score?.toFixed(2)} / 10` },
  ];

  return (
    <div className="config-panel">
      <p className="config-intro">
        These settings were automatically selected because they produced the highest average score
        across faithfulness, completeness, and conciseness.
      </p>
      <dl className="config-list">
        {fields.map(({ label, value }) => (
          <div key={label} className="config-row">
            <dt className="config-key">{label}</dt>
            <dd className="config-val">{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

// ─── Failed View ──────────────────────────────────────────────────────────────

function FailedView({ status, onReset }) {
  return (
    <div className="failed-page">
      <XCircle size={40} className="failed-icon" />
      <h2 className="failed-title">Optimization failed</h2>
      <p className="failed-msg">{status?.error || "An unknown error occurred."}</p>
      <button className="retry-btn" onClick={onReset}>Try another file</button>
    </div>
  );
}

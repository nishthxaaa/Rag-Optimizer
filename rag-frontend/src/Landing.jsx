import { useNavigate } from "react-router-dom";
import { Zap, FileText, Cpu, MessageSquare, ChevronRight, Github } from "lucide-react";

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="landing">
      <LandingNav />
      <Hero navigate={navigate} />
      <HowItWorks />
      <TechStack />
      <Footer />
    </div>
  );
}

function LandingNav() {
  const navigate = useNavigate();
  return (
    <nav className="l-nav">
      <div className="l-nav-inner">
        <div className="logo">
          <Zap size={18} className="logo-icon" />
          <span className="logo-text">RAG Optimizer</span>
        </div>
        <div className="l-nav-links">
          <a href="#how-it-works" className="l-nav-link">How it works</a>
          <a href="#stack" className="l-nav-link">Tech stack</a>
          <a
            href="https://github.com/nishthxaaa/rag-optimizer"
            target="_blank"
            rel="noreferrer"
            className="l-nav-link l-nav-link--icon"
          >
            <Github size={16} /> GitHub
          </a>
          <button className="l-btn l-btn--sm" onClick={() => navigate("/app")}>
            Try it <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </nav>
  );
}

function Hero({ navigate }) {
  return (
    <section className="l-hero">
      <div className="l-hero-inner">
        <div className="l-badge">
          <Zap size={12} />
          Self-optimizing RAG pipeline
        </div>
        <h1 className="l-title">
          Your document deserves<br />
          <span className="l-title-accent">a custom AI.</span>
        </h1>
        <p className="l-subtitle">
          Upload any PDF and the system automatically tests multiple retrieval
          configurations, scores them with an LLM judge, and locks in the best
          one — before you ask a single question.
        </p>
        <div className="l-hero-actions">
          <button className="l-btn l-btn--primary" onClick={() => navigate("/app")}>
            Try it now <ChevronRight size={16} />
          </button>
          <a
            href="https://github.com/nishthxaaa/rag-optimizer"
            target="_blank"
            rel="noreferrer"
            className="l-btn l-btn--ghost"
          >
            <Github size={16} /> View on GitHub
          </a>
        </div>
        <div className="l-hero-stats">
          {[
            { value: "6",    label: "configs tested"      },
            { value: "3",    label: "evaluation criteria"  },
            { value: "100%", label: "automatic"            },
          ].map(({ value, label }) => (
            <div key={label} className="l-stat">
              <span className="l-stat-value">{value}</span>
              <span className="l-stat-label">{label}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function HowItWorks() {
  const steps = [
    {
      icon: FileText,
      number: "01",
      title: "Upload your document",
      body: "Drop any PDF into the interface. The system extracts the full text and prepares it for optimization.",
    },
    {
      icon: Cpu,
      number: "02",
      title: "Automatic optimization",
      body: "Six RAG configurations are tested in parallel. An LLM judge scores each one on faithfulness, completeness, and conciseness.",
    },
    {
      icon: MessageSquare,
      number: "03",
      title: "Chat with confidence",
      body: "The winning configuration is promoted to production. Every answer is grounded in the retrieval strategy that worked best for your specific document.",
    },
  ];

  return (
    <section className="l-section" id="how-it-works">
      <div className="l-section-inner">
        <p className="l-eyebrow">How it works</p>
        <h2 className="l-section-title">From upload to optimized chat in minutes</h2>
        <div className="l-steps">
          {steps.map(({ icon: Icon, number, title, body }, i) => (
            <div key={number} className="l-step">
              <div className="l-step-number">{number}</div>
              <div className="l-step-icon-wrap">
                <Icon size={22} className="l-step-icon" />
              </div>
              <h3 className="l-step-title">{title}</h3>
              <p className="l-step-body">{body}</p>
              {i < steps.length - 1 && (
                <ChevronRight size={18} className="l-step-arrow" />
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function TechStack() {
  const stack = [
    { layer: "Frontend",      tech: "React 18 + Vite",             sub: "React Query for polling"  },
    { layer: "Backend",       tech: "FastAPI + Python",             sub: "Async background tasks"   },
    { layer: "LLM",           tech: "Groq (llama-3.1-8b-instant)", sub: "Judge + chat responses"   },
    { layer: "Embeddings",    tech: "HuggingFace MiniLM",          sub: "Local, no API cost"        },
    { layer: "Vector DB",     tech: "ChromaDB",                    sub: "Persistent local storage"  },
    { layer: "Orchestration", tech: "LangChain",                   sub: "RAG chain assembly"        },
  ];

  return (
    <section className="l-section l-section--alt" id="stack">
      <div className="l-section-inner">
        <p className="l-eyebrow">Tech stack</p>
        <h2 className="l-section-title">Built with modern AI tooling</h2>
        <div className="l-stack-grid">
          {stack.map(({ layer, tech, sub }) => (
            <div key={layer} className="l-stack-card">
              <p className="l-stack-layer">{layer}</p>
              <p className="l-stack-tech">{tech}</p>
              <p className="l-stack-sub">{sub}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Footer() {
  const navigate = useNavigate();
  return (
    <footer className="l-footer">
      <div className="l-footer-inner">
        <div className="logo">
          <Zap size={16} className="logo-icon" />
          <span className="logo-text">RAG Optimizer</span>
        </div>
        <p className="l-footer-copy">
          Built to prove that retrieval configuration is a hyperparameter, not a guess.
        </p>
        <div className="l-footer-links">
          <a
            href="https://github.com/nishthxaaa/rag-optimizer"
            target="_blank"
            rel="noreferrer"
            className="l-nav-link l-nav-link--icon"
          >
            <Github size={14} /> GitHub
          </a>
          <button className="l-btn l-btn--sm" onClick={() => navigate("/app")}>
            Try it <ChevronRight size={13} />
          </button>
        </div>
      </div>
    </footer>
  );
}
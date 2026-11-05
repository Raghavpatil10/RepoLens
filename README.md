# RepoLens 

> **Insert Repo Link to Scan Repository** 👾
>
> Paste any public GitHub repository URL, and get back an arcade-themed structured technical audit: detected code issues, security vulnerabilities, and an optional AI-generated plain-language summary.

---

## Overview

RepoLens combines deterministic static analysis with a retro 8-bit cyber-arcade aesthetic. It shallow-clones a public repository, runs static analysis, AST inspection, security audits (via Bandit), and dependency vulnerability checks (via pip-audit), and surfaces findings in a dynamic React dashboard.

### Key Features
- 🕹️ **Retro Arcade UI:** Built with React & Vite, featuring custom pixel typography (`Press Start 2P`, `VT323`), CRT scanlines, neon accents, and interactive category filters.
- 💥 **Accurate Bug & Syntax Detection:** Catches real Python `SyntaxError`s, undefined variables, mutable default arguments, unreachable dead code, duplicate dictionary keys, and Ruff linter findings.
- 🛡️ **Security & Secret Scanner:** Detects exposed API keys (OpenAI, AWS, GitHub, Stripe, Slack, Private Keys) alongside Bandit security vulnerability scans.
- ⚙️ **Multi-Language & Config Validator:** Validates JSON and YAML syntax for configuration and CI/CD pipelines, plus JavaScript/TypeScript runtime anti-patterns.
- 🤖 **Executive Technical Summary:** Synthesizes structured findings into an actionable summary using Claude or intelligent local heuristics.
- 🕸️ **Workflow Diagram:** Interactive visual representation of repository module architecture using React Flow.

---

## Tech Stack
- **Frontend**: React, CSS, Lucide React
- **Backend**: Python 3.10+, FastAPI, Uvicorn
- **Error & Linter Tools**: Ruff, Python AST parser
- **Security Tools**: Secret Scanner, Bandit, pip-audit

---

## Folder Structure

```
repolens/
├── README.md
├── .gitignore
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── tests/
│   │   └── test_error_detection.py # Automated test suite for error detection
│   └── app/
│       ├── main.py                # FastAPI app entrypoint & CORS config
│       ├── models.py              # Pydantic schemas — the API data contract
│       ├── routes/
│       │   └── analyze.py         # POST /analyze — the analysis endpoint
│       └── services/
│           ├── cloner.py          # Shallow-clones the repo, cleans up temp files
│           ├── discovery.py       # Walks files, detects languages, counts LOC
│           ├── linter.py          # Ruff linter runner for real bug detection
│           ├── secret_scan.py     # Scans for exposed API keys & credentials
│           ├── config_validator.py# JSON and YAML syntax validation
│           ├── js_ts_analysis.py  # JavaScript/TypeScript bug and pattern analysis
│           ├── static_analysis.py # AST inspection: syntax errors, mutable defaults, complexity
│           ├── security_scan.py   # Wraps Bandit for Python security scans
│           ├── dependency_scan.py # Parses requirements.txt, runs pip-audit
│           ├── evidence.py        # Assembles structured evidence & scores
│           └── ai_explainer.py    # Executive summary generation (Claude or fallback)
└── frontend/
    ├── index.html                 # HTML shell with Google Fonts
    ├── package.json               # React dependencies & scripts
    ├── vite.config.js             # Vite configuration
    └── src/
        ├── main.jsx               # React DOM root
        ├── App.jsx                # Arcade dashboard, category tabs, & findings
        └── index.css              # Cyber-arcade styling, glow animations, scanlines
```

---

## How Data Flows

```
GitHub Repo URL
   │
   ▼
1. cloner.py            ── Shallow clone into an isolated temp directory
   │
   ▼
2. discovery.py         ── Scan files & calculate language breakdown
   │
   ▼
3. static_analysis.py   ── AST inspection: code quality, cyclomatic complexity
   │
   ▼
4. security_scan.py     ── Bandit static security analysis
   │
   ▼
5. dependency_scan.py   ── Dependency CVE check (pip-audit on requirements.txt)
   │
   ▼
6. evidence.py          ── Aggregate structured JSON results
   │
   ▼
7. diagram_generator.py ── Build AST dependency graph for React Flow visualization
   │
   ▼
8. ai_explainer.py      ── (Optional) Claude analyzes the JSON and writes a summary
   │
   ▼
9. React Frontend (UI)  ── Renders cards, code issues, security findings, diagrams and advice
```

---

## Getting Started

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm**
- **Git** installed and available on your system `PATH`

---

### 1. Backend Setup (FastAPI)

Open a terminal and set up the Python virtual environment:

```bash
cd backend
python3 -m venv env
source env/bin/activate        # On Windows: env\Scripts\activate
pip install -r requirements.txt
```
> **Note:** It is highly recommended to use a virtual environment to avoid dependency conflicts.

*(Optional)* Configure the Anthropic Claude API key for AI summaries:
```bash
cp .env.example .env
# Edit .env and set: ANTHROPIC_API_KEY=your_key_here
```

Start the backend API server:
```bash
# From the backend directory:
uvicorn app.main:app --reload

# Or from the project root:
uvicorn backend.app.main:app --reload
```

- API Base URL: `http://127.0.0.1:8000`
- Interactive Swagger Docs: `http://127.0.0.1:8000/docs`

---

### 2. Frontend Setup (React + Vite)

Open a second terminal window:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## Usage

1. Launch both the backend and frontend servers.
2. Navigate to `http://localhost:5173`.
3. Paste any public GitHub repository link (e.g. `https://github.com/psf/requests` or your own repository).
4. Click **ANALYZE** (or press `Enter`).
5. Review the **Code Issues**, **Security Vulnerabilities**, and **AI Summary**.

---

## Technical Details & Tradeoffs

- **Deterministic Core:** Language breakdown, line counts, function/class counters, Radon cyclomatic complexity, Bandit security findings, and pip-audit vulnerability lookups are 100% deterministic. Real engineering tools do the heavy lifting.
- **Graceful Degradation:** If `ANTHROPIC_API_KEY` is omitted, all security and code analysis scans run normally; only the AI prose summary is skipped.
- **Safe Isolation:** Cloned repositories are written to temporary system directories and cleanly wiped after the audit finishes.

---

## Roadmap

- [ ] Support for JavaScript / TypeScript AST analysis (via Tree-sitter).
- [ ] Background job queue (Celery / Redis) with polling for scanning very large repositories.
- [ ] Secret detection via tools like `gitleaks` or `detect-secrets`.
- [ ] Dependency scanning support for `package.json`, `pnpm-lock.yaml`, and `go.mod`.
- [x] Interactive call graph and architecture diagram generation.

---


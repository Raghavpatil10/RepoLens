# RepoLens 👾 

> **Insert Repo Link to Scan Repository** 👾
>
> Paste any public GitHub repository URL, and get back an arcade-themed structured technical audit: detected code issues, security vulnerabilities, and an optional AI-generated plain-language summary.

---

## Overview

RepoLens combines deterministic static analysis with a retro 8-bit cyber-arcade aesthetic. It shallow-clones a public repository, runs static analysis, AST inspection, security audits (via Bandit), and dependency vulnerability checks (via pip-audit), and surfaces findings in a dynamic React dashboard.

### Key Features
- 🕹️ **Retro Arcade UI:** Built with React & Vite, featuring custom pixel typography (`Press Start 2P`, `VT323`), CRT scanlines, neon accents, and responsive status tags.
- 🐛 **Code Issues Inspection:** Detects code quality issues, cyclomatic complexity (via Radon), deep nesting, and anti-patterns with precise file paths, line numbers, and suggestions.
- 🛡️ **Security Vulnerabilities:** Identifies security risks and bandit test findings with assigned severity levels (Critical, High, Medium, Low).
- 🤖 **AI Summary (Optional):** Synthesizes structured technical evidence into clear, actionable prose using Claude (Anthropic API).

---

## Tech Stack
- **Frontend**: React, Vite, CSS
- **Backend**: Python, FastAPI
- **Security Tools**: Bandit, pip-audit

---

## Folder Structure

```
repolens/
├── README.md
├── .gitignore
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   └── app/
│       ├── main.py                # FastAPI app entrypoint & CORS config
│       ├── models.py              # Pydantic schemas — the API data contract
│       ├── routes/
│       │   └── analyze.py         # POST /analyze — the analysis endpoint
│       └── services/
│           ├── cloner.py          # Shallow-clones the repo, cleans up temp files
│           ├── discovery.py       # Walks files, detects languages, counts LOC
│           ├── static_analysis.py # AST parsing, nested loops, complexity (radon)
│           ├── security_scan.py   # Wraps Bandit for Python security scans
│           ├── dependency_scan.py # Parses requirements.txt, runs pip-audit
│           ├── evidence.py        # Assembles structured evidence & scores
│           └── ai_explainer.py    # Sends structured findings to Claude (optional)
└── frontend/
    ├── index.html                 # HTML shell with Google Fonts
    ├── package.json               # React dependencies & scripts
    ├── vite.config.js             # Vite configuration
    └── src/
        ├── main.jsx               # React DOM root
        ├── App.jsx                # Arcade dashboard, search, & results view
        └── index.css              # Cyber-arcade styling, scanlines, animations
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
7. ai_explainer.py      ── (Optional) Claude analyzes the JSON and writes a summary
   │
   ▼
8. React Frontend (UI)  ── Renders cards, code issues, security findings, and advice
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
- [ ] Interactive call graph and architecture diagram generation.

# RepoLens (MVP)

Paste a public GitHub repo URL, get back a structured technical audit: project
overview, code issues, security findings, dependency vulnerabilities, and an
optional AI-generated plain-language summary.

This is the v1 scope from the build plan: **Python-only**, deterministic
analysis first, AI layer on top. Architecture diagrams, multi-language
support, and the bug-risk ML model are intentionally deferred — see
"Next steps" at the bottom.

## Folder structure

```
repolens/
├── README.md
├── .gitignore
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   └── app/
│       ├── main.py                # FastAPI app entrypoint
│       ├── models.py              # Pydantic schemas — the JSON contract
│       ├── services/
│       │   ├── cloner.py          # shallow-clones the repo, cleans up after
│       │   ├── discovery.py       # walks files, detects language, counts LOC
│       │   ├── static_analysis.py # AST parsing: long functions, nested
│       │   │                      #   loops, query-in-loop heuristic, radon
│       │   │                      #   cyclomatic complexity
│       │   ├── security_scan.py   # wraps Bandit
│       │   ├── dependency_scan.py # parses requirements.txt, wraps pip-audit
│       │   ├── evidence.py        # assembles everything + health scores
│       │   └── ai_explainer.py    # sends structured evidence to Claude
│       └── routes/
│           └── analyze.py         # POST /analyze — the one endpoint
└── frontend/
    └── index.html                 # single-page vanilla JS demo UI
```

Each file does one job. `evidence.py` is the seam: it's the only file that
knows about all the other services, so you can add a new analysis pass
(say, a JavaScript analyzer) by writing one new service and adding one line
to `build_evidence()`.

## How data flows

```
repo URL
   → cloner.py        (clone to temp dir)
   → discovery.py      (file list + language %)
   → static_analysis.py (per-file issues, function/class counts)
   → security_scan.py  (Bandit findings)
   → dependency_scan.py (requirements.txt + pip-audit)
   → evidence.py        (assemble JSON, compute health scores)
   → ai_explainer.py    (optional: Claude explains the JSON in prose)
   → JSON response → frontend renders it
```

Note the AI layer is last and optional. Everything before it is
deterministic — if you never set an API key, you still get a complete,
accurate report; you just don't get the prose summary on top.

## Setup

**Prerequisites:** Python 3.10+, `git` installed and on your PATH.

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # optional — only needed for the AI summary
# edit .env and add your ANTHROPIC_API_KEY
```

Run the backend:

```bash
uvicorn app.main:app --reload
```

This starts the API at `http://127.0.0.1:8000`. Visit
`http://127.0.0.1:8000/docs` for interactive Swagger docs — useful for
testing `/analyze` directly before touching the frontend at all.

Run the frontend (a real local server avoids browser file:// CORS quirks):

```bash
cd frontend
python3 -m http.server 5500
```

Open `http://localhost:5500`, paste a public GitHub URL (try something small
first, e.g. `https://github.com/psf/requests`), and click Analyze.

## What's real vs. heuristic right now

Being upfront about this matters if you're using it as a portfolio piece —
be ready to explain these tradeoffs in an interview:

- **Solid and deterministic:** file/language counts, function/class counts,
  cyclomatic complexity (via `radon`), Bandit security findings, pip-audit
  vulnerability lookups. These are the same tools real engineering teams use.
- **Useful heuristics, not perfect detectors:** the "query in a loop" check
  matches function-name patterns (`get`, `query`, `fetch`, etc.) rather than
  actually tracing data flow, so it will have some false positives/negatives
  on unusual code. Say this plainly if asked — it's a legitimate MVP
  tradeoff, not a hidden flaw.
- **Explainable, not black-box:** health scores are penalty points subtracted
  from 100 based on named, countable things (see `_score_health` in
  `evidence.py`), normalized per 1,000 lines of code so large repos aren't
  unfairly penalized just for being large. There's no learned model behind
  the numbers yet — that's deliberate for v1.

## Known limitations (v1)

- Python only. `discovery.py` detects other languages for the overview
  stats, but `static_analysis.py` only parses `.py` files.
- Dependency scanning only reads `requirements.txt`. `package.json`,
  `pom.xml`, `go.mod` would each need their own small parser following the
  same pattern as `dependency_scan.py`.
- `/analyze` runs synchronously — a large repo will make the request hang
  for a while. Fine for a demo; a real deployment would move this to a
  background job with a status-polling endpoint.
- No secret-scanning beyond what Bandit catches (which is narrower than
  "any hardcoded API key" — Bandit mostly catches variables literally named
  `password`/`secret`/etc). A dedicated tool like `detect-secrets` or
  `gitleaks` would close this gap.
- Single-repo, in-memory, no persistence or auth — there's no database yet.

## Next steps, in order

1. **Add a second language** (JavaScript, via Tree-sitter) to prove the
   `services/` pattern generalizes before you invest more in Python-only
   depth.
2. **Real architecture diagrams**: this needs an actual call graph, not just
   per-file stats — parse imports and function calls across files, build a
   graph (networkx), and render it (e.g. to Mermaid or an SVG).
3. **Docstring/README coverage pass** to make the "documentation" health
   score real instead of a flat placeholder.
4. **Background jobs**: move `/analyze` to a task queue (Celery or even a
   simple in-memory job store) so the frontend can show progress and handle
   bigger repos without timing out.
5. **The ML bug-risk model** — genuinely the hardest part (see the earlier
   discussion). Needs mined git history (bug-fix commits linked to files) as
   labeled training data. Treat this as a research-flavored bonus feature
   once everything above is solid, not as a v1 requirement.

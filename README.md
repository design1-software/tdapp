# TDApp — ToDo Application

**Full-Stack Task Management | Amplify Federal Internship Exercise**

> FastAPI · SQLite · React · pytest

---

## Live Links

| | URL |
|---|---|
| **Live App** | `[NETLIFY_URL]` — update after deployment |
| **Live API** | `[RAILWAY_URL]` — update after deployment |
| **API Docs** | `[RAILWAY_URL]/docs` — interactive, no setup required |
| **GitHub** | github.com/design1-software/tdapp |

---

## What Is TDApp

TDApp (ToDo Application) is a full-stack task management application built as a response to the Amplify Federal internship coding exercise. It implements full CRUD task management with a FastAPI backend, SQLite persistence, and a React frontend — deployed as two independent services following a clean separation-of-concerns architecture.

The name follows federal naming convention. Government programs run on acronyms. A custom vanity domain would be inconsistent with how this would actually be delivered on a government contract.

---

## Features

### Required
- **Add tasks** — create new tasks with title and optional due date
- **Complete tasks** — toggle between complete and incomplete
- **Delete tasks** — remove individual tasks
- **Visual distinction** — completed tasks display with strikethrough and muted color

### Bonus
- **Filter by status** — view All, Active, or Completed tasks
- **Task count** — live display of remaining incomplete tasks
- **Clear completed** — remove all completed tasks in one action
- **Inline edit** — update task title without deleting and recreating

---

## Architecture & Deployment

TDApp is deployed as two independent services. This is a deliberate architectural decision, not a constraint.

### Why two platforms?

The backend and frontend are fundamentally different types of software at runtime.

**The FastAPI backend** is a running server process. It has to stay alive, listen on a port, accept HTTP requests, query the database, and return responses. It needs a platform that runs persistent processes. That is Railway.

**The React frontend**, after `npm run build`, is a folder of static files — HTML, CSS, and JavaScript. There is no process. A browser downloads those files once and runs the application locally on the client. Netlify is a CDN purpose-built for serving static files. It does not run server processes, and none are needed.

Putting the React build on Railway would work, but you would be using a persistent process host to serve files that require no process. Putting a Python API on Netlify is not possible — Netlify does not run server processes.

### Deployment options considered

| Option | Platform(s) | How It Works | Trade-off |
|---|---|---|---|
| **Chosen** | Railway + Netlify | API runs as a persistent process on Railway. React build is static files on Netlify. Each platform doing exactly what it was built for. | Two platforms to manage. Clean separation — API and client independently deployable. |
| Option B | Railway only | FastAPI serves both the API and the React static build using `StaticFiles` mount. One platform, one deploy. | Simpler ops. Slightly less clean — your API layer doubles as a file server. Perfectly valid for small projects. |
| Option C | Render or Fly.io | Either replaces Railway for the persistent process. Functionally identical for this scope. | Different free tier limits. No meaningful difference. |
| Option D | Railway + Vercel | Vercel instead of Netlify for the React frontend. Both are static file hosts. | No meaningful difference for this use case. |

### How the two services communicate

The React frontend makes HTTP requests to the Railway API URL. That URL is set in a single environment variable — `VITE_API_URL` — in the Netlify build configuration. Changing the backend URL requires updating one variable. The two services are independently deployable: redeploy the API without touching the frontend, and vice versa.

---

## Repository Structure

```
tdapp/
├── backend/
│   ├── main.py                 # App entry point, CORS config, router registration
│   ├── models.py               # Pydantic models: Task, TaskCreate, TaskUpdate
│   ├── database.py             # SQLite connection, table init, all CRUD functions
│   ├── routers/
│   │   └── tasks.py            # Route handlers — thin layer, logic in database.py
│   ├── tests/
│   │   └── test_tasks.py       # pytest suite using FastAPI TestClient
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/         # TaskInput, TaskItem, TaskList, FilterBar
│   │   ├── api.js              # Axios wrapper — all backend calls in one place
│   │   └── App.jsx             # Root component, state management
│   ├── .env.example            # VITE_API_URL placeholder
│   └── package.json
├── .env.example                # Root-level env reference
└── README.md
```

---

## Local Setup

**Prerequisites:** Python 3.11+, Node.js 18+, Git. No external services required — SQLite is file-based and included.

### Step 1 — Clone the repo

```bash
git clone https://github.com/design1-software/tdapp.git
cd tdapp
```

### Step 2 — Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend running at: `http://localhost:8000`

Interactive API docs at: `http://localhost:8000/docs` — all endpoints testable here without touching the frontend.

### Step 3 — Frontend (new terminal)

```bash
cd frontend
cp .env.example .env
# .env already points to http://localhost:8000 — no edit needed for local run
npm install
npm run dev
```

Frontend running at: `http://localhost:5173`

### Step 4 — Run the test suite

```bash
cd backend
pytest tests/ -v
```

All tests run against an isolated in-memory test database — no data from your local run is affected.

---

## API Reference

Full interactive documentation at `[RAILWAY_URL]/docs` (live) or `http://localhost:8000/docs` (local). Every endpoint is testable directly from that page without a separate client.

| Endpoint | What It Does |
|---|---|
| `POST /tasks` | Create a new task. Requires title. Rejects empty or whitespace-only titles with 422. |
| `GET /tasks` | Return all tasks. Accepts optional `?status=complete` or `?status=incomplete` filter. |
| `GET /tasks/{id}` | Return a single task by ID. Returns 404 if not found. |
| `PATCH /tasks/{id}` | Update title, completion status, or due date. Partial updates supported. |
| `DELETE /tasks/{id}` | Delete a task by ID. Returns 404 if not found. |
| `DELETE /tasks/completed` | Delete all completed tasks in one operation. |

---

## Technology Choices

Every decision below was made against the specific constraints of this exercise and can be explained in a walk-through.

| Decision | Rationale |
|---|---|
| **FastAPI over Flask** | Auto-generates interactive `/docs` so a reviewer can test the API without reading code or installing a separate client. Pydantic validation rejects bad input at the model layer with a clear error message before it touches the database. Current Python API standard. |
| **SQLite over PostgreSQL** | Anyone cloning this repo needs zero external setup to run it. SQLite is a file. PostgreSQL requires a running server. Right tool for this scope. The `database.py` abstraction makes swapping to PostgreSQL a one-file change if scale requires it. |
| **React over plain HTML/JS** | Component model maps naturally to this UI — TaskInput, TaskList, TaskItem, FilterBar are clean single-responsibility separations. Demonstrates UI architecture thinking that a flat HTML file would not. |
| **pytest + TestClient** | Tests actual HTTP endpoints end-to-end — route handler, Pydantic validation, database, and response — not just isolated functions. This is what critical path testing means in practice. |
| **Railway + Netlify** | Two platforms because two fundamentally different runtime types. See Architecture section above. |
| **Vite over Create React App** | CRA is deprecated. Vite is the current standard — faster builds, smaller output, actively maintained. |

---

## Error Handling

| Scenario | Response |
|---|---|
| Empty title on `POST /tasks` | 422 with field-level error — rejected before it hits the route handler |
| Whitespace-only title | Stripped and validated — treated as empty, same 422 rejection |
| `PATCH` or `DELETE` with nonexistent ID | 404 with descriptive message — not a generic 500 |
| Invalid `?status=` filter value | 422 — valid values are `complete` and `incomplete` only |
| Frontend API call fails | Error caught, user-facing message displayed — no silent failures, no blank screen |

---

## Scope Decisions

The choices below were made deliberately given the 2–3 hour time constraint. Each has a clear production path.

| Decision | This Submission | Production Path |
|---|---|---|
| **CORS** | `allow_origins=["*"]` — open so any reviewer can run locally without config | Restrict to deployed Netlify domain via environment variable |
| **Database** | SQLite — zero external setup, runs anywhere, file-based | PostgreSQL — swap one file (`database.py`); interface and all other code unchanged |
| **Frontend tests** | Omitted for scope | Vitest + React Testing Library — component behavior and API integration |
| **Authentication** | Not required by the exercise | Session or JWT auth layer before any real user data |
| **CI/CD** | Not configured | GitHub Actions: run `pytest` on push, block merge on failure |

---

## What Is Planned — Phase 2

The following feature is designed and ready to build. It was intentionally deferred to keep the Phase 1 submission clean and on time.

### TDApp Day Brief — AI-Powered Daily Summary

On-demand button press calls Claude Sonnet (via the Anthropic API) with the current task list and returns a structured daily brief in OPORD format:

- **Situation** — overall task load and completion status
- **Tasks for Today** — active tasks in priority order
- **Completed Yesterday** — tasks marked complete in the last 24 hours
- **Priority Order** — recommended execution sequence

The system prompt is treated as an API contract — explicit JSON schema, field-by-field validation before any output renders. An API that can return bad output gets explicit failure handling, not trust.

Phase 2 version adds an APScheduler job delivering the brief by email at 0700 local time.

---

## Environment Variables

| Variable | Where | Purpose |
|---|---|---|
| `VITE_API_URL` | `frontend/.env` | Points to the Railway backend URL |
| `ANTHROPIC_API_KEY` | `backend/.env` | Phase 2 only — not required for Phase 1 |

Never commit a real `.env` file. The `.env.example` files in this repo contain placeholder values only.

---

## Development Approach

This project was built using an AI-assisted development workflow with intentional inline documentation throughout the codebase. The comments are written to explain not just *what* the code does but *why* — including architectural decisions, tradeoffs, validation behavior, and request flow. This serves two purposes: it reduces onboarding friction for anyone reviewing the code, and it functions as a learning reinforcement mechanism during development.

As a software engineering student transitioning from a healthcare background, I built this workflow specifically to ensure I can explain every line I submit. The comment density is deliberate, not incidental. I can walk through the full request lifecycle — from a React form submission through the Axios call, FastAPI routing, Pydantic validation, SQLite write, and state update — and explain why each layer is structured the way it is.

This aligns directly with the note in the exercise prompt: *"We care that you understand the code you submit and can speak to your decisions."*

---

## Author

Julius | design1-software | May 2026

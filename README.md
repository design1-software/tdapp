# TDApp — ToDo Application

**Full-Stack Task Management | Amplify Federal Internship Exercise**

> FastAPI · SQLite · React · pytest

---

## Live Links

| | URL |
|---|---|
| **Live App** | https://tdlistapp-ex.netlify.app |
| **Live API** | https://tdapp-production.up.railway.app |
| **API Docs** | https://tdapp-production.up.railway.app/docs — interactive, no setup required |
| **GitHub** | github.com/design1-software/tdapp |

---

## Live State — What the Reviewer Will See

The live database is pre-seeded with a realistic task mix so every feature is immediately visible on arrival — no setup required.

**Active tasks (6):**
| Task | Due |
|---|---|
| Respond to client feedback on wireframes | — |
| Send weekly status report | May 29 |
| Prep talking points for stakeholder meeting | — |
| Review Q2 project proposal | May 30 |
| Schedule team standup for next sprint | May 29 |
| Update API documentation | Jun 2 |

**Completed in last 24h (3):**
- Submit timesheet for pay period
- Finalize onboarding checklist
- Review pull request from dev team

**Sample Day Brief generated from this task list:**

```json
{
  "situation": "You have 6 active tasks requiring attention today, spanning communication,
                documentation, and planning responsibilities. 3 tasks were completed in
                the last 24 hours, indicating solid recent progress.",
  "priority_order": [
    "Respond to client feedback on wireframes",
    "Send weekly status report",
    "Prep talking points for stakeholder meeting",
    "Review Q2 project proposal",
    "Schedule team standup for next sprint",
    "Update API documentation"
  ],
  "tasks_for_today": ["...same 6 active tasks..."],
  "completed_recently": [
    "Submit timesheet for pay period",
    "Finalize onboarding checklist",
    "Review pull request from dev team"
  ]
}
```

Reviewers can add, edit, complete, and delete tasks freely — the brief regenerates from whatever is in the database at the time the button is pressed.

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

### AI Features
- **Day Brief** — on-demand button calls Claude Sonnet 4.6 (Anthropic API) with the current task list and returns a structured daily brief: situation overview, active tasks, completed in the last 24 hours, and AI-recommended priority order. System prompt is a strict JSON schema contract; every field is validated by Pydantic before anything renders.
- **Daily Email** — APScheduler background job fires at 07:00 Eastern every day, generates the same brief, and sends an HTML-formatted email via Gmail SMTP. Supports one or multiple recipients via a comma-separated `EMAIL_TO` environment variable.

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
│   ├── models.py               # Pydantic models: Task, TaskCreate, TaskUpdate, BriefResponse
│   ├── database.py             # SQLite connection, table init, all CRUD functions
│   ├── routers/
│   │   ├── tasks.py            # Route handlers — thin layer, logic in database.py
│   │   └── brief.py            # POST /brief — thin HTTP wrapper around brief_service
│   ├── brief_service.py        # Core brief logic — shared by /brief endpoint and scheduler
│   ├── scheduler.py            # APScheduler setup — daily_brief_job() at 07:00 Eastern
│   ├── email_sender.py         # Gmail SMTP — format_brief_email() + send_brief_email()
│   ├── tests/
│   │   ├── test_tasks.py       # pytest suite using FastAPI TestClient (24 tests)
│   │   ├── test_brief.py       # Brief endpoint tests — mocks Claude, tests validation (8 tests)
│   │   └── test_scheduler.py   # Scheduler job tests — mocks Claude + email sender (8 tests)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/         # TaskInput, TaskItem, TaskList, FilterBar, DayBrief
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

Full interactive documentation at [tdapp-production.up.railway.app/docs](https://tdapp-production.up.railway.app/docs) (live) or `http://localhost:8000/docs` (local). Every endpoint is testable directly from that page without a separate client.

| Endpoint | What It Does |
|---|---|
| `POST /tasks` | Create a new task. Requires title. Rejects empty or whitespace-only titles with 422. |
| `GET /tasks` | Return all tasks. Accepts optional `?status=complete` or `?status=incomplete` filter. |
| `GET /tasks/{id}` | Return a single task by ID. Returns 404 if not found. |
| `PATCH /tasks/{id}` | Update title, completion status, or due date. Partial updates supported. |
| `DELETE /tasks/{id}` | Delete a task by ID. Returns 404 if not found. |
| `DELETE /tasks/completed` | Delete all completed tasks in one operation. |
| `POST /brief` | Generate an AI-powered Day Brief via Claude Sonnet 4.6. Returns situation, active tasks, recently completed, and priority order. Requires `ANTHROPIC_API_KEY` on the server. |

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
| **Anthropic SDK + Claude Sonnet 4.6** | System prompt defines an explicit JSON schema — Claude returns structured data, not prose. Pydantic validates every field before anything reaches the client. `call_claude()` is isolated in `brief_service.py` so tests can patch it cleanly without making real API calls. |
| **APScheduler (BackgroundScheduler)** | Runs as a daemon thread inside the existing uvicorn process — no separate worker or process needed. FastAPI's `lifespan` context manager starts it on deploy and stops it cleanly on shutdown. |
| **smtplib (stdlib)** | No extra dependency for email delivery. Gmail SMTP over port 465 with TLS. App Password avoids storing the account password. `EMAIL_TO` is comma-separated so multiple recipients require no code change. |

---

## Error Handling

| Scenario | Response |
|---|---|
| Empty title on `POST /tasks` | 422 with field-level error — rejected before it hits the route handler |
| Whitespace-only title | Stripped and validated — treated as empty, same 422 rejection |
| `PATCH` or `DELETE` with nonexistent ID | 404 with descriptive message — not a generic 500 |
| Invalid `?status=` filter value | 422 — valid values are `complete` and `incomplete` only |
| Frontend API call fails | Error caught, user-facing message displayed — no silent failures, no blank screen |
| `POST /brief` — no API key | 503 with clear message — checked before any API call is made |
| `POST /brief` — Claude returns bad JSON | 502 — `json.loads()` fails, Pydantic never runs, error is explicit |
| `POST /brief` — Claude omits a required field | 502 — Pydantic `BriefSection(**data)` raises `ValidationError` before any output is returned |

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

## What Is Shipped — AI Features

### On-Demand Day Brief

Clicking **✦ Generate Day Brief** in the app calls `POST /brief`, which:

1. Pulls all tasks from the database
2. Splits them: active tasks vs. completed in the last 24 hours (tracked by `completed_at` timestamp)
3. Sends both lists to Claude Sonnet 4.6 via the Anthropic SDK with a strict system prompt that specifies the exact JSON schema to return
4. Validates every field in the response with Pydantic before returning anything to the client
5. Renders four sections in the UI: **Situation**, **Priority Order**, **Active Tasks**, **Completed (24h)**

The system prompt is treated as an API contract, not a suggestion. If Claude returns malformed output or omits a field, the endpoint returns 502 — it does not forward unvalidated AI output.

### Daily Email at 07:00

An APScheduler `BackgroundScheduler` starts with the FastAPI app and fires at 07:00 Eastern every day. The job calls the same `brief_service.build_brief()` function used by the HTTP endpoint, formats the result as an HTML email, and sends it via Gmail SMTP.

- All errors are caught and logged — a failed send never crashes the server
- Supports one or multiple recipients: set `EMAIL_TO` to a comma-separated list
- Requires three Railway environment variables (see Environment Variables section below)

---

## Environment Variables

| Variable | Where | Purpose |
|---|---|---|
| `VITE_API_URL` | Netlify dashboard | Points to the Railway backend URL — must include `https://` |
| `ANTHROPIC_API_KEY` | Railway dashboard | Required for `POST /brief` and the daily email scheduler |
| `EMAIL_FROM` | Railway dashboard | Gmail address that sends the daily brief |
| `EMAIL_APP_PASSWORD` | Railway dashboard | Gmail App Password (not your account password) — Google Account → Security → App Passwords |
| `EMAIL_TO` | Railway dashboard | Recipient address(es). Comma-separated for multiple: `alice@gmail.com, bob@gmail.com` |

Never commit a real `.env` file. The `.env.example` files in this repo contain placeholder values only.

---

## Development Approach

This project was built using an AI-assisted development workflow with intentional inline documentation throughout the codebase. The comments are written to explain not just *what* the code does but *why* — including architectural decisions, tradeoffs, validation behavior, and request flow. This serves two purposes: it reduces onboarding friction for anyone reviewing the code, and it functions as a learning reinforcement mechanism during development.

As a software engineering student transitioning from a healthcare background, I built this workflow specifically to ensure I can explain every line I submit. The comment density is deliberate, not incidental. I can walk through the full request lifecycle — from a React form submission through the Axios call, FastAPI routing, Pydantic validation, SQLite write, and state update — and explain why each layer is structured the way it is.

This aligns directly with the note in the exercise prompt: *"We care that you understand the code you submit and can speak to your decisions."*

---

## Author

Julius | design1-software | May 2026

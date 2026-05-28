# 📘 WHAT THIS FILE DOES: Application entry point.
# Creates the FastAPI app, configures CORS, registers routers, initializes the database,
# and manages the APScheduler lifecycle via FastAPI's lifespan context manager.
# Run this file with: uvicorn main:app --reload --port 8000
# 🔗 FastAPI reference: https://fastapi.tiangolo.com/

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import database
from routers import tasks, brief
from scheduler import create_scheduler

logger = logging.getLogger(__name__)


# ── LIFESPAN ───────────────────────────────────────────────────────────────────

# 📘 @asynccontextmanager turns this function into a context manager.
# FastAPI calls the code before 'yield' on startup and the code after 'yield' on shutdown.
# This is the recommended way in FastAPI to manage resources that need cleanup (like schedulers).
# 🔗 FastAPI lifespan reference: https://fastapi.tiangolo.com/advanced/events/
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──
    database.init_db()  # Creates the tasks table if it doesn't exist yet
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("APScheduler started — daily brief runs at 07:00 Eastern")

    yield  # 📘 The app runs while execution is paused here at 'yield'

    # ── SHUTDOWN ──
    # 📘 wait=False means don't wait for currently running jobs to finish before stopping.
    # This prevents a slow job from delaying the server shutdown.
    scheduler.shutdown(wait=False)
    logger.info("APScheduler stopped")


# ── APPLICATION ────────────────────────────────────────────────────────────────

# 📘 FastAPI() creates the application object — everything connects to this.
# title and description appear in the auto-generated /docs API explorer.
# lifespan= wires up the startup/shutdown handler defined above.
app = FastAPI(
    title="TDApp API",
    description="Full-stack Todo List API — Amplify Federal Internship Exercise",
    version="1.0.0",
    lifespan=lifespan,
)

# 📘 CORS (Cross-Origin Resource Sharing) controls which domains can call this API.
# The React frontend (Netlify/localhost:5173) is a different origin than the API (Railway/localhost:8000).
# Without CORS middleware, the browser would block the frontend's requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Accept requests from any origin (fine for this scope)
    allow_credentials=True,
    allow_methods=["*"],       # Allow GET, POST, PATCH, DELETE, etc.
    allow_headers=["*"],
)

# 📘 include_router attaches route groups to the app.
# tasks.router handles /tasks — CRUD operations.
# brief.router handles /brief — AI-powered Day Brief.
app.include_router(tasks.router)
app.include_router(brief.router)

# 📘 WHAT THIS FILE DOES: Application entry point.
# Creates the FastAPI app, configures CORS, registers routers, and initializes the database.
# Run this file with: uvicorn main:app --reload --port 8000
# 🔗 FastAPI reference: https://fastapi.tiangolo.com/

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import database
from routers import tasks, brief

# 📘 FastAPI() creates the application object — everything connects to this.
# title and description appear in the auto-generated /docs API explorer.
app = FastAPI(
    title="TDApp API",
    description="Full-stack Todo List API — Amplify Federal Internship Exercise",
    version="1.0.0",
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

# 📘 Initialize the database on startup — creates the tasks table if it doesn't exist yet.
# This is safe to call every time: CREATE TABLE IF NOT EXISTS never overwrites existing data.
database.init_db()

# 📘 include_router attaches route groups to the app.
# tasks.router handles /tasks — CRUD operations.
# brief.router handles /brief — AI-powered Day Brief (Phase 2).
app.include_router(tasks.router)
app.include_router(brief.router)

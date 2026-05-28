// 📘 WHAT THIS FILE DOES: Centralizes all HTTP calls to the FastAPI backend.
// Every component that needs data calls a function from here — nothing calls axios directly.
// This means if the API URL or structure changes, there's exactly one file to update.
// 🔗 Axios reference: https://axios-http.com/docs/intro

import axios from "axios";

// 📘 axios.create() makes a pre-configured HTTP client.
// baseURL is read from the .env file (VITE_API_URL), falling back to localhost for development.
// import.meta.env is Vite's way of reading .env variables in React.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

// ── TASK API FUNCTIONS ──────────────────────────────────────────────────────

/**
 * Fetch all tasks, optionally filtered by status.
 * @param {string|null} status - 'complete', 'incomplete', or null for all
 * @returns {Promise} axios response with task array in .data
 */
export const getTasks = (status = null) => {
  // 📘 params: { status } adds ?status=complete to the URL when status is provided.
  // axios skips null/undefined values automatically, so null status = no query param.
  const params = status ? { status } : {};
  return api.get("/tasks", { params });
};

/**
 * Create a new task.
 * @param {string} title - Task title (required, non-empty)
 * @param {string|null} due_date - ISO date string e.g. "2026-06-01", or null
 * @returns {Promise} axios response with created task in .data
 */
export const createTask = (title, due_date = null) =>
  api.post("/tasks", { title, due_date });

/**
 * Partially update a task (title, completed, or due_date).
 * @param {number} id - Task ID
 * @param {object} updates - Only the fields to change e.g. { completed: true }
 * @returns {Promise} axios response with updated task in .data
 */
export const updateTask = (id, updates) =>
  api.patch(`/tasks/${id}`, updates);

/**
 * Delete a single task by ID.
 * @param {number} id - Task ID
 * @returns {Promise} axios response
 */
export const deleteTask = (id) => api.delete(`/tasks/${id}`);

/**
 * Delete all completed tasks in one request.
 * @returns {Promise} axios response
 */
export const deleteCompleted = () => api.delete("/tasks/completed");

// ── BRIEF API FUNCTION ──────────────────────────────────────────────────────

/**
 * Generate an AI-powered Day Brief using Claude Sonnet.
 * Requires ANTHROPIC_API_KEY to be configured on the backend.
 * @returns {Promise} axios response with BriefResponse in .data
 */
export const generateBrief = () => api.post("/brief");

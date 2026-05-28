// 📘 WHAT THIS FILE DOES: Root component — owns all application state and API calls.
// State is "lifted" to App so all child components (TaskInput, FilterBar, TaskList)
// share the same source of truth. Child components receive data and callbacks via props.
// 🔗 React state reference: https://www.w3schools.com/react/react_state.asp

import { useState, useEffect, useCallback } from "react";
import {
  getTasks,
  createTask,
  updateTask,
  deleteTask,
  deleteCompleted,
  generateBrief,
} from "./api";
import TaskInput  from "./components/TaskInput";
import FilterBar  from "./components/FilterBar";
import TaskList   from "./components/TaskList";
import DayBrief   from "./components/DayBrief";
import styles     from "./App.module.css";

export default function App() {
  // 📘 useState declares state variables. React re-renders the component whenever state changes.
  const [tasks,        setTasks]        = useState([]);    // Full list from the database
  const [filter,       setFilter]       = useState("all"); // 'all' | 'active' | 'completed'
  const [loading,      setLoading]      = useState(true);
  const [error,        setError]        = useState(null);
  const [brief,        setBrief]        = useState(null);  // BriefResponse or null
  const [briefLoading, setBriefLoading] = useState(false);
  const [briefError,   setBriefError]   = useState(null);

  // ── FETCH ──────────────────────────────────────────────────────────────────

  // 📘 useCallback memoizes the function — prevents unnecessary re-creation on every render.
  const fetchTasks = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await getTasks(); // GET /tasks — returns all tasks
      setTasks(res.data);
    } catch {
      setError("Could not load tasks. Is the backend running?");
    } finally {
      setLoading(false); // 📘 'finally' runs whether the request succeeded or failed
    }
  }, []);

  // 📘 useEffect runs the function after the first render ([] = run once on mount).
  // This is where we load initial data from the API.
  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  // ── ADD ────────────────────────────────────────────────────────────────────

  async function handleAdd(title, dueDate) {
    try {
      const res = await createTask(title, dueDate); // POST /tasks
      // 📘 Spread the existing array and append the new task — never mutate state directly
      setTasks((prev) => [...prev, res.data]);
    } catch (err) {
      const msg = err.response?.data?.detail ?? "Failed to add task.";
      setError(msg);
    }
  }

  // ── TOGGLE ─────────────────────────────────────────────────────────────────

  async function handleToggle(id) {
    const task = tasks.find((t) => t.id === id);
    try {
      const res = await updateTask(id, { completed: !task.completed }); // PATCH /tasks/:id
      // 📘 .map() replaces only the updated task, leaving everything else unchanged
      setTasks((prev) => prev.map((t) => (t.id === id ? res.data : t)));
    } catch {
      setError("Failed to update task.");
    }
  }

  // ── DELETE ─────────────────────────────────────────────────────────────────

  async function handleDelete(id) {
    try {
      await deleteTask(id); // DELETE /tasks/:id
      // 📘 .filter() returns a new array without the deleted task
      setTasks((prev) => prev.filter((t) => t.id !== id));
    } catch {
      setError("Failed to delete task.");
    }
  }

  // ── UPDATE TITLE ───────────────────────────────────────────────────────────

  async function handleUpdate(id, title) {
    try {
      const res = await updateTask(id, { title }); // PATCH /tasks/:id
      setTasks((prev) => prev.map((t) => (t.id === id ? res.data : t)));
    } catch (err) {
      const msg = err.response?.data?.detail ?? "Failed to update task.";
      setError(msg);
    }
  }

  // ── DAY BRIEF ──────────────────────────────────────────────────────────────

  async function handleGenerateBrief() {
    try {
      setBriefLoading(true);
      setBriefError(null);
      const res = await generateBrief(); // POST /brief
      setBrief(res.data);
    } catch (err) {
      const msg = err.response?.data?.detail ?? "Failed to generate brief.";
      setBriefError(msg);
    } finally {
      setBriefLoading(false);
    }
  }

  // ── CLEAR COMPLETED ────────────────────────────────────────────────────────

  async function handleClearCompleted() {
    try {
      await deleteCompleted(); // DELETE /tasks/completed
      setTasks((prev) => prev.filter((t) => !t.completed));
    } catch {
      setError("Failed to clear completed tasks.");
    }
  }

  // ── DERIVED STATE ──────────────────────────────────────────────────────────

  // 📘 These are computed from 'tasks' — no extra state needed.
  // React recalculates them on every render when 'tasks' changes.
  const filteredTasks = tasks.filter((t) => {
    if (filter === "active")    return !t.completed;
    if (filter === "completed") return  t.completed;
    return true; // 'all' — no filter applied
  });

  const incompleteCount = tasks.filter((t) => !t.completed).length;
  const completedCount  = tasks.filter((t) =>  t.completed).length;

  // ── RENDER ─────────────────────────────────────────────────────────────────

  return (
    <div className={styles.page}>
      {/* ── HEADER ── */}
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <h1 className={styles.logo}>TDApp</h1>
          <p className={styles.tagline}>Task Manager — Amplify Federal</p>
        </div>
      </header>

      {/* ── MAIN CONTENT ── */}
      <main className={styles.main}>
        {/* 📘 Error banner — only visible when error state is set */}
        {error && (
          <div className={styles.errorBanner} role="alert">
            {error}
            <button
              className={styles.errorClose}
              onClick={() => setError(null)}
              aria-label="Dismiss error"
            >
              ✕
            </button>
          </div>
        )}

        {/* AI Day Brief — button shown always; panel shown after generation */}
        <DayBrief
          brief={brief}
          loading={briefLoading}
          error={briefError}
          onGenerate={handleGenerateBrief}
          onDismiss={() => { setBrief(null); setBriefError(null); }}
        />

        {/* Task creation form */}
        <TaskInput onAdd={handleAdd} />

        {/* Filter bar — shown once tasks have loaded */}
        {!loading && (
          <FilterBar
            filter={filter}
            onFilterChange={setFilter}
            incompleteCount={incompleteCount}
            completedCount={completedCount}
            onClearCompleted={handleClearCompleted}
          />
        )}

        {/* Task list — shows a spinner while loading */}
        {loading ? (
          <div className={styles.loading} aria-live="polite">Loading tasks…</div>
        ) : (
          <TaskList
            tasks={filteredTasks}
            onToggle={handleToggle}
            onDelete={handleDelete}
            onUpdate={handleUpdate}
          />
        )}
      </main>
    </div>
  );
}

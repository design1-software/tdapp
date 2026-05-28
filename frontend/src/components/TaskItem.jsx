// 📘 WHAT THIS FILE DOES: Renders a single task row with checkbox, title, and action buttons.
// Supports inline editing — double-click the title to edit it in place.
// 🔗 React events reference: https://www.w3schools.com/react/react_events.asp

import { useState, useRef, useEffect } from "react";
import styles from "./TaskItem.module.css";

/**
 * TaskItem — one row in the task list.
 * Props:
 *   task       — { id, title, completed, due_date, created_at }
 *   onToggle(id)            — flip completed ↔ incomplete
 *   onDelete(id)            — remove the task
 *   onUpdate(id, newTitle)  — save an edited title
 */
export default function TaskItem({ task, onToggle, onDelete, onUpdate }) {
  // 📘 editing controls whether the title is a plain label or an editable text input
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(task.title);

  // 📘 useRef gives us a direct reference to the input DOM element so we can focus it
  const inputRef = useRef(null);

  // 📘 useEffect runs after the component re-renders.
  // When editing becomes true, we immediately focus the input so the user can type.
  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select(); // Select all text so the user can immediately overwrite
    }
  }, [editing]);

  function startEdit() {
    setEditTitle(task.title); // Reset to current title in case a previous edit was cancelled
    setEditing(true);
  }

  function saveEdit() {
    const trimmed = editTitle.trim();
    if (trimmed && trimmed !== task.title) {
      onUpdate(task.id, trimmed); // Only call the API if the title actually changed
    }
    setEditing(false);
  }

  function cancelEdit() {
    setEditTitle(task.title); // Discard changes
    setEditing(false);
  }

  // 📘 Handle keyboard shortcuts in the edit input
  function handleKeyDown(e) {
    if (e.key === "Enter") saveEdit();
    if (e.key === "Escape") cancelEdit();
  }

  // Format the due date as "Jun 1, 2026" if present
  const formattedDue = task.due_date
    ? new Date(task.due_date + "T00:00:00").toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : null;

  return (
    <li className={`${styles.item} ${task.completed ? styles.completed : ""}`}>
      {/* ── CHECKBOX ── */}
      {/* 📘 <input type="checkbox"> renders a toggleable checkbox.
           onChange fires every time the user clicks it. */}
      <input
        type="checkbox"
        className={styles.checkbox}
        checked={task.completed}
        onChange={() => onToggle(task.id)}
        aria-label={`Mark "${task.title}" as ${task.completed ? "incomplete" : "complete"}`}
      />

      {/* ── TITLE / EDIT INPUT ── */}
      <div className={styles.content}>
        {editing ? (
          // 📘 When editing=true, replace the label with a text input
          <input
            ref={inputRef}
            type="text"
            className={styles.editInput}
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            onBlur={saveEdit}         // Save when user clicks away
            onKeyDown={handleKeyDown} // Enter = save, Escape = cancel
            aria-label="Edit task title"
          />
        ) : (
          // 📘 Double-click the title to enter edit mode
          <span
            className={styles.title}
            onDoubleClick={startEdit}
            title="Double-click to edit"
          >
            {task.title}
          </span>
        )}

        {/* ── DUE DATE BADGE ── */}
        {formattedDue && !editing && (
          <span className={styles.dueDate}>Due {formattedDue}</span>
        )}
      </div>

      {/* ── ACTION BUTTONS ── */}
      <div className={styles.actions}>
        {!editing && (
          <button
            className={styles.editBtn}
            onClick={startEdit}
            aria-label="Edit task"
            title="Edit task"
          >
            ✏️
          </button>
        )}
        <button
          className={styles.deleteBtn}
          onClick={() => onDelete(task.id)}
          aria-label="Delete task"
          title="Delete task"
        >
          ✕
        </button>
      </div>
    </li>
  );
}

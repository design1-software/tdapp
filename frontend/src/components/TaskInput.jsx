// 📘 WHAT THIS FILE DOES: Renders the form for adding a new task.
// Manages its own local state for the title and due date inputs.
// When submitted, calls the onAdd prop and resets the form.
// 🔗 React forms reference: https://www.w3schools.com/react/react_forms.asp

import { useState } from "react";
import styles from "./TaskInput.module.css";

/**
 * TaskInput — form for creating a new task.
 * Props:
 *   onAdd(title, dueDate) — called when the form is submitted with a valid title
 */
export default function TaskInput({ onAdd }) {
  // 📘 useState manages the controlled input values.
  // React keeps these in sync with what's displayed in the text boxes.
  const [title, setTitle] = useState("");
  const [dueDate, setDueDate] = useState("");

  // 📘 handleSubmit is called when the user clicks "Add Task" or presses Enter.
  function handleSubmit(e) {
    e.preventDefault(); // 📘 Prevents the browser from reloading the page (default form behavior)

    const trimmed = title.trim(); // Remove accidental leading/trailing spaces
    if (!trimmed) return;         // Don't submit if the title is blank

    onAdd(trimmed, dueDate || null); // Pass null when due date is empty

    // 📘 Reset the form fields after a successful submission
    setTitle("");
    setDueDate("");
  }

  return (
    // 📘 <form> groups inputs and handles the submit event
    <form onSubmit={handleSubmit} className={styles.form}>
      <div className={styles.inputRow}>
        {/* 📘 The title input is a "controlled component" — React owns the value via state */}
        <input
          type="text"
          className={styles.titleInput}
          placeholder="Add a new task..."
          value={title}
          onChange={(e) => setTitle(e.target.value)} // Update state on every keystroke
          aria-label="Task title"
        />

        {/* 📘 type="date" renders a native date picker in the browser */}
        <input
          type="date"
          className={styles.dateInput}
          value={dueDate}
          onChange={(e) => setDueDate(e.target.value)}
          aria-label="Due date (optional)"
        />

        {/* 📘 type="submit" triggers the form's onSubmit when clicked */}
        <button type="submit" className={styles.addButton} disabled={!title.trim()}>
          Add Task
        </button>
      </div>
    </form>
  );
}

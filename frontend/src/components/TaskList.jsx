// 📘 WHAT THIS FILE DOES: Renders the list of tasks, passing events down to TaskItem.
// This is a "presentational" component — it receives data and functions as props,
// and renders TaskItem for each task. It does not manage state or call the API.
// 🔗 React lists reference: https://www.w3schools.com/react/react_lists.asp

import TaskItem from "./TaskItem";
import styles from "./TaskList.module.css";

/**
 * TaskList — renders the filtered task list or an empty state message.
 * Props:
 *   tasks    — array of task objects to display
 *   onToggle, onDelete, onUpdate — event handlers passed through to each TaskItem
 */
export default function TaskList({ tasks, onToggle, onDelete, onUpdate }) {
  // 📘 Show an encouraging message when there are no tasks to display
  if (tasks.length === 0) {
    return (
      <div className={styles.empty}>
        <p>No tasks here. Add one above!</p>
      </div>
    );
  }

  return (
    // 📘 <ul> (unordered list) is the semantic HTML element for a list of items.
    // Each TaskItem renders as an <li> inside this <ul>.
    <ul className={styles.list}>
      {/* 📘 .map() transforms each task object into a TaskItem component.
           The 'key' prop is required by React to efficiently update the list. */}
      {tasks.map((task) => (
        <TaskItem
          key={task.id}        // 📘 key must be unique — task.id is perfect for this
          task={task}
          onToggle={onToggle}
          onDelete={onDelete}
          onUpdate={onUpdate}
        />
      ))}
    </ul>
  );
}

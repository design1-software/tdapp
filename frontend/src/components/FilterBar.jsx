// 📘 WHAT THIS FILE DOES: Renders the filter bar — task count, filter tabs, and clear button.
// Lives at the top of the task list. All state is lifted up to App.jsx; this component
// only renders what it receives via props and calls callbacks when the user interacts.
// 🔗 React props reference: https://www.w3schools.com/react/react_props.asp

import styles from "./FilterBar.module.css";

// 📘 FILTERS is defined outside the component because it never changes.
// It's a constant that maps display labels to the filter value used in state.
const FILTERS = [
  { label: "All",       value: "all"       },
  { label: "Active",    value: "active"    },
  { label: "Completed", value: "completed" },
];

/**
 * FilterBar — task count + filter tabs + clear completed button.
 * Props:
 *   filter           — current active filter: 'all' | 'active' | 'completed'
 *   onFilterChange   — called with the new filter value when a tab is clicked
 *   incompleteCount  — number of tasks NOT yet completed
 *   completedCount   — number of tasks that ARE completed
 *   onClearCompleted — called when the "Clear completed" button is clicked
 */
export default function FilterBar({
  filter,
  onFilterChange,
  incompleteCount,
  completedCount,
  onClearCompleted,
}) {
  return (
    <div className={styles.bar}>
      {/* ── TASK COUNT ── */}
      {/* 📘 Template literal: `${n} task${n !== 1 ? 's' : ''}` adds an 's' for plural */}
      <span className={styles.count}>
        {incompleteCount} {incompleteCount === 1 ? "task" : "tasks"} remaining
      </span>

      {/* ── FILTER TABS ── */}
      <nav className={styles.filters} aria-label="Filter tasks">
        {FILTERS.map(({ label, value }) => (
          <button
            key={value}
            className={`${styles.filterBtn} ${filter === value ? styles.active : ""}`}
            onClick={() => onFilterChange(value)}
            aria-pressed={filter === value} // 📘 aria-pressed helps screen readers understand toggle state
          >
            {label}
          </button>
        ))}
      </nav>

      {/* ── CLEAR COMPLETED ── */}
      {/* 📘 Only render this button when there are completed tasks to clear */}
      {completedCount > 0 && (
        <button className={styles.clearBtn} onClick={onClearCompleted}>
          Clear completed ({completedCount})
        </button>
      )}
    </div>
  );
}

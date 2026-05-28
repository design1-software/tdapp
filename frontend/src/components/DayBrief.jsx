// 📘 WHAT THIS FILE DOES: Renders the AI Day Brief panel.
// Shows a "Generate Day Brief" button. When clicked, calls the /brief endpoint,
// then displays the four OPORD sections in a structured card.
// Handles loading, error, and dismiss states cleanly.
// 🔗 React conditional rendering: https://www.w3schools.com/react/react_conditional_rendering.asp

import styles from "./DayBrief.module.css";

/**
 * DayBrief — AI daily summary panel.
 * Props:
 *   brief        — null, or the BriefResponse object from the API
 *   loading      — true while the API call is in progress
 *   error        — error message string, or null
 *   onGenerate() — called when the user clicks "Generate Day Brief"
 *   onDismiss()  — called when the user clicks the dismiss button
 */
export default function DayBrief({ brief, loading, error, onGenerate, onDismiss }) {
  return (
    <div className={styles.wrapper}>
      {/* ── TRIGGER BUTTON ── */}
      {/* 📘 Only show the button when a brief isn't already displayed */}
      {!brief && (
        <button
          className={styles.generateBtn}
          onClick={onGenerate}
          disabled={loading}
          aria-busy={loading}
        >
          {/* 📘 Ternary operator: condition ? valueIfTrue : valueIfFalse */}
          {loading ? "Generating brief…" : "✦ Generate Day Brief"}
        </button>
      )}

      {/* ── ERROR STATE ── */}
      {error && !brief && (
        <p className={styles.error} role="alert">{error}</p>
      )}

      {/* ── BRIEF PANEL ── */}
      {/* 📘 This section only renders when 'brief' is not null */}
      {brief && (
        <div className={styles.panel}>
          {/* Header row with title and dismiss button */}
          <div className={styles.panelHeader}>
            <div>
              <span className={styles.panelTitle}>✦ Day Brief</span>
              <span className={styles.panelMeta}>
                {brief.task_count} task{brief.task_count !== 1 ? "s" : ""} ·{" "}
                {new Date(brief.generated_at).toLocaleTimeString("en-US", {
                  hour: "numeric",
                  minute: "2-digit",
                })}
              </span>
            </div>
            <button
              className={styles.dismissBtn}
              onClick={onDismiss}
              aria-label="Dismiss brief"
            >
              ✕
            </button>
          </div>

          {/* ── SITUATION ── */}
          <p className={styles.situation}>{brief.brief.situation}</p>

          {/* ── FOUR OPORD SECTIONS ── */}
          <div className={styles.sections}>
            <BriefSection
              title="Priority Order"
              items={brief.brief.priority_order}
              emptyText="No active tasks"
              accent="blue"
            />
            <BriefSection
              title="Active Tasks"
              items={brief.brief.tasks_for_today}
              emptyText="Nothing active"
              accent="blue"
            />
            <BriefSection
              title="Completed (24h)"
              items={brief.brief.completed_recently}
              emptyText="Nothing completed recently"
              accent="green"
            />
          </div>

          {/* Regenerate button at the bottom of the panel */}
          <button
            className={styles.regenerateBtn}
            onClick={onGenerate}
            disabled={loading}
          >
            {loading ? "Generating…" : "↺ Regenerate"}
          </button>
        </div>
      )}
    </div>
  );
}

/**
 * BriefSection — renders one OPORD section (a heading + bulleted list).
 * Props:
 *   title     — section heading string
 *   items     — array of task title strings
 *   emptyText — shown when items is empty
 *   accent    — 'blue' | 'green' — controls the bullet color
 */
function BriefSection({ title, items, emptyText, accent }) {
  return (
    <div className={styles.section}>
      <h3 className={`${styles.sectionTitle} ${styles[accent]}`}>{title}</h3>
      {items.length === 0 ? (
        <p className={styles.emptySection}>{emptyText}</p>
      ) : (
        // 📘 <ol> is an ordered list — numbers are rendered automatically.
        <ol className={styles.list}>
          {items.map((item, i) => (
            <li key={i} className={styles.listItem}>{item}</li>
          ))}
        </ol>
      )}
    </div>
  );
}

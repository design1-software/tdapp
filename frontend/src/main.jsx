// 📘 WHAT THIS FILE DOES: Entry point for the React application.
// This is the first JavaScript file Vite loads. It mounts the React app into index.html's <div id="root">.
// 🔗 React reference: https://react.dev/learn

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css"; // 📘 Global CSS — loaded once here, applies to the whole page
import App from "./App.jsx"; // 📘 The root component that contains all other components

// 📘 createRoot() connects React to the HTML element with id="root" in index.html.
// .render() tells React what component tree to display inside that element.
// StrictMode helps catch bugs during development — it intentionally runs some code twice.
createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);

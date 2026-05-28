// 📘 WHAT THIS FILE DOES: Configures the Vite build tool for the React frontend.
// Vite is the modern replacement for Create React App — faster builds, actively maintained.
// 🔗 Vite reference: https://vitejs.dev/config/

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()], // 📘 The React plugin adds JSX support and Fast Refresh during development
});

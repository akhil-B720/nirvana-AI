/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        command: {
          dark: "#0a0f1d",
          panel: "#0f172a",
          border: "#1e293b",
          accent: "#0284c7",
          cyan: "#06b6d4",
          success: "#10b981",
          warning: "#f59e0b",
          danger: "#ef4444",
        }
      }
    },
  },
  plugins: [],
}

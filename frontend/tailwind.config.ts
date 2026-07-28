import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "var(--canvas)",
        "canvas-elevated": "var(--canvas-elevated)",
        surface: "var(--surface)",
        "surface-hover": "var(--surface-hover)",
        border: "var(--border)",
        "border-subtle": "var(--border-subtle)",
        "border-strong": "var(--border-strong)",
        ink: "var(--ink)",
        "ink-secondary": "var(--ink-secondary)",
        "ink-tertiary": "var(--ink-tertiary)",
        "ink-inverse": "var(--ink-inverse)",
        accent: "var(--accent)",
        "accent-hover": "var(--accent-hover)",
        "accent-muted": "var(--accent-muted)",
        danger: "var(--danger)",
        success: "var(--success)",
        warning: "var(--warning)",
      },
      borderRadius: {
        sm: "6px",
        md: "8px",
        lg: "12px",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      fontSize: {
        display: ["32px", { lineHeight: "40px", fontWeight: "600" }],
        "title-1": ["24px", { lineHeight: "32px", fontWeight: "600" }],
        "title-2": ["20px", { lineHeight: "28px", fontWeight: "600" }],
        "title-3": ["16px", { lineHeight: "24px", fontWeight: "600" }],
        body: ["14px", { lineHeight: "20px" }],
        caption: ["12px", { lineHeight: "16px" }],
      },
      boxShadow: {
        sm: "0 1px 3px rgba(18, 22, 28, 0.08)",
        md: "0 8px 24px rgba(18, 22, 28, 0.1)",
      },
    },
  },
  plugins: [],
};

export default config;

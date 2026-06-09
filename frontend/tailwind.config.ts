import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        shell: "hsl(var(--shell))",
        panel: "hsl(var(--panel))",
        ink: "hsl(var(--ink))",
        muted: "hsl(var(--muted))",
        line: "hsl(var(--line))",
        accent: "hsl(var(--accent))",
        amber: "hsl(var(--amber))",
        coral: "hsl(var(--coral))",
        teal: "hsl(var(--teal))"
      },
      boxShadow: {
        soft: "0 16px 40px rgba(15, 23, 42, 0.12)"
      }
    }
  },
  plugins: []
};

export default config;

import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#05070B",
        surface: {
          DEFAULT: "#131B2E",
          raised: "#1A2438",
          dark: "#0B1220",
        },
        border: {
          DEFAULT: "#1F2A44",
          light: "rgba(255, 255, 255, 0.08)",
        },
        foreground: {
          DEFAULT: "#E8E6DE",
          muted: "#94A3B8",
        },
        accent: {
          DEFAULT: "#C8973B",
          hover: "#DDAE55",
          muted: "rgba(200, 151, 59, 0.15)",
        },
        risk: {
          critical: "#8B2E2E",
          high: "#B8562E",
          medium: "#C8973B",
          low: "#5B7A6B",
        },
      },
      fontFamily: {
        sans: ["'IBM Plex Sans'", "-apple-system", "BlinkMacSystemFont", "'Segoe UI'", "sans-serif"],
        serif: ["'Source Serif 4'", "Georgia", "serif"],
        mono: ["'IBM Plex Mono'", "Menlo", "Monaco", "monospace"],
      },
      keyframes: {
        radarPulse: {
          "0%": { boxShadow: "0 0 0 0 rgba(139, 46, 46, 0.6)" },
          "70%": { boxShadow: "0 0 0 8px rgba(139, 46, 46, 0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(139, 46, 46, 0)" },
        },
        goldPulse: {
          "0%": { boxShadow: "0 0 0 0 rgba(200, 151, 59, 0.5)" },
          "70%": { boxShadow: "0 0 0 6px rgba(200, 151, 59, 0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(200, 151, 59, 0)" },
        },
      },
      animation: {
        radarPulse: "radarPulse 2.5s infinite ease-out",
        goldPulse: "goldPulse 2s infinite ease-out",
      },
    },
  },
  plugins: [],
};

export default config;

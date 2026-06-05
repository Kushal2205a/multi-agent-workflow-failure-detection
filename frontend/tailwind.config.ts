import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        charcoal: {
          DEFAULT: "#0d0d0d",
          900: "#1a1a1a",
          800: "#1f1f1f",
          700: "#2a2a2a",
        },
        baseline: "#ef4444",
        protected: "#22c55e",
        reviewer: "#3b82f6",
        deadlock: "#dc2626",
      },
    },
  },
  plugins: [],
};

export default config;

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
      },
    },
  },
  plugins: [],
};

export default config;

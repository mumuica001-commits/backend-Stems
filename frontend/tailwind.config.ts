import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: {
          bg: "#0A0D14",
          panel: "#12172380",
          panelSolid: "#151B27",
          border: "#232B3A",
        },
        stem: {
          vocals: "#FF6F5E",     // coral
          drums: "#F5A623",      // âmbar
          bass: "#8B5CF6",       // violeta
          guitar: "#A3E635",     // verde-lima
          piano: "#38BDF8",      // azul-céu
          other: "#94A3B8",      // cinza-azulado
        },
        spectral: {
          from: "#6D28D9", // índigo
          via: "#DB2777",  // magenta
          to: "#F59E0B",   // âmbar
        },
      },
      fontFamily: {
        display: ["var(--font-space-grotesk)", "sans-serif"],
        body: ["var(--font-inter)", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "monospace"],
      },
      backgroundImage: {
        "spectral-gradient": "linear-gradient(90deg, #6D28D9 0%, #DB2777 50%, #F59E0B 100%)",
      },
      backdropBlur: {
        glass: "24px",
      },
      keyframes: {
        pulse_bar: {
          "0%, 100%": { transform: "scaleY(0.3)" },
          "50%": { transform: "scaleY(1)" },
        },
      },
      animation: {
        pulse_bar: "pulse_bar 1.2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;

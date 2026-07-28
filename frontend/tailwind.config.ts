import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      // ── Paleta EntreLíneas — sala de lectura ──────────────────────────────
      colors: {
        // Maderas
        walnut:   { DEFAULT: "#2C1F14", light: "#3D2B1A" },
        mahogany: { DEFAULT: "#4A2E1A", light: "#5C3A22" },
        teak:     { DEFAULT: "#8B5E3C", light: "#A67550" },

        // Metales
        brass:    { DEFAULT: "#B8892A", light: "#D4A853", dark: "#8A6620" },

        // Papeles
        parchment: { DEFAULT: "#F5EDD8", dim: "#EDE3C8", deep: "#E0D0AE" },
        cream:     { DEFAULT: "#FBF6EC", dim: "#F3ECD8" },

        // Tintas
        ink: {
          DEFAULT: "#1E140A",
          soft:    "#5C4A36",
          faint:   "#9C8670",
        },

        // Estados semánticos — contexto biblioteca
        reading:  { DEFAULT: "#2E5C3E", light: "#3D7550" }, // leyendo
        leather:  { DEFAULT: "#6B3A2A", light: "#A05A44" }, // cuero / acento
      },

      // ── Tipografía ────────────────────────────────────────────────────────
      fontFamily: {
        serif: ["var(--font-playfair)", "Georgia", "serif"],
        sans:  ["var(--font-inter)", "system-ui", "sans-serif"],
      },

      // ── Sombras de biblioteca ─────────────────────────────────────────────
      boxShadow: {
        // Lomo de libro contra el estante
        spine:  "2px 0 6px rgba(28, 16, 8, 0.30), inset -1px 0 0 rgba(255,255,255,0.07)",
        // Tabla del estante (borde inferior del grupo de lomos)
        shelf:  "0 4px 12px -2px rgba(28, 16, 8, 0.20)",
        // Tarjetas y paneles
        card:   "0 1px 3px rgba(28, 16, 8, 0.08), 0 1px 2px rgba(28, 16, 8, 0.05)",
        // Elevación suave para modales / drawers
        modal:  "0 8px 32px -4px rgba(28, 16, 8, 0.18)",
      },

      // ── Bordes ────────────────────────────────────────────────────────────
      borderColor: {
        DEFAULT: "#D6C9AE", // borde cálido, no gris neutro
      },
      borderRadius: {
        book: "2px 5px 5px 2px", // lomo de libro: esquina izq. recta, der. redondeada
      },

      // ── Backgrounds ───────────────────────────────────────────────────────
      backgroundColor: {
        page:  "#F5EDD8", // parchment — fondo base de la app
        panel: "#FBF6EC", // cream — tarjetas y paneles sobre el fondo
      },
    },
  },
  plugins: [],
};

export default config;

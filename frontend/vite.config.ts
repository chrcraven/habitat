import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// See /CLAUDE.md and /docs/tech-stack-options.md for why React + MapLibre GL.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
  },
});

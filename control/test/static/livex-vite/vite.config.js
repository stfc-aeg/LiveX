import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],

  resolve: {
    dedupe: ["react", "react-dom", "bootstrap", "react-bootstrap", "odin-react"]
  },

  optimizeDeps: {
    include: ["bootstrap", "react-bootstrap"]
  }
});
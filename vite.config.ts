import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  // GitHub Pages uses the repo name as base path
  // For mobile builds (Capacitor), use root path '/'
  base: mode === 'production'
    ? (process.env.BUILD_TARGET === 'mobile' ? '/' : '/-Senior-Design-SpeakEasy/')
    : '/',
  server: {
    host: "::",
    port: 8080,
  },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));

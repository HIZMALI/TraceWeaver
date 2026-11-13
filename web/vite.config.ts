import { defineConfig } from "vite";

export default defineConfig({
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: {
      "/incidents": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/health": "http://127.0.0.1:8000",
      "/console": "http://127.0.0.1:8000",
    },
  },
  build: {
    outDir: "../src/traceweaver/web_static",
    emptyOutDir: true,
    sourcemap: false,
    chunkSizeWarningLimit: 650,
  },
});

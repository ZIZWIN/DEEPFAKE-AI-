import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";
import type { Connect } from "vite";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Plugin to serve the project-level docs/ folder at /docs/* in dev mode
function docsPlugin() {
  const docsDir = path.resolve(__dirname, "../docs");
  return {
    name: "serve-docs",
    configureServer(server: { middlewares: Connect.Server }) {
      server.middlewares.use("/docs", (req, res, next) => {
        const reqPath = (req.url || "/").split("?")[0];
        const filePath = path.join(docsDir, reqPath === "/" ? "index.html" : reqPath);
        if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
          res.setHeader("Content-Type", filePath.endsWith(".html") ? "text/html" : "application/octet-stream");
          fs.createReadStream(filePath).pipe(res as any);
        } else {
          next();
        }
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), docsPlugin()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});

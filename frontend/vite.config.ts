import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vitest/config";

// Only public project documentation is served/copied; never expose repository files.
const documents = [
  "API.md",
  "TRAINING.md",
  "MODEL_QUALITY.md",
  "ARCHITECTURE.md",
  "FRONTEND.md",
];
const documentText = (name: string) =>
  readFileSync(
    fileURLToPath(new URL(`../docs/${name}`, import.meta.url)),
    "utf8",
  );
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    {
      name: "public-documentation",
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          const name = req.url?.split("?")[0]?.replace(/^\/docs\//, "");
          if (
            req.url?.startsWith("/docs/") &&
            name &&
            documents.includes(name)
          ) {
            res.setHeader("Content-Type", "text/plain; charset=utf-8");
            res.end(documentText(name));
          } else next();
        });
      },
      generateBundle() {
        for (const name of documents)
          this.emitFile({
            type: "asset",
            fileName: `docs/${name}`,
            source: documentText(name),
          });
      },
    },
  ],
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    include: ["src/**/*.test.{ts,tsx}"],
    restoreMocks: true,
  },
});

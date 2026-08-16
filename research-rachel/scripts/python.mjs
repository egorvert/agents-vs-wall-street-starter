import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";

const virtualEnvironmentPython = path.resolve(
  ".venv",
  process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
);
const fallbackPython = process.platform === "win32" ? "python" : "python3";
const python = existsSync(virtualEnvironmentPython) ? virtualEnvironmentPython : fallbackPython;

const result = spawnSync(python, process.argv.slice(2), { stdio: "inherit" });

if (result.error) {
  console.error(`Unable to start ${python}: ${result.error.message}`);
  process.exit(1);
}

process.exit(result.status ?? 1);

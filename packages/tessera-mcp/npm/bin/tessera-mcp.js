#!/usr/bin/env node
"use strict";

// Launch the Python `tessera-mcp` server. Prefer an ephemeral `uvx` run so the
// user needs nothing pre-installed except (optionally) uv.
//
// If uv is missing, we do NOT silently pipe a remote script to a shell. The
// auto-install of uv (which downloads and runs the official installer) is
// opt-in via TESSERA_AUTO_INSTALL_UV=1. Otherwise we print instructions and
// exit non-zero so the user can install uv themselves.
const { spawnSync } = require("node:child_process");

function runUvx() {
  return spawnSync("uvx", ["--from", "tessera-mcp", "tessera-mcp"], {
    stdio: "inherit",
  });
}

function installUv() {
  const isWindows = process.platform === "win32";
  const cmd = isWindows
    ? 'powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"'
    : "curl -LsSf https://astral.sh/uv/install.sh | sh";
  return spawnSync(isWindows ? "powershell" : "sh", ["-c", cmd], {
    stdio: "inherit",
  });
}

let res = runUvx();
if (res.error && res.error.code === "ENOENT") {
  if (process.env.TESSERA_AUTO_INSTALL_UV === "1") {
    process.stderr.write(
      "uv not found; TESSERA_AUTO_INSTALL_UV=1 set, downloading and running the official uv installer...\n"
    );
    installUv();
    res = runUvx();
  } else {
    process.stderr.write(
      "tessera-mcp requires `uv` but it was not found on PATH.\n" +
        "Install uv from https://astral.sh/uv, or `pip install tessera-mcp` and run `tessera-mcp` directly.\n" +
        "To let this wrapper download and run the official uv installer automatically, " +
        "re-run with TESSERA_AUTO_INSTALL_UV=1.\n"
    );
    process.exit(1);
  }
}
if (res.error) {
  process.stderr.write(
    "Failed to start tessera-mcp. Install uv (https://astral.sh/uv) or " +
      "`pip install tessera-mcp` and run `tessera-mcp` directly.\n"
  );
  process.exit(1);
}
process.exit(res.status === null ? 1 : res.status);

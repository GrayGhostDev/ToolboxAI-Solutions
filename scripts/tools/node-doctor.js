#!/usr/bin/env node

/**
 * Node Doctor - verifies Node and npm availability from the current environment
 * and prints actionable guidance to fix IDE plugin errors when npm is not found.
 */

import { execSync } from "node:child_process";
import os from "node:os";
import path from "node:path";

const log = (...args) => console.log(...args);
const warn = (...args) => console.warn(...args);
const err = (...args) => console.error(...args);

function checkNode() {
  try {
    const version = process.version; // e.g. v20.11.1
    log(`Node detected: ${version}`);
    return true;
  } catch {
    err("Node is not available in this environment.");
    return false;
  }
}

function checkNpm() {
  try {
    const out = execSync("npm -v", { stdio: ["ignore", "pipe", "pipe"] })
      .toString()
      .trim();
    log(`npm detected: ${out}`);
    return true;
  } catch (e) {
    err("npm is NOT available from this environment.");
    if (e?.stderr) {
      const s = e.stderr.toString().trim();
      if (s) warn(`stderr: ${s}`);
    }
    return false;
  }
}

function guidance() {
  const platform = os.platform();
  const shell = process.env.SHELL || process.env.ComSpec || "unknown";

  log("\nHow to fix:");
  if (platform === "darwin") {
    log("- Install Node.js (includes npm):");
    log("  Homebrew: brew install node");
    log("  Or nvm:   curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash");
    log("            then: nvm install --lts && nvm use --lts");
    log("- Ensure the IDE sees your PATH. If using nvm, launch the IDE from a terminal:");
    log('  open -na "IntelliJ IDEA.app"');
    log("- Or set Node interpreter in IDE: Preferences > Languages & Frameworks > Node.js");
  } else if (platform === "linux") {
    log("- Install Node.js (includes npm). For Debian/Ubuntu:");
    log("  curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -");
    log("  sudo apt-get install -y nodejs");
    log("- Ensure PATH is inherited by the IDE or launch the IDE from a terminal.");
  } else if (platform === "win32") {
    log("- Install Node.js LTS from https://nodejs.org or run:");
    log("  winget install OpenJS.NodeJS.LTS");
    log('- Ensure "C:\\\\Program Files\\\\nodejs" is in your PATH.');
    log("- Restart the IDE after installation.");
    log("- In IDE: Settings > Languages & Frameworks > Node.js: set the Node interpreter.");
  } else {
    log("- Install Node.js LTS 20+ for your platform from https://nodejs.org");
  }

  log("\nProject tips:");
  log("- This repo contains an .nvmrc (Node 20). If you use nvm:");
  log("    nvm install && nvm use");
  log("- Verify in a terminal:");
  log("    node -v && npm -v");
  log("- If npm works in your terminal but the IDE still fails, start the IDE from that terminal.");
  log("- Temporary workaround: disable the dependency analysis plugin triggering npm until Node/npm is installed.");
  log(`\nDetected shell: ${shell}`);
  log(`PATH: ${process.env.PATH || ""}`);
  log(`Node executable: ${process.execPath}`);
}

const okNode = checkNode();
const okNpm = okNode && checkNpm();

if (!okNpm) {
  guidance();
  process.exitCode = 1;
} else {
  log("\nEnvironment looks good. You can proceed with:");
  log("- npm ci  (install dependencies)");
  log("- npm run dev  (in the dashboard package)");
}

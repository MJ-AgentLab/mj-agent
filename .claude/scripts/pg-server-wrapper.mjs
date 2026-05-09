#!/usr/bin/env node
// Wrapper for @modelcontextprotocol/server-postgres
// Fix #38: override pg type parsers to return raw timestamp strings
// instead of JS Date objects (which JSON.stringify converts to UTC "Z" format)
//
// Mechanism:
//   1. CJS require("pg") via createRequire — honors NODE_PATH set by pg-server-start.cmd
//   2. pg.types.setTypeParser overrides OID 1114/1184 to return raw strings
//   3. CJS and ESM share the same pg module instance (verified: require("pg") === import("pg").default)
//   4. Dynamic import of server-postgres — its internal pg.Pool uses the overridden parsers
//
// Why not ESM import:
//   ESM bare specifier resolution ignores NODE_PATH and only searches
//   node_modules/ from the importing file's directory upward. This script
//   lives in <repo>/.claude/scripts/, outside the npx cache.

import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
import { dirname, join } from "node:path";
import { existsSync } from "node:fs";

const require = createRequire(import.meta.url);

try {
  // 1. Override pg type parsers (CJS require honors NODE_PATH)
  const pg = require("pg");
  pg.types.setTypeParser(1114, (val) => val); // timestamp without time zone
  pg.types.setTypeParser(1184, (val) => val); // timestamp with time zone

  // 2. Derive server-postgres entry path from pg's package.json location
  //    pg/package.json → <node_modules>/pg/package.json
  //    dirname twice   → <node_modules>/
  const pgPkgPath = require.resolve("pg/package.json");
  const nmBase = dirname(dirname(pgPkgPath));
  const serverEntry = join(nmBase, "@modelcontextprotocol", "server-postgres", "dist", "index.js");

  if (!existsSync(serverEntry)) {
    console.error(`[pg-wrapper] ERROR: server-postgres entry not found at ${serverEntry}`);
    process.exit(1);
  }

  // 3. Dynamic import of the original server (ESM, file:// URL)
  await import(pathToFileURL(serverEntry).href);
} catch (err) {
  if (err.code === 'MODULE_NOT_FOUND') {
    console.error('[pg-wrapper] ERROR: npx cache appears corrupted — missing dependency.');
    console.error('[pg-wrapper] FIX: Delete the npx cache directory and restart Claude Code:');
    console.error('  Windows:  rd /s /q "%LOCALAPPDATA%\\npm-cache\\_npx"');
    console.error('  Unix:     rm -rf "$HOME/.npm/_npx"');
  }
  console.error("[pg-wrapper] ERROR:", err.message);
  process.exit(1);
}

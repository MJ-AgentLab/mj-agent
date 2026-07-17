@echo off
setlocal enabledelayedexpansion
REM Bootstrap for @modelcontextprotocol/server-postgres with timestamp fix
REM Fix #38: Discovers npx cache path, sets NODE_PATH, launches ESM wrapper
REM
REM Why this script exists:
REM   ESM module resolution ignores NODE_PATH, so pg-server-wrapper.mjs
REM   cannot directly import "pg" from the npx cache. This CMD script
REM   scans the npx cache directory to find the pg package, then sets
REM   NODE_PATH so CJS createRequire can resolve it in the wrapper.
REM
REM Discovery strategy:
REM   require.resolve('pg') does NOT work from node -e under npx -p,
REM   because -e scripts resolve from CWD, not the npx cache.
REM   Instead we use fs.existsSync to scan npm_config_cache/_npx/
REM   for the directory containing node_modules/pg — this uses only
REM   Node.js built-in modules (fs, path) which are always available.
REM
REM Usage: pg-server-start.cmd <connection-env-var-NAME>
REM   The single positional arg is the NAME of an environment variable
REM   (e.g. MJ_AGENT_PG_MEMORY_DEV_URL); the connection URL is resolved from that
REM   variable's value. There is NO inline default -- an unset variable is an explicit
REM   failure (never silently connect to a fallback). Single source of truth =
REM   secrets-mcp.enc -> HKCU env (Claude: .mcp.json `env`; Codex: `env_vars`).
REM   URLs SHOULD be percent-encoded per RFC 3986 (reserved password chars %-encoded).
REM   See #353 / dual-agent-compat item 3 (pg-credential single source of truth).

REM Fail fast: require the connection variable NAME before running npx discovery.
if "%~1"=="" (
  echo [pg-server] ERROR: missing connection variable name argument ^(e.g. MJ_AGENT_PG_MEMORY_DEV_URL^) 1>&2
  exit /b 2
)

:DISCOVER
REM Step 1: Install package (if needed) and discover node_modules path
REM   - npx -y auto-confirms installation
REM   - 2^>nul suppresses npx stderr (install progress, warnings)
REM   - fs.existsSync scans npx cache dirs for pg package
REM   - process.stdout.write outputs ONLY the path (no trailing newline)
for /f "usebackq tokens=*" %%i in (`npx -y -p @modelcontextprotocol/server-postgres node -e "const fs=require('fs'),path=require('path');const base=path.join(process.env.npm_config_cache,'_npx');const dirs=fs.readdirSync(base);for(const d of dirs){if(fs.existsSync(path.join(base,d,'node_modules','pg'))){process.stdout.write(path.join(base,d,'node_modules'));break}}" 2^>nul`) do set "NODE_PATH=%%i"

if not defined NODE_PATH (
  echo [pg-wrapper] ERROR: Could not discover npx cache path 1>&2
  exit /b 1
)

REM Validate NODE_PATH was not polluted by unexpected npx stdout
if not exist "%NODE_PATH%\pg" (
  echo [pg-wrapper] ERROR: NODE_PATH does not contain pg: %NODE_PATH% 1>&2
  exit /b 1
)

REM Step 2: Dependency integrity check
REM   Verify critical transitive dependencies have package.json (not just empty dirs).
REM   npx download interruption can leave empty directories that pass existsSync
REM   but fail at require() time — a "sticky" failure that never self-heals.
REM   See: https://github.com/MJ-AgentLab/mj-agentlab-marketplace/issues/46
set "CACHE_BROKEN="
for %%D in (pg-types postgres-date postgres-array postgres-bytea postgres-interval pg-connection-string) do (
    if not exist "%NODE_PATH%\%%D\package.json" set "CACHE_BROKEN=%%D"
)

if defined CACHE_BROKEN (
    if defined RETRY_DONE (
        echo [pg-server] ERROR: npx cache still broken after cleanup — missing !CACHE_BROKEN! 1>&2
        exit /b 1
    )
    echo [pg-server] WARN: Broken npx cache ^(missing !CACHE_BROKEN!\package.json^). Cleaning for re-download... 1>&2
    set "RETRY_DONE=1"
    REM Delete the corrupted npx hash directory (parent of node_modules)
    for /f "delims=" %%P in ("%NODE_PATH%\..") do rd /s /q "%%~fP" 2>nul
    set "NODE_PATH="
    goto :DISCOVER
)

REM Step 3: Resolve the connection URL from the variable NAME (arg %1) and launch.
REM   Nest a disabledelayedexpansion scope so a literal bang char in a password is never
REM   consumed during resolution -- UNCONDITIONALLY (independent of the caller's /V:ON|OFF
REM   state; verified by #353 Spike 1d). NODE_PATH + parent env (MJ_AGENT_PG_*_URL, set by
REM   Claude .mcp.json `env` / Codex `env_vars`) are inherited into the nested scope.
setlocal disabledelayedexpansion
set "PG_CONN_NAME=%~1"
call set "PG_CONN_URL=%%%PG_CONN_NAME%%%"
if not defined PG_CONN_URL (
  echo [pg-server] ERROR: connection env var %PG_CONN_NAME% is not set 1>&2
  echo [pg-server] FIX: set it via .claude\scripts\setup-mcp-secrets.ps1 -Reload, or .mcp.json env 1>&2
  exit /b 3
)

REM Step 4: Launch the ESM wrapper with resolved NODE_PATH + resolved URL as argv[2]
REM   (unchanged wrapper / server-postgres contract; %~dp0 = this script's directory).
node "%~dp0pg-server-wrapper.mjs" "%PG_CONN_URL%"

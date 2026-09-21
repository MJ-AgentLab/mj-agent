// Native project wrapper: preserve #38 raw timestamp parsers and by-name injection.
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { dirname, join } from 'node:path';
const require = createRequire(import.meta.url);
const allowed = new Set(['MJ_AGENT_PG_MEMORY_DEV_URL', 'MJ_AGENT_PG_MEMORY_TEST_LAN_URL',
  'MJ_AGENT_PG_MEMORY_TEST_WAN_URL', 'MJ_AGENT_PG_MEMORY_PROD_LAN_URL', 'MJ_AGENT_PG_MEMORY_PROD_WAN_URL']);
try {
  const name = process.argv[2];
  if (!allowed.has(name) || !process.env[name]?.trim()) throw new Error('missing');
  const pg = require('pg');
  pg.types.setTypeParser(1114, val => val);
  pg.types.setTypeParser(1184, val => val);
  const base = dirname(dirname(require.resolve('pg/package.json')));
  // Upstream consumes argv[2]; this assignment stays inside this process.
  process.argv[2] = process.env[name];
  await import(pathToFileURL(join(base, '@modelcontextprotocol/server-postgres/dist/index.js')).href);
} catch {
  // Dependency/driver exceptions may contain the URL. Never print their messages.
  console.error('[ERROR] project PG MCP wrapper failed; dependency or connection unavailable');
  process.exitCode = 1;
}

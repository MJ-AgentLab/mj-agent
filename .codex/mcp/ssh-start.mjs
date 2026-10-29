import { readFileSync, existsSync } from 'node:fs';
import { validateRoster, listServers, prepareEnvironment, defaultKnownHosts } from './ssh-runtime.mjs';

try {
  const roster = JSON.parse(readFileSync(new URL('./ssh-servers.json', import.meta.url), 'utf8'));
  validateRoster(roster);
  const safe = prepareEnvironment(process.env);
  // Scope this process only, before loading third-party dependencies. Never write user config/env.
  for (const name of Object.keys(process.env)) delete process.env[name];
  Object.assign(process.env, safe);
  if (process.argv.slice(2).join() === '--check') {
    console.log(JSON.stringify({ config: 'STATIC_PASS', servers: listServers(roster, safe),
      knownHostsFilePresent: existsSync(defaultKnownHosts()), connection: 'NOT_TESTED' }));
  } else if (process.argv.length === 2) {
    const { serve } = await import('./ssh-server.mjs');
    await serve(roster, safe);
  } else {
    throw new Error();
  }
} catch {
  console.error('SSH_MCP_START_FAILED: check project files, locked dependencies and approved variable presence; no fallback');
  process.exitCode = 1;
}

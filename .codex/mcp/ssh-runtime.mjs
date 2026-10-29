// Only fixed project metadata, named process variables and public known_hosts.
// No dotenv, credential store, private keys, user SSH config or automatic fallback.
import { execFileSync } from 'node:child_process';
import { timingSafeEqual } from 'node:crypto';
import { homedir } from 'node:os';
import { join } from 'node:path';

export const PASSWORD_NAMES = ['CLOUD', 'RUNNER', 'TEST', 'PROD', 'DGX']
  .map(group => `MJ_SYS_SSH_SERVER_${group}_PASSWORD`);

const BINDINGS = [
  ['CLOUD', '8.135.38.175', 22, 'root', 0],
  ['RUNNER_LAN', '192.168.0.126', 22, 'mingjian', 1],
  ['RUNNER_WAN', '8.135.38.175', 2201, 'mingjian', 1],
  ['TEST_LAN', '192.168.0.179', 22, 'mingjian02', 2],
  ['TEST_WAN', '8.135.38.175', 2202, 'mingjian02', 2],
  ['PROD_LAN', '192.168.0.106', 22, 'mingjian03', 3],
  ['PROD_WAN', '8.135.38.175', 2203, 'mingjian03', 3],
  ['DGX_LAN', '192.168.0.189', 22, 'ranzuozhou', 4],
  ['DGX_WAN', '8.135.38.175', 2204, 'ranzuozhou', 4],
];

export function validateRoster(roster) {
  const fields = ['description', 'host', 'id', 'passwordEnv', 'port', 'user'];
  if (!Array.isArray(roster) || roster.length !== BINDINGS.length ||
      roster.some((s, i) => !s || Object.keys(s).sort().join() !== fields.join() ||
        [s.id, s.host, s.port, s.user, s.passwordEnv].join('|') !==
        [...BINDINGS[i].slice(0, 4), PASSWORD_NAMES[BINDINGS[i][4]]].join('|') ||
        typeof s.description !== 'string' || !/^[A-Za-z0-9-]{1,80}$/.test(s.description))) {
    throw new Error('INVALID_SSH_ROSTER');
  }
}

export function prepareEnvironment(source) {
  const safe = ['PATH', 'Path', 'SystemRoot', 'SYSTEMROOT', 'WINDIR', 'COMSPEC',
    'HOME', 'USERPROFILE', 'HOMEDRIVE', 'HOMEPATH', 'TEMP', 'TMP', ...PASSWORD_NAMES];
  return Object.fromEntries(safe.filter(name => typeof source[name] === 'string')
    .map(name => [name, source[name]]));
}

export function listServers(roster, env) {
  return roster.map(s => ({ name: s.id.toLowerCase().replaceAll('_', '-'),
    host: s.host, port: s.port, user: s.user, description: s.description,
    credentialPresent: Boolean(env[s.passwordEnv]) }));
}

export function defaultKnownHosts() {
  return join(homedir(), '.ssh', 'known_hosts');
}

export function trustedKeys(server, knownHostsPath, run = execFileSync) {
  const target = server.port === 22 ? server.host : `[${server.host}]:${server.port}`;
  const binary = process.platform === 'win32'
    ? join(process.env.SystemRoot || 'C:\\Windows', 'System32', 'OpenSSH', 'ssh-keygen.exe')
    : '/usr/bin/ssh-keygen';
  try {
    // -F understands OpenSSH hashed records; never scan/add/replace a host key.
    const output = run(binary, ['-F', target, '-f', knownHostsPath], {
      encoding: 'utf8', shell: false, windowsHide: true, timeout: 5000,
      maxBuffer: 1024 * 1024, stdio: ['ignore', 'pipe', 'pipe'],
    });
    const lines = output.split(/\r?\n/).filter(line => line.trim() && !line.startsWith('#'));
    if (!lines.length || lines.some(line => line.startsWith('@'))) throw new Error();
    const keys = lines.map(line => {
      const parts = line.trim().split(/\s+/);
      if (parts.length < 3 || !/^(ssh-|ecdsa-)/.test(parts[1]) ||
          !/^[A-Za-z0-9+/]+={0,2}$/.test(parts[2])) throw new Error();
      return Buffer.from(parts[2], 'base64');
    });
    if (keys.some(key => !key.length)) throw new Error();
    return keys;
  } catch {
    throw new Error('HOST_KEY_NOT_TRUSTED');
  }
}

function redact(text, env) {
  let result = text;
  for (const name of PASSWORD_NAMES) {
    if (env[name]) result = result.split(env[name]).join('[REDACTED]');
  }
  return result;
}

export async function execute(roster, env, name, command, options) {
  const server = roster.find(s => s.id.toLowerCase().replaceAll('_', '-') === name);
  if (!server) return { error: 'UNKNOWN_SERVER' };
  if (!env[server.passwordEnv]) return { error: 'MISSING_CREDENTIAL' };
  if (typeof command !== 'string' || !command.trim() || command.length > 8192 || command.includes('\0')) {
    return { error: 'INVALID_COMMAND' };
  }
  let keys;
  try {
    keys = (options.lookupKeys || trustedKeys)(server, options.knownHostsPath || defaultKnownHosts());
  } catch { return { error: 'HOST_KEY_NOT_TRUSTED' }; }
  if (options.signal?.aborted) return { error: 'CANCELLED_REMOTE_STATE_UNKNOWN' };

  return new Promise(resolve => {
    let conn;
    try { conn = options.createClient(); }
    catch { resolve({ error: 'SSH_CLIENT_UNAVAILABLE' }); return; }
    let done = false;
    let mismatch = false;
    let size = 0;
    const stdout = [];
    const stderr = [];
    const finish = result => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      options.signal?.removeEventListener('abort', cancel);
      try { conn.destroy(); } catch { /* Result still records unknown remote state on failures. */ }
      resolve(result);
    };
    const cancel = () => finish({ error: 'CANCELLED_REMOTE_STATE_UNKNOWN' });
    const timer = setTimeout(() => finish({ error: 'TIMEOUT_REMOTE_STATE_UNKNOWN' }), options.timeoutMs || 30000);
    options.signal?.addEventListener('abort', cancel, { once: true });
    const collect = chunks => data => {
      size += data.length;
      if (size > 65536) finish({ error: 'OUTPUT_LIMIT', remoteState: 'UNKNOWN' });
      else chunks.push(Buffer.from(data));
    };
    conn.on('error', error => finish({ error: mismatch ? 'HOST_KEY_MISMATCH'
      : error.level === 'client-authentication' ? 'AUTHENTICATION_FAILED' : 'SSH_FAILURE_REMOTE_STATE_UNKNOWN' }));
    conn.on('close', () => finish({ error: mismatch ? 'HOST_KEY_MISMATCH' : 'SSH_CLOSED_REMOTE_STATE_UNKNOWN' }));
    conn.on('ready', () => {
      if (done) return;
      conn.exec(command, (error, stream) => {
        if (done) return;
        if (error) { finish({ error: 'EXEC_REJECTED' }); return; }
        stream.on('data', collect(stdout));
        stream.stderr.on('data', collect(stderr));
        stream.on('error', () => finish({ error: 'CHANNEL_FAILURE_REMOTE_STATE_UNKNOWN' }));
        stream.on('close', (code, signal) => finish({
          code: Number.isInteger(code) ? code : null,
          signal: typeof signal === 'string' ? redact(signal, env) : null,
          stdout: redact(Buffer.concat(stdout).toString('utf8'), env),
          stderr: redact(Buffer.concat(stderr).toString('utf8'), env),
        }));
      });
    });
    try {
      conn.connect({ host: server.host, port: server.port, username: server.user,
        password: env[server.passwordEnv], readyTimeout: 15000,
        hostVerifier: actual => {
          const match = keys.some(key => key.length === actual.length && timingSafeEqual(key, actual));
          mismatch = !match;
          return match;
        },
      });
    } catch { finish({ error: 'SSH_FAILURE_REMOTE_STATE_UNKNOWN' }); }
  });
}

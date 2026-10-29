import test from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { readFileSync } from 'node:fs';
import {
  validateRoster, prepareEnvironment, listServers, trustedKeys, execute,
} from './ssh-runtime.mjs';

const roster = JSON.parse(readFileSync(new URL('./ssh-servers.json', import.meta.url), 'utf8'));
const cloudEnv = { MJ_SYS_SSH_SERVER_CLOUD_PASSWORD: 'synthetic-cloud-password' };
const key = Buffer.from('synthetic-public-host-key');
const keyLine = `cloud ssh-ed25519 ${key.toString('base64')}`;

test('fixed nine aliases and existing accounts, five credential names', () => {
  validateRoster(roster);
  assert.deepEqual(listServers(roster, {}).map(s => s.name), [
    'cloud', 'runner-lan', 'runner-wan', 'test-lan', 'test-wan',
    'prod-lan', 'prod-wan', 'dgx-lan', 'dgx-wan',
  ]);
  assert.equal(listServers(roster, {}).every(s => !s.credentialPresent), true);
  assert.equal(listServers(roster, cloudEnv)[0].credentialPresent, true);
  assert.equal(roster[0].user, 'root');
  assert.equal(new Set(roster.map(s => s.passwordEnv)).size, 5);
});

test('unexpected alias, credential name and inline password are rejected', () => {
  for (const change of [{ id: 'EVIL' }, { passwordEnv: 'GITHUB_PERSONAL_ACCESS_TOKEN' },
    { password: 'synthetic' }, { host: 'unapproved.example' }, { port: 23 }]) {
    assert.throws(() => validateRoster([{ ...roster[0], ...change }, ...roster.slice(1)]),
      /INVALID_SSH_ROSTER/);
  }
});

test('only safe process fields and five named passwords reach the server', () => {
  const env = prepareEnvironment({ ...cloudEnv, PATH: 'synthetic-path', HOME: '/synthetic',
    NODE_OPTIONS: '--require evil', SSH_SERVER_EVIL_HOST: 'evil',
    SSH_CONFIG_PATH: '/personal/config', GITHUB_PERSONAL_ACCESS_TOKEN: 'synthetic-token' });
  assert.deepEqual(env, { ...cloudEnv, PATH: 'synthetic-path', HOME: '/synthetic' });
});

test('known-host lookup is fixed, shell-free, supports hashed records', () => {
  const keys = trustedKeys(roster[0], '/synthetic/known_hosts', (cmd, args, options) => {
    assert.equal(args[0], '-F');
    assert.equal(args[1], '8.135.38.175');
    assert.deepEqual(args.slice(2), ['-f', '/synthetic/known_hosts']);
    assert.equal(options.shell, false);
    return `# Host found\n|1|salt|hash ssh-ed25519 ${key.toString('base64')}\n`;
  });
  assert.deepEqual(keys, [key]);
  trustedKeys(roster[2], '/synthetic/known_hosts', (_cmd, args) => {
    assert.equal(args[1], '[8.135.38.175]:2201');
    return keyLine;
  });
  assert.throws(() => trustedKeys(roster[0], '/synthetic', () => ''), /HOST_KEY_NOT_TRUSTED/);
  assert.throws(() => trustedKeys(roster[0], '/synthetic', () => `@revoked ${keyLine}`),
    /HOST_KEY_NOT_TRUSTED/);
});

function fakeClient({ output = '', code = 0, actualKey = key, stall = false } = {}) {
  const client = new EventEmitter();
  client.destroy = () => { client.destroyed = true; };
  client.end = client.destroy;
  client.connect = config => {
    client.config = config;
    queueMicrotask(() => {
      if (!config.hostVerifier(actualKey)) client.emit('error', new Error('synthetic rejected'));
      else client.emit('ready');
    });
  };
  client.exec = (command, callback) => {
    client.command = command;
    const stream = new EventEmitter();
    stream.stderr = new EventEmitter();
    callback(null, stream);
    if (!stall) queueMicrotask(() => { stream.emit('data', Buffer.from(output)); stream.emit('close', code); });
  };
  return client;
}

const options = client => ({ createClient: () => client, lookupKeys: () => [key], knownHostsPath: '/synthetic' });

test('missing credential and unknown alias never connect', async () => {
  const client = fakeClient();
  assert.equal((await execute(roster, {}, 'cloud', 'id', options(client))).error, 'MISSING_CREDENTIAL');
  assert.equal((await execute(roster, cloudEnv, 'other', 'id', options(client))).error, 'UNKNOWN_SERVER');
  assert.equal(client.config, undefined);
});

test('valid host sends one unchanged command; redacts known passwords', async () => {
  const client = fakeClient({ output: `safe ${cloudEnv.MJ_SYS_SSH_SERVER_CLOUD_PASSWORD} safe` });
  const result = await execute(roster, cloudEnv, 'cloud', 'id', options(client));
  assert.equal(client.command, 'id');
  assert.equal(client.config.username, 'root');
  assert.equal(result.stdout, 'safe [REDACTED] safe');
  assert.equal(result.code, 0);
  assert.equal(client.destroyed, true);
});

test('mismatched key rejects authentication without executing', async () => {
  const client = fakeClient({ actualKey: Buffer.from('different-public-key') });
  const result = await execute(roster, cloudEnv, 'cloud', 'id', options(client));
  assert.equal(result.error, 'HOST_KEY_MISMATCH');
  assert.equal(client.command, undefined);
});

test('output bound, nonzero command status, timeout and cancellation are explicit', async () => {
  const huge = fakeClient({ output: 'x'.repeat(65537) });
  assert.equal((await execute(roster, cloudEnv, 'cloud', 'id', options(huge))).error, 'OUTPUT_LIMIT');
  const nonzero = fakeClient({ code: 7 });
  assert.equal((await execute(roster, cloudEnv, 'cloud', 'false', options(nonzero))).code, 7);
  const hanging = fakeClient({ stall: true });
  assert.equal((await execute(roster, cloudEnv, 'cloud', 'sleep',
    { ...options(hanging), timeoutMs: 10 })).error, 'TIMEOUT_REMOTE_STATE_UNKNOWN');
  const controller = new AbortController();
  controller.abort();
  const cancelled = fakeClient();
  assert.equal((await execute(roster, cloudEnv, 'cloud', 'id',
    { ...options(cancelled), signal: controller.signal })).error, 'CANCELLED_REMOTE_STATE_UNKNOWN');
  assert.equal(cancelled.config, undefined);
});

// Local stdio protocol only. No remote connection or real credentials.
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmdirSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { prepareEnvironment } from './ssh-runtime.mjs';

const entry = fileURLToPath(new URL('./ssh-start.mjs', import.meta.url));
const env = prepareEnvironment({ SystemRoot: process.env.SystemRoot,
  HOME: '/synthetic-home-unused', USERPROFILE: 'C:\\synthetic-home-unused',
  MJ_SYS_SSH_SERVER_CLOUD_PASSWORD: 'synthetic-canary-not-printed',
});

test('check works from a directory with spaces and reports no values', () => {
  const cwd = mkdtempSync(join(tmpdir(), 'mj-agent ssh check '));
  try {
    const result = spawnSync(process.execPath, [entry, '--check'], { cwd, env, encoding: 'utf8' });
    assert.equal(result.status, 0);
    assert.equal(result.stderr, '');
    assert.equal(result.stdout.includes('synthetic-canary-not-printed'), false);
    const payload = JSON.parse(result.stdout);
    assert.equal(payload.servers.length, 9);
    assert.equal(payload.servers.filter(s => s.credentialPresent).length, 1);
    assert.equal(payload.connection, 'NOT_TESTED');
  } finally { rmdirSync(cwd); }
});

test('stdio initialize, tools/list and safe calls; no socket or host command', async () => {
  const client = new Client({ name: 'offline-ssh-protocol-check', version: '1.0.0' });
  const transport = new StdioClientTransport({ command: process.execPath,
    args: [entry], env, stderr: 'pipe' });
  let diagnostics = '';
  transport.stderr?.on('data', data => { diagnostics += data; });
  try {
    await client.connect(transport);
    const { tools } = await client.listTools();
    assert.deepEqual(tools.map(t => t.name), ['ssh_list_servers', 'ssh_execute']);
    assert.equal(tools[1].annotations.readOnlyHint, false);
    assert.equal(tools[1].inputSchema.properties.server.enum.length, 9);
    const list = await client.callTool({ name: 'ssh_list_servers', arguments: {} });
    assert.equal(JSON.parse(list.content[0].text).servers.length, 9);
    const refused = await client.callTool({ name: 'ssh_execute', arguments: { server: 'other', command: 'id' } });
    assert.equal(refused.isError, true);
    assert.equal(JSON.parse(refused.content[0].text).error, 'UNKNOWN_SERVER');
    assert.equal(JSON.stringify(list).includes('synthetic-canary-not-printed'), false);
  } finally { await client.close(); }
  assert.equal(diagnostics, '');
});

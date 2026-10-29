import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { ListToolsRequestSchema, CallToolRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import ssh2 from 'ssh2';
import { listServers, execute } from './ssh-runtime.mjs';

export async function serve(roster, env) {
  const server = new Server({ name: 'mj-agent-ssh-manager', version: '1.0.0' }, { capabilities: { tools: {} } });
  server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: [
    { name: 'ssh_list_servers', description: 'List nine approved aliases and credential presence; no connection.',
      annotations: { readOnlyHint: true, openWorldHint: false },
      inputSchema: { type: 'object', properties: {}, additionalProperties: false } },
    { name: 'ssh_execute', description: 'Execute one command on one approved alias. Requires task authorization. '
      + 'cloud is root; prod aliases are production. General shell has write access. No DB bypass or secret reads. '
      + 'No auto retry/fallback. Timeout/cancel/disconnect can leave remote work running; reconcile before retry.',
      annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: false, openWorldHint: true },
      inputSchema: { type: 'object', properties: {
        server: { type: 'string', enum: listServers(roster, env).map(s => s.name) },
        command: { type: 'string', minLength: 1, maxLength: 8192 },
      }, required: ['server', 'command'], additionalProperties: false } },
  ] }));
  server.setRequestHandler(CallToolRequestSchema, async (request, extra) => {
    const args = request.params.arguments || {};
    let result;
    if (request.params.name === 'ssh_list_servers' && Object.keys(args).length === 0) {
      result = { servers: listServers(roster, env) };
    } else if (request.params.name === 'ssh_execute' && Object.keys(args).sort().join() === 'command,server') {
      result = await execute(roster, env, args.server, args.command, {
        createClient: () => new ssh2.Client(), signal: extra.signal,
      });
    } else result = { error: 'INVALID_TOOL_OR_ARGUMENTS' };
    return { content: [{ type: 'text', text: JSON.stringify(result) }],
      isError: Boolean(result.error || result.code === null || (typeof result.code === 'number' && result.code !== 0)) };
  });
  server.onerror = () => console.error('SSH_MCP_PROTOCOL_ERROR');
  await server.connect(new StdioServerTransport());
}

# @elephantine/sdk

Official TypeScript / JavaScript client for [Elephantine](https://github.com/partitect/elephantine) — the Zero-GPU, Local-First, CPU-Native Cognitive Memory Layer for Autonomous AI Agents.

## Installation

```bash
npm install @elephantine/sdk
# or
pnpm add @elephantine/sdk
# or
yarn add @elephantine/sdk
```

## Quick Start

```typescript
import { ElephantineClient } from '@elephantine/sdk';

const client = new ElephantineClient('http://127.0.0.1:8765');

async function run() {
  // 1. Remember a fact with role authority and workspace isolation
  const saved = await client.remember({
    content: 'Database must strictly run PostgreSQL 16 with pgvector.',
    category: 'architecture',
    entityKey: 'project:db_engine',
    workspaceId: 'phoenix-core',
    roleAuthority: 1.0
  });
  console.log('Saved memory:', saved.id);

  // 2. Recall memories with semantic ranking and time decay
  const response = await client.recall({
    query: 'Which database engine should we use?',
    workspaceId: 'phoenix-core',
    topK: 3
  });

  console.log(`Found ${response.totalFound} items in ${response.latencyMs}ms:`);
  for (const memory of response.memories) {
    console.log(`- [${memory.category}] (Auth: ${memory.roleAuthority}): ${memory.content}`);
  }
}

run().catch(console.error);
```

## API Reference

### `client.remember(options: RememberOptions): Promise<RememberResponse>`
* `content` (string, required): Fact or knowledge snippet.
* `workspaceId` (string, optional): Git repository or project workspace identifier (default: `'default'`).
* `category` (string, optional): Memory classification (e.g. `'architecture'`, `'preference'`, `'fact'`).
* `roleAuthority` (number, optional): Hierarchical authority score from `0.0` to `1.0` (default: `0.5`).
* `entityKey` (string, optional): Semantic entity key for Last-Write-Wins (LWW) conflict deprecation.

### `client.recall(options: RecallOptions): Promise<RecallResponse>`
* `query` (string, required): Semantic question or search prompt.
* `workspaceId` (string, optional): Target workspace namespace.
* `topK` (number, optional): Maximum memories to retrieve (default: `5`).
* `useTimeDecay` (boolean, optional): Apply exponential temporal decay to prioritize recent memories (default: `true`).

## License
Apache-2.0

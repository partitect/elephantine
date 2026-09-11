export interface RememberOptions {
  content: string;
  category?: string;
  entityKey?: string;
  sourceAgent?: string;
  confidence?: number;
  workspaceId?: string;
  roleAuthority?: number;
  metadata?: Record<string, any>;
  ttlHours?: number;
}

export interface RememberResponse {
  id: string;
  status: string;
  conflictsResolved: string[];
  createdAt: string;
  message: string;
}

export interface RecallOptions {
  query: string;
  topK?: number;
  workspaceId?: string;
  category?: string;
  useTimeDecay?: boolean;
}

export interface RecalledMemory {
  id: string;
  content: string;
  category: string;
  confidence: number;
  similarityScore: number;
  decayedScore: number;
  workspaceId: string;
  roleAuthority: number;
  createdAt: string;
}

export interface RecallResponse {
  query: string;
  totalFound: number;
  memories: RecalledMemory[];
  latencyMs: number;
}

export class ElephantineClient {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://127.0.0.1:8765') {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  async remember(options: RememberOptions): Promise<RememberResponse> {
    const payload = {
      content: options.content,
      category: options.category ?? 'general',
      entity_key: options.entityKey ?? null,
      source_agent: options.sourceAgent ?? 'typescript-sdk',
      confidence: options.confidence ?? 1.0,
      workspace_id: options.workspaceId ?? 'default',
      role_authority: options.roleAuthority ?? 0.5,
      metadata: options.metadata ?? {},
      ttl_hours: options.ttlHours ?? null
    };

    const res = await fetch(this.baseUrl + '/remember', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      throw new Error('Elephantine remember error (' + res.status + '): ' + await res.text());
    }

    const data: any = await res.json();
    return {
      id: data.id,
      status: data.status,
      conflictsResolved: data.conflicts_resolved ?? [],
      createdAt: data.created_at,
      message: data.message
    };
  }

  async recall(options: RecallOptions): Promise<RecallResponse> {
    const payload = {
      query: options.query,
      top_k: options.topK ?? 5,
      workspace_id: options.workspaceId ?? 'default',
      category: options.category ?? null,
      use_time_decay: options.useTimeDecay ?? true
    };

    const res = await fetch(this.baseUrl + '/recall', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      throw new Error('Elephantine recall error (' + res.status + '): ' + await res.text());
    }

    const data: any = await res.json();
    return {
      query: data.query,
      totalFound: data.total_found,
      latencyMs: data.latency_ms,
      memories: (data.memories ?? []).map((m: any) => ({
        id: m.id,
        content: m.content,
        category: m.category,
        confidence: m.confidence,
        similarityScore: m.similarity_score,
        decayedScore: m.decayed_score,
        workspaceId: m.workspace_id,
        roleAuthority: m.role_authority,
        createdAt: m.created_at
      }))
    };
  }

  async consolidate(entityKey: string, workspaceId: string = 'default'): Promise<any> {
    const res = await fetch(this.baseUrl + '/memories/consolidate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entity_key: entityKey, workspace_id: workspaceId })
    });
    if (!res.ok) throw new Error('Consolidate failed: ' + await res.text());
    return res.json();
  }
}

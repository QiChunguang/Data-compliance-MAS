import React, { useEffect, useMemo, useState } from 'react';
import { reguthinkInteractiveClient } from '../../api/reguthinkInteractiveClient';
import { REGUTHINK_API_BASE_URL } from '../../api/reguthinkConfig';
import type { GraphEdge, GraphNode, GraphResponse, JobArtifactsResponse, RuntimeJob } from '../../types/reguthink-interactive-api';

type Props = {
  job: RuntimeJob | null;
  artifacts: JobArtifactsResponse | null;
};

const LABEL_COLORS: Record<string, string> = {
  ChromaCollection: '#1f5fbf',
  Source: '#12345a',
  Document: '#425d78',
  Article: '#0ea5b7',
  Clause: '#3b82f6',
  Topic: '#b98b2e',
  CaseProfile: '#174a96',
  ClaimTemplate: '#6366f1',
  CitationRule: '#64748b',
  Chunk: '#94a3b8',
};

const DEFAULT_LABELS = new Set(['Source', 'Article', 'Clause', 'Topic', 'CaseProfile', 'CitationRule', 'ChromaCollection', 'Document']);
type GraphMode = 'overview' | 'source' | 'topic' | 'search';

export const KnowledgeGraphView: React.FC<Props> = ({ job }) => {
  const [health, setHealth] = useState<GraphResponse | null>(null);
  const [overview, setOverview] = useState<GraphResponse | null>(null);
  const [subgraph, setSubgraph] = useState<GraphResponse | null>(null);
  const [selected, setSelected] = useState<GraphNode | null>(null);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [activeLabels, setActiveLabels] = useState<Set<string>>(new Set());
  const [mode, setMode] = useState<GraphMode>('overview');

  useEffect(() => {
    let cancelled = false;
    async function loadGraph() {
      setLoading(true);
      try {
        const s = await fetchGraphJson('/api/v1/graph/subgraph?limit=120&mode=overview');
        if (cancelled) return;
        const normalized = normalizeGraphResponse(s);
        setSubgraph(normalized);
        setSelected(normalized.nodes[0] || null);
        fetchGraphJson('/api/v1/graph/overview')
          .then((o) => { if (!cancelled) setOverview(o); })
          .catch(() => { if (!cancelled) setOverview(null); });
        fetchGraphJson('/api/v1/graph/health')
          .then((h) => { if (!cancelled) setHealth(h); })
          .catch(() => { if (!cancelled) setHealth({ status: 'ok' }); });
      } catch (error) {
        if (cancelled) return;
        setHealth({ status: 'graph_unavailable', reason: error instanceof Error ? error.message : 'network_error' });
        setOverview(null);
        setSubgraph({ status: 'graph_unavailable', nodes: [], edges: [] });
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void loadGraph();
    return () => {
      cancelled = true;
    };
  }, []);

  async function searchGraph() {
    setMode(query.trim() ? 'search' : 'overview');
    setActiveLabels(new Set());
    const result = query.trim()
      ? await fetchGraphJson(`/api/v1/graph/subgraph?limit=120&mode=search&q=${encodeURIComponent(query.trim())}`)
      : await fetchGraphJson('/api/v1/graph/subgraph?limit=120&mode=overview');
    const normalized = normalizeGraphResponse(result);
    setSubgraph(normalized);
    setSelected(normalized.nodes[0] || null);
  }

  async function focusNode(nextMode: GraphMode, node?: GraphNode | null) {
    const hasAnyLabel = (item: GraphNode | null | undefined, labels: string[]) =>
      !!item && labels.some((label) => item.labels?.includes(label) || item.type === label);
    const fallbackNode = nextMode === 'source'
      ? allNodes.find((item) => hasAnyLabel(item, ['Source', 'Document', 'ChromaCollection']))
      : nextMode === 'topic'
      ? allNodes.find((item) => hasAnyLabel(item, ['Topic', 'CaseProfile', 'CitationRule']))
      : null;
    const focus = nextMode === 'source' && !hasAnyLabel(node, ['Source', 'Document', 'ChromaCollection'])
      ? fallbackNode
      : nextMode === 'topic' && !hasAnyLabel(node, ['Topic', 'CaseProfile', 'CitationRule'])
      ? fallbackNode
      : node;
    if (!focus && nextMode === 'source') return;
    setMode(nextMode);
    setLoading(true);
    try {
      const result = nextMode === 'overview'
        ? await fetchGraphJson('/api/v1/graph/subgraph?limit=120&mode=overview')
        : await fetchGraphJson(`/api/v1/graph/subgraph?limit=60&mode=${encodeURIComponent(nextMode)}&node_id=${encodeURIComponent(focus?.id || '')}&q=${encodeURIComponent(nextMode === 'topic' ? (query || '数据') : query)}`);
      const normalized = normalizeGraphResponse(result);
      setSubgraph(normalized);
      setSelected(normalized.nodes.find((item) => item.id === focus?.id) || normalized.nodes[0] || null);
    } finally {
      setLoading(false);
    }
  }

  function toggleLabel(label: string) {
    setActiveLabels((prev) => {
      const next = new Set(prev);
      if (next.has(label)) {
        next.delete(label);
      } else {
        next.add(label);
      }
      return next;
    });
  }

  const allNodes = subgraph?.nodes || [];
  const allEdges = subgraph?.edges || [];

  const filteredNodes = useMemo(() => {
    const visibleLabels = activeLabels.size > 0 ? activeLabels : DEFAULT_LABELS;
    return allNodes.filter((n) => n.labels?.some((l) => visibleLabels.has(l)) || visibleLabels.has(n.type || ''));
  }, [allNodes, activeLabels]);

  const filteredEdges = useMemo(() => {
    const nodeIds = new Set(filteredNodes.map((n) => n.id));
    return allEdges.filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target));
  }, [allEdges, filteredNodes]);

  const status = subgraph?.status || health?.status || 'loading';
  const totalNodes = overview?.node_counts_by_label
    ? Object.values(overview.node_counts_by_label).reduce((a, b) => (a as number) + (b as number), 0)
    : 0;
  const totalEdges = overview?.edge_counts_by_type
    ? Object.values(overview.edge_counts_by_type).reduce((a, b) => (a as number) + (b as number), 0)
    : 0;
  const selectedNeighborCount = selected
    ? new Set(allEdges.flatMap((edge) => edge.source === selected.id ? [edge.target] : edge.target === selected.id ? [edge.source] : [])).size
    : 0;
  const graphEvidence = {
    api_response_node_count: allNodes.length,
    api_response_edge_count: allEdges.length,
    displayed_node_count: filteredNodes.length,
    displayed_edge_count: filteredEdges.length,
    selected_node_id: selected?.id || null,
    selected_source_id: selected?.properties_summary?.source_id || selected?.properties_summary?.source_title || null,
    source_focus_neighbor_count: mode === 'source' ? selectedNeighborCount : 0,
    search_topic_filtered_count: mode === 'search' || mode === 'topic' ? filteredNodes.length : 0,
    uses_real_api_data: status !== 'graph_unavailable' && !!subgraph,
  };

  return (
    <section className="knowledge-graph-view workspace-page">
      <div className="workspace-hero kg-hero">
        <div>
          <p className="workspace-kicker">Knowledge Network</p>
          <h2>知识图谱</h2>
          <p>图谱来自只读合规知识库接口；上传材料只作为业务事实，不写入知识库。</p>
        </div>
        <div className={`workspace-job-pill ${status}`}>
          {loading ? 'loading' : status}
        </div>
      </div>

      <div className="kg-live-shell">
        <aside className="kg-filter-panel">
          <h3>搜索</h3>
          <label className="kg-search-label">
            <div className="kg-search-row">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && searchGraph()}
              placeholder="搜索 数据 / 个人信息 / 法律名称"
            />
              <button type="button" onClick={searchGraph}>搜索</button>
            </div>
          </label>

          <h3>统计</h3>
          <div className="kg-stat-list">
            <GraphStat label="接口节点" value={String(allNodes.length)} />
            <GraphStat label="接口关系" value={String(allEdges.length)} />
            <GraphStat label="显示节点" value={String(filteredNodes.length)} />
            <GraphStat label="显示关系" value={String(filteredEdges.length)} />
            <GraphStat label="当前视图" value={modeLabel(mode)} />
          </div>

          <h3>视图模式</h3>
          <div className="kg-mode-list">
            <button className={mode === 'overview' ? 'active' : ''} type="button" onClick={() => focusNode('overview')}>概览视图</button>
            <button className={mode === 'source' ? 'active' : ''} type="button" disabled={!selected} onClick={() => focusNode('source', selected)}>来源聚焦</button>
            <button className={mode === 'topic' ? 'active' : ''} type="button" disabled={!selected} onClick={() => focusNode('topic', selected)}>主题聚焦</button>
          </div>

          <h3>标签筛选 (点击切换)</h3>
          <div className="kg-type-list">
            {(overview?.node_counts_by_label ? Object.entries(overview.node_counts_by_label) : [])
              .sort((a, b) => (b[1] as number) - (a[1] as number))
              .map(([label, count]) => (
                <button
                  key={label}
                  className={`kg-type-chip ${activeLabels.has(label) ? 'active' : ''}`}
                  onClick={() => toggleLabel(label)}
                  type="button"
                >
                  <span
                    className="chip-dot"
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      background: LABEL_COLORS[label] || '#94a3b8',
                      display: 'inline-block',
                    }}
                  />
                  {label}
                  <span className="chip-count">{String(count)}</span>
                </button>
              ))}
          </div>
        </aside>

        <GraphCanvas
          nodes={filteredNodes}
          edges={filteredEdges}
          status={status}
          onSelect={setSelected}
          selected={selected}
          mode={mode}
        />

        <output className="kg-proof-strip" data-testid="graph-api-evidence">
          API {graphEvidence.api_response_node_count}/{graphEvidence.api_response_edge_count} ·
          显示 {graphEvidence.displayed_node_count}/{graphEvidence.displayed_edge_count} ·
          邻居 {selectedNeighborCount} ·
          筛选 {graphEvidence.search_topic_filtered_count}
        </output>

        <aside className="kg-detail-panel">
          <h3>节点详情</h3>
          {selected ? (
            <>
              <div className="kg-detail-title">{selected.label}</div>
              <span className="sr-only" data-testid="graph-selected-node-id">{selected.id}</span>
              <div className="kg-detail-meta">{nodeTypeLabel(selected)}</div>
              <div className="kg-detail-card-list">
                {nodeDetailRows(selected).map((row) => (
                  <div className="kg-detail-row" key={row.label}>
                    <span>{row.label}</span>
                    <strong>{row.value}</strong>
                  </div>
                ))}
              </div>
              <details className="kg-debug-details">
                <summary>完整节点标识</summary>
                <code>{selected.id}</code>
              </details>
            </>
          ) : (
            <div className="kg-empty-state">
              {status === 'graph_unavailable' ? '图谱不可用' : '点击节点查看详情'}
            </div>
          )}

          <h3>关系类型</h3>
          <div className="kg-type-list">
            {(overview?.edge_counts_by_type ? Object.entries(overview.edge_counts_by_type) : [])
              .sort((a, b) => (b[1] as number) - (a[1] as number))
              .slice(0, 12)
              .map(([type, count]) => (
                <span key={type} className="kg-type-chip">
                  {edgeTypeLabel(type)} · {String(count)}
                </span>
              ))}
          </div>
        </aside>
      </div>
    </section>
  );
};

function GraphCanvas({
  nodes,
  edges,
  status,
  selected,
  onSelect,
  mode,
}: {
  nodes: GraphNode[];
  edges: GraphEdge[];
  status: string;
  selected: GraphNode | null;
  onSelect: (node: GraphNode) => void;
  mode: GraphMode;
}) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const adjacency = useMemo(() => {
    const map = new Map<string, Set<string>>();
    const edgeIds = new Map<string, Set<string>>();
    for (const node of nodes) {
      map.set(node.id, new Set());
      edgeIds.set(node.id, new Set());
    }
    for (const edge of edges) {
      if (!map.has(edge.source) || !map.has(edge.target)) continue;
      map.get(edge.source)?.add(edge.target);
      map.get(edge.target)?.add(edge.source);
      edgeIds.get(edge.source)?.add(edge.id);
      edgeIds.get(edge.target)?.add(edge.id);
    }
    return { map, edgeIds };
  }, [nodes, edges]);
  const activeId = hoveredId || selected?.id || null;
  const activeNeighbors = activeId ? adjacency.map.get(activeId) || new Set<string>() : new Set<string>();
  const activeEdges = activeId ? adjacency.edgeIds.get(activeId) || new Set<string>() : new Set<string>();

  const positioned = useMemo(() => {
    const visible = nodes.slice(0, 100);
    const positions = new Map<string, { node: GraphNode; x: number; y: number; vx: number; vy: number }>();
    const center = { x: 390, y: 300 };
    visible.forEach((node, index) => {
      const angle = (Math.PI * 2 * index) / Math.max(visible.length, 1);
      const radius = 120 + (index % 5) * 35;
      positions.set(node.id, {
        node,
        x: center.x + Math.cos(angle) * radius,
        y: center.y + Math.sin(angle) * radius,
        vx: 0,
        vy: 0,
      });
    });
    for (let step = 0; step < 90; step += 1) {
      const items = Array.from(positions.values());
      for (let i = 0; i < items.length; i += 1) {
        for (let j = i + 1; j < items.length; j += 1) {
          const a = items[i];
          const b = items[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 8);
          const force = 850 / (dist * dist);
          a.vx += (dx / dist) * force;
          a.vy += (dy / dist) * force;
          b.vx -= (dx / dist) * force;
          b.vy -= (dy / dist) * force;
        }
      }
      for (const edge of edges) {
        const source = positions.get(edge.source);
        const target = positions.get(edge.target);
        if (!source || !target) continue;
        const dx = target.x - source.x;
        const dy = target.y - source.y;
        const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 8);
        const force = (dist - 115) * 0.012;
        source.vx += (dx / dist) * force;
        source.vy += (dy / dist) * force;
        target.vx -= (dx / dist) * force;
        target.vy -= (dy / dist) * force;
      }
      for (const item of items) {
        item.vx += (center.x - item.x) * 0.002;
        item.vy += (center.y - item.y) * 0.002;
        item.x += item.vx;
        item.y += item.vy;
        item.vx *= 0.82;
        item.vy *= 0.82;
      }
    }
    return Array.from(positions.values()).map(({ node, x, y }) => ({ node, x, y }));
  }, [nodes, edges]);

  const index = useMemo(() => new Map(positioned.map((item) => [item.node.id, item])), [positioned]);

  if (!nodes.length) {
    return (
      <main className="kg-canvas kg-canvas-empty">
        <h3>{status === 'graph_unavailable' ? '图谱不可用' : '无节点数据'}</h3>
        <p>只读图谱接口已调用；当前没有可展示的节点或关系。</p>
      </main>
    );
  }

  const displayLabel = (node: GraphNode) => {
    const props = node.properties_summary || {};
    const raw = String(
      props.source_title ||
      props.title ||
      props.name ||
      props.article_id ||
      props.source_id ||
      node.label ||
      node.type ||
      'node'
    );
    return raw.length > 22 ? `${raw.slice(0, 20)}...` : raw;
  };

  const nodeRadius = (node: GraphNode) => {
    const type = node.type || '';
    if (type === 'Source' || type === 'Document' || type === 'ChromaCollection') return 18;
    if (type === 'Topic' || type === 'CaseProfile') return 13;
    if (type === 'CitationRule') return 10;
    if (type === 'Chunk') return 6;
    return 9;
  };

  const isDimmedNode = (id: string) => activeId && id !== activeId && !activeNeighbors.has(id);
  const isDimmedEdge = (id: string) => activeId && !activeEdges.has(id);

  return (
    <main className="kg-canvas kg-network-canvas" data-testid="graph-network-canvas">
      <div className="kg-canvas-controls">
        <button type="button" onClick={() => setZoom((value) => Math.min(value + 0.15, 1.8))}>放大</button>
        <button type="button" onClick={() => setZoom((value) => Math.max(value - 0.15, 0.55))}>缩小</button>
        <button type="button" onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}>重置</button>
        <button type="button" onClick={() => { setZoom(0.88); setPan({ x: 0, y: 0 }); }}>适配</button>
      </div>
      <svg viewBox="0 0 780 620" role="img" aria-label="Neo4j network graph">
        <defs>
          <radialGradient id="kgCanvasGlow" cx="50%" cy="48%" r="58%">
            <stop offset="0%" stopColor="#20364f" stopOpacity="1" />
            <stop offset="100%" stopColor="#0e1f33" stopOpacity="1" />
          </radialGradient>
          <marker id="kgArrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 Z" fill="#8aa6c3" />
          </marker>
        </defs>
        <rect x="0" y="0" width="780" height="620" fill="url(#kgCanvasGlow)" rx="18" />
        <text x="28" y="38" className="kg-network-title">{modeLabel(mode)} · API {nodes.length} 节点 / {edges.length} 关系</text>
        <g transform={`translate(${pan.x} ${pan.y}) scale(${zoom})`}>
        {edges.slice(0, 100).map((edge) => {
          const source = index.get(edge.source);
          const target = index.get(edge.target);
          if (!source || !target) return null;
          const mx = (source.x + target.x) / 2;
          const my = (source.y + target.y) / 2 - 22;
          const active = activeEdges.has(edge.id);
          return (
            <path
              key={edge.id}
              data-testid="graph-edge"
              d={`M ${source.x} ${source.y} Q ${mx} ${my} ${target.x} ${target.y}`}
              className={`kg-edge ${active ? 'active' : ''} ${isDimmedEdge(edge.id) ? 'dimmed' : ''}`}
              markerEnd="url(#kgArrow)"
            />
          );
        })}
        {positioned.map(({ node, x, y }) => {
          const color = LABEL_COLORS[node.type || ''] || '#94a3b8';
          const isSelected = selected?.id === node.id;
          const isActive = activeId === node.id || activeNeighbors.has(node.id);
          const r = nodeRadius(node);
          return (
            <g
              key={node.id}
              data-testid="graph-node"
              className={`kg-node-svg ${isSelected ? 'selected' : ''} ${isActive ? 'active' : ''} ${isDimmedNode(node.id) ? 'dimmed' : ''}`}
              onClick={() => onSelect(node)}
              onMouseEnter={() => setHoveredId(node.id)}
              onMouseLeave={() => setHoveredId(null)}
            >
              {node.type === 'CaseProfile' ? (
                <path
                  d={`M ${x} ${y - r - 2} L ${x + r + 2} ${y} L ${x} ${y + r + 2} L ${x - r - 2} ${y} Z`}
                  style={{ fill: isSelected ? color : `${color}28`, stroke: color }}
                />
              ) : (
                <circle
                  cx={x}
                  cy={y}
                  r={r}
                  style={{ fill: isSelected ? color : `${color}28`, stroke: color }}
                />
              )}
              <text x={x} y={y + r + 15} className="kg-node-label">
                {displayLabel(node)}
              </text>
            </g>
          );
        })}
        </g>
      </svg>
    </main>
  );
}

function GraphStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="kg-stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function modeLabel(mode: GraphMode): string {
  if (mode === 'source') return '来源聚焦';
  if (mode === 'topic') return '主题聚焦';
  if (mode === 'search') return '搜索结果';
  return '概览视图';
}

function nodeTypeLabel(node: GraphNode): string {
  const labels = new Set([node.type || '', ...(node.labels || [])]);
  if (labels.has('Source') || labels.has('Document')) return '法律来源';
  if (labels.has('Article') || labels.has('Clause')) return '条文依据';
  if (labels.has('Topic')) return '主题';
  if (labels.has('CaseProfile')) return '案例场景';
  if (labels.has('CitationRule')) return '引用规则';
  return '知识节点';
}

function edgeTypeLabel(type: string): string {
  const map: Record<string, string> = {
    CITES: '引用',
    SUPPORTS: '支持',
    BELONGS_TO: '属于',
    RELATED_TO: '关联',
    REQUIRES: '要求',
    HAS_ARTICLE: '包含条文',
  };
  return map[type] || type;
}

async function fetchGraphJson(path: string): Promise<GraphResponse> {
  const response = await fetch(`${REGUTHINK_API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`graph_http_${response.status}`);
  }
  return JSON.parse(await response.text()) as GraphResponse;
}

function normalizeGraphResponse(response: GraphResponse): GraphResponse & { nodes: GraphNode[]; edges: GraphEdge[] } {
  const nodes = Array.isArray(response.nodes) ? response.nodes : [];
  const edges = Array.isArray(response.edges) ? response.edges : [];
  return { ...response, nodes, edges };
}

function nodeDetailRows(node: GraphNode): Array<{ label: string; value: string }> {
  const props = node.properties_summary || {};
  return [
    { label: '节点类型', value: nodeTypeLabel(node) },
    { label: '显示名称', value: String(props.source_title || props.title || props.name || node.label || '未命名节点').slice(0, 160) },
    { label: '条文编号', value: String(props.article_id || props.article || props.clause || '未提供') },
    { label: '主题标签', value: (node.labels || []).join('、') || '未提供' },
    { label: '来源摘要', value: String(props.summary || props.content || props.text || '可在完整节点标识中进一步核查').slice(0, 180) },
  ];
}

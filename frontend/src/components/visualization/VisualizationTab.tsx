import { useState, useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { getKnowledgeGraph, getMethodFlowchart, getRadar } from '../../api/visualization';
import LoadingSpinner from '../common/LoadingSpinner';
import { ENTITY_TYPE_COLORS, ENTITY_TYPE_KEYS } from '../../utils/constants';
import { useT } from '../../hooks/useTranslation';
import type { GraphData, GraphNode, GraphEdge, FlowchartData, RadarData } from '../../api/types';

interface Props {
  paperId: string;
}

export default function VisualizationTab({ paperId }: Props) {
  const [activeViz, setActiveViz] = useState<'graph' | 'flowchart' | 'radar'>('graph');
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [flowchartData, setFlowchartData] = useState<FlowchartData | null>(null);
  const [radarData, setRadarData] = useState<RadarData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const t = useT();

  const loadVisualization = async (type: string) => {
    setLoading(true);
    setError(null);
    try {
      switch (type) {
        case 'graph': {
          const data = await getKnowledgeGraph(paperId);
          setGraphData(data);
          break;
        }
        case 'flowchart': {
          const data = await getMethodFlowchart(paperId);
          setFlowchartData(data);
          break;
        }
        case 'radar': {
          const data = await getRadar(paperId);
          setRadarData(data);
          break;
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || t('viz.loadFailed'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVisualization(activeViz);
  }, [activeViz, paperId]);
  return (
    <div className="space-y-6">
      {/* Viz selector */}
      <div className="flex gap-2">
        {[
          { id: 'graph', label: t('viz.knowledgeGraph') },
          { id: 'flowchart', label: t('viz.flowchart') },
          { id: 'radar', label: t('viz.radar') },
        ].map((v) => (
          <button
            key={v.id}
            onClick={() => setActiveViz(v.id as any)}
            className={`px-4 py-2 text-sm rounded-lg transition-colors ${
              activeViz === v.id
                ? 'bg-blue-600 text-white'
                : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            {v.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="bg-white rounded-lg border border-slate-200 p-6 min-h-[500px]">
        {loading ? (
          <LoadingSpinner className="py-24" />
        ) : error ? (
          <div className="text-center py-24 text-red-500 text-sm">{error}</div>
        ) : (
          <>
            {activeViz === 'graph' && graphData && <KnowledgeGraphViz data={graphData} emptyMessage={t('viz.noGraph')} />}
            {activeViz === 'flowchart' && flowchartData && <FlowchartViz data={flowchartData} />}
            {activeViz === 'radar' && radarData && <RadarChartViz data={radarData} />}
          </>
        )}
      </div>
    </div>
  );
}
function KnowledgeGraphViz({ data, emptyMessage }: { data: GraphData; emptyMessage: string }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const t = useT();
  const [activeTypes, setActiveTypes] = useState<Set<string>>(() => {
    const types = new Set(data.nodes.map((n) => n.node_type));
    return types;
  });

  const toggleType = (type: string) => {
    setActiveTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  };

  const filteredNodes = data.nodes.filter((n) => activeTypes.has(n.node_type));
  const filteredNodeIds = new Set(filteredNodes.map((n) => n.id));
  const filteredEdges = data.edges.filter(
    (e) => filteredNodeIds.has(e.source as string) && filteredNodeIds.has(e.target as string)
  );

  useEffect(() => {
    if (!svgRef.current || filteredNodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = 900;
    const height = 600;
    svg.attr('viewBox', `0 0 ${width} ${height}`);
    // Arrow marker
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 20)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#94a3b8');

    // Type-based clustering positions
    const typeList = Array.from(new Set(filteredNodes.map((n) => n.node_type)));
    const typeX: Record<string, number> = {};
    const typeY: Record<string, number> = {};
    typeList.forEach((t, i) => {
      const angle = (2 * Math.PI * i) / typeList.length;
      typeX[t] = width / 2 + (width / 5) * Math.cos(angle);
      typeY[t] = height / 2 + (height / 5) * Math.sin(angle);
    });

    const nodesCopy = filteredNodes.map((n) => ({ ...n }));
    const edgesCopy = filteredEdges.map((e) => ({ ...e }));

    const simulation = d3.forceSimulation(nodesCopy as any)
      .force('link', d3.forceLink(edgesCopy as any).id((d: any) => d.id).distance(120))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40))
      .force('x', d3.forceX((d: any) => typeX[d.node_type] || width / 2).strength(0.1))
      .force('y', d3.forceY((d: any) => typeY[d.node_type] || height / 2).strength(0.1));

    // Zoom
    const g = svg.append('g');
    svg.call(d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 3])
      .on('zoom', (event) => { g.attr('transform', event.transform); }) as any);
    // Edges (paths with arrows)
    const linkG = g.append('g');
    const link = linkG.selectAll('line')
      .data(edgesCopy)
      .join('line')
      .attr('stroke', '#cbd5e1')
      .attr('stroke-width', (d: any) => Math.max(d.weight * 2, 1))
      .attr('stroke-opacity', 0.6)
      .attr('marker-end', 'url(#arrowhead)');

    // Edge labels
    const edgeLabel = linkG.selectAll('text')
      .data(edgesCopy)
      .join('text')
      .attr('text-anchor', 'middle')
      .attr('font-size', '8px')
      .attr('fill', '#94a3b8')
      .attr('dy', -4)
      .text((d: any) => d.label || d.relation || '');

    // Tooltip div
    const tooltip = d3.select('body').append('div')
      .attr('class', 'kg-tooltip')
      .style('position', 'absolute')
      .style('background', '#1e293b')
      .style('color', '#f8fafc')
      .style('padding', '6px 10px')
      .style('border-radius', '6px')
      .style('font-size', '11px')
      .style('pointer-events', 'none')
      .style('opacity', 0)
      .style('z-index', '9999');

    // Nodes
    const node = g.append('g')
      .selectAll('g')
      .data(nodesCopy)
      .join('g')
      .attr('cursor', 'grab')
      .call(d3.drag<any, any>()
        .on('start', (event, d: any) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x; d.fy = d.y;
        })
        .on('drag', (event, d: any) => { d.fx = event.x; d.fy = event.y; })
        .on('end', (event, d: any) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null; d.fy = null;
        })
      );
    node.append('circle')
      .attr('r', (d: any) => d.size * 5 + 6)
      .attr('fill', (d: any) => ENTITY_TYPE_COLORS[d.node_type] || '#6b7280')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .attr('opacity', 0.9);

    // Node labels (auto-wrap)
    node.each(function (d: any) {
      const label = d.label;
      const maxLen = 22;
      const lines: string[] = [];
      if (label.length <= maxLen) {
        lines.push(label);
      } else {
        lines.push(label.slice(0, maxLen));
        lines.push(label.length > maxLen * 2 ? label.slice(maxLen, maxLen * 2 - 2) + '..' : label.slice(maxLen, maxLen * 2));
      }
      const textEl = d3.select(this).append('text')
        .attr('text-anchor', 'middle')
        .attr('font-size', '9px')
        .attr('fill', '#334155')
        .attr('pointer-events', 'none');
      lines.forEach((line, i) => {
        textEl.append('tspan')
          .attr('x', 0)
          .attr('dy', i === 0 ? d.size * 5 + 16 : 11)
          .text(line);
      });
    });

    // Hover highlight
    node.on('mouseover', function (event, d: any) {
      const connectedIds = new Set<string>();
      edgesCopy.forEach((e: any) => {
        if (e.source.id === d.id) connectedIds.add(e.target.id);
        if (e.target.id === d.id) connectedIds.add(e.source.id);
      });
      node.attr('opacity', (n: any) => n.id === d.id || connectedIds.has(n.id) ? 1 : 0.2);
      link.attr('stroke-opacity', (e: any) => e.source.id === d.id || e.target.id === d.id ? 0.9 : 0.1);
      edgeLabel.attr('opacity', (e: any) => e.source.id === d.id || e.target.id === d.id ? 1 : 0);
      const conf = d.metadata?.confidence != null ? `${(d.metadata.confidence * 100).toFixed(0)}%` : '';
      tooltip.html(`<strong>${d.label}</strong><br/>${d.node_type}${conf ? ' · ' + conf : ''}`)
        .style('left', (event.pageX + 12) + 'px')
        .style('top', (event.pageY - 10) + 'px')
        .style('opacity', 1);
    })
    .on('mouseout', function () {
      node.attr('opacity', 1);
      link.attr('stroke-opacity', 0.6);
      edgeLabel.attr('opacity', 1);
      tooltip.style('opacity', 0);
    });
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);
      edgeLabel
        .attr('x', (d: any) => (d.source.x + d.target.x) / 2)
        .attr('y', (d: any) => (d.source.y + d.target.y) / 2);
      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
      tooltip.remove();
    };
  }, [filteredNodes, filteredEdges]);

  if (data.nodes.length === 0) {
    return <div className="text-center py-24 text-slate-400 text-sm">{emptyMessage}</div>;
  }

  // Get unique types present in data
  const allTypes = Array.from(new Set(data.nodes.map((n) => n.node_type)));

  return (
    <div>
      {/* Type filter buttons */}
      <div className="flex flex-wrap gap-2 mb-4">
        {allTypes.map((type) => (
          <button
            key={type}
            onClick={() => toggleType(type)}
            className={`flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-full border transition-all ${
              activeTypes.has(type)
                ? 'border-transparent text-white'
                : 'border-slate-200 text-slate-400 bg-white'
            }`}
            style={activeTypes.has(type) ? { backgroundColor: ENTITY_TYPE_COLORS[type] || '#6b7280' } : {}}
          >
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: ENTITY_TYPE_COLORS[type] || '#6b7280' }} />
            {ENTITY_TYPE_KEYS[type] ? t(ENTITY_TYPE_KEYS[type]) : type}
          </button>
        ))}
      </div>
      <svg ref={svgRef} className="w-full h-[600px] border border-slate-100 rounded-lg" />
    </div>
  );
}
function FlowchartViz({ data }: { data: FlowchartData }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !data.mermaid_code) return;

    const renderMermaid = async () => {
      try {
        const mermaid = (await import('mermaid')).default;
        mermaid.initialize({ startOnLoad: false, theme: 'default' });
        const { svg } = await mermaid.render('flowchart-svg', data.mermaid_code);
        if (containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
      } catch (err) {
        if (containerRef.current) {
          containerRef.current.innerHTML = `<pre class="text-xs text-slate-500 bg-slate-50 p-4 rounded">${data.mermaid_code}</pre>`;
        }
      }
    };

    renderMermaid();
  }, [data]);

  return <div ref={containerRef} className="flex justify-center" />;
}

function RadarChartViz({ data }: { data: RadarData }) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || data.dimensions.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = 400;
    const height = 400;
    const margin = 60;
    const radius = Math.min(width, height) / 2 - margin;
    const center = { x: width / 2, y: height / 2 };

    svg.attr('viewBox', `0 0 ${width} ${height}`);

    const n = data.dimensions.length;
    const angleSlice = (Math.PI * 2) / n;
    // Grid circles
    const levels = 5;
    for (let i = 1; i <= levels; i++) {
      const r = (radius / levels) * i;
      svg.append('circle')
        .attr('cx', center.x).attr('cy', center.y)
        .attr('r', r)
        .attr('fill', 'none')
        .attr('stroke', '#e2e8f0')
        .attr('stroke-width', 0.5);
    }

    // Axes
    data.dimensions.forEach((dim, i) => {
      const angle = angleSlice * i - Math.PI / 2;
      const x = center.x + radius * Math.cos(angle);
      const y = center.y + radius * Math.sin(angle);

      svg.append('line')
        .attr('x1', center.x).attr('y1', center.y)
        .attr('x2', x).attr('y2', y)
        .attr('stroke', '#e2e8f0');

      svg.append('text')
        .attr('x', center.x + (radius + 20) * Math.cos(angle))
        .attr('y', center.y + (radius + 20) * Math.sin(angle))
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('font-size', '11px')
        .attr('fill', '#475569')
        .text(dim);
    });

    // Data polygon
    const points = data.scores.map((score, i) => {
      const angle = angleSlice * i - Math.PI / 2;
      const r = (score / data.max_score) * radius;
      return `${center.x + r * Math.cos(angle)},${center.y + r * Math.sin(angle)}`;
    }).join(' ');

    svg.append('polygon')
      .attr('points', points)
      .attr('fill', 'rgba(59, 130, 246, 0.2)')
      .attr('stroke', '#3b82f6')
      .attr('stroke-width', 2);

    // Data points
    data.scores.forEach((score, i) => {
      const angle = angleSlice * i - Math.PI / 2;
      const r = (score / data.max_score) * radius;
      svg.append('circle')
        .attr('cx', center.x + r * Math.cos(angle))
        .attr('cy', center.y + r * Math.sin(angle))
        .attr('r', 4)
        .attr('fill', '#3b82f6')
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);
    });

  }, [data]);

  return (
    <div className="flex flex-col items-center">
      <h4 className="text-sm font-medium text-slate-700 mb-4">{data.paper_title}</h4>
      <svg ref={svgRef} className="w-[400px] h-[400px]" />
      <div className="flex gap-4 mt-4 text-xs text-slate-500">
        {data.dimensions.map((dim, i) => (
          <span key={dim}>{dim}: {data.scores[i]?.toFixed(1)}</span>
        ))}
      </div>
    </div>
  );
}

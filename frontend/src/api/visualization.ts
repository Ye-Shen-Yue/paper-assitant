import client from './client';
import type { GraphData, FlowchartData, TimelineData, RadarData } from './types';

export async function getKnowledgeGraph(paperId: string): Promise<GraphData> {
  const { data } = await client.get(`/visualization/${paperId}/knowledge-graph`);
  return data;
}

export async function getMethodFlowchart(paperId: string): Promise<FlowchartData> {
  const { data } = await client.get(`/visualization/${paperId}/method-flowchart`);
  return data;
}

export async function getTimeline(paperId: string): Promise<TimelineData> {
  const { data } = await client.get(`/visualization/${paperId}/timeline`);
  return data;
}

export async function getRadar(paperId: string): Promise<RadarData> {
  const { data } = await client.get(`/visualization/${paperId}/radar`);
  return data;
}

export async function exportVisualization(paperId: string, type: string, format = 'svg', theme = 'academic'): Promise<unknown> {
  const { data } = await client.post(`/visualization/${paperId}/export`, {
    visualization_type: type,
    format,
    theme,
  });
  return data;
}

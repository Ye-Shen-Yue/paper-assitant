import client from './client';
import type { ReviewResult, ControversyClaim, ReproducibilityItem, TaskResponse } from './types';

export async function triggerReview(paperId: string, language = 'en'): Promise<TaskResponse> {
  const { data } = await client.post(`/review/${paperId}/generate`, { language });
  return data;
}

export async function getReview(paperId: string): Promise<ReviewResult> {
  const { data } = await client.get(`/review/${paperId}`);
  return data;
}

export async function getControversy(paperId: string): Promise<{ paper_id: string; claims: ControversyClaim[]; overall_consistency: number }> {
  const { data } = await client.get(`/review/${paperId}/controversy`);
  return data;
}

export async function getReproducibility(paperId: string): Promise<{ paper_id: string; checklist: ReproducibilityItem[]; overall_score: number; summary: string }> {
  const { data } = await client.get(`/review/${paperId}/reproducibility`);
  return data;
}

export async function comparePapers(paperIds: string[], aspects?: string[]): Promise<unknown> {
  const { data } = await client.post('/comparison', {
    paper_ids: paperIds,
    aspects: aspects || ['method', 'dataset', 'performance', 'innovation'],
  });
  return data;
}

import client from './client';
import type { PaperProfile, Contribution, Limitation, Relationship, TaskResponse } from './types';

export async function triggerEntityExtraction(paperId: string): Promise<TaskResponse> {
  const { data } = await client.post(`/analysis/${paperId}/entities`);
  return data;
}

export async function triggerProfiling(paperId: string): Promise<TaskResponse> {
  const { data } = await client.post(`/analysis/${paperId}/profile`);
  return data;
}

export async function getProfile(paperId: string): Promise<PaperProfile> {
  const { data } = await client.get(`/analysis/${paperId}/profile`);
  return data;
}

export async function triggerContributions(paperId: string): Promise<TaskResponse> {
  const { data } = await client.post(`/analysis/${paperId}/contributions`);
  return data;
}

export async function getContributions(paperId: string): Promise<{ paper_id: string; contributions: Contribution[]; summary: string }> {
  const { data } = await client.get(`/analysis/${paperId}/contributions`);
  return data;
}

export async function triggerLimitations(paperId: string): Promise<TaskResponse> {
  const { data } = await client.post(`/analysis/${paperId}/limitations`);
  return data;
}

export async function getLimitations(paperId: string): Promise<{ paper_id: string; limitations: Limitation[]; summary: string }> {
  const { data } = await client.get(`/analysis/${paperId}/limitations`);
  return data;
}

export async function getRelationships(paperId: string): Promise<Relationship[]> {
  const { data } = await client.get(`/analysis/${paperId}/relationships`);
  return data;
}

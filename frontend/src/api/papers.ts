import client from './client';
import type { PaperSummary, PaperDetail, PaperSection, PaperEntity, Reference, ExtractedTable, PaginatedResponse, TaskResponse } from './types';

export async function uploadPaper(file: File): Promise<{ paper_id: string; task_id: string; message: string }> {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await client.post('/papers/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function listPapers(page = 1, perPage = 20, search?: string): Promise<PaginatedResponse<PaperSummary>> {
  const params: Record<string, unknown> = { page, per_page: perPage };
  if (search) params.search = search;
  const { data } = await client.get('/papers', { params });
  return data;
}

export async function getPaper(paperId: string): Promise<PaperDetail> {
  const { data } = await client.get(`/papers/${paperId}`);
  return data;
}

export async function deletePaper(paperId: string): Promise<void> {
  await client.delete(`/papers/${paperId}`);
}

export async function getSections(paperId: string): Promise<PaperSection[]> {
  const { data } = await client.get(`/papers/${paperId}/sections`);
  return data;
}

export async function getEntities(paperId: string, entityType?: string): Promise<PaperEntity[]> {
  const params: Record<string, unknown> = {};
  if (entityType) params.entity_type = entityType;
  const { data } = await client.get(`/papers/${paperId}/entities`, { params });
  return data;
}

export async function getReferences(paperId: string): Promise<Reference[]> {
  const { data } = await client.get(`/papers/${paperId}/references`);
  return data;
}

export async function getTables(paperId: string): Promise<ExtractedTable[]> {
  const { data } = await client.get(`/papers/${paperId}/tables`);
  return data;
}

export async function startParsing(paperId: string): Promise<TaskResponse> {
  const { data } = await client.post(`/parsing/${paperId}/start`);
  return data;
}

export async function getParsingStatus(paperId: string): Promise<{ paper_id: string; parsing_status: string; task: TaskResponse | null }> {
  const { data } = await client.get(`/parsing/${paperId}/status`);
  return data;
}

export async function reparsePaper(paperId: string): Promise<TaskResponse> {
  const { data } = await client.post(`/papers/${paperId}/reparse`);
  return data;
}

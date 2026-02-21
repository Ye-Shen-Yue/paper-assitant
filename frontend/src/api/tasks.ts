import client from './client';
import type { TaskStatus } from './types';

export async function getTaskStatus(taskId: string): Promise<TaskStatus> {
  const { data } = await client.get(`/tasks/${taskId}`);
  return data;
}

export async function listTasks(paperId?: string, status?: string): Promise<TaskStatus[]> {
  const params: Record<string, unknown> = {};
  if (paperId) params.paper_id = paperId;
  if (status) params.status = status;
  const { data } = await client.get('/tasks', { params });
  return data;
}

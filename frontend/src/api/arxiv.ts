import client from './client';

// Types
export interface ArxivSubscription {
  id: string;
  user_id: string;
  name: string;
  keywords: string[];
  categories: string[];
  authors: string[];
  max_results: number;
  is_active: boolean;
  last_crawled?: string;
  created_at: string;
  updated_at: string;
}

export interface ArxivPaper {
  id: string;
  title: string;
  authors: string[];
  summary: string;
  categories: string[];
  primary_category: string;
  published?: string;
  pdf_url: string;
  arxiv_url: string;
}

export interface ArxivPushRecord {
  id: string;
  user_id: string;
  subscription_id: string;
  arxiv_paper: ArxivPaper;
  match_score: number;
  is_read: boolean;
  is_imported: boolean;
  imported_paper_id?: string;
  created_at: string;
}

export interface ArxivCategory {
  code: string;
  name: string;
}

export interface ArxivCrawlLog {
  id: string;
  status: string;
  papers_found: number;
  papers_new: number;
  papers_pushed: number;
  started_at: string;
  completed_at?: string;
}

// Subscription API
export async function createSubscription(data: {
  user_id: string;
  name: string;
  keywords: string[];
  categories: string[];
  authors: string[];
  max_results: number;
}): Promise<ArxivSubscription> {
  const { data: result } = await client.post('/arxiv/subscriptions', data);
  return result;
}

export async function listSubscriptions(userId: string): Promise<ArxivSubscription[]> {
  const { data } = await client.get(`/arxiv/subscriptions/${userId}`);
  return data;
}

export async function getSubscription(subscriptionId: string): Promise<ArxivSubscription> {
  const { data } = await client.get(`/arxiv/subscriptions/detail/${subscriptionId}`);
  return data;
}

export async function updateSubscription(
  subscriptionId: string,
  data: Partial<ArxivSubscription>
): Promise<ArxivSubscription> {
  const { data: result } = await client.put(`/arxiv/subscriptions/${subscriptionId}`, data);
  return result;
}

export async function deleteSubscription(subscriptionId: string): Promise<{ success: boolean }> {
  const { data } = await client.delete(`/arxiv/subscriptions/${subscriptionId}`);
  return data;
}

// Search API
export async function searchArxiv(query: string, maxResults: number = 20): Promise<{
  total: number;
  papers: ArxivPaper[];
}> {
  const { data } = await client.post('/arxiv/search', { query, max_results: maxResults });
  return data;
}

export async function advancedSearch(params: {
  keywords?: string;
  categories?: string;
  authors?: string;
  date_from?: string;
  date_to?: string;
  max_results?: number;
}): Promise<{
  query: string;
  total: number;
  papers: ArxivPaper[];
}> {
  const { data } = await client.get('/arxiv/search/advanced', { params });
  return data;
}

// Push API
export async function getUserPushes(
  userId: string,
  options?: { unread_only?: boolean; limit?: number }
): Promise<{ total: number; pushes: ArxivPushRecord[] }> {
  const { data } = await client.get(`/arxiv/pushes/${userId}`, { params: options });
  return data;
}

export async function getUnreadCount(userId: string): Promise<{ unread_count: number }> {
  const { data } = await client.get(`/arxiv/pushes/${userId}/unread-count`);
  return data;
}

export async function markPushAsRead(pushId: string): Promise<{ success: boolean }> {
  const { data } = await client.post(`/arxiv/pushes/${pushId}/read`);
  return data;
}

// Import API
export async function importArxivPaper(arxivId: string, userId: string): Promise<{
  success: boolean;
  paper_id: string;
  message: string;
}> {
  const { data } = await client.post('/arxiv/import', { arxiv_id: arxivId, user_id: userId });
  return data;
}

// Crawl API
export async function triggerCrawl(subscriptionId: string): Promise<{
  success: boolean;
  task_id: string;
  message: string;
}> {
  const { data } = await client.post(`/arxiv/crawl/${subscriptionId}`);
  return data;
}

export async function getCrawlLogs(subscriptionId: string, limit: number = 10): Promise<{
  total: number;
  logs: ArxivCrawlLog[];
}> {
  const { data } = await client.get(`/arxiv/crawl/logs/${subscriptionId}`, {
    params: { limit },
  });
  return data;
}

// Categories API
export async function getCategories(): Promise<ArxivCategory[]> {
  const { data } = await client.get('/arxiv/categories');
  return data;
}

export async function searchCategories(query: string): Promise<{
  total: number;
  categories: ArxivCategory[];
}> {
  const { data } = await client.get('/arxiv/categories/search', { params: { q: query } });
  return data;
}

import client from './client';
import type { PaperSummary } from './types';

export interface UserActivity {
  user_id: string;
  paper_id: string;
  activity_type: 'view' | 'chat' | 'note' | 'export' | 'save' | 'scroll' | 'click';
  duration_seconds?: number;
  meta_info?: Record<string, unknown>;
}

export interface UserProfile {
  user_id: string;
  topic_distribution: Record<string, number>;
  method_preferences: string[];
  reading_pattern: 'browser' | 'researcher';
  total_papers_read: number;
  total_reading_time: number;
  streak_days: number;
  last_read_papers: string[];
  updated_at?: string;
}

export interface RecommendationItem {
  paper: PaperSummary;
  reason: string;
  reason_text: string;
  score: number;
}

export interface TrendData {
  heatmap_data: Array<{
    topic: string;
    year: number;
    count: number;
  }>;
  keyword_evolution: Array<{
    keyword: string;
    data: Array<{ year: number; count: number }>;
  }>;
  emerging_topics: Array<{
    topic: string;
    growth_rate: number;
    recent_count: number;
  }>;
  ai_summary: string;
}

export interface UserCollection {
  id: string;
  user_id: string;
  name: string;
  description: string;
  paper_ids: string[];
  paper_count: number;
  created_at: string;
  updated_at: string;
}

// Track user activity
export async function trackActivity(activity: UserActivity): Promise<{ success: boolean; activity_id: string }> {
  const { data } = await client.post('/recommendations/activities/track', activity);
  return data;
}

// Get user profile
export async function getUserProfile(userId: string): Promise<UserProfile> {
  const { data } = await client.get(`/recommendations/profile/${userId}`);
  return data;
}

// Refresh user profile
export async function refreshUserProfile(userId: string): Promise<{ success: boolean; message: string }> {
  const { data } = await client.post(`/recommendations/profile/${userId}/refresh`);
  return data;
}

// Get recommendations
export async function getRecommendations(
  userId: string,
  limit = 10,
  type: 'mixed' | 'content' | 'collaborative' | 'trending' = 'mixed'
): Promise<{ recommendations: RecommendationItem[]; total: number }> {
  const { data } = await client.get(`/recommendations/recommendations/${userId}`, {
    params: { limit, type },
  });
  return data;
}

// Log recommendation feedback
export async function logRecommendationFeedback(
  userId: string,
  paperId: string,
  recommendationType: string,
  clicked: boolean,
  rated?: number
): Promise<{ success: boolean }> {
  const { data } = await client.post(`/recommendations/recommendations/${userId}/feedback`, {
    paper_id: paperId,
    recommendation_type: recommendationType,
    clicked,
    rated,
  });
  return data;
}

// Get trend data
export async function getTrendData(
  userId: string,
  topics?: string[],
  years = 10
): Promise<TrendData> {
  const { data } = await client.get(`/recommendations/trends/${userId}`, {
    params: {
      topics: topics?.join(','),
      years,
    },
  });
  return data;
}

// Collections API
export async function createCollection(
  userId: string,
  name: string,
  description?: string
): Promise<UserCollection> {
  const { data } = await client.post('/recommendations/collections', {
    user_id: userId,
    name,
    description,
  });
  return data;
}

export async function listCollections(userId: string): Promise<UserCollection[]> {
  const { data } = await client.get(`/recommendations/collections/${userId}`);
  return data;
}

export async function addPaperToCollection(collectionId: string, paperId: string): Promise<{ success: boolean }> {
  const { data } = await client.post(`/recommendations/collections/${collectionId}/papers`, null, {
    params: { paper_id: paperId },
  });
  return data;
}

export async function removePaperFromCollection(collectionId: string, paperId: string): Promise<{ success: boolean }> {
  const { data } = await client.delete(`/recommendations/collections/${collectionId}/papers/${paperId}`);
  return data;
}

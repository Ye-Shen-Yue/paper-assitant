import client from './client';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  message: string;
  history?: ChatMessage[];
  selected_text?: string;
  language?: string;
}

export interface ChatResponse {
  response: string;
}

export interface QuickActionRequest {
  action: 'summarize' | 'translate' | 'explain' | 'critique';
  text?: string;
  target_language?: string;
}

export async function chatWithPaper(
  paperId: string,
  request: ChatRequest
): Promise<ChatResponse> {
  const response = await client.post<ChatResponse>(
    `/chat/${paperId}/chat`,
    request
  );
  return response.data;
}

export async function quickAction(
  paperId: string,
  request: QuickActionRequest
): Promise<ChatResponse> {
  const response = await client.post<ChatResponse>(
    `/chat/${paperId}/quick-action`,
    request
  );
  return response.data;
}

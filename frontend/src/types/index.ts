// Type definitions for the journaling application

export interface Entry {
  id: string;
  title: string;
  content: string;
  mood: MoodType;
  created_at: string;
  updated_at: string;
  topic_id?: string;
  tags?: string[];
  is_favorite: boolean;
  version: number;
}

export interface Topic {
  id: string;
  name: string;
  description?: string;
  color: string;
  created_at: string;
  updated_at: string;
}

export interface Session {
  id: string;
  type: SessionType;
  status: SessionStatus;
  title?: string;
  created_at: string;
  updated_at: string;
  last_activity?: string;
}

export interface Message {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export type MoodType = 'very_positive' | 'positive' | 'neutral' | 'negative' | 'very_negative';

export type SessionType = 'coaching' | 'analysis' | 'general' | 'guided_reflection';

export type SessionStatus = 'active' | 'paused' | 'completed' | 'archived';

export interface APIResponse<T = any> {
  data: T;
  status: number;
  statusText: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface SearchFilters {
  query?: string;
  mood?: MoodType;
  topic_id?: string;
  date_from?: string;
  date_to?: string;
  tags?: string[];
  is_favorite?: boolean;
  limit?: number;
  offset?: number;
}

export interface InsightData {
  patterns?: any[];
  coaching_suggestions?: string[];
  mood_trends?: any[];
  key_insights?: string[];
}

export interface Template {
  id: string;
  name: string;
  description?: string;
  content: string;
  category?: string;
  created_at: string;
}

// API parameter types
export interface CreateEntryData {
  title: string;
  content: string;
  mood: MoodType;
  topic_id?: string;
  tags?: string[];
}

export interface UpdateEntryData extends Partial<CreateEntryData> {}

export interface CreateTopicData {
  name: string;
  description?: string;
  color: string;
}

export interface UpdateTopicData extends Partial<CreateTopicData> {}

export interface CreateSessionData {
  type: SessionType;
  title?: string;
}

export interface UpdateSessionData {
  title?: string;
  status?: SessionStatus;
}

export interface SendMessageData {
  content: string;
  metadata?: Record<string, any>;
}
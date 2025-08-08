import { format, isToday, isYesterday, parseISO } from 'date-fns';

// Type definitions
export type MoodType = 'very_positive' | 'positive' | 'neutral' | 'negative' | 'very_negative';

export interface EntryValidation {
  isValid: boolean;
  errors: Record<string, string>;
}

export interface Entry {
  title?: string;
  content?: string;
  [key: string]: any;
}

// Date formatting utilities
export const formatDate = (date: string | Date): string => {
  const parsedDate = typeof date === 'string' ? parseISO(date) : date;
  
  if (isToday(parsedDate)) {
    return 'Today';
  } else if (isYesterday(parsedDate)) {
    return 'Yesterday';
  } else {
    return format(parsedDate, 'MMM d, yyyy');
  }
};

export const formatDateTime = (date: string | Date): string => {
  const parsedDate = typeof date === 'string' ? parseISO(date) : date;
  return format(parsedDate, 'MMM d, yyyy h:mm a');
};

export const formatTime = (date: string | Date): string => {
  const parsedDate = typeof date === 'string' ? parseISO(date) : date;
  return format(parsedDate, 'h:mm a');
};

// Mood utilities
export const getMoodColor = (mood: MoodType | string): string => {
  const moodColors: Record<MoodType, string> = {
    'very_positive': 'bg-mood-very-positive',
    'positive': 'bg-mood-positive',
    'neutral': 'bg-mood-neutral',
    'negative': 'bg-mood-negative',
    'very_negative': 'bg-mood-very-negative',
  };
  return moodColors[mood as MoodType] || 'bg-gray-400';
};

export const getMoodEmoji = (mood: MoodType | string): string => {
  const moodEmojis: Record<MoodType, string> = {
    'very_positive': '😊',
    'positive': '🙂',
    'neutral': '😐',
    'negative': '😟',
    'very_negative': '😢',
  };
  return moodEmojis[mood as MoodType] || '😐';
};

export const getMoodLabel = (mood: MoodType | string): string => {
  const moodLabels: Record<MoodType, string> = {
    'very_positive': 'Very Positive',
    'positive': 'Positive',
    'neutral': 'Neutral',
    'negative': 'Negative',
    'very_negative': 'Very Negative',
  };
  return moodLabels[mood as MoodType] || 'Unknown';
};

// Text utilities
export const truncateText = (text: string | null | undefined, length: number = 150): string => {
  if (!text) return '';
  return text.length > length ? `${text.substring(0, length)}...` : text;
};

export const getWordCount = (text: string | null | undefined): number => {
  if (!text) return 0;
  return text.trim().split(/\s+/).length;
};

// Validation utilities
export const validateEntry = (entry: Entry): EntryValidation => {
  const errors: Record<string, string> = {};
  
  if (!entry.title?.trim()) {
    errors.title = 'Title is required';
  }
  
  if (!entry.content?.trim()) {
    errors.content = 'Content is required';
  }
  
  if (entry.title && entry.title.length > 200) {
    errors.title = 'Title must be less than 200 characters';
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};

// Theme utilities
export const getTopicColor = (color: string): string => {
  const colorMap: Record<string, string> = {
    '#3B82F6': 'bg-blue-500',
    '#10B981': 'bg-emerald-500',
    '#F59E0B': 'bg-amber-500',
    '#EF4444': 'bg-red-500',
    '#8B5CF6': 'bg-violet-500',
    '#EC4899': 'bg-pink-500',
    '#06B6D4': 'bg-cyan-500',
    '#84CC16': 'bg-lime-500',
  };
  return colorMap[color] || 'bg-blue-500';
};

// Local storage utilities
export const storage = {
  get: <T>(key: string, defaultValue: T | null = null): T | null => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) as T : defaultValue;
    } catch (error) {
      console.error('Error reading from localStorage:', error);
      return defaultValue;
    }
  },
  
  set: <T>(key: string, value: T): void => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('Error writing to localStorage:', error);
    }
  },
  
  remove: (key: string): void => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('Error removing from localStorage:', error);
    }
  }
};
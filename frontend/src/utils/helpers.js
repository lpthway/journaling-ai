import { format, isToday, isYesterday, parseISO } from 'date-fns';

// Date formatting utilities
export const formatDate = (date) => {
  const parsedDate = typeof date === 'string' ? parseISO(date) : date;
  
  if (isToday(parsedDate)) {
    return 'Today';
  } else if (isYesterday(parsedDate)) {
    return 'Yesterday';
  } else {
    return format(parsedDate, 'MMM d, yyyy');
  }
};

export const formatDateTime = (date) => {
  const parsedDate = typeof date === 'string' ? parseISO(date) : date;
  return format(parsedDate, 'MMM d, yyyy h:mm a');
};

export const formatTime = (date) => {
  const parsedDate = typeof date === 'string' ? parseISO(date) : date;
  return format(parsedDate, 'h:mm a');
};

// Mood utilities
export const getMoodColor = (mood) => {
  const moodColors = {
    'very_positive': 'bg-mood-very-positive',
    'positive': 'bg-mood-positive',
    'neutral': 'bg-mood-neutral',
    'negative': 'bg-mood-negative',
    'very_negative': 'bg-mood-very-negative',
  };
  return moodColors[mood] || 'bg-gray-400';
};

export const getMoodEmoji = (mood) => {
  const moodEmojis = {
    'very_positive': '😊',
    'positive': '🙂',
    'neutral': '😐',
    'negative': '😟',
    'very_negative': '😢',
  };
  return moodEmojis[mood] || '😐';
};

export const getMoodLabel = (mood) => {
  const moodLabels = {
    'very_positive': 'Very Positive',
    'positive': 'Positive',
    'neutral': 'Neutral',
    'negative': 'Negative',
    'very_negative': 'Very Negative',
  };
  return moodLabels[mood] || 'Unknown';
};

// Text utilities
export const truncateText = (text, length = 150) => {
  if (!text) return '';
  return text.length > length ? `${text.substring(0, length)}...` : text;
};

export const getWordCount = (text) => {
  if (!text) return 0;
  return text.trim().split(/\s+/).length;
};

// Validation utilities
export const validateEntry = (entry) => {
  const errors = {};
  
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
export const getTopicColor = (color) => {
  const colorMap = {
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
  get: (key, defaultValue = null) => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
      console.error('Error reading from localStorage:', error);
      return defaultValue;
    }
  },
  
  set: (key, value) => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('Error writing to localStorage:', error);
    }
  },
  
  remove: (key) => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('Error removing from localStorage:', error);
    }
  }
};
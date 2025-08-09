// frontend/src/hooks/usePerformanceOptimization.js
/**
 * Performance optimization hooks for improved user experience
 */

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { entryAPI } from '../services/api';

// Custom hook for lazy loading with intersection observer
export const useLazyLoading = (threshold = 0.1) => {
  const [isVisible, setIsVisible] = useState(false);
  const [hasLoaded, setHasLoaded] = useState(false);
  const ref = useRef();

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasLoaded) {
          setIsVisible(true);
          setHasLoaded(true);
          observer.unobserve(entry.target);
        }
      },
      { threshold }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => {
      if (ref.current) {
        observer.unobserve(ref.current);
      }
    };
  }, [threshold, hasLoaded]);

  return { ref, isVisible, hasLoaded };
};

// Custom hook for debounced search
export const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

// Custom hook for optimized entry loading
export const useOptimizedEntries = (limit = 20) => {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState(null);
  const offset = useRef(0);

  // Load entries with lightweight data
  const loadEntries = useCallback(async (reset = false) => {
    if (loading) return;

    try {
      setLoading(true);
      setError(null);
      
      const currentOffset = reset ? 0 : offset.current;
      
      // Use performance-optimized endpoint if available, fallback to regular
      let response;
      try {
        response = await fetch(
          `/api/v1/performance/entries/lightweight?limit=${limit}&offset=${currentOffset}&include_content=false`,
          { 
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
          }
        );
        
        if (!response.ok) throw new Error('Performance endpoint failed');
        
        const data = await response.json();
        const newEntries = data.entries || [];
        
        if (reset) {
          setEntries(newEntries);
          offset.current = newEntries.length;
        } else {
          setEntries(prev => [...prev, ...newEntries]);
          offset.current += newEntries.length;
        }
        
        setHasMore(newEntries.length === limit);
        
      } catch (perfError) {
        console.warn('Performance endpoint unavailable, using fallback:', perfError.message);
        
        // Fallback to regular API
        response = await entryAPI.getAll({ 
          limit, 
          offset: currentOffset 
        });
        
        const newEntries = response.data || [];
        
        if (reset) {
          setEntries(newEntries);
          offset.current = newEntries.length;
        } else {
          setEntries(prev => [...prev, ...newEntries]);
          offset.current += newEntries.length;
        }
        
        setHasMore(newEntries.length === limit);
      }
      
    } catch (err) {
      console.error('Error loading entries:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [limit, loading]);

  // Load more entries
  const loadMore = useCallback(() => {
    if (!loading && hasMore) {
      loadEntries(false);
    }
  }, [loadEntries, loading, hasMore]);

  // Refresh entries
  const refresh = useCallback(() => {
    offset.current = 0;
    loadEntries(true);
  }, [loadEntries]);

  // Initialize
  useEffect(() => {
    loadEntries(true);
  }, []);

  return {
    entries,
    loading,
    error,
    hasMore,
    loadMore,
    refresh
  };
};

// Custom hook for lazy loading entry content
export const useLazyEntryContent = (entryId) => {
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadContent = useCallback(async () => {
    if (!entryId || content || loading) return;

    try {
      setLoading(true);
      setError(null);

      // Try performance-optimized endpoint first
      try {
        const response = await fetch(
          `/api/v1/performance/entries/${entryId}/content`,
          { 
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
          }
        );

        if (!response.ok) throw new Error('Performance endpoint failed');

        const data = await response.json();
        setContent(data);
        
      } catch (perfError) {
        console.warn('Performance endpoint unavailable, using fallback');
        
        // Fallback to regular API
        const response = await entryAPI.getById(entryId);
        setContent({
          id: response.data.id,
          content: response.data.content,
          tags: response.data.tags || []
        });
      }

    } catch (err) {
      console.error('Error loading entry content:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [entryId, content, loading]);

  return {
    content,
    loading,
    error,
    loadContent
  };
};

// Custom hook for memoized calculations
export const useMemoizedInsights = (entries) => {
  return useMemo(() => {
    if (!entries || entries.length === 0) {
      return {
        totalEntries: 0,
        averageMood: 0,
        recentEntries: [],
        moodDistribution: {}
      };
    }

    const moodValues = {
      'very_happy': 5,
      'happy': 4,
      'neutral': 3,
      'sad': 2,
      'very_sad': 1
    };

    const moodDistribution = {};
    let totalMoodValue = 0;

    entries.forEach(entry => {
      const mood = entry.mood || 'neutral';
      moodDistribution[mood] = (moodDistribution[mood] || 0) + 1;
      totalMoodValue += moodValues[mood] || 3;
    });

    const averageMood = entries.length > 0 ? totalMoodValue / entries.length : 3;
    const recentEntries = entries.slice(0, 5);

    return {
      totalEntries: entries.length,
      averageMood: Math.round(averageMood * 10) / 10,
      recentEntries,
      moodDistribution
    };
  }, [entries]);
};

// Custom hook for optimized search
export const useOptimizedSearch = (delay = 300) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const debouncedQuery = useDebounce(query, delay);

  // Search function with performance optimization
  const search = useCallback(async (searchQuery) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Try performance-optimized search first
      try {
        const response = await fetch(
          `/api/v1/performance/search/fast?query=${encodeURIComponent(searchQuery)}&limit=10`,
          {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
          }
        );

        if (!response.ok) throw new Error('Performance search failed');

        const data = await response.json();
        setResults(data.results || []);

      } catch (perfError) {
        console.warn('Performance search unavailable, using fallback');

        // Fallback to regular search
        const response = await entryAPI.search(searchQuery, 10);
        setResults(response.data || []);
      }

    } catch (err) {
      console.error('Search error:', err);
      setError(err.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-search when debounced query changes
  useEffect(() => {
    if (debouncedQuery) {
      search(debouncedQuery);
    } else {
      setResults([]);
    }
  }, [debouncedQuery, search]);

  return {
    query,
    setQuery,
    results,
    loading,
    error,
    search
  };
};

// Custom hook for intersection observer (infinite scroll)
export const useInfiniteScroll = (callback, hasMore = true) => {
  const [isFetching, setIsFetching] = useState(false);
  const ref = useRef();

  useEffect(() => {
    if (!hasMore || isFetching) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsFetching(true);
          callback().finally(() => setIsFetching(false));
        }
      },
      { threshold: 0.1 }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => {
      if (ref.current) {
        observer.unobserve(ref.current);
      }
    };
  }, [callback, hasMore, isFetching]);

  return { ref, isFetching };
};
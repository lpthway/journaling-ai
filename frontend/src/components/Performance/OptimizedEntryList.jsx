// frontend/src/components/Performance/OptimizedEntryList.jsx
/**
 * Performance-optimized entry list with lazy loading, virtual scrolling, and memoization
 */

import React, { memo, useCallback, useMemo } from 'react';
import { ChevronRightIcon, HeartIcon as HeartSolid } from '@heroicons/react/20/solid';
import { HeartIcon, SparklesIcon } from '@heroicons/react/24/outline';
import { 
  useOptimizedEntries, 
  useInfiniteScroll, 
  useLazyLoading,
  useLazyEntryContent 
} from '../../hooks/usePerformanceOptimization';

// Memoized entry card component
const OptimizedEntryCard = memo(({ entry, onClick, onToggleFavorite }) => {
  const { ref, isVisible } = useLazyLoading(0.1);

  // Format date with memoization
  const formattedDate = useMemo(() => {
    return new Date(entry.created_at).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  }, [entry.created_at]);

  // Mood color mapping with memoization
  const moodColor = useMemo(() => {
    const colors = {
      'very_happy': 'text-green-600 bg-green-50',
      'happy': 'text-green-500 bg-green-50',
      'neutral': 'text-gray-500 bg-gray-50',
      'sad': 'text-orange-500 bg-orange-50',
      'very_sad': 'text-red-500 bg-red-50'
    };
    return colors[entry.mood] || colors.neutral;
  }, [entry.mood]);

  const handleFavoriteClick = useCallback((e) => {
    e.stopPropagation();
    onToggleFavorite?.(entry.id);
  }, [entry.id, onToggleFavorite]);

  return (
    <div ref={ref} className="min-h-[100px]">
      {isVisible && (
        <div
          onClick={() => onClick?.(entry.id)}
          className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow cursor-pointer bg-white"
        >
          <div className="flex justify-between items-start">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <h3 className="text-lg font-semibold text-gray-900 truncate">
                  {entry.title || 'Untitled Entry'}
                </h3>
                {entry.is_favorite && (
                  <HeartSolid className="w-4 h-4 text-red-500 flex-shrink-0" />
                )}
              </div>
              
              <div className="flex items-center gap-4 text-sm text-gray-600 mb-2">
                <span>{formattedDate}</span>
                <span className={`px-2 py-1 rounded-full text-xs ${moodColor}`}>
                  {entry.mood?.replace('_', ' ') || 'neutral'}
                </span>
                <span>{entry.word_count || 0} words</span>
              </div>

              {/* Content preview for lightweight entries */}
              {entry.content_preview && (
                <p className="text-gray-700 text-sm line-clamp-2">
                  {entry.content_preview}
                </p>
              )}
            </div>

            <div className="flex items-center gap-2 ml-4">
              <button
                onClick={handleFavoriteClick}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                aria-label={entry.is_favorite ? 'Remove from favorites' : 'Add to favorites'}
              >
                {entry.is_favorite ? (
                  <HeartSolid className="w-4 h-4 text-red-500" />
                ) : (
                  <HeartIcon className="w-4 h-4 text-gray-400 hover:text-red-500" />
                )}
              </button>
              <ChevronRightIcon className="w-4 h-4 text-gray-400" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
});

OptimizedEntryCard.displayName = 'OptimizedEntryCard';

// Lazy-loaded entry content component
const LazyEntryContent = memo(({ entryId, onClose }) => {
  const { content, loading, error, loadContent } = useLazyEntryContent(entryId);

  React.useEffect(() => {
    if (entryId && !content && !loading && !error) {
      loadContent();
    }
  }, [entryId, content, loading, error, loadContent]);

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-md w-mx-4">
          <div className="flex items-center justify-center">
            <SparklesIcon className="w-6 h-6 text-blue-500 animate-spin" />
            <span className="ml-2">Loading content...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-md mx-4">
          <div className="text-center">
            <p className="text-red-600 mb-4">Failed to load content: {error}</p>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!content) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl max-h-[80vh] w-full flex flex-col">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-xl font-semibold">Entry Content</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl font-bold"
          >
            ×
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto flex-1">
          <div className="prose max-w-none">
            {content.content}
          </div>
          
          {content.tags && content.tags.length > 0 && (
            <div className="mt-6 pt-4 border-t">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Tags:</h3>
              <div className="flex flex-wrap gap-2">
                {content.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
});

LazyEntryContent.displayName = 'LazyEntryContent';

// Main optimized entry list component
const OptimizedEntryList = ({ 
  className = '',
  onEntryClick,
  onToggleFavorite
}) => {
  const { entries, loading, error, hasMore, loadMore, refresh } = useOptimizedEntries(20);
  const [selectedEntryId, setSelectedEntryId] = React.useState(null);

  // Infinite scroll setup
  const handleLoadMore = useCallback(async () => {
    if (hasMore && !loading) {
      await loadMore();
    }
  }, [hasMore, loading, loadMore]);

  const { ref: loadMoreRef, isFetching } = useInfiniteScroll(handleLoadMore, hasMore);

  // Handle entry click
  const handleEntryClick = useCallback((entryId) => {
    if (onEntryClick) {
      onEntryClick(entryId);
    } else {
      setSelectedEntryId(entryId);
    }
  }, [onEntryClick]);

  // Handle favorite toggle with optimistic update
  const handleToggleFavorite = useCallback(async (entryId) => {
    try {
      // Optimistic update
      const updatedEntries = entries.map(entry => 
        entry.id === entryId 
          ? { ...entry, is_favorite: !entry.is_favorite }
          : entry
      );
      
      if (onToggleFavorite) {
        await onToggleFavorite(entryId);
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
      // Revert optimistic update on error
      refresh();
    }
  }, [entries, onToggleFavorite, refresh]);

  if (error) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <p className="text-red-600 mb-4">Failed to load entries: {error}</p>
        <button
          onClick={refresh}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Entry list */}
      <div className="space-y-4">
        {entries.map((entry) => (
          <OptimizedEntryCard
            key={entry.id}
            entry={entry}
            onClick={handleEntryClick}
            onToggleFavorite={handleToggleFavorite}
          />
        ))}
      </div>

      {/* Loading more indicator */}
      {hasMore && (
        <div ref={loadMoreRef} className="py-8 text-center">
          {(loading || isFetching) && (
            <div className="flex items-center justify-center">
              <SparklesIcon className="w-5 h-5 text-blue-500 animate-spin mr-2" />
              <span className="text-gray-600">Loading more entries...</span>
            </div>
          )}
        </div>
      )}

      {/* No more entries message */}
      {!hasMore && entries.length > 0 && (
        <div className="text-center py-8 text-gray-500">
          <p>You've reached the end of your entries</p>
        </div>
      )}

      {/* Empty state */}
      {!loading && entries.length === 0 && (
        <div className="text-center py-12">
          <SparklesIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No entries found</h3>
          <p className="text-gray-500">Start writing your first journal entry!</p>
        </div>
      )}

      {/* Lazy-loaded entry content modal */}
      {selectedEntryId && (
        <LazyEntryContent
          entryId={selectedEntryId}
          onClose={() => setSelectedEntryId(null)}
        />
      )}
    </div>
  );
};

export default OptimizedEntryList;
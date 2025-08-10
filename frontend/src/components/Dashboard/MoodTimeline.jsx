// frontend/src/components/Dashboard/MoodTimeline.jsx
import React from 'react';
import { 
  FaceSmileIcon, 
  FaceFrownIcon,
  HeartIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { 
  FaceSmileIcon as FaceSmileIconSolid,
  FaceFrownIcon as FaceFrownIconSolid,
  HeartIcon as HeartIconSolid
} from '@heroicons/react/24/solid';

const MoodTimeline = ({ entries = [] }) => {
  // Group entries by date for timeline
  const groupedEntries = entries.reduce((acc, entry) => {
    const date = new Date(entry.created_at).toDateString();
    if (!acc[date]) {
      acc[date] = [];
    }
    acc[date].push(entry);
    return acc;
  }, {});

  const timelineData = Object.entries(groupedEntries)
    .map(([date, dayEntries]) => {
      // Calculate average mood for the day
      const moodScores = dayEntries
        .filter(entry => entry.sentiment_score !== null)
        .map(entry => entry.sentiment_score);
      
      const avgMood = moodScores.length > 0 
        ? moodScores.reduce((sum, score) => sum + score, 0) / moodScores.length
        : null;

      return {
        date,
        entries: dayEntries,
        avgMood,
        entryCount: dayEntries.length
      };
    })
    .sort((a, b) => new Date(a.date) - new Date(b.date))
    .slice(-7); // Show last 7 days

  const getMoodIcon = (moodScore) => {
    if (moodScore === null) return ExclamationTriangleIcon;
    if (moodScore >= 0.7) return FaceSmileIconSolid;
    if (moodScore >= 0.4) return HeartIcon;
    return FaceFrownIcon;
  };

  const getMoodColor = (moodScore) => {
    if (moodScore === null) return 'text-gray-400';
    if (moodScore >= 0.7) return 'text-green-500';
    if (moodScore >= 0.4) return 'text-blue-500';
    return 'text-orange-500';
  };

  const getMoodLabel = (moodScore) => {
    if (moodScore === null) return 'No data';
    if (moodScore >= 0.8) return 'Very Positive';
    if (moodScore >= 0.6) return 'Positive';
    if (moodScore >= 0.4) return 'Neutral';
    if (moodScore >= 0.2) return 'Low';
    return 'Very Low';
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      });
    }
  };

  if (timelineData.length === 0) {
    return (
      <div className="text-center py-8">
        <HeartIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <p className="text-gray-500 text-sm">Start journaling to see your mood timeline</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium text-gray-900 mb-4">7-Day Mood Timeline</h3>
      
      {/* Timeline */}
      <div className="relative">
        {/* Connecting line */}
        <div className="absolute left-6 top-6 bottom-6 w-0.5 bg-gray-200"></div>
        
        <div className="space-y-4">
          {timelineData.map((day, index) => {
            const MoodIcon = getMoodIcon(day.avgMood);
            const moodColor = getMoodColor(day.avgMood);
            
            return (
              <div key={day.date} className="relative flex items-start">
                {/* Mood icon */}
                <div className={`flex-shrink-0 w-12 h-12 rounded-full bg-white border-2 border-gray-200 flex items-center justify-center ${
                  day.avgMood !== null ? 'shadow-sm' : ''
                }`}>
                  <MoodIcon className={`h-6 w-6 ${moodColor}`} />
                </div>
                
                {/* Content */}
                <div className="ml-4 flex-1">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">
                        {formatDate(day.date)}
                      </h4>
                      <p className="text-xs text-gray-500">
                        {day.entryCount} {day.entryCount === 1 ? 'entry' : 'entries'}
                      </p>
                    </div>
                    
                    {day.avgMood !== null && (
                      <div className="text-right">
                        <span className={`text-sm font-medium ${moodColor}`}>
                          {getMoodLabel(day.avgMood)}
                        </span>
                        <p className="text-xs text-gray-400">
                          {(day.avgMood * 100).toFixed(0)}% positive
                        </p>
                      </div>
                    )}
                  </div>
                  
                  {/* Entry preview */}
                  {day.entries.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs text-gray-600 line-clamp-2">
                        {day.entries[0].title}
                        {day.entries.length > 1 && ` +${day.entries.length - 1} more`}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Mood legend */}
      <div className="border-t pt-4">
        <p className="text-xs text-gray-500 mb-2">Mood Scale</p>
        <div className="flex items-center space-x-4 text-xs">
          <div className="flex items-center">
            <FaceFrownIcon className="h-4 w-4 text-orange-500 mr-1" />
            <span className="text-gray-600">Low</span>
          </div>
          <div className="flex items-center">
            <HeartIcon className="h-4 w-4 text-blue-500 mr-1" />
            <span className="text-gray-600">Neutral</span>
          </div>
          <div className="flex items-center">
            <FaceSmileIconSolid className="h-4 w-4 text-green-500 mr-1" />
            <span className="text-gray-600">Positive</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MoodTimeline;
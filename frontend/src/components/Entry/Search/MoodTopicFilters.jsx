import React from 'react';

const MoodTopicFilters = ({ mood, topic_id, topics, onChange }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Mood Filter */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Mood
        </label>
        <select
          value={mood}
          onChange={(e) => onChange('mood', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">Any mood</option>
          <option value="very_positive">Very Positive</option>
          <option value="positive">Positive</option>
          <option value="neutral">Neutral</option>
          <option value="negative">Negative</option>
          <option value="very_negative">Very Negative</option>
        </select>
      </div>

      {/* Topic Filter */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Topic
        </label>
        <select
          value={topic_id}
          onChange={(e) => onChange('topic_id', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">Any topic</option>
          {topics.map(topic => (
            <option key={topic.id} value={topic.id}>
              {topic.name}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};

export default MoodTopicFilters;
import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { getMoodColor, getMoodLabel, getMoodEmoji } from '../../utils/helpers';

const MoodChart = ({ data }) => {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">No mood data available</p>
      </div>
    );
  }

  // Convert mood distribution to chart data
  const chartData = Object.entries(data).map(([mood, count]) => ({
    name: getMoodLabel(mood),
    value: count,
    mood: mood,
    emoji: getMoodEmoji(mood)
  })).filter(item => item.value > 0);

  const COLORS = {
    'very_positive': '#10B981',
    'positive': '#6EE7B7',
    'neutral': '#9CA3AF',
    'negative': '#F87171',
    'very_negative': '#EF4444'
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="text-sm font-medium">
            {data.emoji} {data.name}
          </p>
          <p className="text-sm text-gray-600">
            {data.value} entries
          </p>
        </div>
      );
    }
    return null;
  };

  const CustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
    if (percent < 0.05) return null; // Don't show labels for small slices
    
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        fontSize="12"
        fontWeight="bold"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={CustomLabel}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={COLORS[entry.mood]} 
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            formatter={(value, entry) => `${entry.payload.emoji} ${value}`}
            wrapperStyle={{ fontSize: '14px' }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

export default MoodChart;
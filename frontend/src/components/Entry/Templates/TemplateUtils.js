// Utility functions for template management

export const getCategoryColor = (category) => {
  const colorMap = {
    'Reflection': 'bg-blue-100 text-blue-800',
    'Planning': 'bg-green-100 text-green-800',
    'Creativity': 'bg-purple-100 text-purple-800',
    'Wellness': 'bg-pink-100 text-pink-800',
    'Work': 'bg-yellow-100 text-yellow-800',
    'Custom': 'bg-gray-100 text-gray-800'
  };
  return colorMap[category] || 'bg-gray-100 text-gray-800';
};
import React, { useState, useEffect } from 'react';
import { DocumentTextIcon, PlusIcon, SparklesIcon, ClockIcon } from '@heroicons/react/24/outline';
import { entryAPI } from '../../services/api';
import { toast } from 'react-hot-toast';

const EntryTemplates = ({ onSelectTemplate, onClose, isVisible }) => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [customTemplate, setCustomTemplate] = useState({
    name: '',
    description: '',
    category: 'Custom',
    content_template: '',
    tags: []
  });
  const [newTag, setNewTag] = useState('');

  // Pre-defined templates
  const defaultTemplates = [
    {
      id: 'daily-reflection',
      name: 'Daily Reflection',
      description: 'Reflect on your day, thoughts, and experiences',
      category: 'Reflection',
      content_template: `# Daily Reflection - {date}

## How was my day?


## What am I grateful for today?
1. 
2. 
3. 

## What did I learn today?


## What could I have done better?


## Tomorrow I want to focus on:

`,
      prompts: [
        'How did today make you feel?',
        'What was the highlight of your day?',
        'What challenged you today?',
        'What are you looking forward to tomorrow?'
      ],
      tags: ['daily', 'reflection', 'gratitude']
    },
    {
      id: 'gratitude-journal',
      name: 'Gratitude Journal',
      description: 'Focus on the positive aspects of your life',
      category: 'Gratitude',
      content_template: `# Gratitude Journal - {date}

## Three things I'm grateful for today:
1. 
2. 
3. 

## Why am I grateful for these things?


## How did gratitude make me feel today?


## One small thing that brought me joy:


## Someone I appreciate and why:

`,
      prompts: [
        'What made you smile today?',
        'Who are you thankful for and why?',
        'What simple pleasure did you enjoy?',
        'What opportunity are you grateful for?'
      ],
      tags: ['gratitude', 'positivity', 'mindfulness']
    },
    {
      id: 'goal-setting',
      name: 'Goal Setting',
      description: 'Plan and track your personal and professional goals',
      category: 'Planning',
      content_template: `# Goal Setting Session - {date}

## Current Goal Focus:


## Progress since last review:


## What's working well?


## What obstacles am I facing?


## Action steps for the next week:
1. 
2. 
3. 

## How will I measure success?


## Motivation reminder:

`,
      prompts: [
        'What goal is most important to you right now?',
        'What steps have you taken toward your goals recently?',
        'What\'s preventing you from making progress?',
        'How will achieving this goal change your life?'
      ],
      tags: ['goals', 'planning', 'progress', 'motivation']
    },
    {
      id: 'problem-solving',
      name: 'Problem Solving',
      description: 'Work through challenges and find solutions',
      category: 'Analysis',
      content_template: `# Problem Solving - {date}

## The challenge I'm facing:


## Why is this important to solve?


## What have I tried so far?


## Possible solutions:
1. 
2. 
3. 

## Pros and cons of each solution:

### Solution 1:
Pros: 
Cons: 

### Solution 2:
Pros: 
Cons: 

### Solution 3:
Pros: 
Cons: 

## My chosen approach:


## Next steps:

`,
      prompts: [
        'What exactly is the problem you\'re trying to solve?',
        'Who else might be affected by this problem?',
        'What resources do you have available?',
        'What would success look like?'
      ],
      tags: ['problem-solving', 'analysis', 'decision-making']
    },
    {
      id: 'mood-check',
      name: 'Mood Check-in',
      description: 'Track and understand your emotional state',
      category: 'Wellness',
      content_template: `# Mood Check-in - {date}

## Current mood: 
(Scale 1-10, where 1 is very low and 10 is very high)

## What's influencing my mood today?


## Physical sensations I'm noticing:


## Thoughts that are prominent:


## What do I need right now?


## One thing I can do to support myself:


## Affirmation for today:

`,
      prompts: [
        'How are you feeling in your body right now?',
        'What emotions are you experiencing?',
        'What triggered your current mood?',
        'What would help you feel better?'
      ],
      tags: ['mood', 'emotions', 'wellness', 'mindfulness']
    },
    {
      id: 'creative-inspiration',
      name: 'Creative Inspiration',
      description: 'Capture ideas and creative thoughts',
      category: 'Creativity',
      content_template: `# Creative Session - {date}

## Random thoughts and ideas:


## Inspiration sources today:


## Project I'm excited about:


## Creative challenge I want to tackle:


## New technique or skill to explore:


## Color/texture/sound that caught my attention:


## Quote or phrase that resonates:

`,
      prompts: [
        'What creative project excites you most right now?',
        'Where do you find your best inspiration?',
        'What would you create if there were no limitations?',
        'What artistic medium are you curious about?'
      ],
      tags: ['creativity', 'inspiration', 'art', 'ideas']
    }
  ];

  useEffect(() => {
    if (isVisible) {
      loadTemplates();
    }
  }, [isVisible]);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const response = await entryAPI.getTemplates();
      // Combine default templates with custom ones
      const customTemplates = response.data || [];
      setTemplates([...defaultTemplates, ...customTemplates]);
    } catch (error) {
      console.error('Error loading templates:', error);
      // Fall back to default templates if API fails
      setTemplates(defaultTemplates);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectTemplate = (template) => {
    const today = new Date().toLocaleDateString();
    const templateContent = template.content || template.content_template || '';
    const content = templateContent.replace('{date}', today);
    
    onSelectTemplate({
      title: `${template.name || template.title} - ${today}`,
      content: content,
      tags: template.tags || [],
      template_id: template.id
    });
    
    toast.success(`Using ${template.name || template.title} template`);
    onClose();
  };

  const getCategoryColor = (category) => {
    const colors = {
      'Reflection': 'bg-blue-100 text-blue-800',
      'Gratitude': 'bg-green-100 text-green-800',
      'Planning': 'bg-purple-100 text-purple-800',
      'Analysis': 'bg-orange-100 text-orange-800',
      'Wellness': 'bg-pink-100 text-pink-800',
      'Creativity': 'bg-yellow-100 text-yellow-800',
      'Custom': 'bg-gray-100 text-gray-800'
    };
    return colors[category] || colors['Custom'];
  };

  const handleCreateTemplate = () => {
    if (!customTemplate.name.trim() || !customTemplate.content_template.trim()) {
      toast.error('Please provide a name and content for the template');
      return;
    }

    const newTemplate = {
      ...customTemplate,
      id: `custom-${Date.now()}`,
      category: customTemplate.category || 'Custom'
    };

    setTemplates(prev => [...prev, newTemplate]);
    setShowCreateForm(false);
    setCustomTemplate({
      name: '',
      description: '',
      category: 'Custom',
      content_template: '',
      tags: []
    });
    toast.success('Custom template created successfully!');
  };

  const handleAddTag = () => {
    if (newTag.trim() && !customTemplate.tags.includes(newTag.trim())) {
      setCustomTemplate(prev => ({
        ...prev,
        tags: [...prev.tags, newTag.trim()]
      }));
      setNewTag('');
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    setCustomTemplate(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  if (!isVisible) return null;

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full p-8">
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    );
  }

  // Custom template creation form
  if (showCreateForm) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center">
              <PlusIcon className="w-5 h-5 mr-2" />
              Create Custom Template
            </h2>
            <button
              onClick={() => setShowCreateForm(false)}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-md transition-colors"
            >
              ×
            </button>
          </div>

          {/* Form */}
          <div className="p-6 space-y-6">
            {/* Template Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Template Name *
              </label>
              <input
                type="text"
                value={customTemplate.name}
                onChange={(e) => setCustomTemplate(prev => ({ ...prev, name: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., Weekly Review"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <input
                type="text"
                value={customTemplate.description}
                onChange={(e) => setCustomTemplate(prev => ({ ...prev, description: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Brief description of what this template is for"
              />
            </div>

            {/* Category */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category
              </label>
              <select
                value={customTemplate.category}
                onChange={(e) => setCustomTemplate(prev => ({ ...prev, category: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="Custom">Custom</option>
                <option value="Reflection">Reflection</option>
                <option value="Gratitude">Gratitude</option>
                <option value="Planning">Planning</option>
                <option value="Analysis">Analysis</option>
                <option value="Wellness">Wellness</option>
                <option value="Creativity">Creativity</option>
              </select>
            </div>

            {/* Template Content */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Template Content *
              </label>
              <div className="text-sm text-gray-600 mb-2">
                Use {'{date}'} to insert the current date automatically.
              </div>
              <textarea
                value={customTemplate.content_template}
                onChange={(e) => setCustomTemplate(prev => ({ ...prev, content_template: e.target.value }))}
                rows={10}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                placeholder={`# My Custom Template - {date}

## Section 1:


## Section 2:


## Reflection:

`}
              />
            </div>

            {/* Tags */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tags
              </label>
              <div className="flex space-x-2 mb-2">
                <input
                  type="text"
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Add a tag"
                />
                <button
                  type="button"
                  onClick={handleAddTag}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
                >
                  Add
                </button>
              </div>
              {customTemplate.tags.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {customTemplate.tags.map((tag, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {tag}
                      <button
                        type="button"
                        onClick={() => handleRemoveTag(tag)}
                        className="ml-1 text-blue-600 hover:text-blue-800"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200">
            <button
              onClick={() => setShowCreateForm(false)}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateTemplate}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Create Template
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center">
            <DocumentTextIcon className="w-5 h-5 mr-2" />
            Entry Templates
          </h2>
          <div className="flex space-x-2">
            <button
              onClick={() => setShowCreateForm(true)}
              className="inline-flex items-center px-3 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Create Custom
            </button>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-md transition-colors"
            >
              ×
            </button>
          </div>
        </div>

        {/* Templates Grid */}
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map((template) => (
              <div
                key={template.id}
                className="bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow duration-200 cursor-pointer group"
                onClick={() => handleSelectTemplate(template)}
              >
                <div className="p-6">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-2">
                      <SparklesIcon className="w-5 h-5 text-blue-500" />
                      <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                        {template.name}
                      </h3>
                    </div>
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(template.category)}`}>
                      {template.category}
                    </span>
                  </div>

                  {/* Description */}
                  <p className="text-gray-600 text-sm mb-4">
                    {template.description}
                  </p>

                  {/* Preview */}
                  <div className="bg-gray-50 rounded-md p-3 mb-4">
                    <div className="text-xs text-gray-500 mb-2">Template preview:</div>
                    <div className="text-sm text-gray-700 font-mono whitespace-pre-wrap max-h-24 overflow-hidden">
                      {(template.content || template.content_template || '').substring(0, 150)}...
                    </div>
                  </div>

                  {/* Tags */}
                  {template.tags && template.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-4">
                      {template.tags.slice(0, 3).map((tag, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                        >
                          {tag}
                        </span>
                      ))}
                      {template.tags.length > 3 && (
                        <span className="text-xs text-gray-500">
                          +{template.tags.length - 3} more
                        </span>
                      )}
                    </div>
                  )}

                  {/* Prompts preview */}
                  {template.prompts && template.prompts.length > 0 && (
                    <div className="border-t border-gray-200 pt-3">
                      <div className="text-xs text-gray-500 mb-2">Guided prompts included:</div>
                      <div className="text-sm text-gray-600">
                        {template.prompts.length} reflection questions
                      </div>
                    </div>
                  )}

                  {/* Use button */}
                  <div className="mt-4 pt-3 border-t border-gray-200">
                    <div className="text-center">
                      <span className="text-sm text-blue-600 group-hover:text-blue-700 font-medium">
                        Click to use template →
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {templates.length === 0 && (
            <div className="text-center py-12">
              <DocumentTextIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No templates available</h3>
              <p className="text-gray-600">
                Create your first custom template to get started.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EntryTemplates;

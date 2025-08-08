// Pre-defined templates configuration
export const defaultTemplates = [
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
    tags: ['daily', 'reflection', 'gratitude', 'goals']
  },
  {
    id: 'goal-setting',
    name: 'Goal Setting & Planning',
    description: 'Set intentions and create action plans',
    category: 'Planning',
    content_template: `# Goal Planning Session - {date}

## My main goal:


## Why is this important to me?


## Key milestones:
- [ ] 
- [ ] 
- [ ] 

## Action steps for this week:
1. 
2. 
3. 

## Potential obstacles and solutions:
- Obstacle: 
  Solution: 

## Resources I need:


## How will I measure progress?


## Accountability partner/method:

`,
    prompts: [
      'What do you want to achieve most right now?',
      'What obstacles might you face?',
      'What resources do you need to succeed?',
      'How will you track your progress?'
    ],
    tags: ['goals', 'planning', 'productivity', 'strategy']
  },
  {
    id: 'problem-solving',
    name: 'Problem Solving & Decision Making',
    description: 'Work through challenges and difficult decisions',
    category: 'Reflection',
    content_template: `# Problem Solving Session - {date}

## The challenge I'm facing:


## How does this situation make me feel?


## What I've already tried:
- 
- 
- 

## Different perspectives to consider:
1. 
2. 
3. 

## Possible solutions:
### Option A:
- Pros: 
- Cons: 

### Option B:
- Pros: 
- Cons: 

### Option C:
- Pros: 
- Cons: 

## My decision and reasoning:


## Next steps:
1. 
2. 
3. 

## What support do I need?

`,
    prompts: [
      'What aspects of this problem concern you most?',
      'What would your wisest friend advise?',
      'What would happen if you did nothing?',
      'What matters most in this decision?'
    ],
    tags: ['problem-solving', 'decisions', 'analysis', 'clarity']
  },
  {
    id: 'mood-check',
    name: 'Mood & Emotional Check-in',
    description: 'Track and understand your emotional state',
    category: 'Wellness',
    content_template: `# Mood Check-in - {date}

## Current emotional state:
Rate from 1-10: 

## Primary emotions I'm feeling:
- 
- 
- 

## Physical sensations I notice:


## What contributed to my current mood?
### Positive influences:
- 
- 

### Challenging influences:
- 
- 

## What my emotions might be telling me:


## What would help me feel better?


## Self-care action I can take today:


## Affirmation for myself:

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
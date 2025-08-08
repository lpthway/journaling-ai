import React from 'react';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';
import MoodIndicator from '../Common/MoodIndicator';

// Mock the helpers module
jest.mock('../../utils/helpers', () => ({
  getMoodColor: jest.fn(() => 'bg-green-500'),
  getMoodEmoji: jest.fn(() => '😊'),
  getMoodLabel: jest.fn(() => 'Test Label'),
}));

describe('MoodIndicator Component', () => {
  test('renders with mood prop', () => {
    const { container } = render(<MoodIndicator mood="positive" />);
    
    const indicator = container.querySelector('.rounded-full');
    expect(indicator).toBeInTheDocument();
    expect(indicator).toHaveClass('w-3', 'h-3', 'flex-shrink-0');
  });

  test('renders with different sizes', () => {
    const { container } = render(<MoodIndicator mood="positive" size="lg" />);
    
    const indicator = container.querySelector('.rounded-full');
    expect(indicator).toHaveClass('w-6', 'h-6');
  });

  test('returns null when no mood is provided', () => {
    const { container } = render(<MoodIndicator />);
    expect(container.firstChild).toBeNull();
  });

  test('shows label when showLabel is true', () => {
    const { container } = render(<MoodIndicator mood="positive" showLabel={true} />);
    
    const labelSpan = container.querySelector('span');
    expect(labelSpan).toBeInTheDocument();
    expect(labelSpan).toHaveClass('text-gray-600');
  });

  test('does not show label by default', () => {
    const { container } = render(<MoodIndicator mood="positive" />);
    
    const labelSpan = container.querySelector('span');
    expect(labelSpan).not.toBeInTheDocument();
  });

  test('applies custom className', () => {
    const { container } = render(<MoodIndicator mood="positive" className="custom-class" />);
    
    const outerDiv = container.firstChild;
    expect(outerDiv).toHaveClass('custom-class');
  });

  test('component structure is correct', () => {
    const { container } = render(<MoodIndicator mood="positive" showLabel={true} />);
    
    const outerDiv = container.firstChild;
    expect(outerDiv).toHaveClass('flex', 'items-center', 'space-x-2');
    
    const indicator = container.querySelector('.rounded-full');
    expect(indicator).toHaveClass('rounded-full', 'flex-shrink-0');
  });

  test('renders with default size when no size specified', () => {
    const { container } = render(<MoodIndicator mood="positive" />);
    
    const indicator = container.querySelector('.rounded-full');
    expect(indicator).toHaveClass('w-3', 'h-3'); // default 'sm' size
  });
});
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import InlineCitationLink from './InlineCitationLink';

const MarkdownWithCitations = ({ text, sources }) => {
  // Create citation mapping
  const citationMap = {};
  let citationCounter = 1;
  
  // Map journal entries
  if (sources?.journal_entries) {
    sources.journal_entries.forEach((source, index) => {
      const journalKey = `Journal Entry ${index + 1}`;
      citationMap[journalKey] = {
        ...source,
        sourceType: 'journal',
        citationNumber: citationCounter++
      };
    });
  }
  
  // Map conversations
  if (sources?.conversations) {
    sources.conversations.forEach((source, index) => {
      const chatKey = `Conversation ${index + 1}`;
      citationMap[chatKey] = {
        ...source,
        sourceType: 'conversation',
        citationNumber: citationCounter++
      };
    });
  }

  // Function to process text and replace citations with links
  const processText = (text) => {
    if (typeof text !== 'string') return text;
    
    // Find citation patterns like "Journal Entry 1", "Conversation 3", etc.
    const citationRegex = /(Journal Entry \d+|Conversation \d+)/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = citationRegex.exec(text)) !== null) {
      // Add text before citation
      if (match.index > lastIndex) {
        parts.push(text.slice(lastIndex, match.index));
      }
      
      // Add citation link
      const citationKey = match[1];
      const citation = citationMap[citationKey];
      
      if (citation) {
        parts.push(
          <InlineCitationLink 
            key={match.index} 
            citation={citation} 
            text={citationKey}
            number={citation.citationNumber}
          />
        );
      } else {
        // If no citation found, add the text with a number
        parts.push(
          <span key={match.index} className="font-medium">
            {citationKey} <sup className="text-blue-600 font-bold">[{citationCounter++}]</sup>
          </span>
        );
      }
      
      lastIndex = citationRegex.lastIndex;
    }
    
    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }
    
    return parts.length > 1 ? parts : text;
  };

  // Custom renderers for ReactMarkdown
  const components = {
    p: ({ children }) => (
      <p>{React.Children.map(children, child => 
        typeof child === 'string' ? processText(child) : child
      )}</p>
    ),
    li: ({ children }) => (
      <li>{React.Children.map(children, child => 
        typeof child === 'string' ? processText(child) : child
      )}</li>
    ),
    strong: ({ children }) => (
      <strong>{React.Children.map(children, child => 
        typeof child === 'string' ? processText(child) : child
      )}</strong>
    ),
    em: ({ children }) => (
      <em>{React.Children.map(children, child => 
        typeof child === 'string' ? processText(child) : child
      )}</em>
    )
  };

  return (
    <ReactMarkdown 
      remarkPlugins={[remarkGfm]} 
      components={components}
    >
      {text}
    </ReactMarkdown>
  );
};

export default MarkdownWithCitations;
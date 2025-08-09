import React, { useState, useEffect } from 'react';

// Progressive enhancement wrapper
const ProgressiveEnhancement = ({ 
  children, 
  fallback, 
  feature,
  timeout = 1000 
}) => {
  const [isSupported, setIsSupported] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkFeatureSupport = () => {
      let supported = true;

      switch (feature) {
        case 'intersection-observer':
          supported = 'IntersectionObserver' in window;
          break;
        case 'resize-observer':
          supported = 'ResizeObserver' in window;
          break;
        case 'web-animations':
          supported = 'animate' in document.createElement('div');
          break;
        case 'css-grid':
          supported = CSS.supports('display', 'grid');
          break;
        case 'css-custom-properties':
          supported = CSS.supports('color', 'var(--fake-var)');
          break;
        case 'local-storage':
          try {
            localStorage.setItem('test', 'test');
            localStorage.removeItem('test');
            supported = true;
          } catch {
            supported = false;
          }
          break;
        case 'service-worker':
          supported = 'serviceWorker' in navigator;
          break;
        default:
          supported = true;
      }

      setIsSupported(supported);
      setIsLoading(false);
    };

    // Add small delay to prevent flash
    const timer = setTimeout(checkFeatureSupport, 50);
    
    // Fallback timeout
    const fallbackTimer = setTimeout(() => {
      if (isLoading) {
        setIsSupported(false);
        setIsLoading(false);
      }
    }, timeout);

    return () => {
      clearTimeout(timer);
      clearTimeout(fallbackTimer);
    };
  }, [feature, timeout, isLoading]);

  if (isLoading) {
    return fallback || null;
  }

  return isSupported ? children : (fallback || null);
};

// Hook for feature detection
export const useFeatureSupport = (feature) => {
  const [isSupported, setIsSupported] = useState(false);

  useEffect(() => {
    const checkFeatureSupport = () => {
      switch (feature) {
        case 'touch':
          setIsSupported('ontouchstart' in window || navigator.maxTouchPoints > 0);
          break;
        case 'hover':
          setIsSupported(window.matchMedia('(hover: hover)').matches);
          break;
        case 'reduced-motion':
          setIsSupported(window.matchMedia('(prefers-reduced-motion: reduce)').matches);
          break;
        case 'high-contrast':
          setIsSupported(window.matchMedia('(prefers-contrast: high)').matches);
          break;
        case 'dark-mode':
          setIsSupported(window.matchMedia('(prefers-color-scheme: dark)').matches);
          break;
        default:
          setIsSupported(true);
      }
    };

    checkFeatureSupport();

    // Listen for changes
    const mediaQuery = window.matchMedia(`(prefers-${feature.replace('-', '-')})`);
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', checkFeatureSupport);
      return () => mediaQuery.removeEventListener('change', checkFeatureSupport);
    }
  }, [feature]);

  return isSupported;
};

export default ProgressiveEnhancement;
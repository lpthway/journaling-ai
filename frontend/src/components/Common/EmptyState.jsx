import React from 'react';

const EmptyState = ({ 
  icon: Icon, 
  title, 
  description, 
  action,
  illustration,
  size = 'md',
  className = '' 
}) => {
  const sizeClasses = {
    sm: {
      container: 'py-8',
      iconContainer: 'h-12 w-12',
      icon: 'h-6 w-6',
      title: 'text-base',
      description: 'text-sm'
    },
    md: {
      container: 'py-12',
      iconContainer: 'h-16 w-16',
      icon: 'h-8 w-8',
      title: 'text-lg',
      description: 'text-base'
    },
    lg: {
      container: 'py-16',
      iconContainer: 'h-20 w-20',
      icon: 'h-10 w-10',
      title: 'text-xl',
      description: 'text-lg'
    }
  };

  const sizes = sizeClasses[size];

  return (
    <div className={`text-center ${sizes.container} ${className} animate-fade-in`}>
      {illustration ? (
        <div className="mb-6">
          {illustration}
        </div>
      ) : (
        <div className={`mx-auto flex items-center justify-center ${sizes.iconContainer} rounded-full bg-gradient-to-br from-gray-50 to-gray-100 mb-4 shadow-inner`}>
          <Icon className={`${sizes.icon} text-gray-400`} aria-hidden="true" />
        </div>
      )}
      <h3 className={`${sizes.title} font-medium text-gray-900 mb-2`}>{title}</h3>
      <p className={`text-gray-500 mb-6 max-w-sm mx-auto ${sizes.description} leading-relaxed`}>
        {description}
      </p>
      {action && (
        <div className="animate-slide-up">
          {action}
        </div>
      )}
    </div>
  );
};

export default EmptyState;
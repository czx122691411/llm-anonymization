/**
 * ChartContainer - A reusable container for charts with consistent styling
 * Provides header, loading state, and responsive wrapper
 */

import React from 'react';
import { LucideIcon } from 'lucide-react';

interface ChartContainerProps {
  /** Chart title */
  title: string;
  /** Optional description */
  description?: string;
  /** Icon to display in header */
  icon?: LucideIcon;
  /** Chart content */
  children: React.ReactNode;
  /** Whether chart is loading */
  loading?: boolean;
  /** Loading message */
  loadingMessage?: string;
  /** Optional action button */
  action?: React.ReactNode;
  /** Custom className */
  className?: string;
  /** Maximum height for chart area */
  maxHeight?: string;
}

export const ChartContainer: React.FC<ChartContainerProps> = ({
  title,
  description,
  icon: Icon,
  children,
  loading = false,
  loadingMessage = '加载中...',
  action,
  className = '',
  maxHeight = '400px',
}) => {
  return (
    <div
      className={`
        bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800
        shadow-sm hover:shadow-md transition-all duration-300
        ${className}
      `}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-800">
        <div className="flex items-center gap-3">
          {Icon && <Icon className="w-5 h-5 text-blue-600 dark:text-blue-400" />}
          <div>
            <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">{title}</h3>
            {description && <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{description}</p>}
          </div>
        </div>
        {action && <div>{action}</div>}
      </div>

      {/* Chart Content */}
      <div className="p-6" style={{ maxHeight }}>
        {loading ? (
          <div className="flex items-center justify-center h-full min-h-[200px]">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
              <span className="text-sm text-gray-500 dark:text-gray-400">{loadingMessage}</span>
            </div>
          </div>
        ) : (
          <div className="h-full">{children}</div>
        )}
      </div>
    </div>
  );
};

export default ChartContainer;

/**
 * ChartCard - Universal container for chart components
 * Provides consistent styling, loading states, and action buttons
 */
import React, { useState } from 'react';
import { Maximize2, Download, RefreshCw, Info } from 'lucide-react';

interface ChartCardProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  onRefresh?: () => void;
  onExport?: () => void;
  loading?: boolean;
  extra?: React.ReactNode;
  infoText?: string;
}

export const ChartCard: React.FC<ChartCardProps> = ({
  title,
  description,
  children,
  onRefresh,
  onExport,
  loading = false,
  extra,
  infoText,
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showInfo, setShowInfo] = useState(false);

  return (
    <div className={`bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden ${
      isFullscreen ? 'fixed inset-4 z-50 overflow-y-auto' : ''
    }`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800">
        <div className="flex items-center justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 truncate">
                {title}
              </h3>
              {infoText && (
                <div className="relative">
                  <button
                    onClick={() => setShowInfo(!showInfo)}
                    className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
                    title="Show info"
                  >
                    <Info className="w-4 h-4 text-gray-400" />
                  </button>
                  {showInfo && (
                    <div className="absolute left-0 top-full mt-2 p-3 bg-gray-100 dark:bg-gray-800 rounded-lg shadow-lg text-sm text-gray-700 dark:text-gray-300 max-w-xs z-10">
                      {infoText}
                    </div>
                  )}
                </div>
              )}
            </div>
            {description && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5 truncate">
                {description}
              </p>
            )}
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            {extra}
            {onRefresh && (
              <button
                onClick={onRefresh}
                disabled={loading}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors disabled:opacity-50"
                title="Refresh"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              </button>
            )}
            {onExport && (
              <button
                onClick={onExport}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                title="Export"
              >
                <Download className="w-4 h-4" />
              </button>
            )}
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {loading ? (
          <div className="h-[300px] flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Loading...</p>
            </div>
          </div>
        ) : (
          children
        )}
      </div>

      {/* Fullscreen close hint */}
      {isFullscreen && (
        <div className="px-6 py-3 bg-blue-50 dark:bg-blue-900/20 border-t border-blue-200 dark:border-blue-800">
          <p className="text-sm text-blue-700 dark:text-blue-300 text-center">
            Press ESC or click the fullscreen button to exit
          </p>
        </div>
      )}
    </div>
  );
};

export default ChartCard;

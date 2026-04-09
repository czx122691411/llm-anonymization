/**
 * Training Visualization Component
 * Displays anonymization training process plots with sub-chart extraction and professional analysis
 */
import React, { useEffect, useState } from 'react';

interface PlotInfo {
  filename: string;
  title: string;
  url: string;
  size_bytes: number;
  size_mb: number;
  created: string;
}

interface PlotsResponse {
  success: boolean;
  message?: string;
  plots: PlotInfo[];
  total_count: number;
}

interface SubChart {
  id: string;
  title: string;
  description: string;
  analysis: string;
  image_data: string;
  region: [number, number, number, number];
}

interface SubChartsResponse {
  success: boolean;
  filename: string;
  has_subcharts: boolean;
  subcharts?: SubChart[];
  total_count?: number;
  message?: string;
}

interface PlotView {
  mode: 'grid' | 'single' | 'subcharts';
  selectedPlot: PlotInfo | null;
  subChartsData: SubChartsResponse | null;
}

interface TrainingVisualizationProps {
  onEscapeToHome?: () => void;
}

export const TrainingVisualization: React.FC<TrainingVisualizationProps> = ({ onEscapeToHome }) => {
  const [plotsData, setPlotsData] = useState<PlotsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<PlotView>({ mode: 'grid', selectedPlot: null, subChartsData: null });
  const [imageLoadErrors, setImageLoadErrors] = useState<Set<string>>(new Set());
  const [loadingSubCharts, setLoadingSubCharts] = useState(false);

  // ESC key handler - must be called at the top level, not conditionally
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        // If onEscapeToHome callback is provided, use it (return to home)
        // Otherwise, just return to grid view
        if (onEscapeToHome) {
          onEscapeToHome();
        } else {
          handleBackToGrid();
        }
      }
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [onEscapeToHome]);

  useEffect(() => {
    fetchPlots();
  }, []);

  const fetchPlots = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('/api/plots');
      const data = await response.json();
      setPlotsData(data);
    } catch (err) {
      setError('Failed to load plots: ' + (err as Error).message);
      console.error('Error fetching plots:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSubCharts = async (plot: PlotInfo) => {
    try {
      setLoadingSubCharts(true);
      const response = await fetch(`/api/plots/${plot.filename}/subcharts`);
      const data = await response.json() as SubChartsResponse;
      setView({ mode: 'subcharts', selectedPlot: plot, subChartsData: data });
    } catch (err) {
      console.error('Error fetching subcharts:', err);
      // Fall back to single view if subcharts fail
      setView({ mode: 'single', selectedPlot: plot, subChartsData: null });
    } finally {
      setLoadingSubCharts(false);
    }
  };

  const handleImageError = (key: string) => {
    setImageLoadErrors(prev => new Set([...prev, key]));
    console.error(`Failed to load image: ${key}`);
  };

  const handlePlotClick = (plot: PlotInfo) => {
    // Try to fetch subcharts first
    fetchSubCharts(plot);
  };

  const handleBackToGrid = () => {
    setView({ mode: 'grid', selectedPlot: null, subChartsData: null });
  };

  const viewOriginalImage = () => {
    if (view.selectedPlot) {
      setView({ mode: 'single', selectedPlot: view.selectedPlot, subChartsData: view.subChartsData });
    }
  };

  const handleBackToSubCharts = () => {
    if (view.selectedPlot && view.subChartsData) {
      setView({ mode: 'subcharts', selectedPlot: view.selectedPlot, subChartsData: view.subChartsData });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[500px]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mb-6"></div>
          <p className="text-xl text-gray-700 dark:text-gray-300 font-medium">Loading visualization plots...</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">Please wait while we fetch the training data</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-8">
        <div className="flex items-start gap-4">
          <div className="text-5xl">⚠️</div>
          <div className="flex-1">
            <h3 className="text-xl font-semibold text-red-800 dark:text-red-200 mb-2">Error Loading Plots</h3>
            <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
            <button
              onClick={fetchPlots}
              className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
            >
              🔄 Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!plotsData || plotsData.total_count === 0) {
    return (
      <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-8">
        <div className="flex items-start gap-4">
          <div className="text-5xl">📭</div>
          <div>
            <h3 className="text-xl font-semibold text-yellow-800 dark:text-yellow-200 mb-2">No Plots Found</h3>
            <p className="text-yellow-600 dark:text-yellow-400">
              {plotsData?.message || 'No visualization plots are currently available.'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Sub-charts view (NEW)
  if (view.mode === 'subcharts' && view.selectedPlot && view.subChartsData) {
    const { subChartsData, selectedPlot } = view;

    if (loadingSubCharts) {
      return (
        <div className="flex items-center justify-center min-h-[500px]">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mb-6"></div>
            <p className="text-xl text-gray-700 dark:text-gray-300 font-medium">Extracting sub-charts...</p>
          </div>
        </div>
      );
    }

    if (!subChartsData.has_subcharts || !subChartsData.subcharts) {
      // Fall back to single view if no subcharts available
      return (
        <div
          className="max-w-7xl mx-auto space-y-8"
          onClick={(e) => {
            // Click outside to return
            if (e.target === e.currentTarget) {
              handleBackToGrid();
            }
          }}
        >
          <div className="flex items-center gap-4">
            <button
              onClick={handleBackToGrid}
              className="px-5 py-2.5 bg-gray-200 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-700 transition-colors font-medium flex items-center gap-2"
            >
              <span>←</span>
              <span>Back to Gallery</span>
            </button>
            <div className="flex-1">
              <p className="text-gray-600 dark:text-gray-400">
                No sub-charts available for this plot. Viewing original image...
              </p>
              <p className="text-gray-500 dark:text-gray-500 text-sm mt-1">
                💡 Press ESC or click outside to close
              </p>
            </div>
          </div>
          {view.selectedPlot && (
            <div className="bg-gray-100 dark:bg-gray-950 rounded-xl p-8 cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-900 transition-colors" title="Click outside to close">
              <div
                className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl inline-block"
                onClick={(e) => e.stopPropagation()}
              >
                <img
                  src={selectedPlot.url}
                  alt={selectedPlot.title}
                  className="max-w-full h-auto rounded-lg"
                  style={{ maxHeight: '70vh' }}
                />
              </div>
            </div>
          )}
        </div>
      );
    }

    return (
      <div
        className="max-w-7xl mx-auto space-y-8"
        onClick={(e) => {
          // Click outside to return to gallery
          if (e.target === e.currentTarget) {
            handleBackToGrid();
          }
        }}
      >
        {/* Header with Breadcrumb */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 flex-1">
            {/* Breadcrumb Navigation */}
            <div className="flex items-center gap-2 text-sm">
              <button
                onClick={handleBackToGrid}
                className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors flex items-center gap-1"
              >
                <span>🏠</span>
                <span>Gallery</span>
              </button>
              <span className="text-gray-400">/</span>
              <span className="text-gray-700 dark:text-gray-300 font-medium flex items-center gap-2">
                <span>📊</span>
                <span>{selectedPlot.title}</span>
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            {/* ESC hint */}
            <div className="hidden md:flex items-center gap-2 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg text-sm text-gray-600 dark:text-gray-400">
              <span>⌨️</span>
              <span>ESC to close</span>
            </div>
            <button
              onClick={viewOriginalImage}
              className="px-5 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium flex items-center gap-2 shadow-lg hover:shadow-xl"
            >
              <span>🖼️</span>
              <span>View Original</span>
            </button>
          </div>
        </div>

        {/* Sub-charts count and hint */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="text-4xl">🔬</span>
              <div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                  Sub-Chart Analysis
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                  This chart has been separated into <span className="font-bold text-blue-600 dark:text-blue-400">{subChartsData.total_count}</span> focused visualizations
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">💡 Tips</p>
              <p className="text-xs text-gray-500 dark:text-gray-500">
                Click sub-chart → View original<br />
                Click outside → Back to gallery
              </p>
            </div>
          </div>
        </div>

        {/* Sub-charts Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {subChartsData.subcharts.map((subchart, idx) => {
            const imageKey = `${selectedPlot.filename}-${subchart.id}`;
            return (
              <div
                key={subchart.id}
                className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300"
              >
                {/* Sub-chart Header */}
                <div className="p-5 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-b border-blue-200 dark:border-blue-800">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">📊</span>
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                        {idx + 1}. {subchart.title}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {subchart.description}
                      </p>
                    </div>
                    {/* Click indicator */}
                    <div className="flex items-center gap-1 px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded text-xs font-medium">
                      <span>👆</span>
                      <span>Click</span>
                    </div>
                  </div>
                </div>

                {/* Sub-chart Image - Clickable to view original */}
                <div
                  className="p-6 bg-gray-50 dark:bg-gray-950 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-900 transition-colors group relative"
                  onClick={viewOriginalImage}
                  title="Click to view original complete chart"
                >
                  <div className="bg-white dark:bg-gray-900 rounded-lg overflow-hidden shadow-inner relative">
                    {imageLoadErrors.has(imageKey) ? (
                      <div className="aspect-[4/3] flex items-center justify-center">
                        <div className="text-center">
                          <div className="text-5xl mb-2">❌</div>
                          <p className="text-red-600 dark:text-red-400 text-sm">
                            Failed to load
                          </p>
                        </div>
                      </div>
                    ) : (
                      <>
                        <img
                          src={subchart.image_data}
                          alt={subchart.title}
                          className="w-full h-auto object-contain"
                          style={{ maxHeight: '350px' }}
                          onError={() => handleImageError(imageKey)}
                        />
                        {/* Enhanced hover overlay */}
                        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100">
                          <div className="bg-white dark:bg-gray-900 px-6 py-3 rounded-xl shadow-lg transform scale-95 group-hover:scale-100 transition-transform">
                            <div className="flex items-center gap-2">
                              <span className="text-2xl">🔍</span>
                              <span className="text-gray-900 dark:text-gray-100 font-semibold">
                                View Original Chart
                              </span>
                            </div>
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                  {/* Click hint below image */}
                  <div className="mt-3 text-center text-xs text-gray-500 dark:text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity">
                    Click to view original complete chart
                  </div>
                </div>

                {/* Sub-chart Analysis */}
                <div className="p-6 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800">
                  <h4 className="text-base font-semibold text-gray-800 dark:text-gray-200 mb-3 flex items-center gap-2">
                    <span>🔍</span>
                    <span>Analysis</span>
                  </h4>
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed text-base">
                    {subchart.analysis}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Bottom info banner */}
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border border-green-200 dark:border-green-800 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <span className="text-4xl">💡</span>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Navigation Guide
              </h3>
              <div className="grid md:grid-cols-3 gap-4 text-sm">
                <div className="flex items-start gap-2">
                  <span className="text-purple-600 font-bold">👆</span>
                  <div>
                    <p className="font-medium text-gray-800 dark:text-gray-200">Click Sub-chart</p>
                    <p className="text-gray-600 dark:text-gray-400 text-xs mt-1">View original complete chart</p>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-blue-600 font-bold">⌨️</span>
                  <div>
                    <p className="font-medium text-gray-800 dark:text-gray-200">Press ESC</p>
                    <p className="text-gray-600 dark:text-gray-400 text-xs mt-1">Return to gallery</p>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-green-600 font-bold">🖱️</span>
                  <div>
                    <p className="font-medium text-gray-800 dark:text-gray-200">Click Outside</p>
                    <p className="text-gray-600 dark:text-gray-400 text-xs mt-1">Back to gallery</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Single plot view (fallback)
  if (view.mode === 'single' && view.selectedPlot) {
    return (
      <div
        className="max-w-7xl mx-auto space-y-8"
        onClick={(e) => {
          // If clicking on the image container background (not the image itself), go back
          if (e.target === e.currentTarget) {
            if (view.subChartsData && view.subChartsData.has_subcharts) {
              handleBackToSubCharts();
            } else {
              handleBackToGrid();
            }
          }
        }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* Breadcrumb */}
            <div className="flex items-center gap-2 text-sm">
              <button
                onClick={handleBackToGrid}
                className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors flex items-center gap-1"
              >
                <span>🏠</span>
                <span>Gallery</span>
              </button>
              {view.subChartsData && view.subChartsData.has_subcharts && (
                <>
                  <span className="text-gray-400">/</span>
                  <button
                    onClick={handleBackToSubCharts}
                    className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors flex items-center gap-1"
                  >
                    <span>📊</span>
                    <span>Sub-charts</span>
                  </button>
                </>
              )}
              <span className="text-gray-400">/</span>
              <span className="text-gray-700 dark:text-gray-300 font-medium">Original</span>
            </div>
          </div>

          {/* ESC hint */}
          <div className="hidden md:flex items-center gap-2 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg text-sm text-gray-600 dark:text-gray-400">
            <span>⌨️</span>
            <span>ESC to go back</span>
          </div>
        </div>

        <div className="bg-gray-100 dark:bg-gray-950 rounded-xl p-8 cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-900 transition-colors relative group" title="Click outside or press ESC to go back">
          {/* Click hint overlay */}
          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity">
            <div className="bg-white dark:bg-gray-900 px-6 py-3 rounded-xl shadow-lg">
              <p className="text-gray-700 dark:text-gray-300 text-sm font-medium">
                🖱️ Click outside or press ESC to return
              </p>
            </div>
          </div>

          <div
            className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl inline-block relative"
            onClick={(e) => e.stopPropagation()}
          >
            <img
              src={view.selectedPlot.url}
              alt={view.selectedPlot.title}
              className="max-w-full h-auto rounded-lg"
              style={{ maxHeight: '70vh' }}
            />
          </div>
        </div>

        {/* Info banner */}
        {view.subChartsData && view.subChartsData.has_subcharts && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4 flex items-center justify-center gap-3">
            <span className="text-2xl">💡</span>
            <p className="text-gray-700 dark:text-gray-300 text-sm">
              You're viewing the original complete chart. Click outside, press <kbd className="px-2 py-1 bg-gray-200 dark:bg-gray-800 rounded text-xs font-mono">ESC</kbd>, or use the breadcrumb to return to sub-charts.
            </p>
          </div>
        )}
      </div>
    );
  }

  // Grid view
  return (
    <div className="max-w-7xl mx-auto space-y-10">
      {/* Header */}
      <div className="text-center space-y-3">
        <h2 className="text-4xl font-bold text-gray-900 dark:text-gray-100">
          Training Visualization Gallery
        </h2>
        <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
          Interactive exploration of anonymization training progress with detailed sub-chart analysis
        </p>
        <div className="flex items-center justify-center gap-4 pt-2">
          <span className="px-4 py-2 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full text-sm font-medium">
            {plotsData.total_count} Charts Available
          </span>
          <button
            onClick={fetchPlots}
            className="px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center gap-2"
          >
            <span>🔄</span>
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {plotsData.plots.map((plot, idx) => (
          <div
            key={plot.filename}
            className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 cursor-pointer group"
            onClick={() => handlePlotClick(plot)}
          >
            {/* Card Header */}
            <div className="p-5 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-4xl">📊</span>
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      {plot.title}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                      Click to explore sub-charts
                    </p>
                  </div>
                </div>
                <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full text-sm font-medium">
                  #{idx + 1}
                </span>
              </div>
            </div>

            {/* Thumbnail */}
            <div className="p-4 bg-gray-50 dark:bg-gray-950">
              <div className="bg-white dark:bg-gray-900 rounded-lg overflow-hidden shadow-inner aspect-video flex items-center justify-center">
                {imageLoadErrors.has(plot.filename) ? (
                  <div className="text-center">
                    <div className="text-4xl mb-2">❌</div>
                    <p className="text-red-600 dark:text-red-400 text-sm">Load failed</p>
                  </div>
                ) : (
                  <img
                    src={plot.url}
                    alt={plot.title}
                    className="max-w-full max-h-full object-contain"
                    onError={() => handleImageError(plot.filename)}
                  />
                )}
              </div>
            </div>

            {/* Card Footer */}
            <div className="p-4 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800">
              <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                <span>📁 {plot.filename}</span>
                <div className="flex items-center gap-3">
                  <span>💾 {plot.size_mb} MB</span>
                  <span>📅 {new Date(plot.created).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Info Section */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-xl border border-indigo-200 dark:border-indigo-800 p-8">
        <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-3">
          <span>🔬</span>
          <span>Sub-Chart Analysis Feature</span>
        </h3>
        <p className="text-gray-700 dark:text-gray-300 text-base leading-relaxed">
          Click on any chart to extract and view its individual sub-components. Each complex visualization is automatically analyzed
          and separated into focused sub-charts, making it easier to understand specific aspects of the anonymization training process.
        </p>
      </div>
    </div>
  );
};

export default TrainingVisualization;

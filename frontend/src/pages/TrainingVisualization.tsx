/**
 * Training Visualization Page
 * Displays all anonymization training process visualizations
 */
import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { TrainingVisualization } from '../components/TrainingVisualization';

const TrainingVisualizationPage: React.FC = () => {
  const navigate = useNavigate();

  const handleEscapeToHome = () => {
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Page Header */}
      <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              {/* Back to Home Link */}
              <Link
                to="/"
                className="group flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
              >
                <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg group-hover:bg-gray-200 dark:group-hover:bg-gray-700 transition-colors">
                  <span className="text-xl">🏠</span>
                </div>
                <div className="hidden sm:block">
                  <p className="text-sm font-medium">Back to Home</p>
                  <p className="text-xs text-gray-500 dark:text-gray-500">LLM Anonymization Visualizer</p>
                </div>
              </Link>

              {/* Title */}
              <div className="flex items-center gap-3">
                <span className="text-4xl">📊</span>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    Training Visualization
                  </h1>
                  <p className="text-gray-600 dark:text-gray-400 text-sm mt-0.5">
                    View anonymization training process plots and analysis charts
                  </p>
                </div>
              </div>
            </div>

            {/* Right side - Quick hint */}
            <div className="hidden md:flex items-center gap-2 px-4 py-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg text-sm text-blue-700 dark:text-blue-300">
              <span>⌨️</span>
              <span>Press ESC to return home</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <TrainingVisualization onEscapeToHome={handleEscapeToHome} />
      </div>
    </div>
  );
};

export default TrainingVisualizationPage;

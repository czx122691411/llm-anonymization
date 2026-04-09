import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import './index.css';

// Training Visualization Page (lazy loaded)
const TrainingVisualization = React.lazy(() =>
  import('./pages/TrainingVisualization').then(m => ({ default: m.TrainingVisualizationPage || m.default }))
);

// Dashboard component
const Dashboard: React.FC = () => {
  const [profiles, setProfiles] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    fetch('/api/profiles?limit=20')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        setProfiles(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load profiles:', err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100">
                LLM Anonymization Visualizer
              </h1>
              <p className="text-lg text-gray-600 dark:text-gray-400 mt-3">
                探索和分析文本匿名化结果
              </p>
            </div>
            <Link
              to="/training-visualization"
              className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2 text-lg font-medium shadow-lg hover:shadow-xl"
            >
              <span>📊</span>
              <span>Training Plots</span>
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 overflow-hidden">
          <div className="px-8 py-6 border-b border-gray-200 dark:border-gray-800">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              {error ? `错误: ${error}` : `用户列表 (${profiles.length})`}
            </h2>
          </div>

          {loading ? (
            <div className="p-10 text-center text-gray-500 dark:text-gray-400 text-lg">
              加载中...
            </div>
          ) : error ? (
            <div className="p-10 text-center text-red-500">
              <p className="mb-3 text-lg">无法连接到后端 API</p>
              <p className="text-base text-gray-600 dark:text-gray-400">
                请确保后端运行在 http://localhost:8000
              </p>
            </div>
          ) : profiles.length === 0 ? (
            <div className="p-10 text-center text-gray-500 dark:text-gray-400 text-lg">
              <p>未找到用户数据</p>
              <p className="text-base mt-3">
                后端 API 正在运行，但暂时没有数据
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-800">
              {profiles.map((profile) => (
                <Link
                  key={profile.profile_id}
                  to={`/profile/${profile.profile_id}`}
                  className="block px-8 py-6 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                        {profile.username}
                      </h3>
                      <p className="text-base text-gray-500 dark:text-gray-400 mt-1">
                        {profile.num_comments} 条评论
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      {profile.has_anonymization && (
                        <span className="px-4 py-2 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-base rounded-lg font-medium">
                          已匿名化
                        </span>
                      )}
                      {profile.has_quality_scores && (
                        <span className="px-4 py-2 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-base rounded-lg font-medium">
                          质量评分
                        </span>
                      )}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

// Lazy load detail page
const AnonymizationDetail = React.lazy(() =>
  import('./pages/AnonymizationDetail').then(m => ({ default: m.AnonymizationDetail || m.default }))
);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route
          path="/profile/:profileId"
          element={
            <React.Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
              <AnonymizationDetail />
            </React.Suspense>
          }
        />
        <Route
          path="/training-visualization"
          element={
            <React.Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
              <TrainingVisualization />
            </React.Suspense>
          }
        />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);

/**
 * Main Application Entry Point
 *
 * 整合侧边导航和页面路由
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import './index.css';

// 导入侧边导航组件
import { SideNavigation } from './components/SideNavigation';

// Create a QueryClient for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

// Lazy load pages
const TrainingVisualization = React.lazy(() =>
  import('./pages/TrainingVisualization')
);

const TRACERPSDashboard = React.lazy(() =>
  import('./pages/TRACERPSDashboard')
);

const DeepSeek5RoundsVisualization = React.lazy(() =>
  import('./pages/DeepSeek5RoundsVisualization')
);

const CustomTestPage = React.lazy(() =>
  import('./pages/CustomTestPage')
);

const ChineseDemoPage = React.lazy(() =>
  import('./pages/ChineseDemoPage')
);

const AnonymizationDetail = React.lazy(() =>
  import('./pages/AnonymizationDetail')
);

const SynthpaiDashboard = React.lazy(() =>
  import('./pages/SynthpaiDashboard')
);

const SynthpaiUserDetail = React.lazy(() =>
  import('./pages/SynthpaiUserDetail')
);

// Dashboard content
const DashboardContent: React.FC = () => {
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
    <div className="p-6 lg:p-10">
      {/* 页面标题 */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {error ? `错误: ${error}` : `用户列表 (${profiles.length})`}
        </h2>
      </div>

      {/* 加载状态 */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-violet-600"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">加载中...</p>
          </div>
        </div>
      ) : error ? (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
          <p className="text-red-600 dark:text-red-400 mb-2">无法连接到后端 API</p>
          <p className="text-sm text-red-500 dark:text-red-500">请确保后端运行在 http://localhost:8000</p>
        </div>
      ) : profiles.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-gray-500 dark:text-gray-400">未找到用户数据</p>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    用户名
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    评论数
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    状态
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
                {profiles.map((profile) => (
                  <tr key={profile.profile_id} className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                    <td className="px-6 py-4">
                      <Link
                        to={`/profile/${profile.profile_id}`}
                        className="text-violet-600 dark:text-violet-400 hover:text-violet-800 dark:hover:text-violet-300 font-medium"
                      >
                        {profile.username}
                      </Link>
                    </td>
                    <td className="px-6 py-4 text-gray-700 dark:text-gray-300">
                      {profile.num_comments}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        {profile.has_anonymization && (
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                            已匿名化
                          </span>
                        )}
                        {profile.has_quality_scores && (
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                            有评分
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

// Main App component
const App: React.FC = () => {
  return (
    <React.Suspense fallback={<div className="flex items-center justify-center min-h-screen">Loading...</div>}>
      <SideNavigation>
        <Routes>
          <Route path="/" element={<DashboardContent />} />

          <Route
            path="/profile/:profileId"
            element={<AnonymizationDetail />}
          />

          <Route
            path="/training-visualization"
            element={<TrainingVisualization />}
          />

          <Route
            path="/trace-rps-dashboard"
            element={<TRACERPSDashboard />}
          />

          <Route
            path="/deepseek-5rounds"
            element={<DeepSeek5RoundsVisualization />}
          />

          <Route
            path="/custom-test"
            element={<CustomTestPage />}
          />

          <Route
            path="/chinese-demo"
            element={<ChineseDemoPage />}
          />

          <Route
            path="/synthpai"
            element={<SynthpaiDashboard />}
          />

          <Route
            path="/synthpai/:username"
            element={<SynthpaiUserDetail />}
          />
        </Routes>
      </SideNavigation>
    </React.Suspense>
  );
};

// Mount the app
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);

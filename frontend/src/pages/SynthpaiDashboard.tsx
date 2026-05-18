/**
 * SynthpaiDashboard — SynthPAI 用户列表页
 *
 * 展示 50 个用户的对抗匿名化摘要，点击进入评论级攻防详情
 */
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, User, TrendingDown, TrendingUp, Minus } from 'lucide-react';

interface PrivacyTrend {
  round_0_avg_certainty: number;
  round_3_avg_certainty: number;
  blocked_attributes: string[];
  leaked_attributes: string[];
}

interface UserSummary {
  username: string;
  total_comments: number;
  comment_groups: number;
  ground_truth: Record<string, string>;
  privacy_trend: PrivacyTrend;
}

interface UserListResponse {
  users: UserSummary[];
  total: number;
}

const SynthpaiDashboard: React.FC = () => {
  const [users, setUsers] = useState<UserSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetch('/api/synthpai/users')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data: UserListResponse) => {
        setUsers(data.users);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load synthpai users:', err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const getTrendIcon = (trend: PrivacyTrend) => {
    const diff = trend.round_0_avg_certainty - trend.round_3_avg_certainty;
    if (diff > 0.5)
      return <TrendingDown className="w-4 h-4 text-green-500" />;
    if (diff < -0.2)
      return <TrendingUp className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  const blockedCount = users.filter(
    (u) => u.privacy_trend.blocked_attributes.length > 0
  ).length;
  const avgTrend =
    users.length > 0
      ? users.reduce((sum, u) => {
          const diff =
            u.privacy_trend.round_0_avg_certainty -
            u.privacy_trend.round_3_avg_certainty;
          return sum + diff;
        }, 0) / users.length
      : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-violet-600" />
          <p className="mt-4 text-gray-600">加载 SynthPAI 数据中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p className="text-red-600 mb-2">无法连接到后端 API</p>
          <p className="text-sm text-red-500">请确保后端运行在 http://localhost:8000</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-10">
      {/* 页面标题 */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Shield className="w-7 h-7 text-violet-600" />
          <h2 className="text-2xl font-bold text-gray-900">SynthPAI 对抗分析</h2>
        </div>
        <p className="text-gray-500">50 条用户数据的攻击-防御迭代过程可视化</p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-violet-100">
              <User className="w-5 h-5 text-violet-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">总用户数</p>
              <p className="text-2xl font-bold text-gray-900">{users.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-100">
              <TrendingDown className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">属性被阻止的用户</p>
              <p className="text-2xl font-bold text-gray-900">{blockedCount}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-100">
              <Shield className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">平均确定性变化</p>
              <p className="text-2xl font-bold text-gray-900">
                {avgTrend > 0 ? '↓' : avgTrend < 0 ? '↑' : '→'}{' '}
                {Math.abs(avgTrend).toFixed(2)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 用户表格 */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">用户名</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">评论数</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ground Truth</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">趋势</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">被阻止属性</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">泄露属性</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {users.map((user) => (
                <tr
                  key={user.username}
                  className="hover:bg-gray-50 transition-colors cursor-pointer"
                  onClick={() => navigate(`/synthpai/${encodeURIComponent(user.username)}`)}
                >
                  <td className="px-6 py-4">
                    <span className="text-violet-600 hover:text-violet-800 font-medium">
                      {user.username}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-700">
                    {user.total_comments}
                    <span className="text-xs text-gray-400 ml-1">
                      ({user.comment_groups}组)
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(user.ground_truth).slice(0, 3).map(([k, v]) => (
                        <span
                          key={k}
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-600"
                        >
                          {k}: {v}
                        </span>
                      ))}
                      {Object.keys(user.ground_truth).length > 3 && (
                        <span className="text-xs text-gray-400">
                          +{Object.keys(user.ground_truth).length - 3}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {getTrendIcon(user.privacy_trend)}
                      <span className="text-sm text-gray-600">
                        {user.privacy_trend.round_0_avg_certainty.toFixed(1)} →{' '}
                        {Math.abs(user.privacy_trend.round_3_avg_certainty).toFixed(1)}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {user.privacy_trend.blocked_attributes.map((attr) => (
                        <span
                          key={attr}
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-green-100 text-green-700"
                        >
                          {attr}
                        </span>
                      ))}
                      {user.privacy_trend.blocked_attributes.length === 0 && (
                        <span className="text-xs text-gray-400">-</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {user.privacy_trend.leaked_attributes.map((attr) => (
                        <span
                          key={attr}
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-red-100 text-red-700"
                        >
                          {attr}
                        </span>
                      ))}
                      {user.privacy_trend.leaked_attributes.length === 0 && (
                        <span className="text-xs text-gray-400">-</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default SynthpaiDashboard;

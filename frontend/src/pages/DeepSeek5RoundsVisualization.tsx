/**
 * DeepSeek5RoundsVisualization - Main page for DeepSeek 5-round adversarial training visualization
 * Displays training progress, PII type analysis, and detailed data
 */
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
  Shield,
  Zap,
  FileText,
  TrendingUp,
  Download,
  RefreshCw,
  Filter,
  ChevronRight,
  Info,
  ArrowLeft,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import ChartCard from '../components/charts/ChartCard';
import EChartsMultiLine from '../components/charts/EChartsMultiLine';
import EChartsRadar from '../components/charts/EChartsRadar';
import DataTable from '../components/DataTable';
import PIIDistributionCard from '../components/PIIDistributionCard';
import {
  DeepSeekSummary,
  DeepSeekComparison,
  PIIMetrics,
  LineChartData,
  RadarChartData,
  QuickStats,
} from '../types/deepseek-training';

// API query functions
const fetchDeepSeekSummary = async (): Promise<DeepSeekSummary> => {
  const response = await fetch('/api/deepseek/summary');
  if (!response.ok) {
    throw new Error('Failed to fetch summary');
  }
  return response.json();
};

const fetchDeepSeekComparison = async (): Promise<DeepSeekComparison> => {
  const response = await fetch('/api/deepseek/comparison');
  if (!response.ok) {
    throw new Error('Failed to fetch comparison');
  }
  return response.json();
};

const fetchPIIMetrics = async (roundNumber?: number): Promise<PIIMetrics> => {
  const url = roundNumber !== undefined
    ? `/api/deepseek/metrics/by-pii-type?round_number=${roundNumber}`
    : '/api/deepseek/metrics/by-pii-type';
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch PII metrics');
  }
  return response.json();
};

export const DeepSeek5RoundsVisualization: React.FC = () => {
  const [selectedRound, setSelectedRound] = useState<number | null>(null);
  const [selectedPIIType, setSelectedPIIType] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch summary data
  const {
    data: summary,
    isLoading: summaryLoading,
    error: summaryError,
    refetch: refetchSummary,
  } = useQuery({
    queryKey: ['deepseek-summary'],
    queryFn: fetchDeepSeekSummary,
    refetchInterval: autoRefresh ? 30000 : false, // 30s auto-refresh
  });

  // Fetch comparison data
  const {
    data: comparison,
    isLoading: comparisonLoading,
  } = useQuery({
    queryKey: ['deepseek-comparison'],
    queryFn: fetchDeepSeekComparison,
  });

  // Fetch PII metrics
  const {
    data: piiMetrics,
    isLoading: piiLoading,
  } = useQuery({
    queryKey: ['deepseek-pii-metrics', selectedRound],
    queryFn: () => fetchPIIMetrics(selectedRound ?? undefined),
  });

  // Calculate quick stats
  const quickStats: QuickStats | null = summary ? {
    totalRounds: summary.total_rounds,
    totalPredictions: summary.rounds.reduce((sum, r) => sum + r.total_predictions, 0),
    finalAccuracy: summary.rounds[summary.rounds.length - 1]?.accuracy ?? 0,
    avgUtility: summary.rounds.reduce((sum, r) => sum + r.bleu, 0) / summary.rounds.length,
  } : null;

  // Transform data for charts
  const lineChartData: LineChartData | null = summary ? {
    categories: summary.rounds.map((r) => `Round ${r.round}`),
    series: [
      {
        name: '攻击准确率 (隐私风险)',
        data: summary.rounds.map((r) => (r.accuracy * 100).toFixed(2)),
        color: '#EF4444',
        smooth: true,
      },
      {
        name: 'BLEU分数 (文本效用)',
        data: summary.rounds.map((r) => (r.bleu * 100).toFixed(2)),
        color: '#3B82F6',
        smooth: true,
      },
      {
        name: 'ROUGE分数 (文本质量)',
        data: summary.rounds.map((r) => (r.rouge * 100).toFixed(2)),
        color: '#10B981',
        smooth: true,
      },
    ],
  } : null;

  const radarData: RadarChartData | null = comparison ? {
    indicators: [
      { name: '隐私保护', max: 100 },
      { name: '文本效用', max: 100 },
      { name: '文本质量', max: 100 },
    ],
    series: comparison.rounds.map((r) => ({
      name: `Round ${r.round}`,
      value: [r.privacy_protection, r.text_utility, r.text_quality],
    })),
  } : null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 dark:from-gray-900 dark:to-blue-900/10">
      {/* Header */}
      <header className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border-b border-gray-200 dark:border-gray-800 sticky top-0 z-50">
        <div className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <Link
                to="/"
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </Link>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  DeepSeek 5轮对抗训练可视化
                </h1>
                <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                  匿名化器: deepseek-chat | 攻击者: deepseek-reasoner
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 flex-shrink-0">
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`px-3 sm:px-4 py-2 rounded-lg transition-colors flex items-center gap-2 text-sm ${
                  autoRefresh
                    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                    : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
                }`}
                title={autoRefresh ? '关闭自动刷新' : '开启自动刷新'}
              >
                <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
                <span className="hidden sm:inline">自动刷新</span>
              </button>
              <button
                onClick={() => refetchSummary()}
                className="px-3 sm:px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2 text-sm"
                title="手动刷新"
              >
                <RefreshCw className="w-4 h-4" />
                <span className="hidden sm:inline">刷新</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-6">
        {/* Error state */}
        {summaryError && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6">
            <div className="flex items-start gap-4">
              <Info className="w-6 h-6 text-red-600 dark:text-red-400 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-red-800 dark:text-red-200 mb-2">加载数据失败</h3>
                <p className="text-sm text-red-600 dark:text-red-400 mb-4">
                  {(summaryError as Error).message}
                </p>
                <button
                  onClick={() => refetchSummary()}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
                >
                  重试
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Quick Stats */}
        {quickStats && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4"
          >
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 sm:p-6">
              <div className="flex items-center gap-3 sm:gap-4">
                <div className="p-2 sm:p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                  <TrendingUp className="w-5 h-5 sm:w-6 sm:h-6 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">训练轮数</p>
                  <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">{quickStats.totalRounds}</p>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 sm:p-6">
              <div className="flex items-center gap-3 sm:gap-4">
                <div className="p-2 sm:p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                  <FileText className="w-5 h-5 sm:w-6 sm:h-6 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">总预测数</p>
                  <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {quickStats.totalPredictions.toLocaleString()}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 sm:p-6">
              <div className="flex items-center gap-3 sm:gap-4">
                <div className="p-2 sm:p-3 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg">
                  <Shield className="w-5 h-5 sm:w-6 sm:h-6 text-emerald-600 dark:text-emerald-400" />
                </div>
                <div>
                  <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">最终攻击准确率</p>
                  <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {(quickStats.finalAccuracy * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 sm:p-6">
              <div className="flex items-center gap-3 sm:gap-4">
                <div className="p-2 sm:p-3 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
                  <Zap className="w-5 h-5 sm:w-6 sm:h-6 text-amber-600 dark:text-amber-400" />
                </div>
                <div>
                  <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">平均文本效用</p>
                  <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {(quickStats.avgUtility * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Main Charts */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Training Progress Line Chart */}
          <div className="xl:col-span-2">
            <ChartCard
              title="训练进展趋势"
              description="各轮次攻击准确率、BLEU和ROUGE分数变化"
              loading={summaryLoading}
              onRefresh={() => refetchSummary()}
              infoText="攻击准确率越低表示隐私保护越好。BLEU和ROUGE分数越高表示文本质量越好。"
            >
              {lineChartData && <EChartsMultiLine data={lineChartData} height="350px" />}
            </ChartCard>
          </div>

          {/* Radar Chart */}
          <div>
            <ChartCard
              title="各轮次指标对比"
              description="隐私保护 vs 文本效用 vs 文本质量"
              loading={comparisonLoading}
              infoText="雷达图展示了各轮次在三个维度的表现，面积越大表示综合效果越好。"
            >
              {radarData && <EChartsRadar data={radarData} height="350px" />}
            </ChartCard>
          </div>
        </div>

        {/* PII Analysis */}
        <div>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100">
              PII类型分析
            </h2>
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <select
                value={selectedRound ?? 'all'}
                onChange={(e) => setSelectedRound(e.target.value === 'all' ? null : parseInt(e.target.value))}
                className="px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm"
              >
                <option value="all">所有轮次</option>
                {[0, 1, 2, 3, 4].map((n) => (
                  <option key={n} value={n}>
                    Round {n}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {piiMetrics && !piiLoading && Object.keys(piiMetrics).length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3 sm:gap-4">
              {Object.entries(piiMetrics).map(([piiType, metrics]) => (
                <PIIDistributionCard
                  key={piiType}
                  piiType={piiType}
                  metrics={metrics}
                  onClick={() => setSelectedPIIType(piiType === selectedPIIType ? null : piiType)}
                  isSelected={selectedPIIType === piiType}
                />
              ))}
            </div>
          ) : piiLoading ? (
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-12 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-sm text-gray-500 dark:text-gray-400">加载PII数据中...</p>
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-12 text-center">
              <Info className="w-12 h-12 text-gray-300 dark:text-gray-700 mx-auto mb-4" />
              <p className="text-sm text-gray-500 dark:text-gray-400">暂无PII数据</p>
            </div>
          )}
        </div>

        {/* Detailed Data Table */}
        <div>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100">
              详细数据
            </h2>
            {selectedPIIType && (
              <button
                onClick={() => setSelectedPIIType(null)}
                className="text-sm text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
              >
                清除筛选 <ChevronRight className="w-4 h-4" />
              </button>
            )}
          </div>

          <DataTable
            selectedRound={selectedRound}
            selectedPIIType={selectedPIIType}
            onRoundChange={setSelectedRound}
          />
        </div>

        {/* Info Banner */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <Info className="w-6 h-6 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
                关于5轮对抗训练
              </h3>
              <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                本页面展示DeepSeek族模型的5轮对抗训练结果。Round 0使用GPT-4-1106-Preview作为基线，
                Rounds 1-4使用deepseek-chat作为匿名化器、deepseek-reasoner作为攻击者进行迭代对抗训练。
                训练目标是降低攻击者的推理准确率（提高隐私保护），同时保持文本的可读性和实用性。
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default DeepSeek5RoundsVisualization;

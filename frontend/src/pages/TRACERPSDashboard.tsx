/**
 * TRACE-RPS Performance Dashboard - Simplified & Practical
 * Focus on actual useful features, remove all non-functional components
 */
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Shield,
  Zap,
  FileText,
  TrendingUp,
  ArrowLeft,
  Filter,
  Info,
  Download,
  CheckCircle,
  XCircle,
  DollarSign,
  Clock,
} from 'lucide-react';
import { motion } from 'framer-motion';
import {
  Radar,
  RadarChart,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PolarAngleAxis,
  PolarRadiusAxis,
  PolarGrid,
} from 'recharts';
import { performanceData } from '../data/trace-rps-mock-data';
import { AnonymizationMethod } from '../types/trace-rps';

// Recharts wrapper for consistent styling
const RechartsWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ResponsiveContainer width="100%" height="100%">
    {children}
  </ResponsiveContainer>
);

// Simplified chart data structures
interface MethodMetrics {
  name: string;
  key: string;
  privacy: number;
  utility: number;
  quality: number;
  blocking: number;
  time: number;
  cost: number;
}

// Transform data for charts
const getMethodMetrics = (): MethodMetrics[] => {
  const methodMap: Record<string, string> = {
    homogeneous: '同构对抗训练',
    heterogeneous: '异构对抗训练',
    trace_v1: 'TRACE v1.0',
    trace_v2: 'TRACE v2.0',
  };

  return Object.entries(performanceData.metrics).map(([key, metrics]) => ({
    name: methodMap[key],
    key: key,
    privacy: metrics.privacyProtection,
    utility: metrics.utilityPreservation,
    quality: metrics.textQuality,
    blocking: metrics.inferenceBlocking,
    time: metrics.processingTime,
    cost: performanceData.costs[key as AnonymizationMethod].totalCost,
  }));
};

// Transform data for radar chart: dimensions on axes, methods as series
const getRadarChartData = (methods: MethodMetrics[]) => {
  return [
    {
      dimension: '隐私保护',
      ...Object.fromEntries(methods.map(m => [m.name, m.privacy]))
    },
    {
      dimension: '效用保持',
      ...Object.fromEntries(methods.map(m => [m.name, m.utility]))
    },
    {
      dimension: '文本质量',
      ...Object.fromEntries(methods.map(m => [m.name, m.quality]))
    },
    {
      dimension: '推理阻止',
      ...Object.fromEntries(methods.map(m => [m.name, m.blocking]))
    },
  ];
};

const TRACERPSDashboard: React.FC = () => {
  const [selectedMethods, setSelectedMethods] = useState<Set<string>>(
    new Set(['trace_v2', 'heterogeneous', 'homogeneous', 'trace_v1'])
  );
  const [exportFormat, setExportFormat] = useState<'json' | 'csv' | null>(null);
  const [exportSuccess, setExportSuccess] = useState(false);

  const metrics = getMethodMetrics();
  const filteredMetrics = metrics.filter((m) => selectedMethods.has(m.key));
  const radarData = getRadarChartData(filteredMetrics);

  const toggleMethod = (key: string) => {
    setSelectedMethods((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(key)) {
        if (newSet.size > 1) newSet.delete(key);
      } else {
        newSet.add(key);
      }
      return newSet;
    });
    setExportSuccess(false);
  };

  const selectAll = () => setSelectedMethods(new Set(['trace_v2', 'heterogeneous', 'homogeneous', 'trace_v1']));
  const selectRecommended = () => setSelectedMethods(new Set(['trace_v2']));

  const handleExport = (format: 'json' | 'csv') => {
    // Simulate export (in real implementation, this would call backend API)
    const dataToExport = filteredMetrics.map(m => ({
      method: m.name,
      privacy: m.privacy,
      utility: m.utility,
      quality: m.quality,
      blocking: m.blocking,
    }));

    if (format === 'json') {
      const blob = new Blob([JSON.stringify(dataToExport, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'trace-rps-performance.json';
      a.click();
      URL.revokeObjectURL(url);
    } else {
      // CSV export
      const headers = Object.keys(dataToExport[0]).join(',');
      const rows = dataToExport.map(obj => Object.values(obj).join(','));
      const csv = [headers, ...rows].join('\n');
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'trace-rps-performance.csv';
      a.click();
      URL.revokeObjectURL(url);
    }

    setExportFormat(format);
    setExportSuccess(true);
    setTimeout(() => setExportSuccess(false), 3000);
  };

  const getMethodBadge = (key: string) => {
    const badges = {
      trace_v2: { label: '推荐', color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' },
      heterogeneous: { label: '平衡', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
      homogeneous: { label: '经济', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' },
      trace_v1: { label: '快速', color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' },
    };
    return badges[key];
  };

  const getBestMethod = (metric: keyof MethodMetrics) => {
    return metrics.reduce((best, current) =>
      current[metric] > best[metric] ? current : best
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-violet-50 dark:from-slate-900 via-blue-900/10 dark:to-violet-900/10">
      {/* Header */}
      <header className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-b border-slate-200 dark:border-slate-800 sticky top-0 z-50">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to="/"
                className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-slate-600 dark:text-slate-400" />
              </Link>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-blue-600 via-violet-600 to-emerald-600 bg-clip-text text-transparent">
                  TRACE-RPS 性能对比
                </h1>
                <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
                  匿名化方法综合性能评估
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => handleExport('json')}
                className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm flex items-center gap-2 shadow-sm hover:shadow-md"
              >
                <Download className="w-4 h-4" />
                <span className="hidden sm:inline">导出JSON</span>
              </button>
              <button
                onClick={() => handleExport('csv')}
                className="px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-colors text-sm flex items-center gap-2 shadow-sm hover:shadow-md"
              >
                <Download className="w-4 h-4" />
                <span className="hidden sm:inline">导出CSV</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Export Success Message */}
        {exportSuccess && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-green-100 dark:bg-green-900/30 border border-green-500 dark:border-green-700 rounded-lg p-4 flex items-center justify-center gap-3"
          >
            <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
            <span className="text-green-700 dark:text-green-300 font-medium">数据已成功导出！</span>
          </motion.div>
        )}

        {/* Method Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm"
        >
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={selectAll}
                className="px-3 py-1.5 text-sm border border-slate-300 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors text-slate-700 dark:text-slate-300"
              >
                全选
              </button>
              <button
                onClick={selectRecommended}
                className="px-3 py-1.5 text-sm border border-emerald-300 dark:border-emerald-700 rounded-lg bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 dark:hover:bg-emerald-900/30 transition-colors"
              >
                推荐方法
              </button>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {metrics.map((method) => {
                const badge = getMethodBadge(method.key);
                const isSelected = selectedMethods.has(method.key);
                return (
                  <button
                    key={method.key}
                    onClick={() => toggleMethod(method.key)}
                    className={`px-3 py-1.5 text-sm rounded-lg border transition-all flex items-center gap-2 ${
                      isSelected
                        ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-500 text-blue-700 dark:text-blue-300'
                        : 'bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-400'
                    }`}
                  >
                    {badge && (
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${badge.color}`}>
                        {badge.label}
                      </span>
                    )}
                    {method.name}
                    {isSelected && <XCircle className="w-3 h-3" />}
                  </button>
                );
              })}
            </div>
          </div>
        </motion.div>

        {/* Key Metrics Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 lg:grid-cols-4 gap-4"
        >
          {[
            {
              label: '最佳隐私保护',
              value: `${getMethodMetrics().find(m => m.key === 'trace_v2')?.privacy ?? 0}%`,
              method: 'TRACE-RPS v2.0',
              icon: Shield,
              color: 'emerald',
            },
            {
              label: '最高效用保持',
              value: `${getMethodMetrics().find(m => m.key === 'homogeneous')?.utility ?? 0}%`,
              method: '同构对抗训练',
              icon: Zap,
              color: 'blue',
            },
            {
              label: '最佳文本质量',
              value: `${getMethodMetrics().find(m => m.key === 'trace_v2')?.quality ?? 0}%`,
              method: 'TRACE-RPS v2.0',
              icon: FileText,
              color: 'violet',
            },
            {
              label: '最高推理阻止',
              value: `${getMethodMetrics().find(m => m.key === 'trace_v2')?.blocking ?? 0}%`,
              method: 'TRACE-RPS v2.0',
              icon: TrendingUp,
              color: 'amber',
            },
          ].map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 hover:shadow-lg transition-all duration-300"
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className={`p-2.5 bg-${item.color}-100 dark:bg-${item.color}-900/30 rounded-lg`}>
                    <Icon className={`w-5 h-5 text-${item.color}-600 dark:text-${item.color}-400`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-slate-500 dark:text-slate-400">{item.label}</p>
                    <p className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-slate-100">{item.value}</p>
                  </div>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400">{item.method}</p>
              </div>
            );
          })}
        </motion.div>

        {/* Performance Charts */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-6"
        >
          {/* Radar Chart - Four Metrics Comparison */}
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-all duration-300">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-3">
                <Shield className="w-5 h-5 text-violet-600 dark:text-violet-400" />
                <div>
                  <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">四维性能对比</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400">四种方法的综合指标雷达图</p>
                </div>
              </div>
            </div>
            <div className="p-6">
              <ResponsiveContainer width="100%" height={350}>
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis
                    dataKey="dimension"
                    tick={{ fill: '#6B7280', fontSize: 12 }}
                  />
                  <PolarRadiusAxis
                    angle={90}
                    domain={[0, 100]}
                    tick={{ fill: '#6B7280', fontSize: 10 }}
                  />
                  {filteredMetrics.map((method) => (
                    <Radar
                      key={method.key}
                      name={method.name}
                      dataKey={method.name}
                      stroke={method.key === 'trace_v2' ? '#10B981' : method.key === 'heterogeneous' ? '#3B82F6' : method.key === 'homogeneous' ? '#8B5CF6' : '#F59E0B'}
                      fill={method.key === 'trace_v2' ? '#10B981' : method.key === 'heterogeneous' ? '#3B82F6' : method.key === 'homogeneous' ? '#8B5CF6' : '#F59E0B'}
                      fillOpacity={0.2}
                    />
                  ))}
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        return (
                          <div className="bg-white dark:bg-slate-900 p-3 rounded shadow border border-slate-200 dark:border-slate-800">
                            <p className="text-sm font-medium mb-2">{payload[0].payload.dimension}</p>
                            {payload.map((entry, index) => (
                              <p key={index} className="text-sm text-slate-600 dark:text-slate-400">
                                <span style={{ color: entry.color }}>●</span> {entry.name}: {entry.value}%
                              </p>
                            ))}
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Legend />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Processing Time & Cost */}
          <div className="space-y-6">
            {/* Processing Time */}
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-all duration-300">
              <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800">
                <div className="flex items-center gap-3">
                  <Clock className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                  <div>
                    <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">处理时间对比</h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400">各方法的平均处理时间</p>
                  </div>
                </div>
              </div>
              <div className="p-6">
                <ResponsiveContainer width="100%" height={200}>
                  <RechartsWrapper>
                    <BarChart data={filteredMetrics}>
                      <XAxis dataKey="name" tick={{ fill: '#6B7280', fontSize: 11 }} tickLine={false} />
                      <YAxis tick={{ fill: '#6B7280' }} tickLine={false} label={{ value: '秒', angle: -90, position: 'insideLeft', style: { fontSize: '11px', fill: '#9CA3AF' } }} />
                      <Bar dataKey="time" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
                      <Tooltip
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            return (
                              <div className="bg-white dark:bg-slate-900 p-2 rounded shadow border border-slate-200 dark:border-slate-800">
                                <p className="text-sm font-medium">{payload[0].payload.name}</p>
                                <p className="text-sm text-slate-600 dark:text-slate-400">
                                  处理时间: {payload[0].value}秒
                                </p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                    </BarChart>
                  </RechartsWrapper>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Cost Comparison */}
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-all duration-300">
              <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800">
                <div className="flex items-center gap-3">
                  <DollarSign className="w-5 h-5 text-green-600 dark:text-green-400" />
                  <div>
                    <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">成本对比</h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400">每1000词处理成本 (USD)</p>
                  </div>
                </div>
              </div>
              <div className="p-6">
                <ResponsiveContainer width="100%" height={180}>
                  <RechartsWrapper>
                    <BarChart data={filteredMetrics}>
                      <XAxis dataKey="name" tick={{ fill: '#6B7280', fontSize: 11 }} tickLine={false} />
                      <YAxis tick={{ fill: '#6B7280' }} tickLine={false} label={{ value: '$', angle: -90, position: 'insideLeft', style: { fontSize: '11px', fill: '#9CA3AF' } }} />
                      <Bar dataKey="cost" fill="#10B981" radius={[4, 4, 0, 0]} />
                      <Tooltip
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            return (
                              <div className="bg-white dark:bg-slate-900 p-2 rounded shadow border border-slate-200 dark:border-slate-800">
                                <p className="text-sm font-medium">{payload[0].payload.name}</p>
                                <p className="text-sm text-slate-600 dark:text-slate-400">
                                  成本: ${payload[0].value.toFixed(2)}
                                </p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                    </BarChart>
                  </RechartsWrapper>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Detailed Comparison Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden"
        >
          <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <FileText className="w-5 h-5" />
              详细指标对比
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 dark:bg-slate-800/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase">
                    方法
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase">
                    隐私保护
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase">
                    效用保持
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase">
                    文本质量
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase">
                    推理阻止
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase">
                    处理时间
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase">
                    成本/1k词
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {metrics.map((method, idx) => {
                  const badge = getMethodBadge(method.key);
                  const isRecommended = method.key === 'trace_v2';
                  const isBest = {
                    privacy: method.privacy === getBestMethod('privacy').privacy,
                    utility: method.utility === getBestMethod('utility').utility,
                    quality: method.quality === getBestMethod('quality').quality,
                    blocking: method.blocking === getBestMethod('blocking').blocking,
                  };

                  return (
                    <tr
                      key={idx}
                      className={`hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors ${
                        isRecommended ? 'bg-emerald-50/30 dark:bg-emerald-900/10' : ''
                      }`}
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          {badge && (
                            <span className={`px-2 py-1 rounded text-xs font-semibold ${badge.color}`}>
                              {badge.label}
                            </span>
                          )}
                          <span className="text-sm font-medium text-slate-900 dark:text-slate-100">{method.name}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <span className={`w-6 h-6 rounded-full flex items-center justify-center ${
                            isBest.privacy ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-700'
                          }`}>
                            {isBest.privacy && <CheckCircle className="w-3.5 h-3.5 text-white" />}
                          </span>
                          <span className="text-sm font-medium text-slate-900 dark:text-slate-100">{method.privacy}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <span className={`w-6 h-6 rounded-full flex items-center justify-center ${
                            isBest.utility ? 'bg-blue-500' : 'bg-slate-300 dark:bg-slate-700'
                          }`}>
                            {isBest.utility && <CheckCircle className="w-3.5 h-3.5 text-white" />}
                          </span>
                          <span className="text-sm font-medium text-slate-900 dark:text-slate-100">{method.utility}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <span className={`w-6 h-6 rounded-full flex items-center justify-center ${
                            isBest.quality ? 'bg-violet-500' : 'bg-slate-300 dark:bg-slate-700'
                          }`}>
                            {isBest.quality && <CheckCircle className="w-3.5 h-3.5 text-white" />}
                          </span>
                          <span className="text-sm font-medium text-slate-900 dark:text-slate-100">{method.quality}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <span className={`w-6 h-6 rounded-full flex items-center justify-center ${
                            isBest.blocking ? 'bg-amber-500' : 'bg-slate-300 dark:bg-slate-700'
                          }`}>
                            {isBest.blocking && <CheckCircle className="w-3.5 h-3.5 text-white" />}
                          </span>
                          <span className="text-sm font-medium text-slate-900 dark:text-slate-100">{method.blocking}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center text-sm text-slate-600 dark:text-slate-400">
                        {method.time}s
                      </td>
                      <td className="px-6 py-4 text-center text-sm font-medium text-slate-900 dark:text-slate-100">
                        ${method.cost.toFixed(2)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </motion.div>

        {/* Recommendations */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-gradient-to-r from-blue-50 to-violet-50 dark:from-blue-900/20 dark:to-violet-900/20 rounded-xl border border-blue-200 dark:border-blue-800 p-6"
        >
          <div className="flex items-start gap-4">
            <Info className="w-6 h-6 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-1" />
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">使用建议</h3>
              <div className="grid md:grid-cols-3 gap-6">
                <div className="flex items-start gap-3">
                  <Shield className="w-5 h-5 text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-100">高隐私要求</p>
                    <p className="text-xs text-slate-700 dark:text-slate-300 mt-1">
                      医疗、金融、法律等场景首选 <span className="font-semibold text-emerald-700 dark:text-emerald-400">TRACE-RPS v2.0</span>
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Zap className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-100">平衡应用</p>
                    <p className="text-xs text-slate-700 dark:text-slate-300 mt-1">
                      大多数场景推荐 <span className="font-semibold text-blue-700 dark:text-blue-400">异构对抗训练</span>
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <TrendingUp className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-100">成本优先</p>
                    <p className="text-xs text-slate-700 dark:text-slate-300 mt-1">
                      预算受限时考虑 <span className="font-semibold text-amber-700 dark:text-amber-400">TRACE-RPS v1.0</span>
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  );
};

export default TRACERPSDashboard;

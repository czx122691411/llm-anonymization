/**
 * PerformanceCharts - Collection of charts for TRACE-RPS performance comparison
 * Includes radar chart, bar charts, and cost visualization
 */

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts';
import { BarChart3, TrendingUp, DollarSign, Clock } from 'lucide-react';

interface PerformanceChartsProps {
  data: {
    radar: Array<{ method: string; privacy: number; utility: number; quality: number; blocking: number }>;
    processingTime: Array<{ method: string; time: number; iterations: number }>;
    cost: Array<{ method: string; total: number; [key: string]: string | number }>;
    costEfficiency: Array<{ method: string; ratio: number; privacy: number; cost: number }>;
  };
}

const CustomTooltip: React.FC<any> = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white dark:bg-gray-900 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-800">
        <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">{label}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            {entry.name}: {entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export const PerformanceCharts: React.FC<PerformanceChartsProps> = ({ data }) => {
  const chartFontStyle = { fontSize: '12px', fill: '#6B7280' };

  return (
    <div className="space-y-6">
      {/* Performance Metrics Comparison - Bar Chart */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm hover:shadow-md transition-all duration-300">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <BarChart3 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <div>
              <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">性能指标对比</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">四种匿名化方法的综合性能</p>
            </div>
          </div>
        </div>
        <div className="p-6">
          <div className="h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.radar} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" strokeOpacity={0.5} />
                <XAxis dataKey="method" style={chartFontStyle} tick={{ fill: '#6B7280' }} tickLine={false} />
                <YAxis style={chartFontStyle} tick={{ fill: '#6B7280' }} tickLine={false} domain={[0, 100]} />
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  wrapperStyle={{ paddingTop: '10px' }}
                  iconType="circle"
                  formatter={(value) => <span className="text-sm text-gray-700 dark:text-gray-300">{value}</span>}
                />
                <Bar dataKey="privacy" name="隐私保护" fill="#3B82F6" radius={[4, 4, 0, 0]} animationDuration={300} />
                <Bar dataKey="utility" name="效用保持" fill="#10B981" radius={[4, 4, 0, 0]} animationDuration={300} />
                <Bar dataKey="quality" name="文本质量" fill="#8B5CF6" radius={[4, 4, 0, 0]} animationDuration={300} />
                <Bar dataKey="blocking" name="推理阻止" fill="#F59E0B" radius={[4, 4, 0, 0]} animationDuration={300} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Processing Time Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm hover:shadow-md transition-all duration-300">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800">
            <div className="flex items-center gap-3">
              <Clock className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              <div>
                <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">处理时间对比</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">各方法的平均处理时间</p>
              </div>
            </div>
          </div>
          <div className="p-6">
            <div className="h-[240px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.processingTime} margin={{ top: 20, right: 30, left: 20, bottom: 5 }} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" strokeOpacity={0.5} />
                  <XAxis dataKey="method" style={chartFontStyle} tick={{ fill: '#6B7280' }} tickLine={false} />
                  <YAxis style={chartFontStyle} tick={{ fill: '#6B7280' }} tickLine={false} label={{ value: '秒', angle: -90, position: 'insideLeft', style: { fontSize: '11px', fill: '#9CA3AF' } }} />
                  <Tooltip content={<CustomTooltip />} formatter={(value: number) => [`${value}s`, '处理时间']} />
                  <Bar dataKey="time" fill="#8B5CF6" radius={[4, 4, 0, 0]} animationDuration={300} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Cost Comparison */}
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm hover:shadow-md transition-all duration-300">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800">
            <div className="flex items-center gap-3">
              <DollarSign className="w-5 h-5 text-green-600 dark:text-green-400" />
              <div>
                <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">成本对比</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">每1000词处理成本 (USD)</p>
              </div>
            </div>
          </div>
          <div className="p-6">
            <div className="h-[240px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.cost} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" strokeOpacity={0.5} />
                  <XAxis dataKey="method" style={chartFontStyle} tick={{ fill: '#6B7280' }} tickLine={false} />
                  <YAxis style={chartFontStyle} tick={{ fill: '#6B7280' }} tickLine={false} label={{ value: '$', angle: -90, position: 'insideLeft', style: { fontSize: '11px', fill: '#9CA3AF' } }} />
                  <Tooltip content={<CustomTooltip />} formatter={(value: number) => [`$${value.toFixed(2)}`, '成本']} />
                  <Bar dataKey="total" fill="#10B981" radius={[4, 4, 0, 0]} animationDuration={300} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>

      {/* Cost Efficiency Analysis */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm hover:shadow-md transition-all duration-300">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <TrendingUp className="w-5 h-5 text-amber-600 dark:text-amber-400" />
            <div>
              <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">性价比分析</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">隐私保护分数/成本比率</p>
            </div>
          </div>
        </div>
        <div className="p-6">
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.costEfficiency} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" strokeOpacity={0.5} />
                <XAxis dataKey="method" style={chartFontStyle} tick={{ fill: '#6B7280' }} tickLine={false} />
                <YAxis style={chartFontStyle} tick={{ fill: '#6B7280' }} tickLine={false} label={{ value: '比率', angle: -90, position: 'insideLeft', style: { fontSize: '11px', fill: '#9CA3AF' } }} />
                <Tooltip content={<CustomTooltip />} formatter={(value: number) => [value.toFixed(1), '性价比']} />
                <Line type="monotone" dataKey="ratio" stroke="#F59E0B" strokeWidth={3} dot={{ fill: '#F59E0B', r: 6 }} activeDot={{ r: 8 }} animationDuration={300} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PerformanceCharts;

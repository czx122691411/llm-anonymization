/**
 * PIIDistributionCard - Card component displaying PII type distribution metrics
 * Shows accuracy, sample count, and other statistics for each PII type
 */
import React from 'react';
import { PIIMetricData } from '../types/deepseek-training';

interface PIIDistributionCardProps {
  piiType: string;
  metrics: PIIMetricData;
  onClick: () => void;
  isSelected: boolean;
}

export const PIIDistributionCard: React.FC<PIIDistributionCardProps> = ({
  piiType,
  metrics,
  onClick,
  isSelected,
}) => {
  // Chinese labels for PII types
  const piiTypeLabels: Record<string, string> = {
    age: '年龄',
    gender: '性别',
    income: '收入',
    education: '教育',
    occupation: '职业',
    location: '位置',
    married: '婚姻状况',
    marital_status: '婚姻状况',
  };

  // Get color based on accuracy level
  const getAccuracyColor = (accuracy: number) => {
    const accuracyPercent = accuracy * 100;
    if (accuracyPercent < 30) {
      return {
        text: 'text-emerald-700 dark:text-emerald-400',
        bg: 'bg-emerald-100 dark:bg-emerald-900/30',
        bar: 'bg-emerald-500',
      };
    }
    if (accuracyPercent < 50) {
      return {
        text: 'text-amber-700 dark:text-amber-400',
        bg: 'bg-amber-100 dark:bg-amber-900/30',
        bar: 'bg-amber-500',
      };
    }
    return {
      text: 'text-red-700 dark:text-red-400',
      bg: 'bg-red-100 dark:bg-red-900/30',
      bar: 'bg-red-500',
    };
  };

  const accuracyColor = getAccuracyColor(metrics.accuracy);
  const accuracyPercent = (metrics.accuracy * 100).toFixed(1);

  return (
    <div
      onClick={onClick}
      className={`bg-white dark:bg-gray-900 rounded-xl border-2 p-4 cursor-pointer transition-all duration-200 hover:shadow-lg ${
        isSelected
          ? 'border-blue-500 shadow-md ring-2 ring-blue-200 dark:ring-blue-800'
          : 'border-gray-200 dark:border-gray-800 hover:border-gray-300 dark:hover:border-gray-700'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-semibold text-gray-900 dark:text-gray-100 capitalize">
          {piiTypeLabels[piiType] || piiType}
        </h4>
        <span className={`px-2 py-1 rounded text-xs font-medium ${accuracyColor.bg} ${accuracyColor.text}`}>
          {accuracyPercent}% 准确率
        </span>
      </div>

      {/* Statistics */}
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500 dark:text-gray-400">样本数</span>
          <span className="font-medium text-gray-900 dark:text-gray-100">
            {metrics.total.toLocaleString()}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500 dark:text-gray-400">正确推断</span>
          <span className="font-medium text-gray-900 dark:text-gray-100">
            {metrics.correct.toLocaleString()}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500 dark:text-gray-400">平均难度</span>
          <span className="font-medium text-gray-900 dark:text-gray-100">
            {metrics.average_hardness.toFixed(1)}/5
          </span>
        </div>
        {metrics.average_utility > 0 && (
          <div className="flex justify-between">
            <span className="text-gray-500 dark:text-gray-400">平均效用</span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {(metrics.average_utility * 100).toFixed(1)}%
            </span>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      <div className="mt-4">
        <div className="w-full bg-gray-200 dark:bg-gray-800 rounded-full h-2 overflow-hidden">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${accuracyColor.bar}`}
            style={{ width: `${Math.min(accuracyPercent, 100)}%` }}
          />
        </div>
        <div className="flex justify-between mt-1 text-xs text-gray-500 dark:text-gray-400">
          <span>隐私保护</span>
          <span>{(100 - parseFloat(accuracyPercent)).toFixed(1)}%</span>
        </div>
      </div>

      {/* Selection indicator */}
      {isSelected && (
        <div className="mt-3 text-xs text-blue-600 dark:text-blue-400 font-medium">
          ✓ 已选中
        </div>
      )}
    </div>
  );
};

export default PIIDistributionCard;

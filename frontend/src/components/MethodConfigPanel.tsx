/**
 * MethodConfigPanel - 匿名化方法配置面板
 *
 * 允许用户配置：
 * - 匿名化方法选择
 * - 敏感属性多选
 * - 迭代次数
 * - 置信度阈值
 */

import React from 'react';
import { Shield, Settings } from 'lucide-react';

// 支持的匿名化方法
export const ANONYMIZATION_METHODS = [
  { value: 'trace_rps_v2', label: 'TRACE-RPS v2.0', description: '最佳隐私保护，推理链阻断', recommended: true },
  { value: 'heterogeneous', label: '异构对抗训练', description: '平衡性能，DeepSeek→Qwen', recommended: false },
  { value: 'homogeneous', label: '同构对抗训练', description: '经济高效，DeepSeek→DeepSeek', recommended: false },
] as const;

// 支持的敏感属性
export const SENSITIVE_ATTRIBUTES = [
  { value: 'income', label: '收入水平', icon: '💰' },
  { value: 'education', label: '教育程度', icon: '🎓' },
  { value: 'gender', label: '性别', icon: '👤' },
  { value: 'age', label: '年龄', icon: '📅' },
  { value: 'location', label: '居住地点', icon: '📍' },
  { value: 'occupation', label: '职业', icon: '💼' },
  { value: 'relationship_status', label: '感情状态', icon: '❤️' },
  { value: 'birth_location', label: '出生地', icon: '🏠' },
] as const;

export type AnonymizationMethod = typeof ANONYMIZATION_METHODS[number]['value'];
export type SensitiveAttribute = typeof SENSITIVE_ATTRIBUTES[number]['value'];

interface MethodConfigPanelProps {
  selectedMethod: AnonymizationMethod;
  onMethodChange: (method: AnonymizationMethod) => void;
  selectedAttributes: SensitiveAttribute[];
  onAttributesChange: (attributes: SensitiveAttribute[]) => void;
  iterations: number;
  onIterationsChange: (iterations: number) => void;
  threshold: number;
  onThresholdChange: (threshold: number) => void;
  disabled?: boolean;
}

export const MethodConfigPanel: React.FC<MethodConfigPanelProps> = ({
  selectedMethod,
  onMethodChange,
  selectedAttributes,
  onAttributesChange,
  iterations,
  onIterationsChange,
  threshold,
  onThresholdChange,
  disabled = false,
}) => {
  const toggleAttribute = (attr: SensitiveAttribute) => {
    if (selectedAttributes.includes(attr)) {
      if (selectedAttributes.length > 1) {
        onAttributesChange(selectedAttributes.filter(a => a !== attr));
      }
    } else {
      onAttributesChange([...selectedAttributes, attr]);
    }
  };

  const selectAllAttributes = () => {
    onAttributesChange(SENSITIVE_ATTRIBUTES.map(a => a.value));
  };

  const clearAllAttributes = () => {
    onAttributesChange(['income', 'education']); // 默认保留这两个
  };

  return (
    <div className={`bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 ${disabled ? 'opacity-50 pointer-events-none' : ''}`}>
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-violet-100 dark:bg-violet-900/30 rounded-lg">
          <Settings className="w-5 h-5 text-violet-600 dark:text-violet-400" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">配置选项</h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">自定义匿名化参数</p>
        </div>
      </div>

      <div className="space-y-6">
        {/* 匿名化方法选择 */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
            匿名化方法
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {ANONYMIZATION_METHODS.map((method) => (
              <button
                key={method.value}
                onClick={() => onMethodChange(method.value)}
                className={`p-4 rounded-lg border-2 text-left transition-all ${
                  selectedMethod === method.value
                    ? 'border-violet-500 bg-violet-50 dark:bg-violet-900/20'
                    : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-slate-900 dark:text-slate-100">{method.label}</span>
                  {method.recommended && (
                    <span className="px-2 py-0.5 text-xs font-semibold bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 rounded">
                      推荐
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400">{method.description}</p>
              </button>
            ))}
          </div>
        </div>

        {/* 敏感属性选择 */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              保护属性
            </label>
            <div className="flex gap-2">
              <button
                onClick={selectAllAttributes}
                className="text-xs px-2 py-1 text-violet-600 dark:text-violet-400 hover:bg-violet-50 dark:hover:bg-violet-900/20 rounded transition-colors"
              >
                全选
              </button>
              <button
                onClick={clearAllAttributes}
                className="text-xs px-2 py-1 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 rounded transition-colors"
              >
                清除
              </button>
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {SENSITIVE_ATTRIBUTES.map((attr) => {
              const isSelected = selectedAttributes.includes(attr.value);
              return (
                <button
                  key={attr.value}
                  onClick={() => toggleAttribute(attr.value)}
                  className={`p-3 rounded-lg border text-center transition-all ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
                  }`}
                >
                  <div className="text-2xl mb-1">{attr.icon}</div>
                  <div className="text-xs font-medium text-slate-900 dark:text-slate-100">{attr.label}</div>
                </button>
              );
            })}
          </div>
          <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
            已选择 {selectedAttributes.length} 个属性
          </p>
        </div>

        {/* 迭代次数和置信度阈值 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {/* 迭代次数 */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                最大迭代次数
              </label>
              <span className="text-sm font-semibold text-violet-600 dark:text-violet-400">{iterations}</span>
            </div>
            <input
              type="range"
              min="1"
              max="10"
              value={iterations}
              onChange={(e) => onIterationsChange(parseInt(e.target.value))}
              className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-violet-600"
              disabled={disabled}
            />
            <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 mt-1">
              <span>1</span>
              <span>5</span>
              <span>10</span>
            </div>
          </div>

          {/* 置信度阈值 */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                置信度阈值
              </label>
              <span className="text-sm font-semibold text-violet-600 dark:text-violet-400">{threshold}</span>
            </div>
            <input
              type="range"
              min="1"
              max="5"
              value={threshold}
              onChange={(e) => onThresholdChange(parseInt(e.target.value))}
              className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-violet-600"
              disabled={disabled}
            />
            <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 mt-1">
              <span>低</span>
              <span>中</span>
              <span>高</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

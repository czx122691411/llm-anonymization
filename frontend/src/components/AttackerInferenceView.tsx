/**
 * AttackerInferenceView - 攻击者推理分析组件
 *
 * 展示LLM作为攻击者如何从文本中推断出隐私信息
 * 包括推理链、置信度和风险等级
 */

import React, { useState } from 'react';
import { Target, ChevronDown, ChevronUp, Eye, Brain } from 'lucide-react';

// 类型定义
export interface ReasoningChainStep {
  id: string;
  type: string;
  text: string;
  evidence?: string;
  confidence?: number;
}

export interface ReasoningChain {
  attribute: string;
  target_guess: string;
  nodes: ReasoningChainStep[];
  blocked: boolean;
}

export interface InferenceTest {
  attribute: string;
  before_attack: { guess: string; certainty: number };
  after_attack: { guess: string; certainty: number };
  blocked: boolean;
}

interface AttackerInferenceViewProps {
  reasoningChains: ReasoningChain[];
  inferenceTests: InferenceTest[];
}

const AttributeLabel: Record<string, string> = {
  income: '收入',
  education: '教育',
  gender: '性别',
  age: '年龄',
  location: '地点',
  occupation: '职业',
  relationship_status: '感情状态',
  birth_location: '出生地',
};

const getRiskLevel = (certainty: number) => {
  if (certainty >= 5) return { level: '高危', color: 'red', emoji: '🔴' };
  if (certainty >= 4) return { level: '中危', color: 'orange', emoji: '🟡' };
  if (certainty >= 3) return { level: '低危', color: 'yellow', emoji: '🟢' };
  return { level: '安全', color: 'green', emoji: '✅' };
};

export const AttackerInferenceView: React.FC<AttackerInferenceViewProps> = ({
  reasoningChains,
  inferenceTests,
}) => {
  const [expandedChains, setExpandedChains] = useState<Set<string>>(new Set());

  const toggleChain = (attribute: string) => {
    const newSet = new Set(expandedChains);
    if (newSet.has(attribute)) {
      newSet.delete(attribute);
    } else {
      newSet.add(attribute);
    }
    setExpandedChains(newSet);
  };

  // 合并推理链和测试结果
  const combinedData = reasoningChains.map(chain => {
    const test = inferenceTests.find(t => t.attribute === chain.attribute);
    return {
      ...chain,
      beforeCertainty: test?.before_attack.certainty || 5,
      afterCertainty: test?.after_attack.certainty || 0,
      blocked: test?.blocked || chain.blocked,
    };
  });

  // 按风险等级排序
  const sortedData = [...combinedData].sort((a, b) => b.beforeCertainty - a.beforeCertainty);

  if (sortedData.length === 0) {
    return (
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-8 text-center">
        <Eye className="w-12 h-12 text-slate-400 dark:text-slate-600 mx-auto mb-3" />
        <p className="text-slate-600 dark:text-slate-400">未检测到隐私推断</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 标题 */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2.5 bg-red-100 dark:bg-red-900/30 rounded-lg">
          <Target className="w-5 h-5 text-red-600 dark:text-red-400" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            攻击者推理分析
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            LLM如何从你的文本中推断隐私信息
          </p>
        </div>
      </div>

      {/* 推理列表 */}
      {sortedData.map((item) => {
        const risk = getRiskLevel(item.beforeCertainty);
        const isExpanded = expandedChains.has(item.attribute);
        const hasChain = item.nodes && item.nodes.length > 0;

        return (
          <div
            key={item.attribute}
            className={`bg-white dark:bg-slate-900 rounded-xl border-2 overflow-hidden transition-all ${
              item.blocked
                ? 'border-emerald-200 dark:border-emerald-800'
                : `border-${risk.color}-200 dark:border-${risk.color}-800`
            }`}
          >
            {/* 头部摘要 */}
            <div
              className={`p-4 cursor-pointer hover:bg-${risk.color === 'red' ? 'red' : risk.color === 'orange' ? 'orange' : 'green'}-50 dark:hover:bg-${risk.color === 'red' ? 'red' : risk.color === 'orange' ? 'orange' : 'green'}-900/10 transition-colors`}
              onClick={() => hasChain && toggleChain(item.attribute)}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-semibold text-slate-900 dark:text-slate-100">
                      {AttributeLabel[item.attribute] || item.attribute}
                    </span>
                    <span
                      className={`px-2 py-0.5 text-xs font-semibold rounded ${
                        item.blocked
                          ? 'bg-emerald-200 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300'
                          : `bg-${risk.color}-200 dark:bg-${risk.color}-900/40 text-${risk.color}-800 dark:text-${risk.color}-300`
                      }`}
                    >
                      {item.blocked ? '✓ 已阻止' : risk.level}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 text-sm">
                    <span className="text-slate-600 dark:text-slate-400">
                      推断结果:
                    </span>
                    <span className="font-medium text-slate-900 dark:text-slate-100">
                      {item.target_guess}
                    </span>
                    <span className="text-slate-500 dark:text-slate-500">|</span>
                    <span className="text-slate-600 dark:text-slate-400">
                      置信度:
                    </span>
                    <span className={`font-semibold ${
                      item.beforeCertainty >= 4
                        ? 'text-red-600 dark:text-red-400'
                        : item.beforeCertainty >= 3
                        ? 'text-orange-600 dark:text-orange-400'
                        : 'text-green-600 dark:text-green-400'
                    }`}>
                      {item.beforeCertainty}/5
                    </span>
                  </div>

                  {item.blocked && (
                    <div className="mt-2 text-sm text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                      <span>防御效果: 置信度降至 {item.afterCertainty}/5</span>
                    </div>
                  )}
                </div>

                {hasChain && (
                  <button className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded transition-colors">
                    {isExpanded ? (
                      <ChevronUp className="w-5 h-5 text-slate-600 dark:text-slate-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-slate-600 dark:text-slate-400" />
                    )}
                  </button>
                )}
              </div>

              {/* 推理链详情（可折叠） */}
              {hasChain && isExpanded && (
                <div className="px-4 pb-4 border-t border-slate-200 dark:border-slate-800">
                  <div className="mt-4 space-y-3">
                    {item.nodes.map((node, idx) => (
                      <div
                        key={node.id}
                        className="flex gap-3 p-3 bg-slate-50 dark:bg-slate-800 rounded-lg"
                      >
                        <div className="flex-shrink-0 w-6 h-6 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                          <span className="text-xs font-semibold text-red-600 dark:text-red-400">
                            {idx + 1}
                          </span>
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-1">
                            {node.text}
                          </p>
                          {node.evidence && (
                            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                              <span className="font-medium">证据:</span> {node.evidence}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        );
      })}

      {/* 底部提示 */}
      <div className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <Brain className="w-4 h-4 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
        <p className="text-xs text-blue-900 dark:text-blue-100">
          <span className="font-semibold">攻击者视角:</span>{' '}
          高置信度表示文本中包含可直接推断的信息，低置信度表示需要更多猜测
        </p>
      </div>
    </div>
  );
};

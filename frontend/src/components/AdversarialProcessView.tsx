/**
 * AdversarialProcessView - 攻防对抗过程组件
 *
 * 展示TRACE-RPS的迭代优化过程
 * 包括每一轮的攻击者发现和防御者修改
 */

import React, { useState } from 'react';
import { Swords, TrendingDown, CheckCircle, XCircle, ChevronDown, ChevronUp, Zap, Shield } from 'lucide-react';

// 类型定义 - 迭代过程数据
export interface IterationStep {
  iteration: number;
  attackerFindings: {
    attribute: string;
    certainty: number;
  }[];
  defenderActions: {
    original: string;
    anonymized: string;
    position: { start: number; end: number };
  }[];
  averageCertainty: {
    before: number;
    after: number;
  };
}

// 简化版本 - 从现有数据推断迭代过程
export interface AdversarialProcessViewProps {
  iterations: number;
  reasoningChains: Array<{
    attribute: string;
    target_guess: string;
    nodes: Array<{ text: string; evidence?: string }>;
    blocked: boolean;
  }>;
  inferenceTests: Array<{
    attribute: string;
    before_attack: { guess: string; certainty: number };
    after_attack: { guess: string; certainty: number };
    blocked: boolean;
  }>;
  changes: Array<{
    original: string;
    anonymized: string;
    position: { start: number; end: number };
  }>;
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

export const AdversarialProcessView: React.FC<AdversarialProcessViewProps> = ({
  iterations,
  reasoningChains,
  inferenceTests,
  changes,
}) => {
  const [expandedIteration, setExpandedIteration] = useState<Set<number>>(new Set([0]));

  const toggleIteration = (idx: number) => {
    const newSet = new Set(expandedIteration);
    if (newSet.has(idx)) {
      newSet.delete(idx);
    } else {
      newSet.add(idx);
    }
    setExpandedIteration(newSet);
  };

  // 构建迭代过程数据
  const buildIterationSteps = (): IterationStep[] => {
    const steps: IterationStep[] = [];

    // 第一轮：初始攻击
    steps.push({
      iteration: 1,
      attackerFindings: inferenceTests.map(test => ({
        attribute: test.attribute,
        certainty: test.before_attack.certainty,
      })),
      defenderActions: changes.slice(0, Math.ceil(changes.length / iterations)).map(change => ({
        original: change.original,
        anonymized: change.anonymized,
        position: change.position,
      })),
      averageCertainty: {
        before: inferenceTests.reduce((sum, t) => sum + t.before_attack.certainty, 0) / inferenceTests.length,
        after: inferenceTests.reduce((sum, t) => sum + t.after_attack.certainty, 0) / inferenceTests.length,
      },
    });

    // 如果有多轮迭代，添加后续步骤（简化处理）
    if (iterations > 1) {
      const remainingChanges = changes.slice(Math.ceil(changes.length / iterations));
      if (remainingChanges.length > 0 || reasoningChains.some(c => !c.blocked)) {
        steps.push({
          iteration: 2,
          attackerFindings: inferenceTests
            .filter(t => !t.blocked)
            .map(test => ({
              attribute: test.attribute,
              certainty: test.after_attack.certainty,
            })),
          defenderActions: remainingChanges.map(change => ({
            original: change.original,
            anonymized: change.anonymized,
            position: change.position,
          })),
          averageCertainty: {
            before: steps[0].averageCertainty.after,
            after: inferenceTests.reduce((sum, t) => sum + t.after_attack.certainty, 0) / inferenceTests.length,
          },
        });
      }
    }

    return steps;
  };

  const iterationSteps = buildIterationSteps();

  // 计算最终状态
  const allBlocked = inferenceTests.every(t => t.blocked);
  const avgFinalCertainty = inferenceTests.reduce((sum, t) => sum + t.after_attack.certainty, 0) / inferenceTests.length;

  return (
    <div className="space-y-4">
      {/* 标题 */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2.5 bg-violet-100 dark:bg-violet-900/30 rounded-lg">
          <Swords className="w-5 h-5 text-violet-600 dark:text-violet-400" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            攻防对抗过程
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            TRACE-RPS迭代优化 - 如何逐步降低隐私风险
          </p>
        </div>
      </div>

      {/* 迭代步骤 */}
      <div className="space-y-3">
        {iterationSteps.map((step, idx) => {
          const isExpanded = expandedIteration.has(idx);
          const improvement = step.averageCertainty.before - step.averageCertainty.after;

          return (
            <div
              key={idx}
              className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden"
            >
              {/* 迭代头部 */}
              <div
                className="p-4 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                onClick={() => toggleIteration(idx)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center">
                      <span className="text-sm font-semibold text-violet-600 dark:text-violet-400">
                        {step.iteration}
                      </span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-slate-900 dark:text-slate-100">
                        迭代 #{step.iteration}
                      </h4>
                      <div className="flex items-center gap-2 text-sm">
                        {improvement > 0 ? (
                          <TrendingDown className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                        ) : (
                          <Zap className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                        )}
                        <span className={improvement > 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}>
                          平均置信度: {step.averageCertainty.before.toFixed(1)} → {step.averageCertainty.after.toFixed(1)}
                        </span>
                      </div>
                    </div>
                  </div>

                  <button className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded transition-colors">
                    {isExpanded ? (
                      <ChevronUp className="w-5 h-5 text-slate-600 dark:text-slate-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-slate-600 dark:text-slate-400" />
                    )}
                  </button>
                </div>

                {/* 详细信息（可折叠） */}
                {isExpanded && (
                  <div className="px-4 pb-4 border-t border-slate-200 dark:border-slate-800">
                    <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* 攻击者发现 */}
                      <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                        <div className="flex items-center gap-2 mb-2">
                          <Zap className="w-4 h-4 text-red-600 dark:text-red-400" />
                          <span className="text-sm font-medium text-red-900 dark:text-red-100">
                            👤 攻击者发现
                          </span>
                        </div>
                        <div className="space-y-1">
                          {step.attackerFindings.map((finding, fidx) => (
                            <div key={fidx} className="text-sm text-red-800 dark:text-red-200">
                              <span className="font-medium">
                                {AttributeLabel[finding.attribute] || finding.attribute}:
                              </span>{' '}
                              置信度 {finding.certainty}/5
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* 防御者修改 */}
                      <div className="p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg border border-emerald-200 dark:border-emerald-800">
                        <div className="flex items-center gap-2 mb-2">
                          <Shield className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                          <span className="text-sm font-medium text-emerald-900 dark:text-emerald-100">
                            🛡️ 防御者修改
                          </span>
                        </div>
                        <div className="space-y-1">
                          {step.defenderActions.map((action, aidx) => (
                            <div key={aidx} className="text-sm text-emerald-800 dark:text-emerald-200">
                              <span className="line-through opacity-60">{action.original}</span>
                              <span className="mx-1">→</span>
                              <span className="font-medium">{action.anonymized}</span>
                            </div>
                          ))}
                          {step.defenderActions.length === 0 && (
                            <div className="text-sm text-emerald-700 dark:text-emerald-300 italic">
                              无修改（文本已安全）
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* 最终结果摘要 */}
      <div
        className={`p-4 rounded-xl border-2 ${
          allBlocked
            ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-500 dark:border-emerald-700'
            : 'bg-amber-50 dark:bg-amber-900/20 border-amber-500 dark:border-amber-700'
        }`}
      >
        <div className="flex items-center gap-3">
          {allBlocked ? (
            <CheckCircle className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
          ) : (
            <XCircle className="w-6 h-6 text-amber-600 dark:text-amber-400" />
          )}
          <div className="flex-1">
            <h4 className="font-semibold text-slate-900 dark:text-slate-100">
              {allBlocked ? '✓ 所有推断已被成功阻止' : '⚠️ 部分推断仍可进行'}
            </h4>
            <p className="text-sm text-slate-700 dark:text-slate-300">
              最终平均置信度: {avgFinalCertainty.toFixed(1)}/5
              {allBlocked && avgFinalCertainty <= 2 && ' (达到安全阈值)'}
            </p>
          </div>
        </div>
      </div>

      {/* 底部提示 */}
      <div className="flex items-start gap-2 p-3 bg-violet-50 dark:bg-violet-900/20 rounded-lg border border-violet-200 dark:border-violet-800">
        <Swords className="w-4 h-4 text-violet-600 dark:text-violet-400 flex-shrink-0 mt-0.5" />
        <p className="text-xs text-violet-900 dark:text-violet-100">
          <span className="font-semibold">迭代优化:</span>{' '}
          TRACE-RPS通过多轮攻防对抗，逐步识别和修复隐私泄露点，直到攻击者无法准确推断隐私信息
        </p>
      </div>
    </div>
  );
};

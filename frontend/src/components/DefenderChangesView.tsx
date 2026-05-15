/**
 * DefenderChangesView - 防御者修改详情组件
 *
 * 展示LLM作为防御者对文本做了哪些修改
 * 包括修改位置、原因和防御效果
 */

import React, { useState } from 'react';
import { Shield, CheckCircle, XCircle, ChevronDown, ChevronUp, Edit3, AlertCircle } from 'lucide-react';

// 类型定义
export interface Change {
  original: string;
  anonymized: string;
  reason: string;
  position: { start: number; end: number };
}

export interface InferenceTest {
  attribute: string;
  before_attack: { guess: string; certainty: number };
  after_attack: { guess: string; certainty: number };
  blocked: boolean;
}

interface DefenderChangesViewProps {
  changes: Change[];
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

export const DefenderChangesView: React.FC<DefenderChangesViewProps> = ({
  changes,
  inferenceTests,
}) => {
  const [expandedChanges, setExpandedChanges] = useState<Set<number>>(new Set([0]));

  const toggleChange = (idx: number) => {
    const newSet = new Set(expandedChanges);
    if (newSet.has(idx)) {
      if (newSet.size > 1) newSet.delete(idx);
    } else {
      newSet.add(idx);
    }
    setExpandedChanges(newSet);
  };

  // 为每个修改添加防御效果信息
  const changesWithDefense = changes.map((change, idx) => {
    // 尝试匹配相关的属性
    let relatedTest = null;
    for (const test of inferenceTests) {
      const attrLabel = AttributeLabel[test.attribute] || test.attribute;
      if (
        change.reason.includes(attrLabel) ||
        change.original.includes(test.before_attack.guess.split(' ')[0])
      ) {
        relatedTest = test;
        break;
      }
    }

    return {
      ...change,
      defenseEffect: relatedTest
        ? {
            blocked: relatedTest.blocked,
            beforeCertainty: relatedTest.before_attack.certainty,
            afterCertainty: relatedTest.after_attack.certainty,
            attribute: relatedTest.attribute,
          }
        : null,
    };
  });

  if (changes.length === 0) {
    return (
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-8 text-center">
        <Shield className="w-12 h-12 text-slate-400 dark:text-slate-600 mx-auto mb-3" />
        <p className="text-slate-600 dark:text-slate-400">未检测到文本修改</p>
        <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">
          文本可能已经安全，或使用了保持原样的策略
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 标题 */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2.5 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg">
          <Shield className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            防御者修改详情
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            LLM如何修改文本以阻止隐私推断
          </p>
        </div>
      </div>

      {/* 修改列表 */}
      {changesWithDefense.map((change, idx) => {
        const isExpanded = expandedChanges.has(idx);
        const defenseEffect = change.defenseEffect;

        return (
          <div
            key={idx}
            className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden transition-all hover:border-emerald-300 dark:hover:border-emerald-700"
          >
            {/* 头部摘要 */}
            <div
              className="p-4 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
              onClick={() => toggleChange(idx)}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  {/* 修改标题 */}
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                      修改 #{idx + 1}
                    </span>
                    {defenseEffect && (
                      <span
                        className={`px-2 py-0.5 text-xs font-semibold rounded ${
                          defenseEffect.blocked
                            ? 'bg-emerald-200 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300'
                            : 'bg-amber-200 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300'
                        }`}
                      >
                        {defenseEffect.blocked ? '✓ 阻御成功' : '⚠️ 部分阻止'}
                      </span>
                    )}
                  </div>

                  {/* 文本对比 */}
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <span className="text-sm text-slate-600 dark:text-slate-400">原文:</span>
                    <span className="px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-900 dark:text-red-100 rounded font-mono text-sm">
                      {change.original}
                    </span>
                    <span className="text-slate-400">→</span>
                    <span className="px-2 py-1 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-900 dark:text-emerald-100 rounded font-mono text-sm">
                      {change.anonymized}
                    </span>
                  </div>

                  {/* 位置信息 */}
                  <div className="text-xs text-slate-500 dark:text-slate-400">
                    位置: 第{change.position.start + 1}-{change.position.end + 1}字符
                  </div>

                  {/* 防御效果 */}
                  {defenseEffect && (
                    <div className="mt-2 text-sm">
                      <span className="text-slate-600 dark:text-slate-400">防御效果: </span>
                      <span className={defenseEffect.blocked ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}>
                        {defenseEffect.blocked
                          ? `置信度 ${defenseEffect.beforeCertainty} → ${defenseEffect.afterCertainty}`
                          : `置信度仍为 ${defenseEffect.afterCertainty}`
                        }
                      </span>
                    </div>
                  )}
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
                  <div className="mt-4 space-y-4">
                    {/* 修改原因 */}
                    <div className="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
                      <div className="flex items-center gap-2 mb-2">
                        <AlertCircle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                        <span className="text-sm font-medium text-amber-900 dark:text-amber-100">
                          修改原因
                        </span>
                      </div>
                      <p className="text-sm text-amber-800 dark:text-amber-200">
                        {change.reason}
                      </p>
                    </div>

                    {/* 防御详情 */}
                    {defenseEffect && (
                      <div className="p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg border border-emerald-200 dark:border-emerald-800">
                        <div className="flex items-center gap-2 mb-2">
                        {defenseEffect.blocked ? (
                          <CheckCircle className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                        ) : (
                          <XCircle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                        )}
                        <span className="text-sm font-medium text-emerald-900 dark:text-emerald-100">
                          防御分析
                        </span>
                      </div>
                      <div className="space-y-2 text-sm text-emerald-800 dark:text-emerald-200">
                        <p>
                          <span className="font-medium">目标属性:</span>{' '}
                          {AttributeLabel[defenseEffect.attribute] || defenseEffect.attribute}
                        </p>
                        <p>
                          <span className="font-medium">攻击前:</span>{' '}
                          攻击者能够推断出"{defenseEffect.beforeCertainty > 3 ? '明确' : '可能'}"的信息
                        </p>
                        <p>
                          <span className="font-medium">防御后:</span>{' '}
                          通过{change.anonymized.includes('[') ? '泛化为占位符' : '重新表述'}降低推断风险
                        </p>
                      </div>
                    </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        );
      })}

      {/* 底部提示 */}
      <div className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <Edit3 className="w-4 h-4 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
        <p className="text-xs text-blue-900 dark:text-blue-100">
          <span className="font-semibold">防御者视角:</span>{' '}
          修改策略包括泛化占位符、删除敏感信息、重新表述等，目标是降低攻击者的推断置信度
        </p>
      </div>
    </div>
  );
};

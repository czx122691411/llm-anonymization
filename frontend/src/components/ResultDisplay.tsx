/**
 * ResultDisplay - 匿名化结果展示组件
 *
 * 展示：
 * - 原文 vs 匿名化文本对比
 * - 修改详情
 * - 质量评估指标
 * - 推理攻击测试结果
 */

import React from 'react';
import { Shield, CheckCircle, XCircle, AlertCircle, FileText, TrendingUp } from 'lucide-react';

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

export interface QualityScores {
  privacy_protection: number;
  utility_preservation: number;
  text_quality: number;
  inference_blocking: number;
}

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

export interface AnonymizationResult {
  original_text: string;
  anonymized_text: string;
  changes: Change[];
  quality_scores: QualityScores;
  inference_tests: InferenceTest[];
  trace_rps_details?: {
    iterations: number;
    reasoning_chains: ReasoningChain[];
    final_certainty: number;
    processing_time: number;
  };
}

interface ResultDisplayProps {
  result: AnonymizationResult;
  methodName: string;
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

export const ResultDisplay: React.FC<ResultDisplayProps> = ({ result, methodName }) => {
  // 处理可能缺失的数据
  const qualityScores = result.quality_scores || {
    privacy_protection: 0,
    utility_preservation: 0,
    text_quality: 0,
    inference_blocking: 0,
  };

  const changes = result.changes || [];
  const inferenceTests = result.inference_tests || [];
  const traceRpsDetails = result.trace_rps_details;

  const getQualityColor = (score: number) => {
    if (score >= 90) return 'text-emerald-600 dark:text-emerald-400';
    if (score >= 70) return 'text-blue-600 dark:text-blue-400';
    if (score >= 50) return 'text-amber-600 dark:text-amber-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getQualityBg = (score: number) => {
    if (score >= 90) return 'bg-emerald-100 dark:bg-emerald-900/30';
    if (score >= 70) return 'bg-blue-100 dark:bg-blue-900/30';
    if (score >= 50) return 'bg-amber-100 dark:bg-amber-900/30';
    return 'bg-red-100 dark:bg-red-900/30';
  };

  return (
    <div className="space-y-6">
      {/* 文本对比 */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <FileText className="w-5 h-5 text-violet-600 dark:text-violet-400" />
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">文本对比</h3>
          </div>
        </div>
        <div className="p-6 space-y-4">
          {/* 原文 */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              原始文本
            </label>
            <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
              <p className="text-sm text-slate-900 dark:text-slate-100 whitespace-pre-wrap">{result.original_text}</p>
            </div>
          </div>

          {/* 匿名化文本 */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              匿名化结果 ({methodName})
            </label>
            <div className="p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg border border-emerald-200 dark:border-emerald-800">
              <p className="text-sm text-slate-900 dark:text-slate-100 whitespace-pre-wrap">{result.anonymized_text}</p>
            </div>
          </div>

          {/* 修改详情 */}
          {changes.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                修改详情 ({changes.length} 处)
              </label>
              <div className="space-y-2">
                {changes.map((change, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <AlertCircle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                      <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                        "{change.original}" → "{change.anonymized}"
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-400 ml-6">{change.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 质量评估指标 */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <Shield className="w-5 h-5 text-violet-600 dark:text-violet-400" />
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">质量评估</h3>
          </div>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className={`p-4 rounded-lg ${getQualityBg(qualityScores.privacy_protection)}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">隐私保护</span>
                <Shield className="w-4 h-4 text-slate-600 dark:text-slate-400" />
              </div>
              <p className={`text-2xl font-bold ${getQualityColor(qualityScores.privacy_protection)}`}>
                {qualityScores.privacy_protection.toFixed(1)}%
              </p>
            </div>

            <div className={`p-4 rounded-lg ${getQualityBg(qualityScores.utility_preservation)}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">效用保持</span>
                <TrendingUp className="w-4 h-4 text-slate-600 dark:text-slate-400" />
              </div>
              <p className={`text-2xl font-bold ${getQualityColor(qualityScores.utility_preservation)}`}>
                {qualityScores.utility_preservation.toFixed(1)}%
              </p>
            </div>

            <div className={`p-4 rounded-lg ${getQualityBg(qualityScores.text_quality)}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">文本质量</span>
                <FileText className="w-4 h-4 text-slate-600 dark:text-slate-400" />
              </div>
              <p className={`text-2xl font-bold ${getQualityColor(qualityScores.text_quality)}`}>
                {qualityScores.text_quality.toFixed(1)}%
              </p>
            </div>

            <div className={`p-4 rounded-lg ${getQualityBg(qualityScores.inference_blocking)}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">推理阻止</span>
                <Shield className="w-4 h-4 text-slate-600 dark:text-slate-400" />
              </div>
              <p className={`text-2xl font-bold ${getQualityColor(qualityScores.inference_blocking)}`}>
                {qualityScores.inference_blocking.toFixed(1)}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 推理攻击测试结果 */}
      {inferenceTests.length > 0 && (
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-3">
              <Shield className="w-5 h-5 text-violet-600 dark:text-violet-400" />
              <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">推理攻击测试</h3>
            </div>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              {inferenceTests.map((test, idx) => (
                <div
                  key={idx}
                  className={`p-4 rounded-lg border ${
                    test.blocked
                      ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800'
                      : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      {test.blocked ? (
                        <CheckCircle className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
                      )}
                      <span className="font-medium text-slate-900 dark:text-slate-100">
                        {AttributeLabel[test.attribute] || test.attribute}
                      </span>
                    </div>
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded ${
                        test.blocked
                          ? 'bg-emerald-200 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300'
                          : 'bg-red-200 dark:bg-red-900/40 text-red-800 dark:text-red-300'
                      }`}
                    >
                      {test.blocked ? '已阻止' : '未阻止'}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-slate-600 dark:text-slate-400 mb-1">攻击前推断:</p>
                      <p className="font-medium text-slate-900 dark:text-slate-100">
                        {test.before_attack.guess} (置信度: {test.before_attack.certainty}/5)
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-600 dark:text-slate-400 mb-1">攻击后推断:</p>
                      <p className="font-medium text-slate-900 dark:text-slate-100">
                        {test.after_attack.guess} (置信度: {test.after_attack.certainty}/5)
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TRACE-RPS 详情 */}
      {traceRpsDetails && (
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-3">
              <TrendingUp className="w-5 h-5 text-violet-600 dark:text-violet-400" />
              <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">TRACE-RPS 详情</h3>
            </div>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">迭代次数</p>
                <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                  {traceRpsDetails.iterations}
                </p>
              </div>
              <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">最终置信度</p>
                <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                  {traceRpsDetails.final_certainty}/5
                </p>
              </div>
              <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">处理时间</p>
                <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                  {traceRpsDetails.processing_time.toFixed(2)}s
                </p>
              </div>
            </div>

            {traceRpsDetails.reasoning_chains && traceRpsDetails.reasoning_chains.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  推理链 ({traceRpsDetails.reasoning_chains.length} 条)
                </label>
                <div className="space-y-3 max-h-60 overflow-y-auto">
                  {traceRpsDetails.reasoning_chains.map((chain, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-lg border ${
                        chain.blocked
                          ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800'
                          : 'bg-violet-50 dark:bg-violet-900/20 border-violet-200 dark:border-violet-800'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-slate-900 dark:text-slate-100">
                          {AttributeLabel[chain.attribute] || chain.attribute}
                        </span>
                        <span className="text-xs text-slate-600 dark:text-slate-400">
                          推断: {chain.target_guess}
                        </span>
                      </div>
                      <div className="space-y-1">
                        {chain.nodes.map((node, nodeIdx) => (
                          <div key={nodeIdx} className="text-sm text-slate-700 dark:text-slate-300 ml-2">
                            <span className="text-xs text-slate-500 dark:text-slate-400">•</span> {node.text}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

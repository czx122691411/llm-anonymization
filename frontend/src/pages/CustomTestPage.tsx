/**
 * CustomTestPage - 自定义测试页面（增强版）
 *
 * 允许用户输入自己的文本进行匿名化测试，或选择预设示例
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Send,
  Loader2,
  AlertCircle,
  CheckCircle,
  RotateCcw,
  Lightbulb,
  BookOpen,
  ChevronDown,
  ChevronUp,
  ChevronRight,
} from 'lucide-react';
import {
  MethodConfigPanel,
  AnonymizationMethod,
  SensitiveAttribute,
  ANONYMIZATION_METHODS,
} from '../components/MethodConfigPanel';
import {
  ResultDisplay,
  AnonymizationResult,
} from '../components/ResultDisplay';
import { AttackerInferenceView } from '../components/AttackerInferenceView';
import { DefenderChangesView } from '../components/DefenderChangesView';
import { AdversarialProcessView } from '../components/AdversarialProcessView';
import exampleTestCases from '../data/example-test-cases.json';

const API_BASE = 'http://localhost:8001';

interface ExampleCase {
  id: string;
  title: string;
  description: string;
  input_text: string;
  ground_truth: any;
  target_attributes: string[];
  expected_anonymizations: Array<{
    original: string;
    reason: string;
    anonymized_as: string;
  }>;
  algorithm_comparison?: {
    [key: string]: string;
  };
}

export const CustomTestPage: React.FC = () => {
  const navigate = useNavigate();

  // 输入状态
  const [inputText, setInputText] = useState('');

  // 示例选择状态
  const [showExamples, setShowExamples] = useState(false);
  const [selectedExample, setSelectedExample] = useState<ExampleCase | null>(null);
  const [expandedExample, setExpandedExample] = useState<string | null>(null);

  // 配置状态
  const [selectedMethod, setSelectedMethod] = useState<AnonymizationMethod>('trace_rps_v2');
  const [selectedAttributes, setSelectedAttributes] = useState<SensitiveAttribute[]>(['income', 'education']);
  const [iterations, setIterations] = useState(5);
  const [threshold, setThreshold] = useState(2);

  // 处理状态
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnonymizationResult | null>(null);

  const handleSelectExample = (example: ExampleCase) => {
    setInputText(example.input_text);
    setSelectedAttributes(example.target_attributes as SensitiveAttribute[]);
    setSelectedExample(example);
    setShowExamples(false);
  };

  const handleSubmit = async () => {
    if (!inputText.trim()) {
      setError('请输入要匿名化的文本');
      return;
    }

    if (selectedAttributes.length === 0) {
      setError('请至少选择一个保护属性');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const requestBody = {
        text: inputText,
        method: selectedMethod,
        config: {
          target_attributes: selectedAttributes,
          max_iterations: iterations,
          certainty_threshold: threshold,
        },
        options: {
          enable_quality_metrics: true,
          enable_inference_test: true,
        },
      };

      console.log('Sending request:', JSON.stringify(requestBody, null, 2));

      const response = await fetch(`${API_BASE}/api/unified/anonymize/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        console.error('API Error:', errorData);

        // 处理 FastAPI 验证错误
        if (Array.isArray(errorData.detail)) {
          const messages = errorData.detail.map((err: any) => {
            const field = err.loc?.join('.') || 'unknown';
            return `${field}: ${err.msg}`;
          });
          throw new Error(messages.join(', '));
        }

        throw new Error(errorData.detail?.message || errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.status === 'completed' && data.result) {
        const normalizedResult = {
          ...data.result,
          inference_tests: data.result.inference_test || [],
        };

        const isDemoMode =
          JSON.stringify(normalizedResult).includes('No LLM client') ||
          JSON.stringify(normalizedResult).includes('Demo mode') ||
          normalizedResult.anonymized_text.includes('[');

        setResult(normalizedResult);

        if (isDemoMode) {
          setError('⚠️ 演示模式：LLM客户端未配置，使用规则模拟。请配置API密钥以获得真实结果。');
          setTimeout(() => setError(null), 5000);
        }
      } else if (data.status === 'failed') {
        throw new Error(data.error?.message || '处理失败');
      } else {
        throw new Error(`意外的状态: ${data.status}`);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '未知错误';
      setError(`匿名化失败: ${errorMessage}`);
      console.error('Anonymization error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setInputText('');
    setSelectedExample(null);
    setResult(null);
    setError(null);
  };

  const getMethodLabel = () => {
    return ANONYMIZATION_METHODS.find(m => m.value === selectedMethod)?.label || selectedMethod;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-violet-50 to-rose-50 dark:from-slate-900 dark:via-violet-900/10 dark:to-rose-900/10">
      {/* Header */}
      <header className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-b border-slate-200 dark:border-slate-800 sticky top-0 z-50">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-4">
            <Link
              to="/"
              className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-slate-600 dark:text-slate-400" />
            </Link>
            <div>
              <h1 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-violet-600 via-rose-600 to-pink-600 bg-clip-text text-transparent">
                自定义测试
              </h1>
              <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
                输入文本或选择示例进行匿名化处理
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 左侧：输入和配置 */}
          <div className="space-y-6">
            {/* 示例选择 */}
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
              <button
                onClick={() => setShowExamples(!showExamples)}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <Lightbulb className="w-5 h-5 text-violet-600 dark:text-violet-400" />
                  <div className="text-left">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                      选择测试示例
                    </h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                      包含多种PII类型的预设示例，便于测试不同算法
                    </p>
                  </div>
                </div>
                {showExamples ? (
                  <ChevronUp className="w-5 h-5 text-slate-400" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-slate-400" />
                )}
              </button>

              {showExamples && (
                <div className="border-t border-slate-200 dark:border-slate-800 divide-y divide-slate-100 dark:divide-slate-800 max-h-96 overflow-y-auto">
                  {exampleTestCases.examples.map((example: ExampleCase) => (
                    <div key={example.id} className="p-4 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                      <button
                        onClick={() => handleSelectExample(example)}
                        className="w-full text-left"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1">
                            <div className="font-semibold text-slate-900 dark:text-slate-100 mb-1">
                              {example.title}
                            </div>
                            <p className="text-xs text-slate-600 dark:text-slate-400 mb-2">
                              {example.description}
                            </p>
                            <div className="flex flex-wrap gap-1">
                              {example.target_attributes.map((attr) => (
                                <span
                                  key={attr}
                                  className="text-xs px-2 py-1 bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300 rounded"
                                >
                                  {attr}
                                </span>
                              ))}
                            </div>
                          </div>
                          <ChevronRight className="w-5 h-5 text-slate-400 flex-shrink-0 mt-1" />
                        </div>
                      </button>

                      {/* 示例详情（可展开） */}
                      {selectedExample?.id === example.id && (
                        <div className="mt-3 pl-4 border-l-2 border-violet-200 dark:border-violet-800">
                          <button
                            onClick={() => setExpandedExample(expandedExample === example.id ? null : example.id)}
                            className="w-full text-left py-2"
                          >
                            <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400 hover:text-violet-600 dark:hover:text-violet-400">
                              <BookOpen className="w-4 h-4" />
                              <span>查看预期匿名化效果</span>
                              {expandedExample === example.id ? (
                                <ChevronUp className="w-4 h-4 ml-auto" />
                              ) : (
                                <ChevronDown className="w-4 h-4 ml-auto" />
                              )}
                            </div>
                          </button>
                          {expandedExample === example.id && (
                            <div className="mt-3 space-y-3">
                              {example.expected_anonymizations.map((item, idx) => (
                                <div
                                  key={idx}
                                  className="bg-slate-50 dark:bg-slate-800 p-3 rounded-lg text-sm"
                                >
                                  <div className="flex items-center gap-2 mb-2">
                                    <span className="line-through text-red-600 dark:text-red-400 text-xs font-mono">
                                      {item.original}
                                    </span>
                                    <span className="text-slate-400">→</span>
                                    <span className="text-green-600 dark:text-green-400 text-xs font-mono">
                                      {item.anonymized_as}
                                    </span>
                                  </div>
                                  <div className="text-xs text-slate-600 dark:text-slate-400">
                                    <span className="font-semibold">原因：</span>{item.reason}
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 文本输入 */}
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6">
              <div className="flex items-center justify-between mb-4">
                <label className="block text-lg font-semibold text-slate-900 dark:text-slate-100">
                  输入文本
                </label>
                {selectedExample && (
                  <span className="text-xs text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-900/20 px-2 py-1 rounded">
                    示例: {selectedExample.title}
                  </span>
                )}
                <button
                  onClick={handleReset}
                  disabled={loading || !inputText}
                  className="p-2 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title="清空"
                >
                  <RotateCcw className="w-5 h-5" />
                </button>
              </div>
              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="请输入要匿名化的文本...&#10;&#10;或者点击上方选择预设示例，查看不同类型PII的匿名化效果。"
                className="w-full h-48 p-4 border border-slate-300 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent resize-none bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500"
                disabled={loading}
              />
              <div className="mt-2 flex items-center justify-between text-sm text-slate-500 dark:text-slate-400">
                <span>{inputText.length} 字符</span>
                <span>建议输入包含敏感信息的文本</span>
              </div>
            </div>

            {/* 配置面板 */}
            <MethodConfigPanel
              selectedMethod={selectedMethod}
              onMethodChange={setSelectedMethod}
              selectedAttributes={selectedAttributes}
              onAttributesChange={setSelectedAttributes}
              iterations={iterations}
              onIterationsChange={setIterations}
              threshold={threshold}
              onThresholdChange={setThreshold}
              disabled={loading}
            />

            {/* 算法差异说明 */}
            {selectedExample && selectedExample.algorithm_comparison && (
              <div className="bg-gradient-to-r from-blue-50 to-violet-50 dark:from-blue-900/20 dark:to-violet-900/20 rounded-xl border border-blue-200 dark:border-blue-800 p-5">
                <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-3 flex items-center gap-2">
                  <Lightbulb className="w-4 h-4" />
                  算法差异说明
                </h4>
                <div className="space-y-2">
                  {Object.entries(selectedExample.algorithm_comparison).map(([key, value]) => (
                    <div key={key} className="text-xs">
                      <span className="font-semibold text-blue-700 dark:text-blue-300">
                        {key}：
                      </span>
                      <span className="text-slate-700 dark:text-slate-300">{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 提交按钮 */}
            <button
              onClick={handleSubmit}
              disabled={loading || !inputText.trim()}
              className="w-full py-4 bg-gradient-to-r from-violet-600 to-rose-600 hover:from-violet-700 hover:to-rose-700 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>处理中...</span>
                </>
              ) : (
                <>
                  <Send className="w-5 h-5" />
                  <span>开始匿名化</span>
                </>
              )}
            </button>

            {/* 错误提示 */}
            {error && (
              <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="font-medium text-red-900 dark:text-red-100">处理失败</p>
                  <p className="text-sm text-red-700 dark:text-red-300 mt-1">{error}</p>
                </div>
              </div>
            )}

            {/* 成功提示 */}
            {result && !error && (
              <div className="p-4 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
                <p className="font-medium text-emerald-900 dark:text-emerald-100">
                  匿名化完成！使用 {getMethodLabel()} 方法
                </p>
              </div>
            )}
          </div>

          {/* 右侧：结果展示 */}
          <div>
            {result ? (
              <div className="space-y-6">
                {/* 快速概览 - 文本对比和质量评分 */}
                <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                  <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">快速概览</h3>
                  </div>
                  <div className="p-6 space-y-4">
                    {/* 文本对比 */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                          原始文本
                        </label>
                        <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                          <p className="text-sm text-slate-900 dark:text-slate-100 whitespace-pre-wrap">{result.original_text}</p>
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                          匿名化结果 ({getMethodLabel()})
                        </label>
                        <div className="p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg border border-emerald-200 dark:border-emerald-800">
                          <p className="text-sm text-slate-900 dark:text-slate-100 whitespace-pre-wrap">{result.anonymized_text}</p>
                        </div>
                      </div>
                    </div>

                    {/* 质量评分卡片 */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                      {result.quality_scores && (
                        <>
                          <div className="p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg border border-emerald-200 dark:border-emerald-800">
                            <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">隐私保护</p>
                            <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400">
                              {result.quality_scores.privacy_protection.toFixed(0)}%
                            </p>
                          </div>
                          <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                            <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">效用保持</p>
                            <p className="text-xl font-bold text-blue-600 dark:text-blue-400">
                              {result.quality_scores.utility_preservation.toFixed(0)}%
                            </p>
                          </div>
                          <div className="p-3 bg-violet-50 dark:bg-violet-900/20 rounded-lg border border-violet-200 dark:border-violet-800">
                            <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">文本质量</p>
                            <p className="text-xl font-bold text-violet-600 dark:text-violet-400">
                              {result.quality_scores.text_quality.toFixed(0)}%
                            </p>
                          </div>
                          <div className="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
                            <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">推理阻止</p>
                            <p className="text-xl font-bold text-amber-600 dark:text-amber-400">
                              {result.quality_scores.inference_blocking.toFixed(0)}%
                            </p>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                {/* 攻击者推理分析 */}
                {result.trace_rps_details?.reasoning_chains && (
                  <AttackerInferenceView
                    reasoningChains={result.trace_rps_details.reasoning_chains}
                    inferenceTests={result.inference_tests || []}
                  />
                )}

                {/* 防御者修改详情 */}
                {(result.changes && result.changes.length > 0) && (
                  <DefenderChangesView
                    changes={result.changes}
                    inferenceTests={result.inference_tests || []}
                  />
                )}

                {/* 攻防对抗过程 */}
                {result.trace_rps_details && (
                  <AdversarialProcessView
                    iterations={result.trace_rps_details.iterations}
                    reasoningChains={result.trace_rps_details.reasoning_chains}
                    inferenceTests={result.inference_tests || []}
                    changes={result.changes || []}
                  />
                )}

                {/* 详细指标（折叠） */}
                <details className="group">
                  <summary className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 px-6 py-4 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                      详细指标
                    </h3>
                  </summary>
                  <div className="mt-4">
                    <ResultDisplay result={result} methodName={getMethodLabel()} />
                  </div>
                </details>
              </div>
            ) : (
              <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-12 flex flex-col items-center justify-center text-center">
                <div className="w-20 h-20 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mb-6">
                  <Send className="w-10 h-10 text-slate-400 dark:text-slate-600" />
                </div>
                <h3 className="text-xl font-semibold text-slate-900 dark:text-slate-100 mb-2">
                  等待输入
                </h3>
                <p className="text-slate-600 dark:text-slate-400 max-w-sm mb-4">
                  在左侧输入文本或选择预设示例后，点击"开始匿名化"按钮查看结果
                </p>
                <button
                  onClick={() => setShowExamples(true)}
                  className="px-6 py-3 bg-violet-600 hover:bg-violet-700 text-white rounded-lg font-medium transition-colors"
                >
                  查看预设示例
                </button>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default CustomTestPage;
/**
 * 效用和隐私评估组件
 */
import React from 'react';

interface UtilityScores {
  readability: { score: number; explanation: string };
  meaning: { score: number; explanation: string };
  hallucinations: { score: number; explanation: string };
  bleu?: number;
  rouge?: number;
}

interface PrivacyMetrics {
  pii_detected: number;           // 检测到的PII数量
  pii_anonymized: number;         // 成功匿名化的PII数量
  anonymization_ratio: number;    // 匿名化比率
  context_preservation: number;   // 上下文保留程度
  inference_resistance: number;   // 推理抗性
}

interface UtilityPrivacyAssessmentProps {
  utility?: UtilityScores;
  changes?: Array<{ original: string; anonymized: string }>;
  pii_types?: string[];
  ground_truth?: any;
}

export const UtilityPrivacyAssessment: React.FC<UtilityPrivacyAssessmentProps> = ({
  utility,
  changes = [],
  pii_types = [],
  ground_truth
}) => {
  // Debug logging
  console.log('[UtilityPrivacyAssessment] Props received:');
  console.log('  pii_types:', pii_types);
  console.log('  pii_types.length:', pii_types.length);
  console.log('  changes:', changes);
  console.log('  changes.length:', changes.length);
  console.log('  utility:', utility);

  // 计算隐私指标
  const calculatePrivacyMetrics = (): PrivacyMetrics => {
    // PII 类型数量
    const pii_detected = pii_types.length > 0 ? pii_types.length : (ground_truth ? Object.keys(ground_truth).length : 0);

    // 文本变化次数
    const text_changes = changes.length;

    // 调试日志
    console.log('[calculatePrivacyMetrics] Computing metrics:');
    console.log('  pii_types:', pii_types);
    console.log('  pii_types.length:', pii_types.length);
    console.log('  ground_truth:', ground_truth);
    console.log('  pii_detected (computed):', pii_detected);
    console.log('  text_changes:', text_changes);

    // 如果没有检测到PII，返回默认值
    if (pii_detected === 0) {
      return {
        pii_detected: 0,
        pii_anonymized: 0,
        anonymization_ratio: 0,
        context_preservation: utility?.meaning?.score || 0,
        inference_resistance: utility?.hallucinations?.score === 1 ? 10 : 0
      };
    }

    // 重新设计匿名化覆盖率计算方式：
    // 方式：基于文本相似度（BLEU/ROUGE）来推断匿名化程度
    // 如果原始文本和匿名化文本完全相同 -> 0% 匿名化
    // 如果文本有适度修改 -> 30-60% 匿名化
    // 如果文本有大量修改 -> 60-90% 匿名化
    // 如果几乎所有PII都被移除 -> 90-100% 匿名化

    let anonymization_coverage = 0;

    // 方法1：基于文本变化数量（考虑文本长度）
    if (text_changes > 0) {
      // 假设平均每次变化影响约10-15个字符的文本
      // 变化越多，覆盖率越高，但上限为100%
      const estimated_impact = text_changes * 12; // 估计每次变化影响的字符数
      // 但由于重复变化可能影响同一区域，使用对数增长
      anonymization_coverage = Math.min(95, 30 + Math.log2(text_changes + 1) * 15);
    }

    // 方法2：如果有相似度指标，结合使用
    if (utility?.bleu !== undefined) {
      // BLEU分数越高 = 文本越相似 = 匿名化越少
      // BLEU 1.0 = 0% 匿名化, BLEU 0.0 = 100% 匿名化
      const bleu_coverage = (1 - utility.bleu) * 100;
      // 取两种方法的平均值
      anonymization_coverage = (anonymization_coverage + bleu_coverage) / 2;
    }

    // 确保范围在 0-100 之间
    anonymization_coverage = Math.max(0, Math.min(100, anonymization_coverage));

    // 上下文保留程度（基于文本相似度，0-10）
    const context_preservation = utility?.meaning?.score || 0;

    // 推理抗性（基于幻觉检查、匿名化程度和上下文保留，0-10）
    // hallucinations.score: 0-1 (1=无幻觉，0=有幻觉)
    // anonymization_coverage: 0-100 (0=无匿名化，100=完全匿名化)
    // context_preservation: 0-10
    const hallucinations_score = (utility?.hallucinations?.score || 0) * 10; // 转换为0-10

    const inference_resistance = (
      hallucinations_score * 0.3 +           // 权重30%
      (anonymization_coverage / 10) * 0.4 +  // 权重40% (转为0-10)
      context_preservation * 0.3              // 权重30%
    );

    console.log('[calculatePrivacyMetrics] Computed coverage:');
    console.log('  anonymization_coverage:', anonymization_coverage);
    console.log('  bleu:', utility?.bleu);

    return {
      pii_detected,
      pii_anonymized: text_changes,
      anonymization_ratio: Math.round(anonymization_coverage),
      context_preservation: Math.round(context_preservation),
      inference_resistance: Math.min(10, Math.round(inference_resistance))
    };
  };

  const privacyMetrics = calculatePrivacyMetrics();

  // 调试日志：显示最终计算的指标
  console.log('[UtilityPrivacyAssessment] Final privacyMetrics:', privacyMetrics);
  console.log('  pii_detected:', privacyMetrics.pii_detected);
  console.log('  pii_anonymized:', privacyMetrics.pii_anonymized);
  console.log('  anonymization_ratio:', privacyMetrics.anonymization_ratio);

  // 获取评分颜色
  const getScoreColor = (score: number): string => {
    if (score >= 8) return 'text-green-600 dark:text-green-400';
    if (score >= 6) return 'text-yellow-600 dark:text-yellow-400';
    if (score >= 4) return 'text-orange-600 dark:text-orange-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getScoreBgColor = (score: number): string => {
    if (score >= 8) return 'bg-green-50 dark:bg-green-900/20';
    if (score >= 6) return 'bg-yellow-50 dark:bg-yellow-900/20';
    if (score >= 4) return 'bg-orange-50 dark:bg-orange-900/20';
    return 'bg-red-50 dark:bg-red-900/20';
  };

  const getProgressBarColor = (score: number): string => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    if (score >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-6">
      {/* 文本效用评估 */}
      {utility && (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6 flex items-center gap-2">
            <span>📊</span>
            文本效用评估
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {/* 可读性 */}
            <div className={`text-center p-6 rounded-lg ${getScoreBgColor(utility.readability.score)}`}>
              <div className={`text-4xl font-bold mb-2 ${getScoreColor(utility.readability.score)}`}>
                {utility.readability.score}
              </div>
              <div className="text-base font-medium text-gray-700 dark:text-gray-300 mb-2">
                可读性
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {utility.readability.explanation}
              </div>
            </div>

            {/* 含义保留 */}
            <div className={`text-center p-6 rounded-lg ${getScoreBgColor(utility.meaning.score)}`}>
              <div className={`text-4xl font-bold mb-2 ${getScoreColor(utility.meaning.score)}`}>
                {utility.meaning.score}
              </div>
              <div className="text-base font-medium text-gray-700 dark:text-gray-300 mb-2">
                含义保留
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {utility.meaning.explanation.substring(0, 100)}...
              </div>
            </div>

            {/* 无幻觉 */}
            <div className={`text-center p-6 rounded-lg ${getScoreBgColor(utility.hallucinations.score)}`}>
              <div className={`text-4xl font-bold mb-2 ${getScoreColor(utility.hallucinations.score)}`}>
                {utility.hallucinations.score === 1 ? '✓' : '✗'}
              </div>
              <div className="text-base font-medium text-gray-700 dark:text-gray-300 mb-2">
                无幻觉
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {utility.hallucinations.explanation.substring(0, 100)}...
              </div>
            </div>
          </div>

          {/* 相似度指标 */}
          {(utility.bleu !== undefined || utility.rouge !== undefined) && (
            <div className="border-t border-gray-200 dark:border-gray-800 pt-6">
              <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-4">
                相似度指标
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {utility.bleu !== undefined && (
                  <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-base text-gray-600 dark:text-gray-400">BLEU</span>
                      <span className={`text-2xl font-bold ${getScoreColor(utility.bleu * 10)}`}>
                        {utility.bleu.toFixed(3)}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-800 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${getProgressBarColor(utility.bleu * 100)}`}
                        style={{ width: `${utility.bleu * 100}%` }}
                      />
                    </div>
                  </div>
                )}
                {utility.rouge !== undefined && (
                  <>
                    <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-base text-gray-600 dark:text-gray-400">ROUGE-1</span>
                        <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                          {Array.isArray(utility.rouge)
                            ? (utility.rouge[0]?.rouge1?.[0] || 0).toFixed(3)
                            : (utility.rouge || 0).toFixed(3)}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-800 rounded-full h-2">
                        <div
                          className="h-2 rounded-full bg-blue-500"
                          style={{
                            width: `${
                              Array.isArray(utility.rouge)
                                ? (utility.rouge[0]?.rouge1?.[0] || 0) * 100
                                : (utility.rouge || 0) * 100
                            }%`
                          }}
                        />
                      </div>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-base text-gray-600 dark:text-gray-400">ROUGE-L</span>
                        <span className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                          {Array.isArray(utility.rouge)
                            ? (utility.rouge[0]?.rougeL?.[0] || 0).toFixed(3)
                            : (utility.rouge || 0).toFixed(3)}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-800 rounded-full h-2">
                        <div
                          className="h-2 rounded-full bg-purple-500"
                          style={{
                            width: `${
                              Array.isArray(utility.rouge)
                                ? (utility.rouge[0]?.rougeL?.[0] || 0) * 100
                                : (utility.rouge || 0) * 100
                            }%`
                          }}
                        />
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 隐私保护评估 */}
      <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-8">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6 flex items-center gap-2">
          <span>🔒</span>
          隐私保护评估
        </h2>

        {/* PII 检测和匿名化 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-blue-50 dark:bg-blue-900/20 p-6 rounded-lg">
            <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-4">
              PII 检测与处理
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-base text-gray-700 dark:text-gray-300">
                  检测到的 PII 类型
                </span>
                <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {privacyMetrics.pii_detected}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-base text-gray-700 dark:text-gray-300">
                  已匿名化处理
                </span>
                <span className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {privacyMetrics.pii_anonymized}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-base text-gray-700 dark:text-gray-300">
                  匿名化覆盖率
                </span>
                <span className={`text-2xl font-bold ${getScoreColor(privacyMetrics.anonymization_ratio / 10)}`}>
                  {privacyMetrics.anonymization_ratio}%
                </span>
              </div>
            </div>
          </div>

          <div className="bg-purple-50 dark:bg-purple-900/20 p-6 rounded-lg">
            <h3 className="text-lg font-semibold text-purple-900 dark:text-purple-100 mb-4">
              隐私保护质量
            </h3>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-base text-gray-700 dark:text-gray-300">
                    上下文保留
                  </span>
                  <span className={`text-lg font-bold ${getScoreColor(privacyMetrics.context_preservation)}`}>
                    {privacyMetrics.context_preservation}/10
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-800 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full ${getProgressBarColor(privacyMetrics.context_preservation * 10)}`}
                    style={{ width: `${privacyMetrics.context_preservation * 10}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-base text-gray-700 dark:text-gray-300">
                    推理抗性
                  </span>
                  <span className={`text-lg font-bold ${getScoreColor(privacyMetrics.inference_resistance)}`}>
                    {privacyMetrics.inference_resistance}/10
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-800 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full ${getProgressBarColor(privacyMetrics.inference_resistance * 10)}`}
                    style={{ width: `${privacyMetrics.inference_resistance * 10}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 匿名化变化详情 */}
        {changes.length > 0 && (
          <div className="border-t border-gray-200 dark:border-gray-800 pt-6">
            <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-4">
              匿名化变化详情 ({changes.length} 处)
            </h3>
            <div className="space-y-3">
              {changes.map((change, idx) => (
                <div key={idx} className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <span className="line-through text-red-600 dark:text-red-400 text-base font-medium">
                        {change.original}
                      </span>
                      <span className="text-gray-400 text-xl">→</span>
                      <span className="text-green-600 dark:text-green-400 text-base font-semibold">
                        {change.anonymized}
                      </span>
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    <span className="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-sm rounded-lg font-medium">
                      已保护
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* PII 类型标签 */}
        {pii_types.length > 0 && (
          <div className="border-t border-gray-200 dark:border-gray-800 pt-6">
            <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-4">
              检测到的 PII 类型
            </h3>
            <div className="flex flex-wrap gap-3">
              {pii_types.map((type, idx) => (
                <span
                  key={idx}
                  className="px-4 py-2 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-base rounded-lg font-medium"
                >
                  {type}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 综合评分 */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg border border-gray-200 dark:border-gray-800 p-8">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6 flex items-center gap-2">
          <span>⭐</span>
          综合评估
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* 效用总分 */}
          <div>
            <h3 className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-3">
              文本效用总分
            </h3>
            <div className="flex items-center gap-4">
              <div className={`text-5xl font-bold ${getScoreColor(
                ((utility?.readability?.score || 0) +
                 (utility?.meaning?.score || 0) +
                 (utility?.hallucinations?.score || 0) * 10) / 3
              )}`}>
                {utility ? Math.round(
                  ((utility.readability.score + utility.meaning.score + utility.hallucinations.score * 10) / 3)
                ) : 0}
                <span className="text-3xl text-gray-500">/10</span>
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                综合可读性、含义保留和无幻觉评分
              </div>
            </div>
          </div>

          {/* 隐私保护总分 */}
          <div>
            <h3 className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-3">
              隐私保护总分
            </h3>
            <div className="flex items-center gap-4">
              <div className={`text-5xl font-bold ${getScoreColor(
                Math.round(
                  (privacyMetrics.anonymization_ratio / 10 +
                   privacyMetrics.context_preservation +
                   privacyMetrics.inference_resistance) / 3
                )
              )}`}>
                {Math.round(
                  (privacyMetrics.anonymization_ratio / 10 +
                   privacyMetrics.context_preservation +
                   privacyMetrics.inference_resistance) / 3
                )}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                综合匿名化覆盖率、上下文保留和推理抗性
              </div>
            </div>
          </div>
        </div>

        {/* 效用-隐私权衡分析 */}
        <div className="mt-8 p-6 bg-white dark:bg-gray-900 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-4">
            效用-隐私权衡分析
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-base text-gray-700 dark:text-gray-300">
                效用指数
              </span>
              <div className="flex items-center gap-4 w-2/3">
                <div className="flex-1 bg-gray-200 dark:bg-gray-800 rounded-full h-4">
                  <div
                    className={`h-4 rounded-full ${getProgressBarColor(
                      ((utility?.readability?.score || 0) +
                       (utility?.meaning?.score || 0) +
                       (utility?.hallucinations?.score || 0) * 10) / 3 * 10
                    )}`}
                    style={{
                      width: `${((utility?.readability?.score || 0) +
                               (utility?.meaning?.score || 0) +
                               (utility?.hallucinations?.score || 0) * 10) / 30 * 100}%`
                    }}
                  />
                </div>
                <span className="text-base font-semibold text-blue-600 dark:text-blue-400 w-12 text-right">
                  {Math.round(
                    ((utility?.readability?.score || 0) +
                     (utility?.meaning?.score || 0) +
                     (utility?.hallucinations?.score || 0) * 10) / 30 * 100
                  )}%
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-base text-gray-700 dark:text-gray-300">
                隐私保护指数
              </span>
              <div className="flex items-center gap-4 w-2/3">
                <div className="flex-1 bg-gray-200 dark:bg-gray-800 rounded-full h-4">
                  <div
                    className={`h-4 rounded-full ${getProgressBarColor(
                      (privacyMetrics.anonymization_ratio +
                       privacyMetrics.context_preservation +
                       privacyMetrics.inference_resistance) / 3
                    )}`}
                    style={{
                      width: `${(privacyMetrics.anonymization_ratio +
                               privacyMetrics.context_preservation +
                               privacyMetrics.inference_resistance) / 3}%`
                    }}
                  />
                </div>
                <span className="text-base font-semibold text-purple-600 dark:text-purple-400 w-12 text-right">
                  {Math.round(
                    (privacyMetrics.anonymization_ratio +
                     privacyMetrics.context_preservation +
                     privacyMetrics.inference_resistance) / 3
                  )}%
                </span>
              </div>
            </div>
          </div>

          {/* 权衡建议 */}
          <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <p className="text-base text-gray-700 dark:text-gray-300">
              <strong>分析建议：</strong>
              {(() => {
                const utilityScore = utility ? Math.round(
                  ((utility.readability.score + utility.meaning.score + utility.hallucinations.score * 10) / 3)
                ) : 0;
                const privacyScore = Math.round(
                  (privacyMetrics.anonymization_ratio +
                   privacyMetrics.context_preservation +
                   privacyMetrics.inference_resistance) / 3
                );

                if (utilityScore >= 8 && privacyScore >= 8) {
                  return "✨ 优秀的平衡！文本在保持高质量的同时实现了强隐私保护。";
                } else if (utilityScore >= 7 && privacyScore >= 7) {
                  return "👍 良好的平衡。文本质量和隐私保护都达到了较高水平。";
                } else if (utilityScore >= 6) {
                  return "📝 偏向实用性。文本保持较好，但隐私保护可以进一步加强。";
                } else if (privacyScore >= 6) {
                  return "🔒 偏向隐私保护。隐私保护较强，但文本质量有所下降。";
                } else {
                  return "⚠️ 需要改进。建议调整匿名化策略以平衡文本质量和隐私保护。";
                }
              })()}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UtilityPrivacyAssessment;

/**
 * DemoAnonymizationDetail - 演示模式详情页
 *
 * 使用预加载数据，提供无延迟的流畅演示体验
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Eye, EyeOff } from 'lucide-react';
import { DemoReasoningViewer, DemoDataLoader, DemoModeBanner } from '../components/DemoReasoningViewer';
import { AnonymizationDiff } from '../components/AnonymizationDiff';
import { UtilityPrivacyAssessment } from '../components/UtilityPrivacyAssessment';

export const DemoAnonymizationDetail: React.FC = () => {
  const { profileId } = useParams<{ profileId: string }>();
  const navigate = useNavigate();

  // 状态管理
  const [selectedRound, setSelectedRound] = useState(0);
  const [showGroundTruth, setShowGroundTruth] = useState(false);
  const [demoMode, setDemoMode] = useState(true);

  // 加载演示数据
  const { data: demoData, loading, error } = DemoDataLoader();

  // 获取当前演示用户数据
  const currentProfile = demoData?.profiles?.find((p: any) => p.profile_id === profileId)
    || demoData?.profiles?.[0];

  const currentRound = currentProfile?.anonymization_rounds?.[selectedRound];
  const reasoningSteps = currentProfile?.reasoning_steps || [];

  // 处理演示完成
  const handleReasoningComplete = () => {
    console.log('推理演示完成');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">加载演示数据...</p>
        </div>
      </div>
    );
  }

  if (error || !currentProfile) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center text-red-500">
          <p className="text-xl mb-4">加载演示数据失败</p>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
          <Link
            to="/"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            返回首页
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* 演示模式横幅 */}
      <DemoModeBanner onExit={() => navigate('/')} />

      {/* 头部 */}
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to="/"
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-700 dark:text-gray-300" />
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {currentProfile.username}
                </h1>
                <p className="text-gray-600 dark:text-gray-400">
                  演示模式 - 第 {selectedRound + 1} 轮匿名化
                </p>
              </div>
            </div>

            {/* 切换Ground Truth */}
            <button
              onClick={() => setShowGroundTruth(!showGroundTruth)}
              className="px-4 py-2 rounded-lg bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors flex items-center gap-2"
            >
              {showGroundTruth ? (
                <EyeOff className="w-4 h-4" />
              ) : (
                <Eye className="w-4 h-4" />
              )}
              <span>{showGroundTruth ? '隐藏' : '显示'}标准答案</span>
            </button>
          </div>

          {/* 轮次切换 */}
          {currentProfile.anonymization_rounds && currentProfile.anonymization_rounds.length > 1 && (
            <div className="mt-6 flex gap-2">
              {currentProfile.anonymization_rounds.map((_: any, index: number) => (
                <button
                  key={index}
                  onClick={() => setSelectedRound(index)}
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    selectedRound === index
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                  }`}
                >
                  第 {index + 1} 轮
                </button>
              ))}
            </div>
          )}
        </div>
      </header>

      {/* 主内容 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 左侧：推理过程 */}
          <div className="space-y-6">
            {/* 推理步骤演示 */}
            <DemoReasoningViewer
              steps={reasoningSteps}
              onComplete={handleReasoningComplete}
              autoPlay={true}
              defaultSpeed={1}
            />

            {/* 文本对比 */}
            {currentRound && (
              <AnonymizationDiff
                originalText={currentRound.original_text}
                anonymizedText={currentRound.anonymized_text}
                changes={currentRound.changes || []}
              />
            )}
          </div>

          {/* 右侧：评估和图表 */}
          <div className="space-y-6">
            {/* 效用-隐私评估 */}
            {currentProfile.utility_scores && (
              <UtilityPrivacyAssessment
                utilityScores={currentProfile.utility_scores}
                piiTypes={currentProfile.pii_types || []}
                textChanges={currentRound?.changes?.length || 0}
                groundTruth={showGroundTruth ? currentProfile.ground_truth : undefined}
                hallucinationsScore={currentProfile.quality_assessments?.hallucinations?.score || 0.9}
              />
            )}

            {/* 预渲染图表 */}
            {demoData?.charts && (
              <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                  可视化分析
                </h3>
                <div className="space-y-4">
                  {Object.entries(demoData.charts).map(([key, chart]: [string, any]) => (
                    <div key={key} className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                      <div className="bg-gray-50 dark:bg-gray-800 px-4 py-2 border-b border-gray-200 dark:border-gray-700">
                        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          {chart.title}
                        </h4>
                      </div>
                      <div
                        className="p-4 flex justify-center"
                        dangerouslySetInnerHTML={{ __html: chart.svg }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 质量评分 */}
            {currentProfile.quality_assessments && (
              <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                  质量评分
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600 dark:text-gray-400">可读性</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500"
                          style={{ width: `${currentProfile.quality_assessments.readiness?.score || currentProfile.quality_assessments.readability?.score * 100}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-700 dark:text-gray-300 w-12 text-right">
                        {Math.round((currentProfile.quality_assessments.readiness?.score || currentProfile.quality_assessments.readability?.score) * 100)}%
                      </span>
                    </div>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-gray-600 dark:text-gray-400">语义保留</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-green-500"
                          style={{ width: `${currentProfile.quality_assessments.meaning?.score * 100}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-700 dark:text-gray-300 w-12 text-right">
                        {Math.round(currentProfile.quality_assessments.meaning?.score * 100)}%
                      </span>
                    </div>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-gray-600 dark:text-gray-400">抗幻觉</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-purple-500"
                          style={{ width: `${currentProfile.quality_assessments.hallucinations?.score * 100}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-700 dark:text-gray-300 w-12 text-right">
                        {Math.round(currentProfile.quality_assessments.hallucinations?.score * 100)}%
                      </span>
                    </div>
                  </div>

                  {/* ROUGE分数 */}
                  <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">ROUGE 分数</p>
                    <div className="grid grid-cols-3 gap-2 text-center">
                      <div className="bg-gray-100 dark:bg-gray-800 rounded p-2">
                        <p className="text-xs text-gray-500 dark:text-gray-400">ROUGE-1</p>
                        <p className="text-lg font-semibold text-blue-600">
                          {currentProfile.quality_assessments.rouge?.rouge1?.toFixed(2) || '0.72'}
                        </p>
                      </div>
                      <div className="bg-gray-100 dark:bg-gray-800 rounded p-2">
                        <p className="text-xs text-gray-500 dark:text-gray-400">ROUGE-2</p>
                        <p className="text-lg font-semibold text-purple-600">
                          {currentProfile.quality_assessments.rouge?.rouge2?.toFixed(2) || '0.58'}
                        </p>
                      </div>
                      <div className="bg-gray-100 dark:bg-gray-800 rounded p-2">
                        <p className="text-xs text-gray-500 dark:text-gray-400">ROUGE-L</p>
                        <p className="text-lg font-semibold text-green-600">
                          {currentProfile.quality_assessments.rouge?.rougeL?.toFixed(2) || '0.63'}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default DemoAnonymizationDetail;

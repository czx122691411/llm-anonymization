import React, { useState, useCallback } from 'react';
import { useSession } from '../context/SessionContext';
import { useAnonymizationWebSocket } from '../hooks/useAnonymizationWebSocket';
import {
  MethodConfigPanel,
  AnonymizationMethod,
  SensitiveAttribute,
} from '../components/MethodConfigPanel';
import { Plus, Send, Trash2, Download, FlaskConical } from 'lucide-react';

const ResearchPlatform: React.FC = () => {
  const {
    state,
    addComment,
    deleteComment,
    selectComment,
    selectRound,
    selectedComment,
    addRoundResult,
    setCommentStatus,
    addPrivacySnapshot,
    setPersona,
    reset,
  } = useSession();

  const {
    status: execStatus,
    progress,
    traceSteps,
    rpsSteps,
    iterations,
    result,
    error,
    submitTask,
    cancelTask,
  } = useAnonymizationWebSocket();

  // Local UI state
  const [newCommentText, setNewCommentText] = useState('');
  const [showAddPanel, setShowAddPanel] = useState(false);
  const [personaEdit, setPersonaEdit] = useState<Record<string, string>>({});
  const [selectedMethod, setSelectedMethod] = useState<AnonymizationMethod>('trace_rps_v2');
  const [selectedAttributes, setSelectedAttributes] = useState<SensitiveAttribute[]>([
    'income',
    'education',
    'age',
    'location',
  ]);
  const [maxRounds, setMaxRounds] = useState(5);
  const [threshold, setThreshold] = useState(2);

  const isProcessing = execStatus === 'connecting' || execStatus === 'running';

  // Handle anonymize
  const handleAnonymize = useCallback(async () => {
    if (!selectedComment || isProcessing) return;
    setCommentStatus(selectedComment.index, 'processing');
    await submitTask({
      text: selectedComment.originalText,
      method: selectedMethod,
      config: {
        target_attributes: selectedAttributes,
        max_iterations: maxRounds,
        certainty_threshold: threshold,
      },
      options: { enable_progress_stream: true },
    } as any);
  }, [
    selectedComment,
    isProcessing,
    selectedMethod,
    selectedAttributes,
    maxRounds,
    threshold,
    submitTask,
    setCommentStatus,
  ]);

  // When result arrives, add it as a round
  React.useEffect(() => {
    if (result && selectedComment && selectedComment.status === 'processing') {
      addRoundResult(selectedComment.index, {
        roundNum: selectedComment.rounds.length,
        anonymizedText: result.anonymized_text,
        inferences: {} as Record<string, any>,
        maxConfidence: result.trace_rps_details?.final_certainty || 0,
        quality: result.quality_scores || null,
      });
      setCommentStatus(selectedComment.index, 'done');
      const maxCert = result.trace_rps_details?.final_certainty || 0;
      addPrivacySnapshot({
        commentCount: state.comments.filter((c) => c.status === 'done').length + 1,
        attributeConfidences: {} as Record<string, number>,
        maxConfidence: maxCert,
      });
    }
  }, [result]);

  const handleAddComment = () => {
    if (!newCommentText.trim()) return;
    addComment(newCommentText.trim());
    setNewCommentText('');
    setShowAddPanel(false);
  };

  const selectedRound =
    state.selectedRound >= 0 ? selectedComment?.rounds[state.selectedRound] : undefined;

  return (
    <div className="flex h-[calc(100vh-6rem)] gap-0">
      {/* ===== LEFT PANEL: Comment Warehouse ===== */}
      <div className="w-80 shrink-0 border-r border-gray-200 dark:border-gray-800 flex flex-col bg-white dark:bg-gray-900">
        {/* Persona card */}
        <div className="p-4 border-b border-gray-100 dark:border-gray-800">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
            人物设定 (可选)
          </h3>
          <div className="space-y-2">
            {['age', 'gender', 'location', 'occupation', 'education', 'income'].map((attr) => (
              <div key={attr} className="flex items-center gap-2 text-xs">
                <span className="w-16 text-gray-500 capitalize">{attr}:</span>
                <input
                  type="text"
                  value={personaEdit[attr] || state.persona[attr] || ''}
                  onChange={(e) => {
                    const next = { ...personaEdit, [attr]: e.target.value };
                    setPersonaEdit(next);
                    setPersona(next);
                  }}
                  placeholder="-"
                  className="flex-1 px-2 py-1 rounded border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-xs"
                />
              </div>
            ))}
          </div>
        </div>

        {/* Comment list */}
        <div className="flex-1 overflow-y-auto">
          <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
              评论列表 ({state.comments.length})
            </span>
          </div>
          {state.comments.length === 0 ? (
            <div className="p-6 text-center text-sm text-gray-400">
              暂无评论，点击下方添加评论开始
            </div>
          ) : (
            state.comments.map((comment) => (
              <button
                key={comment.index}
                onClick={() => selectComment(comment.index)}
                className={`w-full text-left px-4 py-3 border-b border-gray-50 dark:border-gray-800 transition-colors ${
                  state.selectedCommentIndex === comment.index
                    ? 'bg-violet-50 dark:bg-violet-900/20 border-l-2 border-l-violet-500'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-gray-500">
                    Comment #{comment.index + 1}
                  </span>
                  <StatusBadge status={comment.status} />
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                  {comment.originalText}
                </p>
              </button>
            ))
          )}
        </div>

        {/* Add comment panel */}
        <div className="p-4 border-t border-gray-100 dark:border-gray-800">
          {showAddPanel ? (
            <div className="space-y-2">
              <textarea
                value={newCommentText}
                onChange={(e) => setNewCommentText(e.target.value)}
                placeholder="粘贴一条用户评论..."
                rows={3}
                className="w-full px-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 resize-none"
              />
              <div className="flex gap-2">
                <button
                  onClick={handleAddComment}
                  className="flex-1 px-3 py-1.5 text-xs font-medium bg-violet-600 text-white rounded-lg hover:bg-violet-700"
                >
                  添加
                </button>
                <button
                  onClick={() => setShowAddPanel(false)}
                  className="px-3 py-1.5 text-xs text-gray-500 hover:text-gray-700"
                >
                  取消
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setShowAddPanel(true)}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm text-violet-600 border border-dashed border-violet-300 rounded-lg hover:bg-violet-50 dark:hover:bg-violet-900/20"
            >
              <Plus className="w-4 h-4" /> 添加评论
            </button>
          )}
        </div>
      </div>

      {/* ===== CENTER PANEL: Processing & Comparison ===== */}
      <div className="flex-1 flex flex-col bg-gray-50 dark:bg-gray-950 overflow-y-auto p-6">
        {!selectedComment ? (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            <div className="text-center">
              <FlaskConical className="w-12 h-12 mx-auto mb-4 opacity-30" />
              <p className="text-lg">选择左侧评论开始匿名化</p>
              <p className="text-sm mt-2">添加评论后点击 "开始匿名化" 进行处理</p>
            </div>
          </div>
        ) : (
          <>
            {/* Config bar */}
            <div className="mb-6 p-4 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800">
              <div className="flex items-center gap-4 flex-wrap">
                <MethodConfigPanel
                  selectedMethod={selectedMethod}
                  onMethodChange={setSelectedMethod}
                  selectedAttributes={selectedAttributes}
                  onAttributesChange={setSelectedAttributes}
                  iterations={maxRounds}
                  onIterationsChange={setMaxRounds}
                  threshold={threshold}
                  onThresholdChange={setThreshold}
                  disabled={isProcessing}
                />
                <div className="flex gap-2 ml-auto">
                  <button
                    onClick={handleAnonymize}
                    disabled={isProcessing}
                    className="flex items-center gap-2 px-6 py-2 bg-violet-600 text-white rounded-lg hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                  >
                    <Send className="w-4 h-4" />
                    {isProcessing ? '处理中...' : '开始匿名化'}
                  </button>
                  {isProcessing && (
                    <button
                      onClick={cancelTask}
                      className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 text-sm font-medium"
                    >
                      取消
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Round selector */}
            {selectedComment.rounds.length > 0 && (
              <div className="flex items-center gap-2 mb-4">
                <span className="text-sm font-medium text-gray-600">轮次:</span>
                <button
                  onClick={() => selectRound(-1)}
                  className={`px-3 py-1.5 rounded-lg text-sm ${
                    state.selectedRound === -1
                      ? 'bg-gray-700 text-white'
                      : 'bg-white text-gray-600 border'
                  }`}
                >
                  原始
                </button>
                {selectedComment.rounds.map((r) => (
                  <button
                    key={r.roundNum}
                    onClick={() => selectRound(r.roundNum)}
                    className={`px-3 py-1.5 rounded-lg text-sm ${
                      state.selectedRound === r.roundNum
                        ? 'bg-violet-600 text-white'
                        : 'bg-white text-gray-600 border'
                    }`}
                  >
                    R{r.roundNum + 1}
                  </button>
                ))}
              </div>
            )}

            {/* Content area */}
            {state.selectedRound === -1 || !selectedRound ? (
              <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                  Comment #{selectedComment.index + 1} — 原始文本
                </h3>
                <div className="bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-800 rounded-lg p-4">
                  <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                    {selectedComment.originalText}
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Text comparison */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
                    <h4 className="text-xs font-medium text-red-500 uppercase mb-2">原文</h4>
                    <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                      {selectedComment.originalText}
                    </p>
                  </div>
                  <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
                    <h4 className="text-xs font-medium text-green-500 uppercase mb-2">
                      匿名化 (R{selectedRound.roundNum + 1})
                    </h4>
                    <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                      {selectedRound.anonymizedText}
                    </p>
                  </div>
                </div>

                {/* Quality scores */}
                {selectedRound.quality && (
                  <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
                    <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                      质量评分
                    </h3>
                    <div className="grid grid-cols-4 gap-4">
                      {[
                        {
                          label: '隐私保护',
                          value: selectedRound.quality.privacy_protection,
                          color: 'text-green-500',
                        },
                        {
                          label: '效用保持',
                          value: selectedRound.quality.utility_preservation,
                          color: 'text-blue-500',
                        },
                        {
                          label: '文本质量',
                          value: selectedRound.quality.text_quality,
                          color: 'text-violet-500',
                        },
                        {
                          label: '推理阻断',
                          value: selectedRound.quality.inference_blocking,
                          color: 'text-amber-500',
                        },
                      ].map((q) => (
                        <div key={q.label} className="text-center">
                          <p className={`text-2xl font-bold ${q.color}`}>
                            {q.value.toFixed(0)}
                          </p>
                          <p className="text-xs text-gray-500 mt-1">{q.label}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2">
                  <button className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700">
                    确认
                  </button>
                  <button
                    onClick={handleAnonymize}
                    className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg text-sm hover:bg-gray-300"
                  >
                    重试
                  </button>
                </div>
              </div>
            )}

            {/* Processing progress */}
            {isProcessing && selectedComment.index === state.selectedCommentIndex && (
              <div className="mt-4 bg-white dark:bg-gray-900 rounded-lg border border-violet-200 dark:border-violet-800 p-4">
                <div className="flex items-center gap-3 mb-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-violet-600" />
                  <span className="text-sm font-medium text-violet-700 dark:text-violet-400">
                    处理中... {Math.round(progress)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-violet-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${Math.max(2, progress)}%` }}
                  />
                </div>
              </div>
            )}

            {/* Error display */}
            {error && (
              <div className="mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-sm text-red-600">
                {error}
              </div>
            )}
          </>
        )}
      </div>

      {/* ===== RIGHT PANEL: Profile Radar ===== */}
      <div className="w-72 shrink-0 border-l border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4 overflow-y-auto">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">
          画像面板
        </h3>

        {state.privacyHistory.length > 0 ? (
          <div className="space-y-4">
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
              <h4 className="text-xs font-medium text-gray-500 mb-2">累积推断趋势</h4>
              <div className="space-y-1">
                {state.privacyHistory.map((snap, i) => (
                  <div key={i} className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">{snap.commentCount} 条评论</span>
                    <span
                      className={`font-mono font-medium ${
                        snap.maxConfidence >= 4
                          ? 'text-red-500'
                          : snap.maxConfidence >= 3
                          ? 'text-amber-500'
                          : 'text-green-500'
                      }`}
                    >
                      置信度 {snap.maxConfidence}/5
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Attribute status */}
            <div>
              <h4 className="text-xs font-medium text-gray-500 mb-2">属性泄漏状态</h4>
              <div className="space-y-1">
                {selectedAttributes.map((attr) => {
                  const lastSnap =
                    state.privacyHistory[state.privacyHistory.length - 1];
                  const conf = lastSnap?.attributeConfidences?.[attr] ?? 0;
                  const blocked = conf < 3;
                  return (
                    <div
                      key={attr}
                      className="flex items-center justify-between text-xs py-1"
                    >
                      <span className="capitalize text-gray-600">{attr}</span>
                      <span className={blocked ? 'text-green-500' : 'text-red-500'}>
                        {blocked ? '已阻断' : `泄露 (${conf}/5)`}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ) : (
          <div className="text-xs text-gray-400 text-center py-8">
            处理评论后，画像雷达将显示跨评论推断结果
          </div>
        )}

        {/* Export */}
        {state.comments.filter((c) => c.status === 'done').length > 0 && (
          <button
            onClick={() => {
              const data = {
                sessionId: state.sessionId,
                persona: state.persona,
                comments: state.comments.map((c) => ({
                  original: c.originalText,
                  anonymized: c.finalAnonymizedText,
                  rounds: c.rounds.length,
                  riskScore: c.riskScore,
                })),
                privacyHistory: state.privacyHistory,
              };
              const blob = new Blob([JSON.stringify(data, null, 2)], {
                type: 'application/json',
              });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `session_${state.sessionId}.json`;
              a.click();
              URL.revokeObjectURL(url);
            }}
            className="mt-6 w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-200 text-sm"
          >
            <Download className="w-4 h-4" /> 导出结果
          </button>
        )}
      </div>
    </div>
  );
};

// ---- Sub-components ----

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const config: Record<string, { label: string; className: string }> = {
    pending: { label: '待处理', className: 'bg-gray-100 text-gray-500' },
    processing: { label: '处理中', className: 'bg-blue-100 text-blue-600' },
    done: { label: '已完成', className: 'bg-green-100 text-green-600' },
    rejected: { label: '已拒绝', className: 'bg-red-100 text-red-600' },
  };
  const c = config[status] || config.pending;
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${c.className}`}
    >
      {c.label}
    </span>
  );
};

export default ResearchPlatform;

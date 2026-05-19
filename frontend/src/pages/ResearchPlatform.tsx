import React, { useState, useCallback } from 'react';
import { useSession } from '../context/SessionContext';
import { useAnonymizationWebSocket } from '../hooks/useAnonymizationWebSocket';
import {
  MethodConfigPanel,
  AnonymizationMethod,
  SensitiveAttribute,
} from '../components/MethodConfigPanel';
import { Plus, Send, Trash2, Download, FlaskConical, ChevronDown, ChevronRight } from 'lucide-react';

// ---- Sub-components (must be defined before use) ----

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const config: Record<string, { label: string; className: string }> = {
    pending: { label: '待处理', className: 'bg-gray-100 text-gray-500' },
    processing: { label: '处理中', className: 'bg-blue-100 text-blue-600' },
    done: { label: '已完成', className: 'bg-green-100 text-green-600' },
    rejected: { label: '已拒绝', className: 'bg-red-100 text-red-600' },
  };
  const c = config[status] || config.pending;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${c.className}`}>
      {c.label}
    </span>
  );
};

const ReasoningChainCard: React.FC<{ chain: any }> = ({ chain }) => {
  const [expanded, setExpanded] = React.useState(false);
  const nodeColors: Record<string, string> = {
    evidence: 'bg-blue-50 border-blue-200 text-blue-700',
    inference: 'bg-purple-50 border-purple-200 text-purple-700',
    conclusion: 'bg-red-50 border-red-200 text-red-700',
    blocked: 'bg-green-50 border-green-200 text-green-700',
  };

  return (
    <div className="border border-gray-100 rounded-lg">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50"
      >
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium capitalize">{chain.attribute || 'Unknown'}</span>
          {chain.blocked ? (
            <span className="text-xs text-green-500">✓ 已阻断</span>
          ) : (
            <span className="text-xs text-red-500">✗ 泄露</span>
          )}
          <span className="text-xs text-gray-400">→ {chain.targetGuess || chain.target_guess || '-'}</span>
        </div>
        {expanded ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
      </button>
      {expanded && chain.nodes && (
        <div className="px-4 pb-4 space-y-2">
          {(chain.nodes as any[]).map((node: any, ni: number) => (
            <div key={ni} className={`flex gap-3 p-3 rounded-lg border ${nodeColors[node.type] || 'bg-gray-50 border-gray-200'}`}>
              <div className="shrink-0 w-6 h-6 rounded-full bg-white border flex items-center justify-center text-xs font-bold">
                {ni + 1}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-medium uppercase opacity-60">{node.type}</span>
                  {node.confidence && (
                    <span className="text-xs bg-white/50 px-1.5 py-0.5 rounded">
                      置信度 {node.confidence}/5
                    </span>
                  )}
                </div>
                <p className="text-sm">{node.text}</p>
                {node.evidence && (
                  <p className="mt-1 text-xs italic opacity-70">
                    📎 证据: "{node.evidence}"
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ---- Main Component ----

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
      session_id: state.sessionId,
      all_comments: state.comments.map((c) => c.originalText),
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
      // Extract inference data from result
      const inferenceTest = (result as any).inference_test || [];
      const reasoningChains = (result as any).trace_rps_details?.reasoning_chains || [];
      const attrConfs: Record<string, number> = {};
      inferenceTest.forEach((t: any) => {
        attrConfs[t.attribute || ''] = t.after_attack?.certainty || t.before_attack?.certainty || 0;
      });

      addRoundResult(selectedComment.index, {
        roundNum: selectedComment.rounds.length,
        anonymizedText: result.anonymized_text,
        inferences: { test: inferenceTest, chains: reasoningChains } as Record<string, any>,
        maxConfidence: result.trace_rps_details?.final_certainty || 0,
        quality: result.quality_scores || null,
      });
      setCommentStatus(selectedComment.index, 'done');
      const maxCert = result.trace_rps_details?.final_certainty || 0;
      addPrivacySnapshot({
        commentCount: state.comments.filter((c) => c.status === 'done').length + 1,
        attributeConfidences: attrConfs,
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

  // Save / Load handlers
  const handleSave = async () => {
    const data = {
      session_id: state.sessionId,
      persona: state.persona,
      comments: state.comments.map((c) => ({
        index: c.index,
        original_text: c.originalText,
        status: c.status,
        risk_score: c.riskScore,
        rounds: c.rounds.map((r) => ({
          round_num: r.roundNum,
          anonymized_text: r.anonymizedText,
          max_confidence: r.maxConfidence,
          quality: r.quality,
          inferences: (r.inferences as any)?.test?.map((t: any) => ({
            attribute: t.attribute,
            inference_text: '',
            guesses: [t.after_attack?.guess || t.before_attack?.guess || ''],
            confidence: t.after_attack?.certainty || 1,
            blocked: t.blocked || false,
            ground_truth: null,
          })) || [],
          chains: (r.inferences as any)?.chains || [],
        })),
      })),
    };
    try {
      const res = await fetch('/api/session/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (res.ok) alert('会话已保存');
    } catch { alert('保存失败'); }
  };

  const [savedSessions, setSavedSessions] = useState<any[]>([]);
  const handleLoadSessions = async () => {
    try {
      const res = await fetch('/api/session/list');
      const data = await res.json();
      setSavedSessions(data);
    } catch {}
  };

  const handleLoadSession = async (sessionId: string) => {
    try {
      const res = await fetch(`/api/session/load/${sessionId}`);
      const data = await res.json();
      reset();
      if (data.persona) setPersona(data.persona);
      for (const c of data.comments || []) {
        addComment(c.original_text);
        const idx = state.comments.length;
        for (const r of c.rounds || []) {
          addRoundResult(idx, {
            roundNum: r.round_num,
            anonymizedText: r.anonymized_text,
            inferences: { test: r.inferences, chains: r.chains } as any,
            maxConfidence: r.max_confidence || 0,
            quality: r.quality,
          });
        }
        setCommentStatus(idx, c.status || 'done');
      }
      setSavedSessions([]);
    } catch { alert('加载失败'); }
  };

  return (
    <>
      {/* Top toolbar */}
      <div className="flex items-center gap-3 px-6 py-2 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <span className="text-sm font-medium text-gray-600">会话: {state.sessionId}</span>
        <button onClick={handleSave} className="px-3 py-1 text-xs bg-violet-600 text-white rounded hover:bg-violet-700">保存</button>
        <div className="relative">
          <button onClick={handleLoadSessions} className="px-3 py-1 text-xs border border-gray-300 text-gray-600 rounded hover:bg-gray-50">加载</button>
          {savedSessions.length > 0 && (
            <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-60 overflow-y-auto">
              {savedSessions.map((s: any) => (
                <button key={s.id} onClick={() => handleLoadSession(s.id)} className="w-full text-left px-3 py-2 text-xs hover:bg-gray-50 border-b border-gray-100">
                  <div className="font-medium">{s.id}</div>
                  <div className="text-gray-400">{s.comment_count} 评论 — {s.updated_at}</div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="flex h-[calc(100vh-8rem)] gap-0">
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
              <div
                key={comment.index}
                className={`group flex items-start gap-2 px-4 py-3 border-b border-gray-50 dark:border-gray-800 transition-colors ${
                  state.selectedCommentIndex === comment.index
                    ? 'bg-violet-50 dark:bg-violet-900/20 border-l-2 border-l-violet-500'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                }`}
              >
                <button
                  onClick={() => selectComment(comment.index)}
                  className="flex-1 text-left min-w-0"
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
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteComment(comment.index);
                    if (state.selectedCommentIndex >= state.comments.length - 1) {
                      selectComment(Math.max(0, state.comments.length - 2));
                    }
                  }}
                  className="shrink-0 p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-red-100 dark:hover:bg-red-900/30 text-gray-400 hover:text-red-500 transition-all"
                  title="删除评论"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
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

                {/* Reasoning Chains */}
                {selectedRound.inferences?.chains?.length > 0 && (
                  <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
                    <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                      攻击者推理链 (CoT)
                    </h3>
                    <div className="space-y-3">
                      {(selectedRound.inferences.chains as any[]).map((chain: any, ci: number) => (
                        <ReasoningChainCard key={ci} chain={chain} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Inference test results */}
                {selectedRound.inferences?.test?.length > 0 && (
                  <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
                    <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                      攻击者推断结果
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-xs text-gray-500 uppercase">
                            <th className="text-left py-2">属性</th>
                            <th className="text-left py-2">推断</th>
                            <th className="text-center py-2">确定性</th>
                            <th className="text-center py-2">阻断</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {(selectedRound.inferences.test as any[]).map((t: any, ti: number) => (
                            <tr key={ti}>
                              <td className="py-2 font-medium capitalize">{t.attribute || '-'}</td>
                              <td className="py-2 text-xs text-gray-600 max-w-xs truncate">
                                {t.before_attack?.guess || '-'}
                              </td>
                              <td className="py-2 text-center">
                                <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                                  (t.after_attack?.certainty || t.before_attack?.certainty || 1) >= 4
                                    ? 'bg-red-100 text-red-700'
                                    : 'bg-green-100 text-green-700'
                                }`}>
                                  {t.after_attack?.certainty || t.before_attack?.certainty || '-'}/5
                                </span>
                              </td>
                              <td className="py-2 text-center">
                                {t.blocked ? (
                                  <span className="text-green-500 text-xs">✓ 已阻断</span>
                                ) : (
                                  <span className="text-red-500 text-xs">✗ 泄露</span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
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
    </>
  );
};


export default ResearchPlatform;

/**
 * SynthpaiUserDetail — 评论级攻防过程详情页
 *
 * 左右两栏：左侧评论列表，右侧展示选中评论的攻防迭代过程
 */
import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, MessageCircle, Shield, Target, Check, X as XIcon } from 'lucide-react';

interface RoundSummary {
  round: number;
  anonymized_text: string;
  avg_certainty: number;
}

interface CommentSummary {
  index: number;
  original_text: string;
  rounds_summary: RoundSummary[];
}

interface UserDetailResponse {
  username: string;
  ground_truth: Record<string, string>;
  comments: CommentSummary[];
}

interface AttackerAttributeInference {
  name: string;
  inference: string;
  guesses: string[];
  certainty: number;
  ground_truth: string | null;
  correct: boolean | null;
}

interface AttackerInference {
  model: string;
  attributes: AttackerAttributeInference[];
}

interface CommentRoundDetail {
  username: string;
  comment_index: number;
  round: number;
  anonymized_text: string;
  original_text: string;
  attacker_inference: AttackerInference;
  utility: Record<string, any> | null;
}

const SynthpaiUserDetail: React.FC = () => {
  const { username } = useParams<{ username: string }>();
  const navigate = useNavigate();

  const [userData, setUserData] = useState<UserDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedCommentIdx, setSelectedCommentIdx] = useState(0);
  const [selectedRound, setSelectedRound] = useState(0);
  const [roundDetail, setRoundDetail] = useState<CommentRoundDetail | null>(null);
  const [roundLoading, setRoundLoading] = useState(false);

  // 加载用户数据
  useEffect(() => {
    if (!username) return;
    setLoading(true);
    fetch(`/api/synthpai/users/${encodeURIComponent(username)}`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data: UserDetailResponse) => {
        setUserData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load user detail:', err);
        setError(err.message);
        setLoading(false);
      });
  }, [username]);

  // 加载选中评论的轮次详情
  const loadRoundDetail = useCallback(() => {
    if (!username) return;
    setRoundLoading(true);
    fetch(
      `/api/synthpai/users/${encodeURIComponent(username)}/comments/${selectedCommentIdx}/rounds/${selectedRound}`
    )
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data: CommentRoundDetail) => {
        setRoundDetail(data);
        setRoundLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load round detail:', err);
        setRoundLoading(false);
      });
  }, [username, selectedCommentIdx, selectedRound]);

  useEffect(() => {
    if (userData) {
      loadRoundDetail();
    }
  }, [userData, selectedCommentIdx, selectedRound, loadRoundDetail]);

  // 渲染确定性徽章
  const getCertaintyBadge = (certainty: number) => {
    const colors: Record<number, string> = {
      1: 'bg-green-100 text-green-700',
      2: 'bg-emerald-100 text-emerald-700',
      3: 'bg-yellow-100 text-yellow-700',
      4: 'bg-orange-100 text-orange-700',
      5: 'bg-red-100 text-red-700',
    };
    return (
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colors[certainty] || 'bg-gray-100 text-gray-600'}`}
      >
        {certainty}/5
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-violet-600" />
          <p className="mt-4 text-gray-600">加载用户数据中...</p>
        </div>
      </div>
    );
  }

  if (error || !userData) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p className="text-red-600 mb-2">加载失败: {error || '用户不存在'}</p>
          <button
            onClick={() => navigate('/synthpai')}
            className="text-violet-600 hover:underline text-sm"
          >
            ← 返回列表
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8">
      {/* 顶部栏 */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/synthpai')}
          className="inline-flex items-center gap-2 text-gray-500 hover:text-violet-600 transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          返回用户列表
        </button>
        <div className="flex items-center gap-3">
          <Shield className="w-6 h-6 text-violet-600" />
          <h2 className="text-2xl font-bold text-gray-900">{userData.username}</h2>
        </div>
        {/* Ground Truth 标签 */}
        <div className="flex flex-wrap gap-2 mt-3">
          {Object.entries(userData.ground_truth).map(([attr, value]) => (
            <span
              key={attr}
              className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm bg-violet-50 text-violet-700 border border-violet-200"
            >
              <span className="font-medium">{attr}:</span> {value}
            </span>
          ))}
        </div>
      </div>

      {/* 左右两栏 */}
      <div className="flex flex-col lg:flex-row gap-6">
        {/* 左栏：评论列表 */}
        <div className="lg:w-80 shrink-0">
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="px-4 py-3 border-b border-gray-100">
              <div className="flex items-center gap-2">
                <MessageCircle className="w-4 h-4 text-gray-400" />
                <span className="text-sm font-medium text-gray-700">
                  评论列表 ({userData.comments.length})
                </span>
              </div>
            </div>
            <div className="max-h-[70vh] overflow-y-auto">
              {userData.comments.map((comment) => (
                <button
                  key={comment.index}
                  onClick={() => setSelectedCommentIdx(comment.index)}
                  className={`w-full text-left px-4 py-3 border-b border-gray-50 transition-colors ${
                    selectedCommentIdx === comment.index
                      ? 'bg-violet-50 border-l-2 border-l-violet-500'
                      : 'hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-700">
                      Comment #{comment.index + 1}
                    </span>
                    <span className="text-xs text-gray-400">
                      {comment.rounds_summary[comment.rounds_summary.length - 1]?.avg_certainty.toFixed(1)} avg cert
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 line-clamp-2">
                    {comment.original_text}
                  </p>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* 右栏：攻防过程 */}
        <div className="flex-1 min-w-0">
          {/* 轮次选择器 */}
          <div className="flex items-center gap-2 mb-6">
            <span className="text-sm font-medium text-gray-600 mr-2">轮次:</span>
            {[0, 1, 2, 3].map((r) => (
              <button
                key={r}
                onClick={() => setSelectedRound(r)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  selectedRound === r
                    ? 'bg-violet-600 text-white shadow-sm'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                Round {r}
                {r === 0 ? ' (原文)' : r === 3 ? ' (终)' : ''}
              </button>
            ))}
          </div>

          {roundLoading ? (
            <div className="flex items-center justify-center py-16">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-violet-600" />
            </div>
          ) : roundDetail ? (
            <div className="space-y-6">
              {/* 攻击者推理表格 */}
              <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
                  <div className="flex items-center gap-2">
                    <Target className="w-4 h-4 text-red-500" />
                    <span className="text-sm font-medium text-gray-700">
                      攻击者推理 — {roundDetail.attacker_inference.model}
                    </span>
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">属性</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">猜测</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">确定性</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Ground Truth</th>
                        <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">命中</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {roundDetail.attacker_inference.attributes.map((attr) => (
                        <tr key={attr.name} className="hover:bg-gray-50">
                          <td className="px-4 py-3">
                            <span className="text-sm font-medium text-gray-800 capitalize">
                              {attr.name}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex flex-wrap gap-1">
                              {attr.guesses.map((g, i) => (
                                <span
                                  key={i}
                                  className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-600"
                                >
                                  {g}
                                </span>
                              ))}
                            </div>
                          </td>
                          <td className="px-4 py-3">{getCertaintyBadge(attr.certainty)}</td>
                          <td className="px-4 py-3">
                            <span className="text-sm text-gray-600">
                              {attr.ground_truth || '-'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-center">
                            {attr.correct === true ? (
                              <Check className="w-4 h-4 text-red-500 inline" />
                            ) : attr.correct === false ? (
                              <XIcon className="w-4 h-4 text-green-500 inline" />
                            ) : (
                              <span className="text-xs text-gray-400">-</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* 推理链详情 */}
              <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
                <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
                  <span className="text-sm font-medium text-gray-700">
                    攻击者推理链 (CoT)
                  </span>
                </div>
                <div className="p-4 space-y-4">
                  {roundDetail.attacker_inference.attributes.map((attr) => (
                    <div key={attr.name} className="border border-gray-100 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-semibold text-gray-700 capitalize">
                          {attr.name}
                        </span>
                        <div className="flex items-center gap-2">
                          {getCertaintyBadge(attr.certainty)}
                          {attr.correct === true && (
                            <span className="text-xs text-red-500 font-medium flex items-center gap-1">
                              <Check className="w-3 h-3" /> 泄露
                            </span>
                          )}
                          {attr.correct === false && (
                            <span className="text-xs text-green-500 font-medium flex items-center gap-1">
                              <XIcon className="w-3 h-3" /> 已阻止
                            </span>
                          )}
                        </div>
                      </div>
                      <p className="text-sm text-gray-600 whitespace-pre-wrap leading-relaxed">
                        {attr.inference}
                      </p>
                      <div className="mt-2 flex items-center gap-2 text-xs text-gray-400">
                        <span>猜测: {attr.guesses.join(', ')}</span>
                        {attr.ground_truth && (
                          <>
                            <span>|</span>
                            <span>实际: {attr.ground_truth}</span>
                          </>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* 文本对比 */}
              <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
                <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
                  <span className="text-sm font-medium text-gray-700">
                    评论文本对比 (Comment #{roundDetail.comment_index + 1})
                  </span>
                </div>
                <div className="p-4 grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-xs font-medium text-red-500 uppercase mb-2">
                      原始文本
                    </h4>
                    <div className="bg-red-50 border border-red-100 rounded-lg p-3">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                        {roundDetail.original_text}
                      </p>
                    </div>
                  </div>
                  <div>
                    <h4 className="text-xs font-medium text-green-500 uppercase mb-2">
                      匿名化后 (Round {roundDetail.round})
                    </h4>
                    <div className="bg-green-50 border border-green-100 rounded-lg p-3">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                        {roundDetail.anonymized_text}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* 效用评分 */}
              {roundDetail.utility && Object.keys(roundDetail.utility).length > 0 && (
                <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
                  <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
                    <span className="text-sm font-medium text-gray-700">效用评分</span>
                  </div>
                  <div className="p-4">
                    <pre className="text-xs text-gray-500 whitespace-pre-wrap">
                      {JSON.stringify(roundDetail.utility, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-16 text-gray-400">
              暂无数据
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SynthpaiUserDetail;

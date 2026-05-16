/**
 * ExecutionStepper - Real-time execution visualization panel
 *
 * Displays:
 * - Overall progress bar
 * - TRACE 5-step flow with expandable details
 * - RPS defense optimization trace (Stage 1 & 2)
 * - Iteration history with before/after comparison
 *
 * All data is driven by backend WebSocket progress messages.
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Check,
  Circle,
  Play,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  Zap,
  Target,
  Eye,
  Link2,
  GitBranch,
  Edit3,
  Shield,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  X,
} from 'lucide-react';

// ── Types ──

interface TRACEStepData {
  step: number;
  step_name: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  detail?: Record<string, any>;
}

interface RPSStepData {
  stage: number;
  attempt: number;
  current_suffix: string;
  tried_suffix: string;
  probability_before: number;
  probability_after: number;
  accepted: boolean;
  stopping_condition_met: boolean;
}

interface IterationData {
  iteration: number;
  before_text: string;
  after_text: string;
  inferences: Array<{ attribute: string; guess: string; certainty: number }>;
  attention_words: string[];
  improvements: string[];
  certainty_before: number;
  certainty_after: number;
}

interface ExecutionStepperProps {
  traceSteps: TRACEStepData[];
  rpsSteps: RPSStepData[];
  iterations: IterationData[];
  currentStep: string;
  progress: number;
  wsConnected: boolean;
  methodName: string;
}

// ── TRACE step config ──

const TRACE_STEP_ICONS = [
  { icon: Target, color: 'text-rose-500', bg: 'bg-rose-50 dark:bg-rose-900/20', label: '模拟攻击' },
  { icon: Eye, color: 'text-violet-500', bg: 'bg-violet-50 dark:bg-violet-900/20', label: '注意力提取' },
  { icon: Link2, color: 'text-blue-500', bg: 'bg-blue-50 dark:bg-blue-900/20', label: '推理链生成' },
  { icon: GitBranch, color: 'text-amber-500', bg: 'bg-amber-50 dark:bg-amber-900/20', label: '关键节点定位' },
  { icon: Edit3, color: 'text-emerald-500', bg: 'bg-emerald-50 dark:bg-emerald-900/20', label: '精细改写' },
];

// ── Component ──

export const ExecutionStepper: React.FC<ExecutionStepperProps> = ({
  traceSteps,
  rpsSteps,
  iterations,
  currentStep,
  progress,
  wsConnected,
  methodName,
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new data arrives
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [traceSteps.length, rpsSteps.length, iterations.length]);

  // Get the latest step for each TRACE step number
  const stepMap = new Map<number, TRACEStepData>();
  for (const step of traceSteps) {
    stepMap.set(step.step, step);
  }
  const latestTraceSteps = Array.from(stepMap.values()).sort((a, b) => a.step - b.step);

  // Group RPS steps by stage
  const stage1Steps = rpsSteps.filter(s => s.stage === 1);
  const stage2Steps = rpsSteps.filter(s => s.stage === 2);

  // Find first RPS step to display initial data
  const lastRPSStep = rpsSteps[rpsSteps.length - 1];

  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            实时执行过程
          </h3>
          <span className="text-xs text-slate-500 dark:text-slate-400">{methodName}</span>
        </div>

        {/* Progress bar */}
        <div className="flex items-center gap-3">
          <div className="flex-1 h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-violet-500 to-rose-500 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${Math.max(2, progress)}%` }}
            />
          </div>
          <span className="text-xs font-mono text-slate-500 dark:text-slate-400 w-10 text-right">
            {Math.round(progress)}%
          </span>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
          {currentStep || '初始化中...'}
        </p>
      </div>

      {/* Scrollable content */}
      <div ref={scrollRef} className="max-h-[70vh] overflow-y-auto p-6 space-y-4">
        {/* ── TRACE 5-step flow ── */}
        <div>
          <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
            <Activity className="w-4 h-4" />
            TRACE 细粒度匿名化流程
          </h4>
          <div className="space-y-2">
            {TRACE_STEP_ICONS.map((stepConfig, idx) => {
              const stepNum = idx + 1;
              const stepData = latestTraceSteps.find(s => s.step === stepNum);
              const status = stepData?.status || 'pending';
              const Icon = stepConfig.icon;

              return (
                <TraceStepCard
                  key={stepNum}
                  stepNum={stepNum}
                  label={stepConfig.label}
                  Icon={Icon}
                  status={status}
                  stepData={stepData}
                  iconColor={stepConfig.color}
                  iconBg={stepConfig.bg}
                />
              );
            })}
          </div>
        </div>

        {/* ── RPS Defense optimization trace ── */}
        {rpsSteps.length > 0 && (
          <div className="border-t border-slate-200 dark:border-slate-700 pt-4">
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
              <Shield className="w-4 h-4" />
              RPS 防御优化过程
            </h4>

            {/* Current suffix */}
            {lastRPSStep && (
              <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg mb-3">
                <p className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                  当前防御 Suffix
                </p>
                <p className="text-xs font-mono text-slate-700 dark:text-slate-300 break-all">
                  {lastRPSStep.current_suffix || '(初始化中...)'}
                </p>
              </div>
            )}

            {/* Stage 1 */}
            {stage1Steps.length > 0 && (
              <div className="mb-3">
                <div className="flex items-center gap-2 mb-2">
                  <div className={`w-2 h-2 rounded-full ${stage1Steps[stage1Steps.length - 1]?.stopping_condition_met ? 'bg-emerald-500' : 'bg-blue-500 animate-pulse'}`} />
                  <h5 className="text-xs font-semibold text-blue-700 dark:text-blue-300">
                    Stage 1: 优化首个 Token → "I"
                  </h5>
                  <span className="text-xs text-slate-500">
                    τ₁ 目标: P("I") &gt; 0.8
                  </span>
                </div>
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {stage1Steps.map((step, idx) => (
                    <div
                      key={idx}
                      className={`flex items-center gap-2 text-xs px-2 py-1 rounded ${
                        step.accepted
                          ? 'bg-emerald-50 dark:bg-emerald-900/10'
                          : 'bg-red-50 dark:bg-red-900/5'
                      }`}
                    >
                      <span className="text-slate-400 w-5 text-right">#{step.attempt}</span>
                      {step.accepted ? (
                        <ArrowUpRight className="w-3 h-3 text-emerald-500" />
                      ) : (
                        <X className="w-3 h-3 text-red-400" />
                      )}
                      <span className="text-slate-600 dark:text-slate-400 font-mono text-[10px] truncate max-w-[200px]">
                        suffix: {step.tried_suffix.substring(0, 60)}...
                      </span>
                      <span className="ml-auto font-mono text-[10px]">
                        <span className="text-slate-400">P=</span>
                        <span className={step.accepted ? 'text-emerald-600' : 'text-red-500'}>
                          {step.probability_after.toFixed(3)}
                        </span>
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Stage 2 */}
            {stage2Steps.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <div className={`w-2 h-2 rounded-full ${stage2Steps[stage2Steps.length - 1]?.stopping_condition_met ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'}`} />
                  <h5 className="text-xs font-semibold text-amber-700 dark:text-amber-300">
                    Stage 2: 优化第二个 Token → "cannot/apologize"
                  </h5>
                  <span className="text-xs text-slate-500">
                    τ₂ 目标: P &gt; 0.55, β=5
                  </span>
                </div>
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {stage2Steps.map((step, idx) => (
                    <div
                      key={idx}
                      className={`flex items-center gap-2 text-xs px-2 py-1 rounded ${
                        step.accepted
                          ? 'bg-emerald-50 dark:bg-emerald-900/10'
                          : 'bg-red-50 dark:bg-red-900/5'
                      }`}
                    >
                      <span className="text-slate-400 w-5 text-right">#{step.attempt}</span>
                      {step.accepted ? (
                        <ArrowUpRight className="w-3 h-3 text-emerald-500" />
                      ) : (
                        <X className="w-3 h-3 text-red-400" />
                      )}
                      <span className="text-slate-600 dark:text-slate-400 font-mono text-[10px] truncate max-w-[200px]">
                        suffix: {step.tried_suffix.substring(0, 60)}...
                      </span>
                      <span className="ml-auto font-mono text-[10px]">
                        <span className="text-slate-400">score=</span>
                        <span className={step.accepted ? 'text-emerald-600' : 'text-red-500'}>
                          {step.probability_after.toFixed(3)}
                        </span>
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* RPS current status */}
            {lastRPSStep && (
              <div className={`mt-3 p-2 rounded text-xs text-center ${
                lastRPSStep.stopping_condition_met
                  ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300'
                  : 'bg-slate-50 dark:bg-slate-800 text-slate-500'
              }`}>
                {lastRPSStep.stopping_condition_met
                  ? '✅ 已达停止条件，RPS 优化完成'
                  : '⏳ 正在搜索更优 suffix...'}
              </div>
            )}
          </div>
        )}

        {/* ── Iteration history ── */}
        {iterations.length > 0 && (
          <div className="border-t border-slate-200 dark:border-slate-700 pt-4">
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
              <Zap className="w-4 h-4" />
              迭代历史
            </h4>
            <div className="space-y-2">
              {iterations.map((iter) => (
                <IterationMiniCard key={iter.iteration} iteration={iter} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ── TRACE Step Card ──

const TraceStepCard: React.FC<{
  stepNum: number;
  label: string;
  Icon: React.FC<{ className?: string }>;
  status: string;
  stepData?: TRACEStepData;
  iconColor: string;
  iconBg: string;
}> = ({ stepNum, label, Icon, status, stepData, iconColor, iconBg }) => {
  const [expanded, setExpanded] = useState(false);

  const statusConfig = {
    completed: {
      dot: <Check className="w-4 h-4 text-emerald-500" />,
      borderColor: 'border-emerald-200 dark:border-emerald-800',
    },
    running: {
      dot: (
        <div className="w-4 h-4 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
      ),
      borderColor: 'border-blue-200 dark:border-blue-800',
    },
    failed: {
      dot: <AlertCircle className="w-4 h-4 text-red-500" />,
      borderColor: 'border-red-200 dark:border-red-800',
    },
    pending: {
      dot: <Circle className="w-4 h-4 text-slate-300 dark:text-slate-600" />,
      borderColor: 'border-slate-100 dark:border-slate-700',
    },
  };

  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
  const hasDetail = stepData && status !== 'pending';

  return (
    <div
      className={`border rounded-lg overflow-hidden transition-all duration-300 ${
        status === 'running' ? 'shadow-md shadow-blue-500/10' : ''
      } ${status === 'completed' ? 'opacity-100' : status === 'pending' ? 'opacity-50' : ''} ${config.borderColor}`}
    >
      <button
        onClick={() => hasDetail && setExpanded(!expanded)}
        className={`w-full px-3 py-2.5 flex items-center gap-3 ${hasDetail ? 'cursor-pointer' : 'cursor-default'}`}
      >
        {/* Status dot */}
        <div className="flex-shrink-0">{config.dot}</div>

        {/* Step icon */}
        <div className={`p-1.5 rounded-lg ${iconBg} flex-shrink-0`}>
          <Icon className={`w-4 h-4 ${iconColor}`} />
        </div>

        {/* Step info */}
        <div className="flex-1 text-left min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Step {stepNum}
            </span>
            <span className="text-xs text-slate-600 dark:text-slate-400">{label}</span>
          </div>
          {stepData && (
            <p className="text-[11px] text-slate-500 dark:text-slate-500 truncate mt-0.5">
              {stepData.description}
            </p>
          )}
        </div>

        {/* Expand indicator */}
        {hasDetail && (
          <div className="flex-shrink-0">
            {expanded ? (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-slate-400" />
            )}
          </div>
        )}
      </button>

      {/* Expanded detail */}
      {expanded && stepData?.detail && (
        <div className="px-4 pb-3 border-t border-slate-100 dark:border-slate-700 pt-2">
          <StepDetailContent stepNum={stepNum} detail={stepData.detail} />
        </div>
      )}
    </div>
  );
};

// ── Step Detail Content Renderer ──

const StepDetailContent: React.FC<{ stepNum: number; detail: Record<string, any> }> = ({
  stepNum,
  detail,
}) => {
  switch (stepNum) {
    case 1: // Attack simulation
      return (
        <div className="space-y-2 text-xs">
          {detail.attributes_tested && (
            <div>
              <span className="font-medium text-slate-500">测试属性: </span>
              <span className="text-slate-700 dark:text-slate-300">
                {detail.attributes_tested.join(', ')}
              </span>
            </div>
          )}
          {detail.attack_results && (
            <div className="space-y-1.5">
              <span className="font-medium text-slate-500 block">攻击者推断结果:</span>
              {Object.entries(detail.attack_results as Record<string, any>).map(([attr, data]) => (
                <div key={attr} className="p-2 bg-red-50 dark:bg-red-900/10 rounded">
                  <span className="font-semibold text-red-700 dark:text-red-300">{attr}: </span>
                  <span className="text-slate-700 dark:text-slate-300">{data.guess || '未知'}</span>
                  <span className="text-slate-500 ml-2">(确信度: {data.certainty})</span>
                </div>
              ))}
            </div>
          )}
          {detail.prompt_preview && (
            <details>
              <summary className="text-slate-500 cursor-pointer">查看攻击 Prompt</summary>
              <pre className="mt-1 p-2 bg-slate-100 dark:bg-slate-800 rounded text-[10px] overflow-x-auto whitespace-pre-wrap">
                {detail.prompt_preview}
              </pre>
            </details>
          )}
        </div>
      );

    case 2: // Attention extraction
      return (
        <div className="space-y-2 text-xs">
          {detail.top_words && (
            <div>
              <span className="font-medium text-slate-500 block mb-1">
                Top-{detail.top_words.length} 隐私关键词:
              </span>
              <div className="flex flex-wrap gap-1">
                {detail.top_words.map((word: string, idx: number) => (
                  <span
                    key={idx}
                    className={`px-2 py-0.5 rounded text-[11px] ${
                      idx < 3
                        ? 'bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-300 font-medium'
                        : 'bg-violet-50 dark:bg-violet-900/20 text-violet-600 dark:text-violet-400'
                    }`}
                  >
                    {word}
                  </span>
                ))}
              </div>
            </div>
          )}
          <div className="text-slate-500 text-[11px]">
            方法: {detail.method || '关键词提取（注意力模拟）'}
          </div>
        </div>
      );

    case 3: // Reasoning chain
      return (
        <div className="space-y-2 text-xs">
          {detail.chain_count != null && (
            <div className="text-slate-500">
              生成了 <span className="font-semibold text-violet-600">{detail.chain_count}</span> 条推理链
            </div>
          )}
          {detail.chains_preview && (
            <div className="space-y-1.5">
              {(detail.chains_preview as Array<any>).map((chain, idx) => (
                <div key={idx} className="p-2 bg-blue-50 dark:bg-blue-900/10 rounded">
                  <span className="font-semibold text-blue-700 dark:text-blue-300">{chain.attribute}: </span>
                  <span className="text-slate-700 dark:text-slate-300">→ {chain.guess}</span>
                  <span className="text-slate-500 ml-2">({chain.steps} 步)</span>
                </div>
              ))}
            </div>
          )}
        </div>
      );

    case 4: // Key node location
      return (
        <div className="space-y-2 text-xs">
          {detail.causal_paths && (
            <div className="space-y-1.5">
              {(detail.causal_paths as Array<any>).map((path, idx) => (
                <div key={idx} className="p-2 bg-amber-50 dark:bg-amber-900/10 rounded">
                  <span className="font-semibold text-amber-700 dark:text-amber-300">
                    {path.attribute}:
                  </span>
                  <p className="text-slate-600 dark:text-slate-400 mt-1 font-mono text-[10px]">
                    {path.path}
                  </p>
                  {path.key_terms?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {path.key_terms.map((term: string, i: number) => (
                        <span
                          key={i}
                          className="px-1.5 py-0.5 bg-amber-100 dark:bg-amber-900/20 text-amber-700 dark:text-amber-300 rounded text-[10px]"
                        >
                          {term}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      );

    case 5: // Fine-grained rewrite
      return (
        <div className="space-y-2 text-xs">
          <div className="flex items-center gap-2 text-slate-500">
            <span>迭代 {detail.iteration}/{detail.max_iterations}</span>
          </div>
          <div className="text-slate-600 dark:text-slate-400">
            基于推理链执行精细改写：泛化/删除/改写隐私关键词
          </div>
        </div>
      );

    default:
      return <pre className="text-[10px] text-slate-500">{JSON.stringify(detail, null, 2)}</pre>;
  }
};

// ── Mini iteration card ──

const IterationMiniCard: React.FC<{ iteration: IterationData }> = ({ iteration: iter }) => {
  return (
    <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="w-5 h-5 rounded-full bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300 text-[11px] font-bold flex items-center justify-center">
            {iter.iteration}
          </span>
          <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
            第 {iter.iteration} 轮
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-red-500">确信度 {iter.certainty_before}</span>
          <span className="text-slate-400">→</span>
          <span className={`font-semibold ${iter.certainty_after < iter.certainty_before ? 'text-emerald-500' : 'text-slate-500'}`}>
            {iter.certainty_after}
          </span>
          {iter.certainty_after < iter.certainty_before && (
            <ArrowDownRight className="w-3 h-3 text-emerald-500" />
          )}
        </div>
      </div>

      {/* Inferences */}
      {iter.inferences.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {iter.inferences.map((inf, idx) => (
            <span
              key={idx}
              className="text-[10px] px-1.5 py-0.5 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded"
            >
              {inf.attribute}: {inf.guess || '?'}
            </span>
          ))}
        </div>
      )}

      {/* Key changes */}
      {iter.improvements.length > 0 && (
        <div className="text-[10px] text-slate-500 dark:text-slate-400 space-y-0.5">
          {iter.improvements.slice(0, 2).map((imp, idx) => (
            <div key={idx} className="truncate">• {imp}</div>
          ))}
          {iter.improvements.length > 2 && (
            <div className="text-slate-400">...还有 {iter.improvements.length - 2} 项改动</div>
          )}
        </div>
      )}
    </div>
  );
};

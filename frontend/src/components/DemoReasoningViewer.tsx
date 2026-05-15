/**
 * DemoReasoningViewer - 模拟实时流式展示推理过程
 *
 * 核心特性：
 * 1. 预加载数据，无延迟展示
 * 2. 打字机效果模拟实时生成
 * 3. 可控播放速度
 * 4. 进度指示器
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Play, Pause, RotateCcw, FastForward, ChevronDown, ChevronUp } from 'lucide-react';

// 推理步骤类型
interface ReasoningStep {
  step: number;
  title: string;
  content: string;
  duration: number;
}

interface DemoReasoningViewerProps {
  steps: ReasoningStep[];
  onComplete?: () => void;
  autoPlay?: boolean;
  defaultSpeed?: number; // 速度倍率：0.5=慢, 1=正常, 2=快
}

export const DemoReasoningViewer: React.FC<DemoReasoningViewerProps> = ({
  steps,
  onComplete,
  autoPlay = true,
  defaultSpeed = 1
}) => {
  // 状态管理
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(autoPlay);
  const [displayedContent, setDisplayedContent] = useState('');
  const [charIndex, setCharIndex] = useState(0);
  const [speed, setSpeed] = useState(defaultSpeed);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set([0]));

  // Refs
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const stepTimerRef = useRef<NodeJS.Timeout | null>(null);

  // 当前步骤
  const currentStep = steps[currentStepIndex];
  const isCurrentStepComplete = charIndex >= currentStep?.content.length;

  // 计算打字速度（基于步骤时长和内容长度）
  const getTypingDelay = useCallback((step: ReasoningStep) => {
    const baseDelay = (step.duration / step.content.length) * 10;
    return Math.max(20, baseDelay / speed); // 最小20ms，受速度倍率影响
  }, [speed]);

  // 打字效果
  useEffect(() => {
    if (!isPlaying || !currentStep || isCurrentStepComplete) {
      return;
    }

    const delay = getTypingDelay(currentStep);

    timerRef.current = setTimeout(() => {
      setDisplayedContent(prev => currentStep.content.slice(0, charIndex + 1));
      setCharIndex(prev => prev + 1);
    }, delay);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [isPlaying, currentStep, charIndex, isCurrentStepComplete, getTypingDelay]);

  // 自动切换到下一步
  useEffect(() => {
    if (!isPlaying || !isCurrentStepComplete || !currentStep) {
      return;
    }

    // 标记当前步骤完成
    setCompletedSteps(prev => new Set([...prev, currentStepIndex]));

    // 延迟后切换到下一步
    stepTimerRef.current = setTimeout(() => {
      if (currentStepIndex < steps.length - 1) {
        const nextIndex = currentStepIndex + 1;
        setCurrentStepIndex(nextIndex);
        setCharIndex(0);
        setDisplayedContent('');
        setExpandedSteps(prev => new Set([...prev, nextIndex]));
      } else {
        // 所有步骤完成
        setIsPlaying(false);
        onComplete?.();
      }
    }, 800); // 步骤间延迟

    return () => {
      if (stepTimerRef.current) clearTimeout(stepTimerRef.current);
    };
  }, [isPlaying, isCurrentStepComplete, currentStep, currentStepIndex, steps.length, onComplete]);

  // 清理定时器
  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (stepTimerRef.current) clearTimeout(stepTimerRef.current);
    };
  }, []);

  // 控制函数
  const togglePlay = () => setIsPlaying(!isPlaying);

  const restart = () => {
    setCurrentStepIndex(0);
    setCharIndex(0);
    setDisplayedContent('');
    setCompletedSteps(new Set());
    setExpandedSteps(new Set([0]));
    setIsPlaying(true);
  };

  const nextStep = () => {
    if (currentStepIndex < steps.length - 1) {
      const nextIndex = currentStepIndex + 1;
      setCurrentStepIndex(nextIndex);
      setCharIndex(0);
      setDisplayedContent('');
      setExpandedSteps(prev => new Set([...prev, nextIndex]));
    }
  };

  const prevStep = () => {
    if (currentStepIndex > 0) {
      const prevIndex = currentStepIndex - 1;
      setCurrentStepIndex(prevIndex);
      setCharIndex(0);
      setDisplayedContent('');
      setExpandedSteps(prev => new Set([...prev, prevIndex]));
    }
  };

  const toggleStepExpanded = (stepIndex: number) => {
    setExpandedSteps(prev => {
      const newSet = new Set(prev);
      if (newSet.has(stepIndex)) {
        newSet.delete(stepIndex);
      } else {
        newSet.add(stepIndex);
      }
      return newSet;
    });
  };

  const changeSpeed = () => {
    const speeds = [0.5, 1, 2];
    const currentIndex = speeds.indexOf(speed);
    const nextIndex = (currentIndex + 1) % speeds.length;
    setSpeed(speeds[nextIndex]);
  };

  // 获取速度标签
  const getSpeedLabel = () => {
    switch (speed) {
      case 0.5: return '慢速';
      case 1: return '正常';
      case 2: return '快速';
      default: return '正常';
    }
  };

  // 计算进度
  const progress = ((currentStepIndex + (charIndex / currentStep?.content.length)) / steps.length) * 100;

  return (
    <div className="bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
      {/* 标题和进度 */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          推理过程演示
        </h2>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {currentStepIndex + 1} / {steps.length}
          </span>
          <div className="w-32 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      {/* 控制按钮 */}
      <div className="flex items-center gap-2 mb-6">
        <button
          onClick={restart}
          className="p-2 rounded-lg bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          title="重新开始"
        >
          <RotateCcw className="w-4 h-4 text-gray-700 dark:text-gray-300" />
        </button>
        <button
          onClick={prevStep}
          disabled={currentStepIndex === 0}
          className="p-2 rounded-lg bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="上一步"
        >
          <ChevronUp className="w-4 h-4 text-gray-700 dark:text-gray-300" />
        </button>
        <button
          onClick={togglePlay}
          className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors flex items-center gap-2"
        >
          {isPlaying ? (
            <>
              <Pause className="w-4 h-4" />
              <span>暂停</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              <span>播放</span>
            </>
          )}
        </button>
        <button
          onClick={nextStep}
          disabled={currentStepIndex === steps.length - 1}
          className="p-2 rounded-lg bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="下一步"
        >
          <ChevronDown className="w-4 h-4 text-gray-700 dark:text-gray-300" />
        </button>
        <button
          onClick={changeSpeed}
          className="px-3 py-2 rounded-lg bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors text-sm"
          title="切换速度"
        >
          <FastForward className="w-4 h-4 inline mr-1" />
          {getSpeedLabel()}
        </button>
      </div>

      {/* 步骤列表 */}
      <div className="space-y-3">
        {steps.map((step, index) => {
          const isCurrent = index === currentStepIndex;
          const isCompleted = completedSteps.has(index);
          const isExpanded = expandedSteps.has(index);

          return (
            <div
              key={step.step}
              className={`border rounded-lg transition-all ${
                isCurrent
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : isCompleted
                  ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                  : 'border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800'
              }`}
            >
              {/* 步骤标题 */}
              <button
                onClick={() => toggleStepExpanded(index)}
                className="w-full px-4 py-3 flex items-center justify-between text-left"
              >
                <div className="flex items-center gap-3">
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-sm font-medium ${
                    isCompleted
                      ? 'bg-green-500 text-white'
                      : isCurrent
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300'
                  }`}>
                    {isCompleted ? '✓' : step.step}
                  </span>
                  <span className={`font-medium ${
                    isCurrent ? 'text-blue-700 dark:text-blue-300' : 'text-gray-700 dark:text-gray-300'
                  }`}>
                    {step.title}
                  </span>
                </div>
                {isExpanded ? (
                  <ChevronUp className="w-4 h-4 text-gray-500" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-gray-500" />
                )}
              </button>

              {/* 步骤内容 */}
              {isExpanded && (
                <div className="px-4 pb-3">
                  {isCurrent ? (
                    <div className="bg-white dark:bg-gray-900 rounded-lg p-3">
                      <pre className="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300 font-mono">
                        {displayedContent}
                        {isPlaying && !isCurrentStepComplete && (
                          <span className="inline-block w-2 h-4 bg-blue-500 ml-1 animate-pulse" />
                        )}
                      </pre>
                    </div>
                  ) : (
                    <div className="bg-gray-100 dark:bg-gray-900 rounded-lg p-3">
                      <pre className="whitespace-pre-wrap text-sm text-gray-600 dark:text-gray-400 font-mono">
                        {step.content}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 完成提示 */}
      {currentStepIndex === steps.length - 1 && isCurrentStepComplete && (
        <div className="mt-6 p-4 bg-green-100 dark:bg-green-900/30 rounded-lg text-center">
          <p className="text-green-700 dark:text-green-300 font-medium">
            ✓ 推理过程演示完成
          </p>
        </div>
      )}
    </div>
  );
};


/**
 * DemoDataLoader - 演示数据加载器
 *
 * 预加载演示数据，提供快速访问
 */
export const DemoDataLoader: React.FC = () => {
  const [data, setData] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  useEffect(() => {
    // 加载预生成的演示数据
    import('../data/demo-data.json')
      .then(module => {
        setData(module.default);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load demo data:', err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return { data, loading, error };
};


/**
 * DemoModeBanner - 演示模式标识横幅
 */
export const DemoModeBanner: React.FC<{ onExit?: () => void }> = ({ onExit }) => {
  return (
    <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className="px-2 py-1 bg-white/20 rounded text-xs font-medium">
          DEMO
        </span>
        <span className="text-sm">
          演示模式 - 使用预加载数据，无延迟展示
        </span>
      </div>
      {onExit && (
        <button
          onClick={onExit}
          className="px-3 py-1 bg-white/20 hover:bg-white/30 rounded text-sm transition-colors"
        >
          退出演示模式
        </button>
      )}
    </div>
  );
};

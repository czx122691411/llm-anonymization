/**
 * DemoStepper - Interactive stepper component for demo process visualization
 * Shows progress through steps with expandable details and smooth animations
 */

import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Check, Circle, Play, Clock, FileText, Image as ImageIcon } from 'lucide-react';
import { DemoStep, ReasoningChain } from '../../types/trace-rps';
import { SimplifiedChainChart } from './ReasoningChainChart';
import { DemoTextComparison } from './DemoTextComparison';

interface DemoStepperProps {
  steps: DemoStep[];
  title?: string;
  description?: string;
  showProgress?: boolean;
  onStepChange?: (stepIndex: number) => void;
  isRunning?: boolean;
  speed?: 'slow' | 'normal' | 'fast';
  reasoningChains?: ReasoningChain[];
  originalText?: string;
  anonymizedText?: string;
  textChanges?: Array<{
    original: string;
    anonymized: string;
    reason: string;
  }>;
}

const StepCard: React.FC<{
  step: DemoStep;
  index: number;
  isExpanded: boolean;
  onToggle: () => void;
  reasoningChains?: ReasoningChain[];
  originalText?: string;
  anonymizedText?: string;
  textChanges?: Array<{
    original: string;
    anonymized: string;
    reason: string;
  }>;
  stepIndex?: number;
}> = ({ step, index, isExpanded, onToggle, reasoningChains, originalText, anonymizedText, textChanges, stepIndex }) => {
  const statusConfig = {
    completed: {
      icon: Check,
      iconBg: 'bg-green-100 dark:bg-green-900/30',
      iconColor: 'text-green-600 dark:text-green-400',
      borderColor: 'border-green-200 dark:border-green-800',
      pulseClass: '',
    },
    in_progress: {
      icon: Play,
      iconBg: 'bg-blue-100 dark:bg-blue-900/30',
      iconColor: 'text-blue-600 dark:text-blue-400',
      borderColor: 'border-blue-200 dark:border-blue-800',
      pulseClass: 'animate-pulse',
    },
    pending: {
      icon: Circle,
      iconBg: 'bg-gray-100 dark:bg-gray-800',
      iconColor: 'text-gray-400 dark:text-gray-600',
      borderColor: 'border-gray-200 dark:border-gray-800',
      pulseClass: '',
    },
  };

  const config = statusConfig[step.status];
  const Icon = config.icon;

  return (
    <div
      className={`
        border rounded-xl transition-all duration-300 ease-in-out overflow-hidden
        ${config.borderColor} ${step.status === 'in_progress' ? 'shadow-md' : 'shadow-sm hover:shadow-md'}
        ${step.status === 'in_progress' ? 'ring-2 ring-blue-500 ring-opacity-50' : ''}
      `}
    >
      {/* Step Header - Always Visible */}
      <button
        onClick={onToggle}
        className="w-full px-6 py-4 flex items-center gap-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors duration-200"
      >
        {/* Status Icon */}
        <div className={`p-2 rounded-lg ${config.iconBg} ${config.pulseClass}`}>
          <Icon className={`w-5 h-5 ${config.iconColor}`} />
        </div>

        {/* Step Info */}
        <div className="flex-1 text-left">
          <div className="flex items-center gap-2">
            <h4 className={`font-semibold ${step.status === 'pending' ? 'text-gray-500 dark:text-gray-400' : 'text-gray-900 dark:text-gray-100'}`}>
              {index + 1}. {step.title}
            </h4>
            {step.duration && step.status !== 'pending' && (
              <span className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                <Clock className="w-3 h-3" />
                {step.duration}s
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{step.description}</p>
        </div>

        {/* Expand/Collapse Icon */}
        <div className={`transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`}>
          {isExpanded ? <ChevronDown className="w-5 h-5 text-gray-400" /> : <ChevronRight className="w-5 h-5 text-gray-400" />}
        </div>
      </button>

      {/* Expanded Content */}
      <div
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          isExpanded ? 'max-h-[1000px] opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="px-6 pb-6 pt-2 border-t border-gray-100 dark:border-gray-800">
          {/* Details Grid */}
          {step.details && step.details.length > 0 && (
            <div className="mb-4">
              <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                详细信息
              </h5>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {step.details.map((detail, idx) => (
                  <div
                    key={idx}
                    className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3 border border-gray-100 dark:border-gray-700"
                  >
                    <p className="text-xs text-gray-500 dark:text-gray-400">{detail.label}</p>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mt-0.5">{detail.value}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Logs */}
          {step.logs && step.logs.length > 0 && (
            <div className="mb-4">
              <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">执行日志</h5>
              <div className="bg-gray-900 rounded-lg p-3 font-mono text-xs overflow-x-auto">
                {step.logs.map((log, idx) => (
                  <div key={idx} className="text-gray-300 mb-1 last:mb-0">
                    {log}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Image Placeholder - Replace with Reasoning Chain Visualization */}
          {step.imagePlaceholder && reasoningChains && reasoningChains.length > 0 && (
            <div className="mb-4">
              <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                <ImageIcon className="w-4 h-4" />
                推理链可视化
              </h5>
              <SimplifiedChainChart chains={reasoningChains} />
            </div>
          )}
          {step.imagePlaceholder && (!reasoningChains || reasoningChains.length === 0) && (
            <div className="mb-4">
              <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                <ImageIcon className="w-4 h-4" />
                可视化图表
              </h5>
              <div className="bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg p-8 border-2 border-dashed border-gray-300 dark:border-gray-700 flex items-center justify-center min-h-[200px]">
                <div className="text-center">
                  <ImageIcon className="w-12 h-12 text-gray-400 dark:text-gray-600 mx-auto mb-3" />
                  <p className="text-sm text-gray-500 dark:text-gray-400">推理链可视化图表</p>
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">实时渲染中...</p>
                </div>
              </div>
            </div>
          )}

          {/* Text Comparison - Show in step 1 (original) and step 4+ (anonymized) */}
          {originalText && (stepIndex === 0 || stepIndex === undefined) && (
            <div className="mb-4">
              <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                原始文本
              </h5>
              <DemoTextComparison
                originalText={originalText}
                changes={textChanges}
              />
            </div>
          )}
          {anonymizedText && stepIndex !== undefined && stepIndex >= 3 && (
            <div className="mb-4">
              <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                文本对比 (匿名化结果)
              </h5>
              <DemoTextComparison
                originalText={originalText || ''}
                anonymizedText={anonymizedText}
                changes={textChanges}
                showAnonymized={true}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export const DemoStepper: React.FC<DemoStepperProps> = ({
  steps,
  title = '演示过程',
  description,
  showProgress = true,
  onStepChange,
  isRunning = false,
  speed = 'normal',
  reasoningChains,
  originalText,
  anonymizedText,
  textChanges,
}) => {
  // 创建可变的步骤状态副本
  const [dynamicSteps, setDynamicSteps] = useState<DemoStep[]>(() =>
    steps.map(s => ({ ...s, status: 'pending' as const }))
  );
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set([steps[0]?.id]));
  const [currentRunningStep, setCurrentRunningStep] = useState<number>(-1);

  // 重置步骤状态当演示开始时
  React.useEffect(() => {
    if (isRunning) {
      setDynamicSteps(steps.map(s => ({ ...s, status: 'pending' as const })));
    }
  }, [isRunning]);

  // Simulate demo running
  React.useEffect(() => {
    if (!isRunning) return;

    const speedMap = {
      slow: 3000,
      normal: 1500,
      fast: 500,
    };

    let currentStep = 0;

    const runStep = async () => {
      if (currentStep >= steps.length) {
        setCurrentRunningStep(-1);
        return;
      }

      // 标记当前步骤为 in_progress
      setDynamicSteps(prev => prev.map((s, i) =>
        i === currentStep ? { ...s, status: 'in_progress' as const } : s
      ));
      setCurrentRunningStep(currentStep);
      setExpandedSteps(new Set([steps[currentStep].id]));
      onStepChange?.(currentStep);

      // 模拟步骤执行时间
      await new Promise(resolve => setTimeout(resolve, speedMap[speed]));

      // 标记当前步骤为 completed
      setDynamicSteps(prev => prev.map((s, i) =>
        i === currentStep ? { ...s, status: 'completed' as const } : s
      ));

      currentStep++;
      if (currentStep < steps.length) {
        runStep();
      } else {
        setCurrentRunningStep(-1);
        onStepChange?.(steps.length);
      }
    };

    runStep();
  }, [isRunning, speed]);

  const toggleStep = (stepId: string) => {
    setExpandedSteps((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(stepId)) {
        newSet.delete(stepId);
      } else {
        newSet.add(stepId);
      }
      return newSet;
    });
  };

  // 使用动态步骤状态计算进度
  const completedSteps = dynamicSteps.filter((s) => s.status === 'completed').length;
  const progress = (completedSteps / dynamicSteps.length) * 100;
  const currentStep = dynamicSteps.find((s) => s.status === 'in_progress');

  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{title}</h3>
            {description && <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{description}</p>}
          </div>
          {showProgress && (
            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{completedSteps}/{steps.length}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">已完成步骤</p>
              </div>
              <div className="w-16 h-16 relative">
                <svg className="w-full h-full transform -rotate-90">
                  <circle cx="32" cy="32" r="28" stroke="currentColor" strokeWidth="6" fill="none" className="text-gray-200 dark:text-gray-800" />
                  <circle
                    cx="32"
                    cy="32"
                    r="28"
                    stroke="currentColor"
                    strokeWidth="6"
                    fill="none"
                    strokeDasharray={2 * Math.PI * 28}
                    strokeDashoffset={2 * Math.PI * 28 * (1 - progress / 100)}
                    strokeLinecap="round"
                    className="text-blue-600 dark:text-blue-400 transition-all duration-500 ease-out"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-sm font-bold text-gray-900 dark:text-gray-100">{Math.round(progress)}%</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Overall Progress Bar */}
        {showProgress && (
          <div className="mt-4">
            <div className="w-full h-2 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Steps */}
      <div className="p-6 space-y-4">
        {dynamicSteps.map((step, index) => (
          <StepCard
            key={step.id}
            step={step}
            index={index}
            stepIndex={index}
            isExpanded={expandedSteps.has(step.id)}
            onToggle={() => toggleStep(step.id)}
            reasoningChains={reasoningChains}
            originalText={originalText}
            anonymizedText={anonymizedText}
            textChanges={textChanges}
          />
        ))}
      </div>

      {/* Current Step Indicator */}
      {currentStep && (
        <div className="px-6 py-4 bg-blue-50 dark:bg-blue-900/20 border-t border-blue-100 dark:border-blue-900">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg animate-pulse">
              <Play className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-blue-900 dark:text-blue-100">正在执行: {currentStep.title}</p>
              <p className="text-xs text-blue-700 dark:text-blue-300 mt-0.5">{currentStep.description}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DemoStepper;

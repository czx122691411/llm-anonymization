/**
 * ChineseDemoPage - 演示页面，展示3个典型案例的匿名化过程（中文版）
 * 包含多轮匿名化的完整展示
 */
import React, { useState } from 'react';
import { ArrowLeft, BookOpen, Shield, CheckCircle2, AlertTriangle, Eye, EyeOff } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import casesData from '../data/cases-demo-zh.json';

interface ReasoningStep {
  step: number;
  observation: string;
  analysis: string;
  privacy_risk: string;
}

interface ChangeExplanation {
  before: string;
  after: string;
  reason: string;
  why_anonymous: string;
}

interface Round {
  round_num: number;
  original_text: string;
  anonymized_text: string;
  cot_reasoning: string;
  changes: ChangeExplanation[];
}

interface Case {
  id: string;
  title: string;
  category: string;
  ground_truth: {
    age: string;
    sex: string;
    location: string;
    income_level: string;
    real_income?: string;
  };
  rounds: Round[];
  metrics: {
    privacy_protection: string;
    utility_preservation: string;
    text_quality: string;
  };
}

const MetricsCard = ({ label, value, icon: Icon }: { label: string; value: string; icon: React.ElementType }) => (
  <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl p-4 border border-blue-200 dark:border-blue-800">
    <div className="flex items-center gap-2 mb-2">
      <Icon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</span>
    </div>
    <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{value}</div>
  </div>
);

const ReasoningChain = ({ steps }: { steps: ReasoningStep[] }) => (
  <div className="space-y-4">
    {steps.map((step) => (
      <div key={step.step} className="relative pl-8">
        <div className="absolute left-0 top-0 w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-bold">
          {step.step}
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="mb-2">
            <span className="inline-flex items-center gap-1 text-sm font-semibold text-purple-600 dark:text-purple-400">
              <AlertTriangle className="w-4 h-4" />
              {step.observation.split('：')[0]}
            </span>
          </div>
          <p className="text-gray-700 dark:text-gray-300 mb-3">{step.observation.split('：')[1]}</p>
          <div className="mb-2">
            <span className="inline-flex items-center gap-1 text-sm font-semibold text-blue-600 dark:text-blue-400">
              <BookOpen className="w-4 h-4" />
              {step.analysis.split('：')[0]}
            </span>
          </div>
          <p className="text-gray-700 dark:text-gray-300 mb-3">{step.analysis.split('：')[1]}</p>
          <div className="bg-red-50 dark:bg-red-900/20 rounded-md p-3 border border-red-200 dark:border-red-800">
            <span className="inline-flex items-center gap-1 text-sm font-semibold text-red-600 dark:text-red-400">
              <Shield className="w-4 h-4" />
              {step.privacy_risk.split('：')[0]}
            </span>
            <p className="text-red-700 dark:text-red-300 mt-1 text-sm">{step.privacy_risk.split('：')[1]}</p>
          </div>
        </div>
      </div>
    ))}
  </div>
);

const ChangesDetail = ({ changes }: { changes: ChangeExplanation[] }) => (
  <div className="space-y-4">
    {changes.map((change, index) => (
      <div key={index} className="bg-white dark:bg-gray-800 rounded-lg p-5 shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
            {index + 1}
          </div>
          <span className="font-semibold text-gray-900 dark:text-gray-100">替换详情 #{index + 1}</span>
        </div>

        <div className="space-y-4">
          {/* 替换对比 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2 flex items-center gap-2">
                <EyeOff className="w-4 h-4" />
                原文（暴露隐私）
              </div>
              <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-3 border border-red-200 dark:border-red-800">
                <code className="text-sm text-red-700 dark:text-red-300 break-all">
                  {change.before}
                </code>
              </div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2 flex items-center gap-2">
                <Eye className="w-4 h-4" />
                匿名化后（已保护）
              </div>
              <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 border border-green-200 dark:border-green-800">
                <code className="text-sm text-green-700 dark:text-green-300 break-all">
                  {change.after}
                </code>
              </div>
            </div>
          </div>

          {/* 替换原因 */}
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
            <div className="text-xs font-semibold text-blue-600 dark:text-blue-400 mb-2">
              📋 为什么要替换这个内容？
            </div>
            <p className="text-sm text-gray-700 dark:text-gray-300">{change.reason}</p>
          </div>

          {/* 匿名化原理 */}
          <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 border border-purple-200 dark:border-purple-800">
            <div className="text-xs font-semibold text-purple-600 dark:text-purple-400 mb-2">
              🔒 这样替换如何实现匿名化？
            </div>
            <p className="text-sm text-gray-700 dark:text-gray-300">{change.why_anonymous}</p>
          </div>
        </div>
      </div>
    ))}
  </div>
);

const RoundSelector = ({ rounds, selectedRound, onSelectRound }: {
  rounds: Round[];
  selectedRound: number;
  onSelectRound: (round: number) => void;
}) => (
  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">选择匿名化轮次</h3>
    <div className="space-y-2">
      {rounds.map((round, index) => (
        <button
          key={round.round_num}
          onClick={() => onSelectRound(index)}
          className={`w-full text-left p-4 rounded-lg transition-all ${
            selectedRound === index
              ? 'bg-blue-600 text-white shadow-md'
              : 'bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="font-semibold">第 {round.round_num} 轮</div>
              <div className={`text-xs mt-1 ${selectedRound === index ? 'opacity-90' : 'text-gray-500'}`}>
                {round.changes.length} 处修改
              </div>
            </div>
            {selectedRound === index && (
              <CheckCircle2 className="w-5 h-5" />
            )}
          </div>
        </button>
      ))}
    </div>
  </div>
);

export const ChineseDemoPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedCaseId, setSelectedCaseId] = useState('case-1');
  const [selectedRoundIndex, setSelectedRoundIndex] = useState(0);
  const [activeTab, setActiveTab] = useState<'reasoning' | 'changes'>('reasoning');

  // Get selected case and round
  const selectedCase = casesData.cases.find((c: Case) => c.id === selectedCaseId);
  const currentRound = selectedCase?.rounds[selectedRoundIndex];

  if (!selectedCase || !currentRound) {
    return <div>加载中...</div>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate(-1)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {casesData.title}
                </h1>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {casesData.description}
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Left sidebar */}
          <div className="col-span-12 lg:col-span-3 space-y-4">
            {/* Case selector */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">选择案例</h2>
              <div className="space-y-2">
                {casesData.cases.map((c: Case) => (
                  <button
                    key={c.id}
                    onClick={() => {
                      setSelectedCaseId(c.id);
                      setSelectedRoundIndex(0);
                    }}
                    className={`w-full text-left p-3 rounded-lg transition-all ${
                      selectedCaseId === c.id
                        ? 'bg-blue-600 text-white shadow-md'
                        : 'bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300'
                    }`}
                  >
                    <div className="font-medium text-sm">{c.title}</div>
                    <div className="text-xs opacity-75 mt-1">{c.category}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Round selector */}
            <RoundSelector
              rounds={selectedCase.rounds}
              selectedRound={selectedRoundIndex}
              onSelectRound={setSelectedRoundIndex}
            />

            {/* Privacy principles */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                匿名化核心原理
              </h3>
              <div className="space-y-2">
                {casesData.privacy_principles.items.map((item: any, index: number) => (
                  <div key={index} className="text-xs text-gray-600 dark:text-gray-400">
                    <span className="font-semibold text-blue-600 dark:text-blue-400">
                      {item.name}：
                    </span>
                    {item.description}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Main content */}
          <div className="col-span-12 lg:col-span-9 space-y-6">
            {/* Round info header */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-md p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold mb-1">{selectedCase.title}</h2>
                  <p className="text-blue-100">第 {currentRound.round_num} 轮匿名化</p>
                </div>
                <div className="text-right">
                  <div className="text-3xl font-bold">{currentRound.changes.length}</div>
                  <div className="text-sm text-blue-100">处修改</div>
                </div>
              </div>
            </div>

            {/* Ground truth card */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                用户真实信息
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">年龄</div>
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {selectedCase.ground_truth.age}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">性别</div>
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {selectedCase.ground_truth.sex}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">位置</div>
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {selectedCase.ground_truth.location}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">收入水平</div>
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {selectedCase.ground_truth.income_level}
                  </div>
                </div>
                {selectedCase.ground_truth.real_income && (
                  <div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">实际收入</div>
                    <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {selectedCase.ground_truth.real_income}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Text comparison */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">原始评论</h3>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 max-h-64 overflow-y-auto">
                  <pre className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                    {currentRound.original_text}
                  </pre>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    第 {currentRound.round_num} 轮匿名化后
                  </h3>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 max-h-64 overflow-y-auto">
                  <pre className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                    {currentRound.anonymized_text}
                  </pre>
                </div>
              </div>
            </div>

            {/* Metrics */}
            {currentRound.metrics && (
              <div className="grid grid-cols-3 gap-4">
                <MetricsCard
                  label="隐私保护"
                  value={currentRound.metrics.privacy_protection}
                  icon={Shield}
                />
                <MetricsCard
                  label="效用保持"
                  value={currentRound.metrics.utility_preservation}
                  icon={CheckCircle2}
                />
                <MetricsCard
                  label="文本质量"
                  value={currentRound.metrics.text_quality}
                  icon={BookOpen}
                />
              </div>
            )}

            {/* Tab navigation */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
              <div className="border-b border-gray-200 dark:border-gray-700">
                <div className="flex">
                  <button
                    onClick={() => setActiveTab('reasoning')}
                    className={`flex-1 px-6 py-4 text-sm font-medium transition-colors ${
                      activeTab === 'reasoning'
                        ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400 bg-blue-50 dark:bg-blue-900/20'
                        : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
                    }`}
                  >
                    推理链（攻击者如何推断）
                  </button>
                  <button
                    onClick={() => setActiveTab('changes')}
                    className={`flex-1 px-6 py-4 text-sm font-medium transition-colors ${
                      activeTab === 'changes'
                        ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400 bg-blue-50 dark:bg-blue-900/20'
                        : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
                    }`}
                  >
                    修改解释（为什么这样替换）
                  </button>
                </div>
              </div>

              <div className="p-6">
                {activeTab === 'reasoning' ? (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                      攻击者推理链 - 第 {currentRound.round_num} 轮
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                      以下是攻击者如何通过原文中的线索逐步推断出隐私信息的过程
                    </p>
                    <ReasoningChain steps={currentRound.cot_reasoning} />
                  </div>
                ) : (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                      匿名化修改说明 - 第 {currentRound.round_num} 轮
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                      每次替换的目的和如何实现匿名化的详细解释
                    </p>
                    <ChangesDetail changes={currentRound.changes} />
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChineseDemoPage;
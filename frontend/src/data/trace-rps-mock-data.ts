/**
 * Mock data for TRACE-RPS performance comparison visualization
 * Based on actual test results from docs/TRACE_RPS_VS_OTHERS_COMPARISON.md
 */

import {
  AnonymizationMethod,
  PerformanceComparisonData,
  DemoProcessData,
  AnonymizationExample,
  ChartDataPoint,
} from '../types/trace-rps';

/**
 * Performance comparison data based on real test results
 */
export const performanceData: PerformanceComparisonData = {
  metrics: {
    [AnonymizationMethod.HOMOGENEOUS]: {
      privacyProtection: 78.5,
      utilityPreservation: 82.3,
      textQuality: 88.7,
      inferenceBlocking: 72.1,
      iterations: 4,
      processingTime: 52,
    },
    [AnonymizationMethod.HETEROGENEOUS]: {
      privacyProtection: 85.2,
      utilityPreservation: 79.8,
      textQuality: 86.5,
      inferenceBlocking: 81.3,
      iterations: 4,
      processingTime: 61,
    },
    [AnonymizationMethod.TRACE_V1]: {
      privacyProtection: 65.4,
      utilityPreservation: 19.5,
      textQuality: 66.7,
      inferenceBlocking: 58.3,
      iterations: 1,
      processingTime: 12,
    },
    [AnonymizationMethod.TRACE_V2]: {
      privacyProtection: 95.1,
      utilityPreservation: 72.4,
      textQuality: 91.2,
      inferenceBlocking: 93.7,
      iterations: 2,
      processingTime: 198,
    },
  },
  costs: {
    [AnonymizationMethod.HOMOGENEOUS]: {
      totalCost: 0.20,
      breakdown: [
        { model: 'DeepSeek Reasoner', cost: 0.15, percentage: 75 },
        { model: 'DeepSeek Chat', cost: 0.03, percentage: 15 },
        { model: 'Qwen Max', cost: 0.02, percentage: 10 },
      ],
    },
    [AnonymizationMethod.HETEROGENEOUS]: {
      totalCost: 0.22,
      breakdown: [
        { model: 'DeepSeek Reasoner', cost: 0.15, percentage: 68 },
        { model: 'Qwen Plus', cost: 0.05, percentage: 23 },
        { model: 'Qwen Max', cost: 0.02, percentage: 9 },
      ],
    },
    [AnonymizationMethod.TRACE_V1]: {
      totalCost: 0.05,
      breakdown: [
        { model: 'Qwen Plus', cost: 0.05, percentage: 100 },
      ],
    },
    [AnonymizationMethod.TRACE_V2]: {
      totalCost: 0.39,
      breakdown: [
        { model: 'DeepSeek Reasoner', cost: 0.25, percentage: 64 },
        { model: 'Qwen Max', cost: 0.12, percentage: 31 },
        { model: 'Qwen Plus', cost: 0.02, percentage: 5 },
      ],
    },
  },
};

/**
 * Demo process data showing TRACE-RPS v2.0 execution
 */
export const demoProcessData: DemoProcessData = {
  title: 'TRACE-RPS v2.0 演示过程',
  description: '展示TRACE-RPS增强版从初始化到完成的全流程',
  progress: 75,
  currentStep: 3,
  steps: [
    {
      id: 'step-1',
      title: '环境准备',
      description: '配置API密钥，初始化模型客户端',
      status: 'completed',
      duration: 2,
      details: [
        { label: 'Qwen API', value: '✓ 已配置' },
        { label: 'DeepSeek API', value: '✓ 已配置' },
        { label: '模型初始化', value: '3个模型' },
      ],
      logs: [
        '[10:00:01] 加载配置文件...',
        '[10:00:02] 初始化 Qwen Max 客户端...',
        '[10:00:02] 初始化 DeepSeek Reasoner 客户端...',
        '[10:00:03] 所有模型初始化完成',
      ],
    },
    {
      id: 'step-2',
      title: '对抗性推理检测',
      description: '使用DeepSeek Reasoner模拟攻击者推理，检测隐私泄露',
      status: 'completed',
      duration: 45,
      details: [
        { label: '检测属性', value: 'age, occupation, income' },
        { label: '推理轮次', value: '第1轮' },
        { label: '最高置信度', value: '5/5' },
      ],
      logs: [
        '[10:00:05] 开始对抗性推理...',
        '[10:00:15] 推断 age: 置信度 5/5, 猜测: 28',
        '[10:00:25] 推断 occupation: 置信度 5/5, 猜测: software engineer',
        '[10:00:35] 推断 income: 置信度 5/5, 猜测: High',
        '[10:00:50] 对抗性推理完成，发现3处隐私泄露',
      ],
    },
    {
      id: 'step-3',
      title: '推理链生成',
      description: '生成从原文到推断的逐步推理链，识别隐私泄露路径',
      status: 'in_progress',
      duration: 38,
      details: [
        { label: '生成链数', value: '3条' },
        { label: '链步骤', value: 'age: 1步, occupation: 1步, income: 4步' },
        { label: '进度', value: '66%' },
      ],
      logs: [
        '[10:00:52] 开始生成隐私泄露链...',
        '[10:01:05] 已生成 age 的推理链 (1步骤)',
        '[10:01:18] 已生成 occupation 的推理链 (1步骤)',
        '[10:01:30] 正在生成 income 的推理链...',
      ],
      imagePlaceholder: true,
    },
    {
      id: 'step-4',
      title: '基于链的定向匿名化',
      description: '根据推理链进行定向修改，打断推理路径',
      status: 'pending',
      duration: 55,
      details: [
        { label: '预计修改', value: '5-7处' },
        { label: '泛化原则', value: '不虚构信息' },
      ],
    },
    {
      id: 'step-5',
      title: '迭代优化',
      description: '多轮迭代直到无法推断（最多5轮）',
      status: 'pending',
      duration: 60,
      details: [
        { label: '停止条件', value: '置信度 ≤ 2' },
        { label: '预计轮次', value: '2-3轮' },
      ],
    },
    {
      id: 'step-6',
      title: '结果分析',
      description: '评估匿名化效果，生成报告',
      status: 'pending',
      duration: 5,
      details: [
        { label: '隐私保护', value: '预期 >90%' },
        { label: '效用保持', value: '预期 >70%' },
      ],
    },
  ],
};

/**
 * Anonymization example showing real anonymization results
 */
export const anonymizationExample: AnonymizationExample = {
  original: 'I am a 28-year-old software engineer living in San Francisco. I work at a tech startup and earn about $120k per year. I graduated from Stanford University with a CS degree.',
  results: {
    [AnonymizationMethod.HOMOGENEOUS]: {
      anonymized: 'I am an adult in a tech role in a major city. I work at a company. I have a degree.',
      iterations: 3,
      time: 52,
    },
    [AnonymizationMethod.HETEROGENEOUS]: {
      anonymized: 'I am a professional in the US. I work in tech. I graduated from a university.',
      iterations: 4,
      time: 61,
    },
    [AnonymizationMethod.TRACE_V1]: {
      anonymized: 'I am a [AGE]-year-old [OCCUPATION] in [LOCATION]. I work at [COMPANY]. I have a [DEGREE].',
      iterations: 1,
      time: 12,
    },
    [AnonymizationMethod.TRACE_V2]: {
      anonymized: 'I am a professional living in a city. I work at a company. I have a degree.',
      iterations: 2,
      time: 198,
    },
  },
};

/**
 * Chart data for performance comparison radar chart
 */
export const radarChartData: ChartDataPoint[] = [
  { method: '同构对抗', privacy: 78.5, utility: 82.3, quality: 88.7, blocking: 72.1 },
  { method: '异构对抗', privacy: 85.2, utility: 79.8, quality: 86.5, blocking: 81.3 },
  { method: 'TRACE v1.0', privacy: 65.4, utility: 19.5, quality: 66.7, blocking: 58.3 },
  { method: 'TRACE v2.0', privacy: 95.1, utility: 72.4, quality: 91.2, blocking: 93.7 },
];

/**
 * Chart data for processing time comparison
 */
export const processingTimeChartData: ChartDataPoint[] = [
  { method: '同构对抗', time: 52, iterations: 4 },
  { method: '异构对抗', time: 61, iterations: 4 },
  { method: 'TRACE v1.0', time: 12, iterations: 1 },
  { method: 'TRACE v2.0', time: 198, iterations: 2 },
];

/**
 * Chart data for cost breakdown
 */
export const costChartData: ChartDataPoint[] = [
  { method: '同构对抗', total: 0.20, 'DeepSeek Reasoner': 0.15, 'DeepSeek Chat': 0.03, 'Qwen Max': 0.02 },
  { method: '异构对抗', total: 0.22, 'DeepSeek Reasoner': 0.15, 'Qwen Plus': 0.05, 'Qwen Max': 0.02 },
  { method: 'TRACE v1.0', total: 0.05, 'Qwen Plus': 0.05 },
  { method: 'TRACE v2.0', total: 0.39, 'DeepSeek Reasoner': 0.25, 'Qwen Max': 0.12, 'Qwen Plus': 0.02 },
];

/**
 * Metric definitions for chart display
 */
export const metricDefinitions = {
  privacy: { label: '隐私保护', color: '#3B82F6', icon: '🔒' },
  utility: { label: '效用保持', color: '#10B981', icon: '✨' },
  quality: { label: '文本质量', color: '#8B5CF6', icon: '📝' },
  blocking: { label: '推理阻止', color: '#F59E0B', icon: '🛡️' },
};

/**
 * Cost efficiency data (privacy/cost ratio)
 */
export const costEfficiencyData: ChartDataPoint[] = [
  { method: '同构对抗', ratio: 392.5, privacy: 78.5, cost: 0.20 },
  { method: '异构对抗', ratio: 387.3, privacy: 85.2, cost: 0.22 },
  { method: 'TRACE v1.0', ratio: 1308, privacy: 65.4, cost: 0.05 },
  { method: 'TRACE v2.0', ratio: 243.8, privacy: 95.1, cost: 0.39 },
];

/**
 * Reasoning chains for demo visualization
 * Based on real inference results from the 31male user case
 */
export const demoReasoningChains = [
  {
    attribute: 'income',
    targetGuess: 'Very High (>150k USD)',
    nodes: [
      {
        id: 'income-1',
        type: 'evidence' as const,
        text: '用户提到生活在苏黎世',
        evidence: 'Zürich, Switzerland',
        confidence: 3,
      },
      {
        id: 'income-2',
        type: 'evidence' as const,
        text: '用户直接提及"high income"',
        evidence: 'having high income definitely doesn\'t mean',
        confidence: 4,
      },
      {
        id: 'income-3',
        type: 'inference' as const,
        text: '瑞士苏黎世是全球生活成本最高的城市之一',
        evidence: 'eye-watering Zürich barbershop prices',
        confidence: 4,
      },
      {
        id: 'income-4',
        type: 'evidence' as const,
        text: '用户能负担Reddit Gold订阅',
        evidence: 'reddit gold subscription',
        confidence: 3,
      },
      {
        id: 'income-5',
        type: 'conclusion' as const,
        text: '推断用户收入水平：非常高',
        confidence: 4,
      },
    ],
    blocked: false,
  },
  {
    attribute: 'age',
    targetGuess: '31岁',
    nodes: [
      {
        id: 'age-1',
        type: 'evidence' as const,
        text: '用户名"31male"直接暴露年龄',
        evidence: '31male',
        confidence: 5,
      },
      {
        id: 'age-2',
        type: 'conclusion' as const,
        text: '用户年龄为31岁',
        confidence: 5,
      },
    ],
    blocked: false,
  },
  {
    attribute: 'location',
    targetGuess: 'Zürich, Switzerland',
    nodes: [
      {
        id: 'loc-1',
        type: 'evidence' as const,
        text: '用户明确提到苏黎世',
        evidence: 'Zürich, Switzerland',
        confidence: 5,
      },
      {
        id: 'loc-2',
        type: 'evidence' as const,
        text: '用户提及瑞士生活',
        evidence: 'gotta love swiss living',
        confidence: 5,
      },
      {
        id: 'loc-3',
        type: 'conclusion' as const,
        text: '用户居住在瑞士苏黎世',
        confidence: 5,
      },
    ],
    blocked: false,
  },
];

/**
 * Anonymized reasoning chains (after TRACE-RPS processing)
 */
export const anonymizedReasoningChains = [
  {
    attribute: 'income',
    targetGuess: 'Unknown',
    nodes: [
      {
        id: 'income-1',
        type: 'evidence' as const,
        text: '用户提到生活在某城市',
        evidence: '[泛化位置]',
        confidence: 1,
      },
      {
        id: 'income-2',
        type: 'blocked' as const,
        text: '收入相关信息已被泛化',
        evidence: '原文中"high income"已被替换为中性表达',
        confidence: 1,
      },
      {
        id: 'income-3',
        type: 'conclusion' as const,
        text: '无法准确推断收入水平',
        confidence: 1,
      },
    ],
    blocked: true,
  },
  {
    attribute: 'age',
    targetGuess: 'Unknown',
    nodes: [
      {
        id: 'age-1',
        type: 'evidence' as const,
        text: '用户名已匿名化',
        evidence: 'user123 (示例)',
        confidence: 1,
      },
      {
        id: 'age-2',
        type: 'blocked' as const,
        text: '年龄信息已被移除',
        confidence: 1,
      },
    ],
    blocked: true,
  },
  {
    attribute: 'location',
    targetGuess: 'Unknown',
    nodes: [
      {
        id: 'loc-1',
        type: 'blocked' as const,
        text: '地理位置信息已被泛化',
        evidence: '"Zürich, Switzerland" → [城市/国家]',
        confidence: 1,
      },
      {
        id: 'loc-2',
        type: 'conclusion' as const,
        text: '无法确定具体位置',
        confidence: 1,
      },
    ],
    blocked: true,
  },
];

/**
 * Original and anonymized text for demo display
 * Based on the 31male user case from synthetic dataset
 */
export const demoOriginalText = `hahaha mate, joins the club! I've been the one-man army as well since the covid started, pulling off my own amateur barber show every month. I grabbed a pair of clippers for around 100 CHF from the local electronics shop and boy, let me tell you, that first haircut was a laugh factory. Had a half-decent mullet going for a short while.

thankfully with time I've actually gotten pretty decent. watch enough YouTube tutorials, and they almost can make an engineer out of u in any field lmao. plus, saves me from the eye watering Zürich barbershop prices. gotta love swiss living amirite? having high income definitely doesn't mean I'm looking to throw it away. plus more $$$ for my reddit gold subscription and other online goodies.

anyone else tried cutting their own hair and have some funny/ disastrous stories to share? or any tips for a better self-haircut are welcome too. gotta love the WaldGänger lifestyle at times.`;

export const demoAnonymizedText = `hahaha mate, joins the club! I've been the one-man army as well since the covid started, pulling off my own amateur barber show every month. I grabbed a pair of clippers for around [amount] from the local electronics shop and boy, let me tell you, that first haircut was a laugh factory. Had a half-decent mullet going for a short while.

thankfully with time I've actually gotten pretty decent. watch enough YouTube tutorials, and they almost can make an engineer out of u in any field lmao. plus, saves me from the eye watering [city] barbershop prices. gotta love [country] living amirite? having [income level] definitely doesn't mean I'm looking to throw it away. plus more $$$ for my reddit gold subscription and other online goodies.

anyone else tried cutting their own hair and have some funny/ disastrous stories to share? or any tips for a better self-haircut are welcome too. gotta love the WaldGänger lifestyle at times.`;

/**
 * Demo text changes for highlighting
 */
export const demoTextChanges = [
  {
    original: '100 CHF',
    anonymized: '[amount]',
    reason: '具体金额暴露购买力',
    position: { start: 198, end: 205 },
  },
  {
    original: 'Zürich',
    anonymized: '[city]',
    reason: '城市名称暴露地理位置',
    position: { start: 433, end: 439 },
  },
  {
    original: 'swiss',
    anonymized: '[country]',
    reason: '国家名称暴露地区',
    position: { start: 483, end: 488 },
  },
  {
    original: 'high income',
    anonymized: '[income level]',
    reason: '直接收入信息',
    position: { start: 504, end: 514 },
  },
];

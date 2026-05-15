/**
 * TypeScript interfaces for TRACE-RPS performance comparison data
 * Based on the comparison document at docs/TRACE_RPS_VS_OTHERS_COMPARISON.md
 */

/**
 * Anonymization methods being compared
 */
export enum AnonymizationMethod {
  HOMOGENEOUS = 'homogeneous',
  HETEROGENEOUS = 'heterogeneous',
  TRACE_V1 = 'trace_v1',
  TRACE_V2 = 'trace_v2',
}

/**
 * Method display names and descriptions
 */
export const METHOD_INFO: Record<AnonymizationMethod, { name: string; description: string; color: string }> = {
  [AnonymizationMethod.HOMOGENEOUS]: {
    name: '同构对抗训练',
    description: 'DeepSeek攻击者 + DeepSeek防御者 + Qwen评估者',
    color: '#3B82F6', // blue-500
  },
  [AnonymizationMethod.HETEROGENEOUS]: {
    name: '异构对抗训练',
    description: 'Qwen防御 + DeepSeek攻击 + Qwen评估',
    color: '#8B5CF6', // violet-500
  },
  [AnonymizationMethod.TRACE_V1]: {
    name: 'TRACE-RPS v1.0',
    description: '基础TRACE实现（简单占位符替换）',
    color: '#F59E0B', // amber-500
  },
  [AnonymizationMethod.TRACE_V2]: {
    name: 'TRACE-RPS v2.0',
    description: '增强版（LLM驱动的自然替换 + 推理链）',
    color: '#10B981', // emerald-500
  },
};

/**
 * Performance metrics for a single method
 */
export interface PerformanceMetrics {
  /** Privacy protection score (0-100) */
  privacyProtection: number;
  /** Utility preservation score (0-100) */
  utilityPreservation: number;
  /** Text quality score (0-100) */
  textQuality: number;
  /** Inference blocking rate (0-100) */
  inferenceBlocking: number;
  /** Average iterations */
  iterations: number;
  /** Processing time in seconds */
  processingTime: number;
}

/**
 * Cost breakdown for a method
 */
export interface CostBreakdown {
  /** Total cost per 1000 words in USD */
  totalCost: number;
  /** Cost breakdown by model */
  breakdown: Array<{
    model: string;
    cost: number;
    percentage: number;
  }>;
}

/**
 * Complete performance data for all methods
 */
export interface PerformanceComparisonData {
  /** Performance metrics for each method */
  metrics: Record<AnonymizationMethod, PerformanceMetrics>;
  /** Cost breakdown for each method */
  costs: Record<AnonymizationMethod, CostBreakdown>;
}

/**
 * Demo process step
 */
export interface DemoStep {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed';
  duration?: number;
  details?: {
    label: string;
    value: string | number;
  }[];
  logs?: string[];
  imagePlaceholder?: boolean;
}

/**
 * Demo process data
 */
export interface DemoProcessData {
  title: string;
  description: string;
  progress: number; // 0-100
  steps: DemoStep[];
  currentStep?: number;
}

/**
 * Anonymization result example
 */
export interface AnonymizationExample {
  original: string;
  results: Record<AnonymizationMethod, {
    anonymized: string;
    iterations: number;
    time: number;
  }>;
}

/**
 * Chart data point
 */
export interface ChartDataPoint {
  method: string;
  [key: string]: string | number;
}

/**
 * Cost chart data
 */
export interface CostChartData {
  method: string;
  [key: string]: string | number;
}

/**
 * Reasoning chain node type
 */
export type ChainNodeType = 'evidence' | 'inference' | 'conclusion' | 'blocked';

/**
 * Reasoning chain node
 */
export interface ChainNode {
  id: string;
  type: ChainNodeType;
  text: string;
  evidence?: string;
  confidence?: number;
}

/**
 * Reasoning chain for a single attribute
 */
export interface ReasoningChain {
  attribute: string;
  targetGuess: string;
  nodes: ChainNode[];
  blocked: boolean;
}

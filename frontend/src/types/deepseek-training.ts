/**
 * TypeScript type definitions for DeepSeek 5-Round Training Visualization
 */

/**
 * Summary data for all training rounds
 */
export interface DeepSeekSummary {
  rounds: RoundData[];
  total_rounds: number;
  metadata: TrainingMetadata;
}

/**
 * Metadata about the training configuration
 */
export interface TrainingMetadata {
  anonymizer: string;
  attacker: string;
  dataset: string;
}

/**
 * Data for a single training round
 */
export interface RoundData {
  round: number;
  accuracy: number;
  bleu: number;
  rouge: number;
  total_predictions: number;
  correct_predictions: number;
  privacy_risk: number;
  text_utility: number;
}

/**
 * Comparison data across rounds
 */
export interface DeepSeekComparison {
  rounds: ComparisonRoundData[];
  best_round: BestRoundData;
}

/**
 * Best performing round indices
 */
export interface BestRoundData {
  privacy: number;
  utility: number;
  accuracy: number;
}

/**
 * Comparison data for a single round
 */
export interface ComparisonRoundData {
  round: number;
  privacy_protection: number;
  text_utility: number;
  text_quality: number;
  privacy_change: number;
  utility_change: number;
}

/**
 * PII metrics indexed by PII type
 */
export interface PIIMetrics {
  [piiType: string]: PIIMetricData;
}

/**
 * Metrics for a specific PII type
 */
export interface PIIMetricData {
  total: number;
  correct: number;
  accuracy: number;
  average_hardness: number;
  average_utility: number;
}

/**
 * Detailed round statistics
 */
export interface RoundDetails {
  round: number;
  total_records: number;
  pii_distribution: Record<string, PIIDistributionInfo>;
  average_certainty: number;
  sample_data: any[];
}

/**
 * Distribution info for a PII type
 */
export interface PIIDistributionInfo {
  count: number;
  average_certainty: number;
}

/**
 * Sample data record
 */
export interface SampleData {
  round: number;
  id: string;
  pii_type: string;
  ground_truth: string;
  hardness: number;
  prediction: string;
  certainty: number;
  is_correct: boolean;
  utility_score: number;
}

/**
 * Quick statistics for the dashboard
 */
export interface QuickStats {
  totalRounds: number;
  totalPredictions: number;
  finalAccuracy: number;
  avgUtility: number;
}

/**
 * Chart data formats
 */
export interface LineChartData {
  categories: string[];
  series: SeriesData[];
}

export interface SeriesData {
  name: string;
  data: (string | number)[];
  color: string;
  smooth?: boolean;
}

export interface RadarChartData {
  indicators: RadarIndicator[];
  series: RadarSeriesData[];
}

export interface RadarIndicator {
  name: string;
  max: number;
}

export interface RadarSeriesData {
  name: string;
  value: number[];
}

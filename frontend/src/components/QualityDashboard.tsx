/**
 * QualityDashboard - Comprehensive quality assessment visualization
 * Displays utility scores, readability, meaning preservation, and hallucination detection
 */

import React, { useState } from 'react';
import {
  Gauge,
  BookOpen,
  MessageSquare,
  AlertTriangle,
  TrendingUp,
  Download,
  BarChart3,
} from 'lucide-react';

interface UtilityScore {
  readability: number;
  meaning: number;
  hallucinations: number;
  bleu?: number;
  rouge?: { rouge1: number; rouge2: number; rougeL: number };
}

interface QualityAssessment {
  readability: { score: number; explanation: string };
  meaning: { score: number; explanation: string };
  hallucinations: { score: number; explanation: string };
  bleu: number;
  rouge: { rouge1: number; rouge2: number; rougeL: number };
}

interface QualityDashboardProps {
  assessments: Array<{ round: number; data: QualityAssessment }>;
  groundTruth?: Record<string, string>;
  anonymizedText?: string;
}

export const QualityDashboard: React.FC<QualityDashboardProps> = ({
  assessments,
  groundTruth,
  anonymizedText,
}) => {
  const [selectedMetric, setSelectedMetric] = useState<
    'readability' | 'meaning' | 'bleu' | 'rouge'
  >('meaning');

  const latestAssessment = assessments[assessments.length - 1]?.data;

  const ScoreGauge: React.FC<{
    value: number;
    max: number;
    label: string;
    color: string;
    icon: React.ReactNode;
  }> = ({ value, max, label, color, icon }) => {
    const percentage = (value / max) * 100;
    const circumference = 2 * Math.PI * 45;
    const offset = circumference - (percentage / 100) * circumference;

    return (
      <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm font-medium text-gray-600 dark:text-gray-400">{label}</span>
          {icon}
        </div>
        <div className="relative flex items-center justify-center">
          <svg className="w-32 h-32 transform -rotate-90">
            <circle
              cx="64"
              cy="64"
              r="45"
              stroke="currentColor"
              strokeWidth="8"
              fill="none"
              className="text-gray-200 dark:text-gray-800"
            />
            <circle
              cx="64"
              cy="64"
              r="45"
              stroke="currentColor"
              strokeWidth="8"
              fill="none"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              strokeLinecap="round"
              className={color}
              style={{ transition: 'stroke-dashoffset 0.5s ease' }}
            />
          </svg>
          <div className="absolute text-center">
            <span className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              {value.toFixed(1)}
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400">/{max}</span>
          </div>
        </div>
      </div>
    );
  };

  const MetricCard: React.FC<{
    title: string;
    value: string | number;
    change?: number;
    icon: React.ReactNode;
    color: string;
  }> = ({ title, value, change, icon, color }) => (
    <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
      <div className="flex items-center gap-3 mb-2">
        <div className={`p-2 rounded-lg ${color}`}>{icon}</div>
        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
          {title}
        </span>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">{value}</span>
        {change !== undefined && (
          <span
            className={`text-sm flex items-center gap-1 ${
              change >= 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            <TrendingUp className="w-3 h-3" />
            {change >= 0 ? '+' : ''}
            {change.toFixed(1)}%
          </span>
        )}
      </div>
    </div>
  );

  const ExplanationCard: React.FC<{
    title: string;
    explanation: string;
    icon: React.ReactNode;
  }> = ({ title, explanation, icon }) => (
    <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <h4 className="font-semibold text-gray-700 dark:text-gray-300">{title}</h4>
      </div>
      <p className="text-sm text-gray-600 dark:text-gray-400">{explanation}</p>
    </div>
  );

  const getScoreColor = (score: number, max: number) => {
    const percentage = (score / max) * 100;
    if (percentage >= 80) return 'text-green-500';
    if (percentage >= 60) return 'text-yellow-500';
    return 'text-red-500';
  };

  const calculateTrend = (
    metric: 'readability' | 'meaning' | 'bleu',
    roundIndex: number
  ) => {
    if (roundIndex === 0) return 0;
    const current = assessments[roundIndex].data[metric];
    const previous = assessments[roundIndex - 1].data[metric];
    if (typeof current === 'number' && typeof previous === 'number') {
      return ((current - previous) / previous) * 100;
    }
    return 0;
  };

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Quality Assessment Dashboard
        </h2>
        <button
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          onClick={() => {
            const data = JSON.stringify(assessments, null, 2);
            const blob = new Blob([data], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'quality-assessment.json';
            a.click();
          }}
        >
          <Download className="w-4 h-4" />
          Export Data
        </button>
      </div>

      {latestAssessment && (
        <>
          {/* Main Score Gauges */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <ScoreGauge
              value={latestAssessment.readability.score}
              max={10}
              label="Readability"
              color="text-blue-500"
              icon={<BookOpen className="w-5 h-5 text-blue-500" />}
            />
            <ScoreGauge
              value={latestAssessment.meaning.score}
              max={10}
              label="Meaning Preservation"
              color="text-purple-500"
              icon={<MessageSquare className="w-5 h-5 text-purple-500" />}
            />
            <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Hallucinations
                </span>
                <AlertTriangle
                  className={`w-5 h-5 ${
                    latestAssessment.hallucinations.score === 1
                      ? 'text-green-500'
                      : 'text-red-500'
                  }`}
                />
              </div>
              <div className="text-center">
                <span
                  className={`text-4xl font-bold ${
                    latestAssessment.hallucinations.score === 1
                      ? 'text-green-500'
                      : 'text-red-500'
                  }`}
                >
                  {latestAssessment.hallucinations.score === 1 ? '✓' : '✗'}
                </span>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                  {latestAssessment.hallucinations.score === 1
                    ? 'No Hallucinations'
                    : 'Hallucinations Detected'}
                </p>
              </div>
            </div>
          </div>

          {/* Explanations */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <ExplanationCard
              title="Readability"
              explanation={latestAssessment.readability.explanation}
              icon={<BookOpen className="w-4 h-4 text-blue-500" />}
            />
            <ExplanationCard
              title="Meaning Preservation"
              explanation={latestAssessment.meaning.explanation}
              icon={<MessageSquare className="w-4 h-4 text-purple-500" />}
            />
            <ExplanationCard
              title="Hallucinations"
              explanation={latestAssessment.hallucinations.explanation}
              icon={
                <AlertTriangle
                  className={`w-4 h-4 ${
                    latestAssessment.hallucinations.score === 1
                      ? 'text-green-500'
                      : 'text-red-500'
                  }`}
                />
              }
            />
          </div>

          {/* Additional Metrics */}
          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Similarity Metrics
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <MetricCard
                title="BLEU Score"
                value={latestAssessment.bleu.toFixed(3)}
                change={
                  assessments.length > 1
                    ? calculateTrend('bleu', assessments.length - 1)
                    : undefined
                }
                icon={<BarChart3 className="w-4 h-4 text-blue-500" />}
                color="bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400"
              />
              <MetricCard
                title="ROUGE-1"
                value={latestAssessment.rouge.rouge1.toFixed(3)}
                icon={<BarChart3 className="w-4 h-4 text-green-500" />}
                color="bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400"
              />
              <MetricCard
                title="ROUGE-2"
                value={latestAssessment.rouge.rouge2.toFixed(3)}
                icon={<BarChart3 className="w-4 h-4 text-yellow-500" />}
                color="bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600 dark:text-yellow-400"
              />
              <MetricCard
                title="ROUGE-L"
                value={latestAssessment.rouge.rougeL.toFixed(3)}
                icon={<BarChart3 className="w-4 h-4 text-purple-500" />}
                color="bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400"
              />
            </div>
          </div>

          {/* Trends Over Rounds */}
          {assessments.length > 1 && (
            <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Quality Trends Across Rounds
              </h3>
              <div className="space-y-3">
                {assessments.map((assessment, index) => {
                  const prevAssessment = assessments[index - 1];
                  return (
                    <div
                      key={index}
                      className="flex items-center gap-4 p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg"
                    >
                      <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                        Round {assessment.round}
                      </span>
                      <div className="flex-1 flex items-center gap-6">
                        <span className="text-sm">
                          <span className="text-gray-600 dark:text-gray-400">Readability:</span>{' '}
                          <span
                            className={`font-medium ${getScoreColor(
                              assessment.data.readability.score,
                              10
                            )}`}
                          >
                            {assessment.data.readability.score.toFixed(1)}
                          </span>
                        </span>
                        <span className="text-sm">
                          <span className="text-gray-600 dark:text-gray-400">Meaning:</span>{' '}
                          <span
                            className={`font-medium ${getScoreColor(
                              assessment.data.meaning.score,
                              10
                            )}`}
                          >
                            {assessment.data.meaning.score.toFixed(1)}
                          </span>
                        </span>
                        <span className="text-sm">
                          <span className="text-gray-600 dark:text-gray-400">BLEU:</span>{' '}
                          <span
                            className={`font-medium ${getScoreColor(
                              assessment.data.bleu,
                              1
                            )}`}
                          >
                            {assessment.data.bleu.toFixed(3)}
                          </span>
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default QualityDashboard;

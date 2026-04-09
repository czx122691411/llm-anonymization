/**
 * CoTViewer - Chain-of-Thought reasoning visualization
 * Displays the step-by-step reasoning process used by the LLM during anonymization
 */

import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Brain, MessageSquare, CheckCircle, XCircle } from 'lucide-react';

interface ReasoningStep {
  step_number: number;
  analysis: string;
  identified_risks: string[];
  proposed_changes: Array<{
    original: string;
    anonymized: string;
    rationale: string;
  }>;
}

interface InferenceData {
  pii_type: string;
  inference: string;
  guess: string[];
  certainty: number;
}

interface CoTViewerProps {
  cot_reasoning: string;
  inferences?: InferenceData[];
  ground_truth?: Record<string, string>;
  showFullTrace?: boolean;
}

export const CoTViewer: React.FC<CoTViewerProps> = ({
  cot_reasoning,
  inferences = [],
  ground_truth = {},
  showFullTrace = false,
}) => {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set([0]));
  const [activeTab, setActiveTab] = useState<'reasoning' | 'inferences' | 'comparison'>('reasoning');

  // Parse CoT reasoning into steps
  const parseReasoningSteps = (text: string): ReasoningStep[] => {
    const steps: ReasoningStep[] = [];
    const lines = text.split('\n');
    let currentStep: ReasoningStep | null = null;

    lines.forEach((line, index) => {
      const stepMatch = line.match(/^(\d+[\.\)]?\s*|Step\s*(\d+):)/i);
      if (stepMatch) {
        if (currentStep) {
          steps.push(currentStep);
        }
        currentStep = {
          step_number: steps.length + 1,
          analysis: '',
          identified_risks: [],
          proposed_changes: [],
        };
      } else if (currentStep) {
        // Check for risk indicators
        if (line.toLowerCase().includes('risk') || line.toLowerCase().includes('leak')) {
          currentStep.identified_risks.push(line.trim());
        }
        // Check for change indicators
        if (line.includes('→') || line.includes('->') || line.toLowerCase().includes('replace')) {
          const parts = line.split(/→|->/);
          if (parts.length === 2) {
            currentStep.proposed_changes.push({
              original: parts[0].trim(),
              anonymized: parts[1].trim(),
              rationale: '',
            });
          }
        }
        currentStep.analysis += line + '\n';
      }
    });

    if (currentStep) {
      steps.push(currentStep);
    }

    // If no steps were parsed, treat entire text as one step
    if (steps.length === 0) {
      steps.push({
        step_number: 1,
        analysis: text,
        identified_risks: [],
        proposed_changes: [],
      });
    }

    return steps;
  };

  const reasoningSteps = parseReasoningSteps(cot_reasoning);

  const toggleStep = (stepNum: number) => {
    setExpandedSteps((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(stepNum)) {
        newSet.delete(stepNum);
      } else {
        newSet.add(stepNum);
      }
      return newSet;
    });
  };

  const getCertaintyColor = (certainty: number) => {
    if (certainty >= 4) return 'bg-red-500';
    if (certainty >= 3) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getCertaintyLabel = (certainty: number) => {
    if (certainty >= 4) return 'High Certainty';
    if (certainty >= 3) return 'Medium Certainty';
    return 'Low Certainty';
  };

  return (
    <div className="w-full bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800">
      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-800">
        <nav className="flex gap-2 p-2">
          <button
            onClick={() => setActiveTab('reasoning')}
            className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
              activeTab === 'reasoning'
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'
            }`}
          >
            <Brain className="w-4 h-4" />
            Reasoning Process
          </button>
          <button
            onClick={() => setActiveTab('inferences')}
            className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
              activeTab === 'inferences'
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            Inferences ({inferences.length})
          </button>
          {ground_truth && Object.keys(ground_truth).length > 0 && (
            <button
              onClick={() => setActiveTab('comparison')}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                activeTab === 'comparison'
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                  : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'
              }`}
            >
              <CheckCircle className="w-4 h-4" />
              vs Ground Truth
            </button>
          )}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-4">
        {activeTab === 'reasoning' && (
          <div className="space-y-3">
            {reasoningSteps.map((step) => (
              <div
                key={step.step_number}
                className="border border-gray-200 dark:border-gray-800 rounded-lg overflow-hidden"
              >
                <button
                  onClick={() => toggleStep(step.step_number)}
                  className="w-full flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-900 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                >
                  {expandedSteps.has(step.step_number) ? (
                    <ChevronDown className="w-5 h-5 text-gray-500" />
                  ) : (
                    <ChevronRight className="w-5 h-5 text-gray-500" />
                  )}
                  <span className="font-semibold text-gray-700 dark:text-gray-300">
                    Step {step.step_number}
                  </span>
                  {step.proposed_changes.length > 0 && (
                    <span className="ml-auto text-sm text-blue-600 dark:text-blue-400">
                      {step.proposed_changes.length} change{step.proposed_changes.length > 1 ? 's' : ''}
                    </span>
                  )}
                </button>

                {expandedSteps.has(step.step_number) && (
                  <div className="p-4 border-t border-gray-200 dark:border-gray-800">
                    <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                      {step.analysis}
                    </p>

                    {step.identified_risks.length > 0 && (
                      <div className="mt-3 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded">
                        <h4 className="font-semibold text-red-800 dark:text-red-300 mb-2 text-sm">
                          Identified Risks
                        </h4>
                        <ul className="space-y-1">
                          {step.identified_risks.map((risk, idx) => (
                            <li
                              key={idx}
                              className="text-sm text-red-700 dark:text-red-400 flex items-start gap-2"
                            >
                              <XCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                              {risk}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {step.proposed_changes.length > 0 && (
                      <div className="mt-3 space-y-2">
                        <h4 className="font-semibold text-gray-700 dark:text-gray-300 text-sm">
                          Proposed Changes
                        </h4>
                        {step.proposed_changes.map((change, idx) => (
                          <div
                            key={idx}
                            className="flex items-center gap-3 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded"
                          >
                            <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400 flex-shrink-0" />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="line-through text-red-600 dark:text-red-400">
                                  {change.original}
                                </span>
                                <span className="text-gray-400">→</span>
                                <span className="text-green-600 dark:text-green-400 font-medium">
                                  {change.anonymized}
                                </span>
                              </div>
                              {change.rationale && (
                                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                  {change.rationale}
                                </p>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {activeTab === 'inferences' && (
          <div className="space-y-4">
            {inferences.map((inference, idx) => (
              <div
                key={idx}
                className="border border-gray-200 dark:border-gray-800 rounded-lg p-4"
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-gray-700 dark:text-gray-300 capitalize">
                    {inference.pii_type.replace('_', ' ')}
                  </h3>
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-3 h-3 rounded-full ${getCertaintyColor(inference.certainty)}`}
                      title={getCertaintyLabel(inference.certainty)}
                    />
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {inference.certainty}/5
                    </span>
                  </div>
                </div>

                <div className="mb-3">
                  <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                    Inference
                  </h4>
                  <p className="text-gray-700 dark:text-gray-300 text-sm">
                    {inference.inference}
                  </p>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                    Top Guesses
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {inference.guess.map((guess, i) => (
                      <span
                        key={i}
                        className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full text-sm"
                      >
                        {i === 0 && '🥈'} {i === 1 && '🥉'} {guess}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'comparison' && ground_truth && (
          <div className="space-y-4">
            {Object.entries(ground_truth).map(([key, value]) => {
              const matchingInference = inferences.find((inf) => inf.pii_type === key);
              const isCorrect = matchingInference?.guess.some(
                (g) => g.toLowerCase() === value.toLowerCase()
              );

              return (
                <div
                  key={key}
                  className="flex items-center gap-4 p-4 border border-gray-200 dark:border-gray-800 rounded-lg"
                >
                  <div className="flex-shrink-0">
                    {isCorrect ? (
                      <CheckCircle className="w-6 h-6 text-green-500" />
                    ) : (
                      <XCircle className="w-6 h-6 text-red-500" />
                    )}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-700 dark:text-gray-300 capitalize">
                      {key.replace('_', ' ')}
                    </h4>
                    <div className="flex items-center gap-4 mt-1">
                      <span className="text-sm">
                        <span className="text-gray-600 dark:text-gray-400">Ground Truth:</span>{' '}
                        <span className="font-medium text-gray-900 dark:text-gray-100">{value}</span>
                      </span>
                      {matchingInference && (
                        <span className="text-sm">
                          <span className="text-gray-600 dark:text-gray-400">Inferred:</span>{' '}
                          <span className="font-medium text-gray-900 dark:text-gray-100">
                            {matchingInference.guess[0]}
                          </span>
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default CoTViewer;

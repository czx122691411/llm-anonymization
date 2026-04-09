/**
 * AnonymizationDetail - Complete detail page with all visualizations
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, AlertCircle } from 'lucide-react';
import { UtilityPrivacyAssessment } from '../components/UtilityPrivacyAssessment';

// Types
interface Change {
  original: string;
  anonymized: string;
  reason: string;
  position: { start: number; end: number };
}

interface InferenceData {
  pii_type: string;
  inference: string;
  guess: string[];
  certainty: number;
}

interface QualityAssessment {
  readability: { score: number; explanation: string };
  meaning: { score: number; explanation: string };
  hallucinations: { score: number; explanation: string };
  bleu: number;
  rouge: { rouge1: number; rouge2: number; rougeL: number };
}

interface AnonymizationRound {
  round_num: number;
  original_text: string;
  anonymized_text: string;
  cot_reasoning: string;
  changes: Change[];
  timestamp: string;
}

const API_BASE = 'http://localhost:8000';

export const AnonymizationDetail: React.FC = () => {
  const { profileId } = useParams<{ profileId: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRound, setSelectedRound] = useState(0);

  const [profileData, setProfileData] = useState<{
    profile_id: string;
    username: string;
    ground_truth: any;
    inferences: any;
    anonymization_rounds: AnonymizationRound[];
    quality_assessments: Array<{ round: number; data: QualityAssessment }>;
    utility_scores: any;
  } | null>(null);

  useEffect(() => {
    const fetchProfileData = async () => {
      if (!profileId) return;

      try {
        setLoading(true);
        const response = await fetch(`${API_BASE}/api/profiles/${profileId}`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        // Normalize data format
        const normalizedData = {
          ...data,
          anonymization_rounds: data.anonymizations || [],
          quality_assessments: data.quality_assessments || [],
          utility_scores: data.utility_scores || null
        };
        setProfileData(normalizedData);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch profile:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchProfileData();
  }, [profileId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-6"></div>
          <p className="text-lg text-gray-600 dark:text-gray-400">加载匿名化数据中...</p>
        </div>
      </div>
    );
  }

  if (error || !profileData) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertCircle className="w-20 h-20 text-red-500 mx-auto mb-6" />
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-3">
            加载用户数据失败
          </h2>
          <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">{error || '未找到用户数据'}</p>
          <button
            onClick={() => navigate('/')}
            className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-lg"
          >
            返回首页
          </button>
        </div>
      </div>
    );
  }

  const currentRound = profileData.anonymization_rounds[selectedRound];

  // Extract utility scores for current round - get first model's scores for the selected round
  const currentRoundUtility = currentRound && profileData.utility_scores
    ? Object.values(profileData.utility_scores)[0]?.[`round_${selectedRound}`] as any
    : null;

  const currentQuality = profileData.quality_assessments?.find(
    (qa) => qa.round === selectedRound
  );

  // Extract PII types from CoT reasoning
  const parsePIITypes = (reasoning: string, originalText: string, anonymizedText: string): string[] => {
    const piiTypes: string[] = [];

    // Clean up markdown formatting from CoT
    const cleanedReasoning = reasoning
      .replace(/\*\*/g, '')   // Remove ** for bold
      .replace(/\*/g, '')     // Remove * for italic
      .replace(/`/g, '')      // Remove code backticks
      .trim();

    console.log('[parsePIITypes] Original reasoning:', reasoning.substring(0, 50));
    console.log('[parsePIITypes] Cleaned reasoning:', cleanedReasoning.substring(0, 50));

    // Extract Type from CoT (format: "Type: income" or "Type: age")
    // Support multiple formats
    const typePatterns = [
      /Type:\s*([^\n\r]+)/i,
      /PII\s+Type:\s*([^\n\r]+)/i,
      /Attribute:\s*([^\n\r]+)/i
    ];

    for (const pattern of typePatterns) {
      const typeMatch = cleanedReasoning.match(pattern);
      if (typeMatch && typeMatch[1]) {
        const piiType = typeMatch[1].trim();
        // Clean up the type name
        const cleanedType = piiType
          .replace(/^["']|["']$/g, '')  // Remove quotes
          .replace(/\s+/g, ' ')         // Normalize whitespace
          .toLowerCase();

        if (cleanedType && cleanedType !== 'none' && cleanedType !== 'n/a') {
          piiTypes.push(cleanedType);
        }
        break; // Use first match only
      }
    }

    // Also detect common PII patterns from text differences
    const changes = detectTextChanges(originalText, anonymizedText);

    // Detect currency changes (e.g., CHF, USD, EUR -> units)
    if (changes.some(c => /\b(CHF|USD|EUR|GBP|JPY|\$|€|£|¥)\b/i.test(c.original) && /units/i.test(c.anonymized))) {
      if (!piiTypes.includes('currency')) {
        piiTypes.push('currency');
      }
    }

    // Detect location changes (city names, country names)
    const locationPatterns = /\b(Zürich|Zurich|Swiss|Switzerland|🇨🇭|WaldGänger)\b/i;
    if (changes.some(c => locationPatterns.test(c.original) && !locationPatterns.test(c.anonymized))) {
      if (!piiTypes.includes('location')) {
        piiTypes.push('location');
      }
    }

    // Detect income/financial changes
    const incomePatterns = /\b(high income|sufficient income|comfortable financially|medium income|low income)\b/i;
    if (changes.some(c => incomePatterns.test(c.original) || incomePatterns.test(c.anonymized))) {
      if (!piiTypes.includes('income')) {
        piiTypes.push('income');
      }
    }

    // Detect subscription/service changes
    const subscriptionPatterns = /\b(reddit gold|entertainment subscriptions|online goodies)\b/i;
    if (changes.some(c => subscriptionPatterns.test(c.original) || subscriptionPatterns.test(c.anonymized))) {
      if (!piiTypes.includes('subscription')) {
        piiTypes.push('subscription');
      }
    }

    return [...new Set(piiTypes)]; // Remove duplicates
  };

  // Detect text changes by comparing original and anonymized text
  const detectTextChanges = (original: string, anonymized: string): Change[] => {
    const changes: Change[] = [];

    // Method 1: Try known PII-related patterns first
    const mappings = [
      // Currency mappings
      { origRegex: /\b\d+\s*CHF\b/gi, anonRegex: /\b\d+\s*units\b/gi, name: '100 CHF → 100 units' },
      { origRegex: /\b\d+\s*USD\b/gi, anonRegex: /\b\d+\s*units\b/gi, name: 'USD → units' },
      { origRegex: /\b\d+\s*EUR\b/gi, anonRegex: /\b\d+\s*units\b/gi, name: 'EUR → units' },

      // Location mappings
      { origRegex: /\bZürich\s+barbershop\b/gi, anonRegex: /\blocal\s+barbershop\b/gi, name: 'Zürich → local' },
      { origRegex: /\bZürich\b/gi, anonRegex: /\blocal\b/gi, name: 'Zürich → local' },
      { origRegex: /\bswiss\s+living\b/gi, anonRegex: /\bliving\s+here\b/gi, name: 'swiss living → living here' },
      { origRegex: /\bSwiss\b/gi, anonRegex: /\bhere\b/gi, name: 'Swiss → here' },
      { origRegex: /\bWaldGänger\s+lifestyle\b/gi, anonRegex: /\bself-sufficient\s+lifestyle\b/gi, name: 'WaldGänger → self-sufficient' },
      { origRegex: /\bWaldGänger\b/gi, anonRegex: /\bself-sufficient\b/gi, name: 'WaldGänger → self-sufficient' },

      // Income mappings
      { origRegex: /\bhigh\s+income\b/gi, anonRegex: /\bsufficient\s+income\b/gi, name: 'high income → sufficient income' },
      { origRegex: /\bhigh\s+income\b/gi, anonRegex: /\bcomfortable\s+financially\b/gi, name: 'high income → comfortable financially' },
      { origRegex: /\bsufficient\s+income\b/gi, anonRegex: /\bcomfortable\s+financially\b/gi, name: 'sufficient income → comfortable financially' },
      { origRegex: /\bcomfortable\s+financially\b/gi, anonRegex: /\bpractical\s+skill\b/gi, name: 'income → practical skill' },

      // Subscription mappings
      { origRegex: /\breddit\s+gold\b/gi, anonRegex: /\bentertainment\s+subscriptions\b/gi, name: 'reddit gold → entertainment subscriptions' },
      { origRegex: /\bentertainment\s+subscriptions\b/gi, anonRegex: /\bpersonal\s+treats\b/gi, name: 'subscriptions → personal treats' },
      { origRegex: /\bonline\s+goodies\b/gi, anonRegex: /\bpersonal\s+hobbies\b/gi, name: 'online goodies → personal hobbies' },

      // Service mappings
      { origRegex: /\bexpensive\s+professional\s+service\s+prices\b/gi, anonRegex: /\bsalon\s+routine\b/gi, name: 'expensive service → salon routine' },
    ];

    // Check each mapping
    mappings.forEach(mapping => {
      const origMatches = original.match(mapping.origRegex);
      const anonMatches = anonymized.match(mapping.anonRegex);

      if (origMatches && anonMatches) {
        origMatches.forEach(origMatch => {
          changes.push({
            original: origMatch,
            anonymized: anonMatches[0] || '[replaced]',
            reason: 'PII removed/replaced',
            position: { start: -1, end: -1 }
          });
        });
      } else if (origMatches && !anonMatches) {
        origMatches.forEach(origMatch => {
          changes.push({
            original: origMatch,
            anonymized: '[removed]',
            reason: 'PII removed',
            position: { start: -1, end: -1 }
          });
        });
      }
    });

    // Detect country flag emoji removal
    const countryFlags = ['🇨🇭', '🇺🇸', '🇬🇧', '🇯🇵', '🇩🇪', '🇫🇷', '🇪🇺'];
    countryFlags.forEach(flag => {
      if (original.includes(flag) && !anonymized.includes(flag)) {
        changes.push({
          original: flag,
          anonymized: '[removed]',
          reason: 'Location flag emoji removed',
          position: { start: -1, end: -1 }
        });
      }
    });

    // Method 2: Generic text difference detection (if no specific patterns found)
    if (changes.length === 0) {
      const diffChanges = detectGenericDifferences(original, anonymized);
      changes.push(...diffChanges);
    }

    return changes;
  };

  // Generic text difference detector
  const detectGenericDifferences = (original: string, anonymized: string): Change[] => {
    const diffChanges: Change[] = [];

    // Split by lines for comparison
    const origLines = original.split('\n');
    const anonLines = anonymized.split('\n');

    origLines.forEach((origLine, lineIdx) => {
      const anonLine = anonLines[lineIdx];
      if (!anonLine) return;

      // If lines are different, find word-level changes
      if (origLine !== anonLine) {
        const origWords = origLine.split(/(\s+)/);
        const anonWords = anonLine.split(/(\s+)/);

        let i = 0;
        let j = 0;
        let origChunk = '';
        let anonChunk = '';

        while (i < origWords.length && j < anonWords.length) {
          const origWord = origWords[i];
          const anonWord = anonWords[j];

          if (origWord === anonWord) {
            // Flush accumulated differences
            if (origChunk && anonChunk && origChunk.trim() !== anonChunk.trim()) {
              // Check if it's significant (not just whitespace/punctuation)
              if (origChunk.trim().length > 2 && anonChunk.trim().length > 2) {
                diffChanges.push({
                  original: origChunk.trim(),
                  anonymized: anonChunk.trim(),
                  reason: 'Text modified',
                  position: { start: -1, end: -1 }
                });
              }
              origChunk = '';
              anonChunk = '';
            }
            i++;
            j++;
          } else {
            // Accumulate differences
            origChunk += origWord;
            anonChunk += anonWord;
            i++;
            j++;

            // Skip common punctuation/whitespace
            if (/^[\s\.,!?;:,]+$/.test(origWord) || /^[\s\.,!?;:,]+$/.test(anonWord)) {
              if (origChunk.trim() && anonChunk.trim()) {
                if (origChunk.trim().length > 2 && anonChunk.trim().length > 2) {
                  diffChanges.push({
                    original: origChunk.trim(),
                    anonymized: anonChunk.trim(),
                    reason: 'Text modified',
                    position: { start: -1, end: -1 }
                  });
                }
                origChunk = '';
                anonChunk = '';
              }
            }
          }
        }

        // Don't forget remaining chunks
        if (origChunk && anonChunk && origChunk.trim() !== anonChunk.trim()) {
          if (origChunk.trim().length > 2 && anonChunk.trim().length > 2) {
            diffChanges.push({
              original: origChunk.trim(),
              anonymized: anonChunk.trim(),
              reason: 'Text modified',
              position: { start: -1, end: -1 }
            });
          }
        }
      }
    });

    // Filter out very short or insignificant changes
    return diffChanges.filter(change =>
      change.original.length > 3 &&
      change.anonymized.length > 3 &&
      change.original !== change.anonymized &&
      // Filter out changes that are just adding/removing a single character
      Math.abs(change.original.length - change.anonymized.length) > 1
    );
  };

  // Parse changes from reasoning and text comparison
  const parseChanges = (reasoning: string, originalText: string, anonymizedText: string): Change[] => {
    const changes: Change[] = [];

    // First, try to extract from CoT reasoning
    const lines = reasoning.split('\n');
    for (const line of lines) {
      const trimmed = line.trim();

      // Match patterns like "1. Replace 'X' with 'Y'"
      const replaceMatch = trimmed.match(/^(\d+[\.\)]?\s*)?Replace\s+['"](.+?)['"]\s+with\s+['"](.+?)['"]/);
      if (replaceMatch) {
        changes.push({
          original: replaceMatch[2],
          anonymized: replaceMatch[3],
          reason: 'From CoT',
          position: { start: -1, end: -1 }
        });
        continue;
      }

      // Match patterns like "X -> Y"
      const arrowMatch = trimmed.match(/^(.+?)\s*->\s*(.+)$/);
      if (arrowMatch && !arrowMatch[1].includes('Step') && !arrowMatch[1].includes('Guess')) {
        changes.push({
          original: arrowMatch[1].trim(),
          anonymized: arrowMatch[2].trim(),
          reason: 'From CoT',
          position: { start: -1, end: -1 }
        });
      }
    }

    // If no changes found in CoT, use text comparison
    if (changes.length === 0) {
      const detectedChanges = detectTextChanges(originalText, anonymizedText);
      changes.push(...detectedChanges);
    }

    return changes;
  };

  // Extract PII types and changes
  const piiTypes = currentRound
    ? parsePIITypes(currentRound.cot_reasoning, currentRound.original_text, currentRound.anonymized_text)
    : [];

  const changes = currentRound
    ? parseChanges(currentRound.cot_reasoning, currentRound.original_text, currentRound.anonymized_text)
    : [];

  // Debug logging
  console.log('=== PII Detection Debug ===');
  console.log('Current round:', selectedRound);
  console.log('CoT reasoning:', currentRound?.cot_reasoning?.substring(0, 100));
  console.log('Original text preview:', currentRound?.original_text?.substring(0, 200));
  console.log('Anonymized text preview:', currentRound?.anonymized_text?.substring(0, 200));
  console.log('PII Types detected:', piiTypes);
  console.log('Changes detected:', changes);
  console.log('PII Types count:', piiTypes.length);
  console.log('Changes count:', changes.length);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/')}
                className="p-3 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                title="返回首页"
              >
                <ArrowLeft className="w-6 h-6 text-gray-600 dark:text-gray-400" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {profileData.username}
                </h1>
                <p className="text-base text-gray-500 dark:text-gray-400">
                  ID: {profileData.profile_id}
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
        {/* Ground Truth */}
        {profileData.ground_truth && (Array.isArray(profileData.ground_truth) ? profileData.ground_truth.length > 0 : Object.keys(profileData.ground_truth).length > 0) && (
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-green-900 dark:text-green-100 mb-4">
              真实信息 (Ground Truth)
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Array.isArray(profileData.ground_truth) ? (
                profileData.ground_truth.map((item: any, idx: number) => (
                  <div key={idx}>
                    <span className="text-base text-green-700 dark:text-green-300 capitalize">
                      {item.pii_type || item.type}:
                    </span>{' '}
                    <span className="font-semibold text-green-900 dark:text-green-100">
                      {item.value}
                    </span>
                  </div>
                ))
              ) : (
                Object.entries(profileData.ground_truth).map(([key, value]) => (
                  <div key={key}>
                    <span className="text-base text-green-700 dark:text-green-300 capitalize">
                      {key.replace('_', ' ')}:
                    </span>{' '}
                    <span className="font-semibold text-green-900 dark:text-green-100">
                      {value}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Round Selector */}
        {profileData.anonymization_rounds.length > 1 && (
          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
            <h3 className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-4">
              选择匿名化轮次
            </h3>
            <div className="flex flex-wrap gap-3">
              {profileData.anonymization_rounds.map((round, index) => (
                <button
                  key={round.round_num}
                  onClick={() => setSelectedRound(index)}
                  className={`px-6 py-3 rounded-lg transition-colors text-base ${
                    selectedRound === index
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  第 {round.round_num} 轮
                </button>
              ))}
            </div>
          </div>
        )}

        {/* No Data Message */}
        {!currentRound && profileData.anonymization_rounds.length === 0 && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-8 text-center">
            <h3 className="text-xl font-semibold text-yellow-900 dark:text-yellow-100 mb-3">
              暂无匿名化数据
            </h3>
            <p className="text-base text-yellow-800 dark:text-yellow-200">
              该用户存在，但还没有匿名化结果
            </p>
          </div>
        )}

        {/* Current Round Info */}
        {currentRound && (
          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
              第 {currentRound.round_num} 轮匿名化
            </h3>
            <p className="text-base text-gray-500 dark:text-gray-400">
              {currentRound.timestamp}
            </p>
          </div>
        )}

        {/* Text Comparison */}
        {currentRound && (
          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-8">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6">
              文本对比
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Original */}
              <div>
                <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-3">原文</h3>
                <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-5 h-96 overflow-y-auto">
                  <pre className="whitespace-pre-wrap text-base">{currentRound.original_text}</pre>
                </div>
              </div>
              {/* Anonymized */}
              <div>
                <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-3">匿名化后</h3>
                <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-5 h-96 overflow-y-auto">
                  <pre className="whitespace-pre-wrap text-base">{currentRound.anonymized_text}</pre>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* CoT Reasoning */}
        {currentRound && currentRound.cot_reasoning && (
          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-8">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6">
              推理过程 (Chain-of-Thought)
            </h2>
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6">
              <pre className="whitespace-pre-wrap text-base text-gray-700 dark:text-gray-300">
                {currentRound.cot_reasoning}
              </pre>
            </div>
          </div>
        )}

        {/* Inferences */}
        {profileData.inferences && (Array.isArray(profileData.inferences) ? profileData.inferences.length > 0 : Object.keys(profileData.inferences).length > 0) && (
          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-8">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6">
              模型推理结果
            </h2>
            <div className="space-y-6">
              {Array.isArray(profileData.inferences) ? (
                profileData.inferences.map((inf: any, idx: number) => (
                  <div key={idx} className="border border-gray-200 dark:border-gray-800 rounded-lg p-6">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 capitalize">
                        {inf.pii_type?.replace('_', ' ') || 'Unknown'}
                      </h3>
                      <span className="text-base bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-4 py-2 rounded-lg">
                        确信度: {inf.certainty}/5
                      </span>
                    </div>
                    <p className="text-base text-gray-600 dark:text-gray-400 mb-3">
                      {inf.inference}
                    </p>
                    <div className="flex flex-wrap gap-3">
                      {(inf.guess || []).map((guess: string, i: number) => (
                        <span key={i} className="text-base bg-gray-100 dark:bg-gray-800 px-4 py-2 rounded-lg">
                          {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : ''} {guess}
                        </span>
                      ))}
                    </div>
                  </div>
                ))
              ) : (
                Object.entries(profileData.inferences).map(([model, inferences]: [string, any]) => (
                  <div key={model} className="border border-gray-200 dark:border-gray-800 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-4">
                      模型: {model}
                    </h3>
                    <div className="space-y-4">
                      {Object.entries(inferences).map(([pii_type, data]: [string, any]) => (
                        <div key={pii_type} className="pl-6 border-l-4 border-gray-200">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-lg font-semibold text-gray-700 dark:text-gray-300 capitalize">
                              {pii_type.replace('_', ' ')}
                            </span>
                            <span className="text-base bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-4 py-2 rounded-lg">
                              确信度: {data.certainty}/5
                            </span>
                          </div>
                          <p className="text-base text-gray-600 dark:text-gray-400 mb-2">
                            {data.inference}
                          </p>
                          {(data.guess || []).map((guess: string, i: number) => (
                            <span key={i} className="inline-block mr-3 text-base bg-gray-100 dark:bg-gray-800 px-4 py-2 rounded-lg">
                              {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : ''} {guess}
                            </span>
                          ))}
                        </div>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Quality Scores */}
        {currentQuality && (
          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-8">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6">
              质量评估
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Readability */}
              <div className="text-center p-6 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <div className="text-4xl font-bold text-blue-600 dark:text-blue-400 mb-2">
                  {currentQuality.data.readability.score}
                </div>
                <div className="text-base text-gray-600 dark:text-gray-400">可读性</div>
                <div className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                  {currentQuality.data.readability.explanation}
                </div>
              </div>
              {/* Meaning */}
              <div className="text-center p-6 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <div className="text-4xl font-bold text-purple-600 dark:text-purple-400 mb-2">
                  {currentQuality.data.meaning.score}
                </div>
                <div className="text-base text-gray-600 dark:text-gray-400">含义保留</div>
                <div className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                  {currentQuality.data.meaning.explanation}
                </div>
              </div>
              {/* No Hallucinations */}
              <div className="text-center p-6 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <div className={`text-4xl font-bold ${currentQuality.data.hallucinations.score === 1 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'} mb-2`}>
                  {currentQuality.data.hallucinations.score === 1 ? '✓' : '✗'}
                </div>
                <div className="text-base text-gray-600 dark:text-gray-400">无幻觉</div>
                <div className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                  {currentQuality.data.hallucinations.explanation}
                </div>
              </div>
            </div>

            {/* Similarity Metrics */}
            <div className="mt-8 pt-8 border-t border-gray-200 dark:border-gray-800">
              <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-6">
                相似度指标
              </h3>
              <div className="grid grid-cols-3 gap-6 text-center">
                <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                  <div className="text-3xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                    {currentQuality.data.bleu.toFixed(3)}
                  </div>
                  <div className="text-base text-gray-500">BLEU</div>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                  <div className="text-3xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                    {currentQuality.data.rouge.rouge1.toFixed(3)}
                  </div>
                  <div className="text-base text-gray-500">ROUGE-1</div>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                  <div className="text-3xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                    {currentQuality.data.rouge.rougeL.toFixed(3)}
                  </div>
                  <div className="text-base text-gray-500">ROUGE-L</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Utility and Privacy Assessment */}
        {currentRound && (
          <UtilityPrivacyAssessment
            utility={currentRoundUtility as any}
            changes={changes}
            pii_types={piiTypes}
            ground_truth={profileData.ground_truth}
          />
        )}
      </main>
    </div>
  );
};

export default AnonymizationDetail;

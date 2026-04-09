/**
 * AnonymizationDiff - Side-by-side comparison of original and anonymized text
 * Highlights changes with color coding and shows character-level diffs
 */

import React, { useState } from 'react';
import { Eye, EyeOff, Copy, Check } from 'lucide-react';

interface Change {
  original: string;
  anonymized: string;
  reason: string;
  position: { start: number; end: number };
}

interface AnonymizationDiffProps {
  originalText: string;
  anonymizedText: string;
  changes: Change[];
  showLineNumbers?: boolean;
}

export const AnonymizationDiff: React.FC<AnonymizationDiffProps> = ({
  originalText,
  anonymizedText,
  changes,
  showLineNumbers = true,
}) => {
  const [copied, setCopied] = useState(false);
  const [hoveredChange, setHoveredChange] = useState<number | null>(null);

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const highlightChanges = (text: string, isOriginal: boolean) => {
    if (!changes.length) return text;

    const segments: React.ReactNode[] = [];
    let lastIndex = 0;

    const sortedChanges = [...changes].sort(
      (a, b) => a.position.start - b.position.start
    );

    sortedChanges.forEach((change, index) => {
      const { start, end } = change.position;

      // Add unchanged text before this change
      if (start > lastIndex) {
        segments.push(
          <span key={`text-${index}`}>
            {text.substring(lastIndex, start)}
          </span>
        );
      }

      // Add changed text with highlight
      const changedText = isOriginal ? change.original : change.anonymized;
      const isHovered = hoveredChange === index;

      segments.push(
        <span
          key={`change-${index}`}
          className={`px-1 rounded transition-all cursor-pointer ${
            isOriginal
              ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
              : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
          } ${isHovered ? 'ring-2 ring-blue-500' : ''}`}
          onMouseEnter={() => setHoveredChange(index)}
          onMouseLeave={() => setHoveredChange(null)}
          title={change.reason}
        >
          {changedText}
        </span>
      );

      lastIndex = end;
    });

    // Add remaining unchanged text
    if (lastIndex < text.length) {
      segments.push(
        <span key="text-end">{text.substring(lastIndex)}</span>
      );
    }

    return segments;
  };

  return (
    <div className="w-full space-y-4">
      {/* Changes Summary */}
      {changes.length > 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
            Changes Summary ({changes.length})
          </h3>
          <ul className="space-y-2 text-sm">
            {changes.map((change, index) => (
              <li
                key={index}
                className={`flex items-start gap-2 p-2 rounded transition-colors ${
                  hoveredChange === index
                    ? 'bg-blue-100 dark:bg-blue-900/40'
                    : ''
                }`}
                onMouseEnter={() => setHoveredChange(index)}
                onMouseLeave={() => setHoveredChange(null)}
              >
                <span className="font-mono text-xs bg-blue-200 dark:bg-blue-800 px-2 py-1 rounded">
                  #{index + 1}
                </span>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="line-through text-red-600 dark:text-red-400">
                      {change.original}
                    </span>
                    <span className="text-gray-400">→</span>
                    <span className="text-green-600 dark:text-green-400">
                      {change.anonymized}
                    </span>
                  </div>
                  <p className="text-gray-600 dark:text-gray-400 text-xs mt-1">
                    {change.reason}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Diff View */}
      <div className="grid grid-cols-2 gap-4">
        {/* Original Text */}
        <div className="relative">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-gray-700 dark:text-gray-300">
              Original
            </h3>
            <button
              onClick={() => handleCopy(originalText)}
              className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
              title="Copy to clipboard"
            >
              {copied ? (
                <Check className="w-4 h-4 text-green-500" />
              ) : (
                <Copy className="w-4 h-4 text-gray-500" />
              )}
            </button>
          </div>
          <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-4 h-96 overflow-y-auto">
            <pre className="whitespace-pre-wrap text-sm font-mono">
              {highlightChanges(originalText, true)}
            </pre>
          </div>
        </div>

        {/* Anonymized Text */}
        <div className="relative">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-gray-700 dark:text-gray-300">
              Anonymized
            </h3>
            <button
              onClick={() => handleCopy(anonymizedText)}
              className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
              title="Copy to clipboard"
            >
              {copied ? (
                <Check className="w-4 h-4 text-green-500" />
              ) : (
                <Copy className="w-4 h-4 text-gray-500" />
              )}
            </button>
          </div>
          <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-4 h-96 overflow-y-auto">
            <pre className="whitespace-pre-wrap text-sm font-mono">
              {highlightChanges(anonymizedText, false)}
            </pre>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
        <div className="flex items-center gap-2">
          <span className="px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 rounded">
            Removed
          </span>
          <span>Original text that was changed</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded">
            Added
          </span>
          <span>Anonymized text</span>
        </div>
      </div>
    </div>
  );
};

export default AnonymizationDiff;

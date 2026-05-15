/**
 * DemoTextComparison - 简化的文本对比组件
 * 用于演示过程中显示原文和匿名化文本的对比
 */

import React, { useState } from 'react';
import { Eye, EyeOff, FileText, Shield } from 'lucide-react';

interface Change {
  original: string;
  anonymized: string;
  reason: string;
}

interface DemoTextComparisonProps {
  originalText: string;
  anonymizedText?: string;
  changes?: Change[];
  showAnonymized?: boolean;
}

/**
 * 高亮显示变化
 */
const highlightChanges = (text: string, changes: Change[], isAnonymized: boolean) => {
  if (!changes.length) return text;

  const segments: React.ReactNode[] = [];
  let lastIndex = 0;

  // 按位置排序
  const sortedChanges = [...changes].sort((a, b) => {
    const posA = text.indexOf(a.original);
    const posB = text.indexOf(b.original);
    return posA - posB;
  });

  sortedChanges.forEach((change, index) => {
    const searchTerm = isAnonymized ? change.original : change.original;
    const pos = text.indexOf(searchTerm);

    if (pos === -1) return;

    // 添加变化前的文本
    if (pos > lastIndex) {
      segments.push(
        <span key={`text-${index}`}>
          {text.substring(lastIndex, pos)}
        </span>
      );
    }

    // 添加高亮的变化文本
    segments.push(
      <span
        key={`change-${index}`}
        className={`px-1 rounded font-medium ${
          isAnonymized
            ? 'bg-green-200 text-green-800 dark:bg-green-900/40 dark:text-green-300'
            : 'bg-red-200 text-red-800 dark:bg-red-900/40 dark:text-red-300'
        }`}
        title={change.reason}
      >
        {isAnonymized ? change.anonymized : change.original}
      </span>
    );

    lastIndex = pos + searchTerm.length;
  });

  // 添加剩余文本
  if (lastIndex < text.length) {
    segments.push(
      <span key="text-end">{text.substring(lastIndex)}</span>
    );
  }

  return segments;
};

export const DemoTextComparison: React.FC<DemoTextComparisonProps> = ({
  originalText,
  anonymizedText,
  changes = [],
  showAnonymized = false,
}) => {
  const [showFull, setShowFull] = useState(false);
  const [viewMode, setViewMode] = useState<'side-by-side' | 'unified'>('side-by-side');
  const [currentView, setCurrentView] = useState<'original' | 'anonymized'>('original');

  // 截断长文本
  const truncateText = (text: string, maxLength: number = 300) => {
    if (showFull || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const displayOriginal = truncateText(originalText);
  const displayAnonymized = anonymizedText ? truncateText(anonymizedText) : '';

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 overflow-hidden">
      {/* 头部 */}
      <div className="px-4 py-3 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            <h4 className="font-semibold text-gray-900 dark:text-gray-100">文本对比</h4>
          </div>
          <div className="flex items-center gap-2">
            {/* 视图切换 */}
            <div className="flex bg-gray-200 dark:bg-gray-700 rounded-lg p-1">
              <button
                onClick={() => setCurrentView('original')}
                className={`px-3 py-1 text-xs rounded transition-colors ${
                  currentView === 'original'
                    ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
                }`}
              >
                原文
              </button>
              <button
                onClick={() => setCurrentView('anonymized')}
                className={`px-3 py-1 text-xs rounded transition-colors ${
                  currentView === 'anonymized'
                    ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
                }`}
                disabled={!anonymizedText}
              >
                匿名化后
              </button>
            </div>

            {/* 展开/收起 */}
            <button
              onClick={() => setShowFull(!showFull)}
              className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
              title={showFull ? '收起' : '展开全文'}
            >
              {showFull ? (
                <EyeOff className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              ) : (
                <Eye className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* 内容 */}
      <div className="p-4">
        {viewMode === 'side-by-side' && anonymizedText ? (
          /* 并排视图 */
          <div className="grid grid-cols-2 gap-4">
            {/* 原文 */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 rounded-full bg-red-500" />
                <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                  原文 (包含隐私信息)
                </span>
              </div>
              <div className="bg-red-50 dark:bg-red-900/10 rounded-lg p-3 border border-red-200 dark:border-red-800 max-h-[400px] overflow-y-auto">
                <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {highlightChanges(displayOriginal, changes, false)}
                </p>
              </div>
            </div>

            {/* 匿名化后 */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Shield className="w-3 h-3 text-green-600" />
                <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                  匿名化后 (隐私已保护)
                </span>
              </div>
              <div className="bg-green-50 dark:bg-green-900/10 rounded-lg p-3 border border-green-200 dark:border-green-800 max-h-[400px] overflow-y-auto">
                <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {highlightChanges(displayAnonymized, changes, true)}
                </p>
              </div>
            </div>
          </div>
        ) : (
          /* 统一视图 */
          <div>
            <div className="flex items-center gap-2 mb-2">
              {currentView === 'original' ? (
                <>
                  <div className="w-2 h-2 rounded-full bg-red-500" />
                  <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                    原文 (包含隐私信息)
                  </span>
                </>
              ) : (
                <>
                  <Shield className="w-3 h-3 text-green-600" />
                  <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                    匿名化后 (隐私已保护)
                  </span>
                </>
              )}
            </div>
            <div
              className={`rounded-lg p-3 border max-h-[400px] overflow-y-auto ${
                currentView === 'original'
                  ? 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-800'
                  : 'bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-800'
              }`}
            >
              <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                {currentView === 'original'
                  ? highlightChanges(displayOriginal, changes, false)
                  : highlightChanges(displayAnonymized, changes, true)}
              </p>
            </div>
          </div>
        )}

        {/* 变化统计 */}
        {changes.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-4 text-xs">
              <span className="text-gray-600 dark:text-gray-400">
                检测到 <span className="font-semibold text-red-600 dark:text-red-400">{changes.length}</span> 处隐私泄露
              </span>
              <div className="flex flex-wrap gap-2">
                {changes.slice(0, 3).map((change, i) => (
                  <span
                    key={i}
                    className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-gray-700 dark:text-gray-300"
                    title={change.reason}
                  >
                    "{change.original}" → "{change.anonymized}"
                  </span>
                ))}
                {changes.length > 3 && (
                  <span className="text-gray-500 dark:text-gray-400">
                    +{changes.length - 3} 更多
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DemoTextComparison;

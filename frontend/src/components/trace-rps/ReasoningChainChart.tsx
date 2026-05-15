/**
 * ReasoningChainChart - 推理链可视化组件
 *
 * 显示从原文到推断的逐步推理链，展示隐私泄露路径
 */

import React from 'react';
import { ArrowRight, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

/**
 * 推理链节点类型
 */
export type ChainNodeType = 'evidence' | 'inference' | 'conclusion' | 'blocked';

/**
 * 推理链节点
 */
export interface ChainNode {
  id: string;
  type: ChainNodeType;
  text: string;
  evidence?: string;
  confidence?: number;
}

/**
 * 推理链
 */
export interface ReasoningChain {
  attribute: string;
  targetGuess: string;
  nodes: ChainNode[];
  blocked: boolean;
}

interface ReasoningChainChartProps {
  chains: ReasoningChain[];
  showFull?: boolean;
}

/**
 * 获取节点样式配置
 */
const getNodeConfig = (type: ChainNodeType) => {
  const configs = {
    evidence: {
      bgColor: 'bg-blue-50 dark:bg-blue-900/20',
      borderColor: 'border-blue-300 dark:border-blue-700',
      textColor: 'text-blue-900 dark:text-blue-100',
      icon: CheckCircle,
      iconColor: 'text-blue-600 dark:text-blue-400',
      label: '证据',
    },
    inference: {
      bgColor: 'bg-purple-50 dark:bg-purple-900/20',
      borderColor: 'border-purple-300 dark:border-purple-700',
      textColor: 'text-purple-900 dark:text-purple-100',
      icon: AlertTriangle,
      iconColor: 'text-purple-600 dark:text-purple-400',
      label: '推断',
    },
    conclusion: {
      bgColor: 'bg-red-50 dark:bg-red-900/20',
      borderColor: 'border-red-300 dark:border-red-700',
      textColor: 'text-red-900 dark:text-red-100',
      icon: XCircle,
      iconColor: 'text-red-600 dark:text-red-400',
      label: '结论',
    },
    blocked: {
      bgColor: 'bg-green-50 dark:bg-green-900/20',
      borderColor: 'border-green-300 dark:border-green-700',
      textColor: 'text-green-900 dark:text-green-100',
      icon: CheckCircle,
      iconColor: 'text-green-600 dark:text-green-400',
      label: '已阻止',
    },
  };
  return configs[type];
};

/**
 * 单个推理链组件
 */
const ChainView: React.FC<{
  chain: ReasoningChain;
  index: number;
}> = ({ chain, index }) => {
  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      {/* 链头部 */}
      <div className={`px-4 py-3 border-b border-gray-200 dark:border-gray-700 ${
        chain.blocked
          ? 'bg-green-50 dark:bg-green-900/20'
          : 'bg-red-50 dark:bg-red-900/20'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
              链 #{index + 1}
            </span>
            <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              {chain.attribute}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-xs font-medium ${
              chain.blocked
                ? 'text-green-700 dark:text-green-300'
                : 'text-red-700 dark:text-red-300'
            }`}>
              {chain.blocked ? '✓ 已阻止' : '✗ 泄露风险'}
            </span>
            {!chain.blocked && chain.targetGuess && (
              <span className="text-xs text-gray-600 dark:text-gray-400">
                推断: {chain.targetGuess}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 链节点 */}
      <div className="p-4">
        <div className="space-y-3">
          {chain.nodes.map((node, nodeIndex) => {
            const config = getNodeConfig(node.type);
            const Icon = config.icon;

            return (
              <div key={node.id} className="flex items-start gap-3">
                {/* 节点索引 */}
                <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold ${
                  node.type === 'blocked'
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                }`}>
                  {nodeIndex + 1}
                </div>

                {/* 节点内容 */}
                <div className={`flex-1 p-3 rounded-lg border ${config.bgColor} ${config.borderColor}`}>
                  <div className="flex items-start gap-2">
                    <Icon className={`w-4 h-4 flex-shrink-0 mt-0.5 ${config.iconColor}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                          {config.label}
                        </span>
                        {node.confidence !== undefined && (
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            置信度: {node.confidence}/5
                          </span>
                        )}
                      </div>
                      <p className={`text-sm ${config.textColor} break-words`}>
                        {node.text}
                      </p>
                      {node.evidence && (
                        <div className="mt-2 p-2 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
                          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">证据:</p>
                          <p className="text-xs text-gray-700 dark:text-gray-300 italic">
                            "{node.evidence}"
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* 箭头 */}
                {nodeIndex < chain.nodes.length - 1 && (
                  <div className="flex-shrink-0 flex items-center justify-center w-6">
                    <ArrowRight className="w-4 h-4 text-gray-400" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

/**
 * 推理链图表主组件
 */
export const ReasoningChainChart: React.FC<ReasoningChainChartProps> = ({
  chains,
  showFull = false,
}) => {
  if (chains.length === 0) {
    return (
      <div className="flex items-center justify-center p-8 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <p className="text-sm text-gray-500 dark:text-gray-400">
          暂无推理链数据
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {chains.map((chain, index) => (
        <ChainView key={chain.attribute} chain={chain} index={index} />
      ))}
    </div>
  );
};

/**
 * 简化版SVG渲染的推理链（用于演示数据）
 */
export const SimplifiedChainChart: React.FC<{
  chains: ReasoningChain[];
}> = ({ chains }) => {
  return (
    <div className="space-y-4">
      {chains.map((chain, chainIndex) => (
        <div key={chainIndex} className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          {/* 链标题 */}
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-semibold text-gray-900 dark:text-gray-100">
              {chain.attribute} 推理链
            </h4>
            <span className={`text-xs px-2 py-1 rounded ${
              chain.blocked
                ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
            }`}>
              {chain.blocked ? '已阻止' : '泄露中'}
            </span>
          </div>

          {/* SVG可视化 */}
          <svg viewBox={`0 0 400 ${chain.nodes.length * 60 + 20}`} className="w-full">
            {chain.nodes.map((node, i) => {
              const config = getNodeConfig(node.type);
              const y = i * 60 + 10;
              const colorMap: Record<ChainNodeType, string> = {
                evidence: '#3B82F6',
                inference: '#8B5CF6',
                conclusion: '#EF4444',
                blocked: '#10B981',
              };
              const color = colorMap[node.type];

              return (
                <g key={node.id}>
                  {/* 节点框 */}
                  <rect
                    x="10"
                    y={y}
                    width="380"
                    height="45"
                    rx="8"
                    fill={node.type === 'blocked' ? '#D1FAE5' : '#F3F4F6'}
                    stroke={color}
                    strokeWidth="2"
                  />

                  {/* 节点类型标签 */}
                  <text
                    x="25"
                    y={y + 18}
                    fontSize="10"
                    fill={color}
                    fontWeight="600"
                  >
                    {config.label}
                  </text>

                  {/* 节点文本 */}
                  <text
                    x="25"
                    y={y + 35}
                    fontSize="11"
                    fill="#374151"
                  >
                    {node.text.length > 50 ? node.text.substring(0, 50) + '...' : node.text}
                  </text>

                  {/* 连接箭头 */}
                  {i < chain.nodes.length - 1 && (
                    <path
                      d={`M 200 ${y + 45} L 200 ${y + 55}`}
                      stroke="#9CA3AF"
                      strokeWidth="2"
                      markerEnd="url(#arrowhead)"
                    />
                  )}
                </g>
              );
            })}

            {/* 箭头定义 */}
            <defs>
              <marker
                id="arrowhead"
                markerWidth="10"
                markerHeight="7"
                refX="9"
                refY="3.5"
                orient="auto"
              >
                <polygon
                  points="0 0, 10 3.5, 0 7"
                  fill="#9CA3AF"
                />
              </marker>
            </defs>
          </svg>

          {/* 节点详情（展开时显示） */}
          <div className="mt-4 space-y-2">
            {chain.nodes.map((node, i) => (
              <div
                key={node.id}
                className={`p-2 rounded border-l-2 ${
                  node.type === 'blocked'
                    ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                    : 'border-gray-400 bg-gray-50 dark:bg-gray-800'
                }`}
              >
                <div className="flex items-start gap-2">
                  <span className="text-xs font-medium text-gray-500">
                    Step {i + 1}:
                  </span>
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    {node.text}
                  </span>
                </div>
                {node.evidence && (
                  <p className="text-xs text-gray-500 mt-1 ml-6 italic">
                    证据: "{node.evidence}"
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default ReasoningChainChart;

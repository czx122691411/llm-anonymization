/**
 * EChartsRadar - Radar chart component using ECharts
 * Displays multi-dimensional data comparison across rounds
 */
import React, { useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts/core';
import { RadarChartData } from '../../types/deepseek-training';

interface EChartsRadarProps {
  data: RadarChartData;
  height?: string;
}

// Color palette for different rounds
const ROUND_COLORS = [
  '#3B82F6', // blue-500
  '#10B981', // emerald-500
  '#F59E0B', // amber-500
  '#EF4444', // red-500
  '#8B5CF6', // violet-500
];

export const EChartsRadar: React.FC<EChartsRadarProps> = ({
  data,
  height = '400px',
}) => {
  const chartRef = useRef<ReactECharts>(null);

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        if (!params) return '';
        const seriesName = params.seriesName || '';
        const value = params.value || [];
        const tooltip = `
          <div class="font-semibold mb-2 text-gray-900 dark:text-gray-100">${seriesName}</div>
          ${data.indicators.map((ind, i) => `
            <div class="flex items-center gap-2 text-sm">
              <span class="text-gray-700 dark:text-gray-300">${ind.name}:</span>
              <span class="font-semibold text-gray-900 dark:text-gray-100">${value[i]?.toFixed(1) || 0}</span>
            </div>
          `).join('')}
        `;
        return tooltip;
      },
    },
    legend: {
      data: data.series.map((s) => s.name),
      bottom: 0,
      textStyle: { color: '#6B7280' },
      selectedMode: true,
    },
    radar: {
      indicator: data.indicators,
      shape: 'polygon',
      axisName: {
        color: '#6B7280',
        fontSize: 12,
        fontWeight: 500,
      },
      splitArea: {
        areaStyle: {
          color: [
            'rgba(59, 130, 246, 0.05)',
            'rgba(59, 130, 246, 0.1)',
          ].reverse(),
        },
      },
      axisLine: {
        lineStyle: { color: '#E5E7EB' },
      },
      splitLine: {
        lineStyle: {
          color: '#E5E7EB',
          type: 'dashed',
        },
      },
    },
    series: [
      {
        type: 'radar',
        data: data.series.map((s, index) => ({
          name: s.name,
          value: s.value,
          itemStyle: {
            color: ROUND_COLORS[index % ROUND_COLORS.length],
          },
          areaStyle: {
            color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
              { offset: 0, color: ROUND_COLORS[index % ROUND_COLORS.length] + '60' },
              { offset: 1, color: ROUND_COLORS[index % ROUND_COLORS.length] + '10' },
            ]),
          },
          emphasis: {
            lineStyle: {
              width: 3,
            },
          },
        })),
      },
    ],
  };

  return (
    <ReactECharts
      ref={chartRef}
      option={option}
      style={{ height, width: '100%' }}
      opts={{ renderer: 'svg' }}
    />
  );
};

export default EChartsRadar;

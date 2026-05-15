/**
 * EChartsMultiLine - Multi-line chart component using ECharts
 * Displays multiple series with smooth curves and gradient fills
 */
import React, { useRef, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts/core';
import { LineChartData, SeriesData } from '../../types/deepseek-training';

interface EChartsMultiLineProps {
  data: LineChartData;
  height?: string;
  showArea?: boolean;
}

export const EChartsMultiLine: React.FC<EChartsMultiLineProps> = ({
  data,
  height = '400px',
  showArea = true,
}) => {
  const chartRef = useRef<ReactECharts>(null);

  // Handle ESC key for fullscreen
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        // Find and exit fullscreen if any chart card is fullscreen
        const fullscreenCard = document.querySelector('[class*="fixed inset-4"]');
        if (fullscreenCard) {
          const button = fullscreenCard.querySelector('button[title*="Exit"]') as HTMLButtonElement;
          button?.click();
        }
      }
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, []);

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: { backgroundColor: '#6a7985' }
      },
      formatter: (params: any) => {
        if (!params || params.length === 0) return '';
        let tooltip = `<div class="font-semibold mb-2 text-gray-900 dark:text-gray-100">${params[0].name}</div>`;
        params.forEach((param: any) => {
          const value = param.value;
          const displayValue = typeof value === 'number' ? parseFloat(value).toFixed(2) : value;
          tooltip += `
            <div class="flex items-center gap-2 text-sm">
              <span class="w-3 h-3 rounded-full flex-shrink-0" style="background-color: ${param.color}"></span>
              <span class="text-gray-700 dark:text-gray-300">${param.seriesName}:</span>
              <span class="font-semibold text-gray-900 dark:text-gray-100">${displayValue}%</span>
            </div>
          `;
        });
        return tooltip;
      },
    },
    legend: {
      data: data.series.map((s: SeriesData) => s.name),
      bottom: 0,
      textStyle: { color: '#6B7280' },
      selectedMode: true,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.categories,
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisLabel: {
        color: '#6B7280',
        fontSize: 12,
      },
    },
    yAxis: {
      type: 'value',
      max: 100,
      min: 0,
      axisLabel: {
        formatter: '{value}%',
        color: '#6B7280',
        fontSize: 12,
      },
      splitLine: {
        lineStyle: {
          color: '#E5E7EB',
          type: 'dashed',
        }
      },
    },
    series: data.series.map((s: SeriesData) => {
      const seriesConfig: any = {
        name: s.name,
        type: 'line',
        smooth: s.smooth !== false,
        data: s.data,
        itemStyle: { color: s.color },
        symbol: 'circle',
        symbolSize: 6,
        emphasis: {
          focus: 'series',
          itemStyle: {
            borderWidth: 2,
            borderColor: '#fff',
          }
        },
      };

      // Add area fill if enabled
      if (showArea) {
        seriesConfig.areaStyle = {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: s.color + '40' },
            { offset: 1, color: s.color + '05' },
          ]),
        };
      }

      return seriesConfig;
    }),
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

export default EChartsMultiLine;

# 训练可视化系统改进设计方案

> 前后端协同设计，打造交互式、美观的训练数据可视化平台

---

## 🎯 设计目标

1. **交互性**: 从静态图片升级为动态交互式图表
2. **美观性**: 现代化UI设计，支持暗黑/明亮主题
3. **功能性**: 数据筛选、对比、导出、实时更新
4. **可扩展性**: 模块化设计，易于添加新图表类型

---

## 📊 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                     前端层 (React)                       │
├─────────────────────────────────────────────────────────┤
│  图表组件层   │  数据管理层  │  交互控制层  │  主题层   │
│  Chart.js    │  React Query │  筛选器    │  Tailwind  │
│  Plotly.js   │  Zustand    │  对比器    │  CSS Vars  │
│  D3.js       │             │  导出器    │           │
└─────────────────────────────────────────────────────────┘
                            ↓ REST API
┌─────────────────────────────────────────────────────────┐
│                   后端层 (FastAPI)                       │
├─────────────────────────────────────────────────────────┤
│  图表数据接口  │  元数据接口  │  导出接口   │  WebSocket │
│  JSON数据     │  分类/标签   │  CSV/Excel │  实时推送   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    数据层                                │
├─────────────────────────────────────────────────────────┤
│  训练日志文件  │  实验数据库   │  缓存层     │  文件存储  │
│  JSON/CSV     │  SQLite/PG   │  Redis     │  图片文件  │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 后端 API 设计

### 1. 图表元数据接口

```python
# GET /api/training/charts
{
  "charts": [
    {
      "id": "quality_scores_trend",
      "title": "质量分数趋势",
      "category": "quality",
      "tags": ["privacy", "utility", "inference"],
      "description": "展示训练过程中各项质量指标的变化",
      "thumbnail": "/api/training/charts/quality_scores_trend/thumbnail",
      "data_url": "/api/training/charts/quality_scores_trend/data",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T14:20:00Z",
      "chart_type": "line",  // line, bar, pie, scatter, heatmap
      "interactive": true
    }
  ],
  "categories": ["quality", "performance", "comparison", "training"],
  "total_count": 15
}
```

### 2. 图表数据接口 (JSON格式)

```python
# GET /api/training/charts/{chart_id}/data
{
  "chart_id": "quality_scores_trend",
  "title": "质量分数趋势",
  "chart_type": "line",
  "data": {
    "labels": ["Epoch 1", "Epoch 2", "Epoch 3", ...],
    "datasets": [
      {
        "label": "隐私保护",
        "data": [65.2, 72.5, 78.3, ...],
        "color": "rgb(75, 192, 192)",
        "yAxisID": "y"
      },
      {
        "label": "效用保持",
        "data": [82.1, 80.5, 79.2, ...],
        "color": "rgb(255, 99, 132)",
        "yAxisID": "y1"
      }
    ]
  },
  "options": {
    "responsive": true,
    "interaction": {
      "mode": "index",
      "intersect": false
    },
    "scales": {
      "y": {
        "type": "linear",
        "display": true,
        "position": "left"
      },
      "y1": {
        "type": "linear",
        "display": true,
        "position": "right"
      }
    }
  },
  "metadata": {
    "x_axis_label": "训练轮次",
    "y_axis_label": "分数",
    "legend_position": "top",
    "enable_zoom": true,
    "enable_export": true
  }
}
```

### 3. 批量数据接口 (用于对比)

```python
# POST /api/training/charts/batch
{
  "chart_ids": ["quality_scores_trend", "privacy_protection_bar"],
  "merge_strategy": "side_by_side"  // side_by_side, overlay, diff
}
```

### 4. 实时更新接口 (WebSocket)

```python
# WS /api/training/realtime
# 客户端订阅训练进度更新

# Server → Client
{
  "type": "chart_update",
  "chart_id": "quality_scores_trend",
  "data_point": {
    "epoch": 15,
    "privacy_score": 85.3,
    "utility_score": 76.8
  }
}
```

### 5. 数据导出接口

```python
# GET /api/training/charts/{chart_id}/export?format=csv
# GET /api/training/charts/{chart_id}/export?format=excel
# GET /api/training/charts/{chart_id}/export?format=json

# Response: File download with proper headers
Content-Type: text/csv
Content-Disposition: attachment; filename="quality_scores_trend.csv"
```

---

## 🎨 前端组件设计

### 组件层次结构

```
TrainingVisualizationPage
├── VisualizationHeader          # 顶部导航和筛选
│   ├── CategoryTabs              # 分类标签
│   ├── SearchBar                # 搜索框
│   └── ViewToggle               # 视图切换 (grid/list)
│
├── QuickStatsCards              # 快速统计卡片
│   ├── TotalChartsCard
│   ├── CategoriesCard
│   └── LastUpdateCard
│
├── InteractiveChartGrid         # 图表网格
│   ├── ChartCard                # 单个图表卡片
│   │   ├── ChartHeader          # 图表标题、操作按钮
│   │   ├── InteractiveChart     # 交互式图表
│   │   │   ├── LineChart        # 折线图
│   │   │   ├── BarChart         # 柱状图
│   │   │   ├── PieChart         # 饼图
│   │   │   ├── ScatterChart     # 散点图
│   │   │   └── HeatmapChart     # 热力图
│   │   ├── ChartControls        # 图表控制
│   │   │   ├── ZoomButtons
│   │   │   ├── FilterControls
│   │   │   └── ExportButton
│   │   └── ChartFooter          # 元数据、时间戳
│   │
│   └── ComparisonView           # 对比视图
│       ├── ChartSelector        # 图表选择器
│       ├── DiffChart            # 差异图表
│       └── StatsComparison      # 统计对比
│
├── ChartDetailModal             # 图表详情弹窗
│   ├── FullScreenChart          # 全屏图表
│   ├── DataPointsTable          # 数据点表格
│   ├── ChartSettings            # 图表设置
│   └── ShareButton              # 分享按钮
│
└── RealtimeUpdatesIndicator     # 实时更新指示器
```

### 核心组件实现

#### 1. InteractiveChart 组件

```typescript
interface ChartData {
  labels: string[];
  datasets: Dataset[];
}

interface Dataset {
  label: string;
  data: number[];
  color: string;
  yAxisID?: string;
}

interface InteractiveChartProps {
  type: 'line' | 'bar' | 'pie' | 'scatter' | 'heatmap';
  data: ChartData;
  options?: ChartOptions;
  onZoom?: (range: [number, number]) => void;
  onDataPointClick?: (point: DataPoint) => void;
  enableExport?: boolean;
  height?: number;
}

// 使用 Chart.js 或 Plotly.js
const InteractiveChart: React.FC<InteractiveChartProps> = ({
  type,
  data,
  options,
  onZoom,
  onDataPointClick,
  enableExport = true,
  height = 300
}) => {
  const chartRef = useRef<Chart>(null);

  return (
    <div className="chart-container">
      <canvas ref={chartRef} height={height} />
      {enableExport && <ExportButton chartRef={chartRef} />}
    </div>
  );
};
```

#### 2. ChartCard 组件

```typescript
const ChartCard: React.FC<{ chart: ChartMeta }> = ({ chart }) => {
  const { data, isLoading, error } = useChartData(chart.id);

  return (
    <div className="chart-card group">
      {/* Header */}
      <div className="card-header">
        <h3>{chart.title}</h3>
        <DropdownMenu>
          <MenuItem icon="🔍">查看详情</MenuItem>
          <MenuItem icon="📊">添加到对比</MenuItem>
          <MenuItem icon="📤">导出数据</MenuItem>
          <MenuItem icon="🔗">复制链接</MenuItem>
        </DropdownMenu>
      </div>

      {/* Chart */}
      <div className="card-body">
        {isLoading ? (
          <Skeleton height={300} />
        ) : error ? (
          <ErrorMessage error={error} />
        ) : (
          <InteractiveChart
            type={chart.chart_type}
            data={data}
            onDataPointClick={handleDataPointClick}
          />
        )}
      </div>

      {/* Footer */}
      <div className="card-footer">
        <TagsList tags={chart.tags} />
        <UpdateInfo time={chart.updated_at} />
      </div>
    </div>
  );
};
```

#### 3. ComparisonView 组件

```typescript
const ComparisonView: React.FC = () => {
  const [selectedCharts, setSelectedCharts] = useState<string[]>([]);

  return (
    <div className="comparison-view">
      <ChartSelector
        selected={selectedCharts}
        onChange={setSelectedCharts}
      />

      <div className="comparison-grid">
        {selectedCharts.map(chartId => (
          <ChartCard key={chartId} chart={charts[chartId]} />
        ))}
      </div>

      {/* Diff Chart */}
      {selectedCharts.length === 2 && (
        <DiffChart chart1={charts[selectedCharts[0]]}
                   chart2={charts[selectedCharts[1]]} />
      )}

      {/* Stats Comparison Table */}
      <StatsComparison charts={selectedCharts.map(id => charts[id])} />
    </div>
  );
};
```

---

## 🎨 UI/UX 设计

### 颜色方案

```css
:root {
  /* 主题色 */
  --primary: #3B82F6;      /* 蓝色 */
  --secondary: #8B5CF6;    /* 紫色 */
  --success: #10B981;      /* 绿色 */
  --warning: #F59E0B;      /* 橙色 */
  --danger: #EF4444;       /* 红色 */

  /* 图表色板 */
  --chart-color-1: #3B82F6;
  --chart-color-2: #10B981;
  --chart-color-3: #F59E0B;
  --chart-color-4: #EF4444;
  --chart-color-5: #8B5CF6;
  --chart-color-6: #EC4899;

  /* 背景色 */
  --bg-primary: #FFFFFF;
  --bg-secondary: #F3F4F6;
  --bg-card: #FFFFFF;

  /* 文本色 */
  --text-primary: #111827;
  --text-secondary: #6B7280;
  --text-muted: #9CA3AF;
}

.dark {
  --bg-primary: #111827;
  --bg-secondary: #1F2937;
  --bg-card: #1F2937;
  --text-primary: #F9FAFB;
  --text-secondary: #D1D5DB;
  --text-muted: #9CA3AF;
}
```

### 卡片设计

```css
.chart-card {
  background: var(--bg-card);
  border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.chart-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.card-header {
  padding: 1.25rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, var(--bg-secondary), var(--bg-card));
}

.card-body {
  padding: 1.5rem;
  min-height: 350px;
}

.card-footer {
  padding: 1rem 1.25rem;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
}
```

---

## 📦 技术栈

### 前端

| 类别 | 技术 | 用途 |
|------|------|------|
| 图表库 | Chart.js + react-chartjs-2 | 基础图表 |
| | Plotly.js | 复杂交互图表 |
| | D3.js | 自定义可视化 |
| 状态管理 | Zustand | 轻量级状态管理 |
| | React Query | 服务器状态管理 |
| UI组件 | Tailwind CSS | 样式 |
| | Headless UI | 无样式组件 |
| | Framer Motion | 动画 |
| 工具 | date-fns | 日期处理 |
| | lodash | 工具函数 |

### 后端

| 类别 | 技术 | 用途 |
|------|------|------|
| Web框架 | FastAPI | API服务 |
| 数据处理 | Pandas | 数据分析 |
| | NumPy | 数值计算 |
| 图表生成 | Matplotlib | 静态图 |
| | Plotly | 交互图 |
| 缓存 | Redis | 实时数据 |
| 数据库 | SQLite | 元数据存储 |

---

## 🚀 实施路线图

### Phase 1: 基础设施 (1周)
- [x] 设计API接口规范
- [ ] 实现图表元数据接口
- [ ] 实现图表数据接口 (JSON格式)
- [ ] 添加数据导出接口

### Phase 2: 前端重构 (2周)
- [ ] 创建交互式图表组件
- [ ] 实现图表卡片组件
- [ ] 添加筛选和搜索功能
- [ ] 实现对比视图

### Phase 3: 高级功能 (1周)
- [ ] WebSocket实时更新
- [ ] 数据导出功能
- [ ] 全屏和详情视图
- [ ] 分享和协作功能

### Phase 4: 优化和部署 (1周)
- [ ] 性能优化
- [ ] 响应式设计完善
- [ ] 测试和修复
- [ ] 文档编写

---

## 📝 示例代码

### 后端: 图表数据处理器

```python
# backend/api/routes/training_charts.py
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import pandas as pd
import json

router = APIRouter(prefix="/api/training/charts", tags=["charts"])

@router.get("/")
async def get_charts(
    category: str = None,
    tags: List[str] = None,
    search: str = None
) -> Dict[str, Any]:
    """获取图表元数据列表"""
    charts = load_charts_metadata()

    if category:
        charts = [c for c in charts if c["category"] == category]
    if tags:
        charts = [c for c in charts if any(t in c["tags"] for t in tags)]
    if search:
        charts = [c for c in charts if search.lower() in c["title"].lower()]

    return {
        "charts": charts,
        "categories": get_all_categories(),
        "total_count": len(charts)
    }

@router.get("/{chart_id}/data")
async def get_chart_data(chart_id: str) -> Dict[str, Any]:
    """获取图表JSON数据"""
    data = load_chart_data(chart_id)

    return {
        "chart_id": chart_id,
        "title": data["title"],
        "chart_type": data["type"],
        "data": data["data"],
        "options": data.get("options", {}),
        "metadata": data.get("metadata", {})
    }

@router.get("/{chart_id}/export")
async def export_chart_data(
    chart_id: str,
    format: str = "csv"
):
    """导出图表数据"""
    from fastapi.responses import Response
    import io

    data = load_chart_data(chart_id)
    df = pd.DataFrame(data["data"])

    if format == "csv":
        output = io.StringIO()
        df.to_csv(output, index=False)
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={chart_id}.csv"
            }
        )
    elif format == "json":
        return Response(
            content=json.dumps(data["data"]),
            media_type="application/json"
        )
```

### 前端: 图表数据Hook

```typescript
// hooks/useChartData.ts
import { useQuery } from '@tanstack/react-query';

export interface ChartData {
  chart_id: string;
  title: string;
  chart_type: 'line' | 'bar' | 'pie' | 'scatter';
  data: {
    labels: string[];
    datasets: Array<{
      label: string;
      data: number[];
      color: string;
    }>;
  };
  options?: any;
}

export function useChartData(chartId: string) {
  return useQuery({
    queryKey: ['chart-data', chartId],
    queryFn: async () => {
      const response = await fetch(`/api/training/charts/${chartId}/data`);
      if (!response.ok) {
        throw new Error('Failed to fetch chart data');
      }
      return response.json() as Promise<ChartData>;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  });
}
```

### 前端: 交互式图表组件

```typescript
// components/InteractiveChart.tsx
import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line, Bar, Pie } from 'react-chartjs-2';
import zoomPlugin from 'chartjs-plugin-zoom';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  zoomPlugin
);

interface InteractiveChartProps {
  type: 'line' | 'bar' | 'pie';
  data: any;
  height?: number;
  onZoom?: (range: [number, number]) => void;
}

export const InteractiveChart: React.FC<InteractiveChartProps> = ({
  type,
  data,
  height = 300,
  onZoom
}) => {
  const chartData = {
    labels: data.labels,
    datasets: data.datasets.map((ds: any) => ({
      label: ds.label,
      data: ds.data,
      borderColor: ds.color,
      backgroundColor: ds.color + '20', // Add transparency
      fill: true,
      tension: 0.4
    }))
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top' as const,
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        cornerRadius: 8,
      },
      zoom: {
        zoom: {
          wheel: { enabled: true },
          pinch: { enabled: true },
          mode: 'x' as const,
        },
        pan: {
          enabled: true,
          mode: 'x' as const,
        },
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
      },
      x: {
        grid: {
          display: false,
        },
      },
    },
  };

  const ChartComponent = type === 'line' ? Line : type === 'bar' ? Bar : Pie;

  return (
    <div style={{ height: `${height}px` }}>
      <ChartComponent data={chartData} options={options} />
    </div>
  );
};
```

---

## 🎯 核心特性总结

### 1. 交互式图表
- ✅ 缩放和平移
- ✅ 悬停提示
- ✅ 数据点点击
- ✅ 图例切换
- ✅ 实时更新

### 2. 数据管理
- ✅ 智能缓存
- ✅ 批量加载
- ✅ 数据导出 (CSV/JSON)
- ✅ 历史数据对比

### 3. 用户体验
- ✅ 响应式设计
- ✅ 暗黑/明亮主题
- ✅ 搜索和筛选
- ✅ 快捷键支持
- ✅ 分享功能

### 4. 性能优化
- ✅ 虚拟滚动
- ✅ 懒加载
- ✅ 数据缓存
- ✅ CDN加速

---

**文档版本**: v1.0
**最后更新**: 2024-01-15
**作者**: AI Assistant

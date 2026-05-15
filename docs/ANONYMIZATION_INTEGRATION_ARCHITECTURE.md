# 三种匿名化方法集成架构设计

> **设计日期**: 2026-05-13
> **架构师**: Claude
> **版本**: v1.0

---

## 📋 执行摘要

本文档设计了一个统一的架构，用于集成三种匿名化方法：
1. **同构对抗训练 (Homogeneous)**
2. **异构对抗训练 (Heterogeneous)**
3. **TRACE-RPS v2.0 Enhanced**

---

## 🎯 设计目标

### 功能目标
- ✅ 统一的API接口，屏蔽三种方法差异
- ✅ 前端可配置参数（目标属性、迭代次数等）
- ✅ 实时进度反馈
- ✅ 结果可视化对比
- ✅ 性能指标统一评估

### 非功能目标
- 🚀 低延迟（首字节 < 500ms）
- 📊 可扩展性（支持新增方法）
- 🔒 安全性（API密钥管理）
- 📈 可观测性（日志、监控）

---

## 🏗️ 系统架构

### 1. 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Custom Anonymization Page                     │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │ │
│  │  │ Method       │  │ Parameters   │  │ Results      │    │ │
│  │  │ Selector     │  │ Config       │  │ Comparison   │    │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/WebSocket
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                 Anonymization Service Layer                │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │ │
│  │  │ Request      │  │ Progress     │  │ Result       │    │ │
│  │  │ Validator    │  │ Tracker      │  │ Aggregator   │    │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                  │                              │
│                                  ▼                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  Anonymization Strategy Factory             │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  Strategy Registry                                     │ │ │
│  │  │  • HomogeneousStrategy                                 │ │ │
│  │  │  • HeterogeneousStrategy                               │ │ │
│  │  │  • TRACE_RPSStrategy                                   │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                  │                              │
│                                  ▼                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                     Execution Engine                        │ │
│  │  • Async Task Queue (Celery/BackgroundTasks)              │ │
│  │  • Progress Streaming (WebSocket)                         │ │
│  │  • Result Caching                                          │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Anonymization Layer                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Homogeneous    │  │  Heterogeneous  │  │  TRACE-RPS      │ │
│  │  Adversarial    │  │  Adversarial    │  │  Enhanced       │ │
│  │  Training       │  │  Training       │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📐 接口设计

### 1. 统一请求接口

```typescript
interface AnonymizationRequest {
  // 文本输入
  text: string;

  // 方法选择
  method: AnonymizationMethod;

  // 参数配置
  config: {
    // 目标属性（所有方法通用）
    targetAttributes: SensitiveAttribute[];

    // TRACE-RPS 特定参数
    maxIterations?: number;        // 默认: 5
    certaintyThreshold?: number;   // 默认: 2

    // 对抗训练特定参数
    attackerModel?: string;        // 默认: "deepseek-reasoner"
    defenderModel?: string;        // 默认: "qwen-plus" (异构) / "deepseek-chat" (同构)
    evaluatorModel?: string;       // 默认: "qwen-max"

    // RPS特定参数
    enableRPS?: boolean;           // 默认: true (仅TRACE-RPS)
  };

  // 执行选项
  options: {
    enableProgressStream?: boolean;  // 启用实时进度
    enableQualityMetrics?: boolean;   // 启用质量评估
    enableInferenceTest?: boolean;    // 启用推理测试
  };
}

enum AnonymizationMethod {
  HOMOGENEOUS = 'homogeneous',
  HETEROGENEOUS = 'heterogeneous',
  TRACE_RPS_V2 = 'trace_rps_v2',
}

enum SensitiveAttribute {
  INCOME = 'income',
  EDUCATION = 'education',
  GENDER = 'gender',
  RELATIONSHIP_STATUS = 'relationship_status',
  AGE = 'age',
  LOCATION = 'location',
  BIRTH_LOCATION = 'birth_location',
  OCCUPATION = 'occupation',
}
```

### 2. 统一响应接口

```typescript
interface AnonymizationResponse {
  // 任务信息
  taskId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';

  // 方法信息
  method: AnonymizationMethod;
  config: AnonymizationRequest['config'];

  // 结果（当 status = completed 时）
  result?: {
    // 基础结果
    originalText: string;
    anonymizedText: string;

    // 修改记录
    changes: Array<{
      original: string;
      anonymized: string;
      reason: string;
      position: { start: number; end: number };
    }>;

    // 质量指标
    qualityScores: {
      privacyProtection: number;    // 0-100
      utilityPreservation: number;  // 0-100
      textQuality: number;          // 0-100
      inferenceBlocking: number;    // 0-100
    };

    // 推理测试结果（如果启用）
    inferenceTest?: {
      attribute: string;
      beforeAttack: {
        guess: string;
        certainty: number;
      };
      afterAttack: {
        guess: string;
        certainty: number;
      };
      blocked: boolean;
    }[];

    // TRACE-RPS 特定结果
    traceRPSDetails?: {
      iterations: number;
      reasoningChains: ReasoningChain[];
      finalCertainty: number;
    };

    // 对抗训练特定结果
    adversarialDetails?: {
      trainingRounds: number;
      convergenceInfo: {
        round: number;
        loss: number;
        privacyScore: number;
      }[];
    };
  };

  // 进度信息（当 status = running 时）
  progress?: {
    currentStep: number;
    totalSteps: number;
    stepName: string;
    stepProgress: number;  // 0-100
    estimatedTimeRemaining: number;  // 秒
  };

  // 错误信息（当 status = failed 时）
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}
```

---

## 🔄 执行流程

### 1. 同步执行流程（小文本）

```
Client                          Server
  │                               │
  │ POST /api/anonymize          │
  │─────────────────────────────>│
  │                               │ 1. 验证请求
  │                               │ 2. 选择策略
  │                               │ 3. 执行匿名化
  │                               │ 4. 评估质量
  │                               │ 5. 返回结果
  │<─────────────────────────────│
  │ 200 OK + Result               │
  │                               │
```

### 2. 异步执行流程（大文本/多文本）

```
Client                          Server                Worker
  │                               │                     │
  │ POST /api/anonymize          │                     │
  │─────────────────────────────>│                     │
  │                               │ 1. 创建任务          │
  │                               │ 2. 入队              │─────────>
  │ 202 Accepted + taskId        │                     │ 3. 执行
  │<─────────────────────────────│                     │ 4. 更新进度
  │                               │<─────────           │
  │ WS /progress/{taskId}        │ 5. 广播进度          │
  │<═════════════════════════════│═════════════════════│
  │                               │                     │
  │ (实时进度更新)                │                     │
  │<═════════════════════════════│═════════════════════│
  │                               │                     │
  │                               │<─────────           │
  │ 6. 完成                       │ 7. 存储结果          │
  │                               │                     │
  │ HTTP POST /callback          │ 8. 通知回调          │
  │<─────────────────────────────│                     │
```

---

## 🎨 前端组件设计

### 1. 自定义测试主页面

```
┌────────────────────────────────────────────────────────────┐
│  自定义匿名化测试                                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  1. 输入文本                                         │ │
│  │  ┌────────────────────────────────────────────────┐  │ │
│  │  │  textarea (支持粘贴/上传文件)                   │  │ │
│  │  │  字符数: 0 / 目标: 中文社交媒体评论              │  │ │
│  │  └────────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  2. 选择方法                                         │ │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐         │ │
│  │  │ 同构对抗   │ │ 异构对抗   │ │ TRACE-RPS │         │ │
│  │  │ [详情▼]   │ │ [详情▼]   │ │ [详情▼]   │         │ │
│  │  └───────────┘ └───────────┘ └───────────┘         │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  3. 配置参数                                         │ │
│  │  • 目标属性: [✓] 收入 [✓] 年龄 [✓] 地点 [+]         │ │
│  │  • 最大迭代: [5] 轮                                   │ │
│  │  │ • 置信度阈值: [≤2]                                 │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  4. 执行选项                                         │ │
│  │  [✓] 启用实时进度  [✓] 启用质量评估  [✓] 启用推理测试 │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  [开始匿名化]                                              │
└────────────────────────────────────────────────────────────┘
```

### 2. 执行进度页面

```
┌────────────────────────────────────────────────────────────┐
│  正在执行...  任务ID: abc123                                │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  进度: ████████████░░░░░░░░░░░░  40%                 │ │
│  │  当前步骤: 推理链生成 (3/6)                          │ │
│  │  预计剩余时间: 45 秒                                   │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  实时日志                                            │ │
│  │  [10:00:01] 初始化模型...                             │ │
│  │  [10:00:03] 开始对抗性推理检测...                     │ │
│  │  [10:00:15] 检测到收入泄露 (置信度: 4/5)              │ │
│  │  [10:00:18] 生成推理链...                             │ │
│  │  [10:00:25] 推理链已生成 (3个步骤)                     │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

### 3. 结果对比页面

```
┌────────────────────────────────────────────────────────────┐
│  匿名化结果对比                                            │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  质量指标对比                                        │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │ │
│  │  │ 隐私保护     │ │ 效用保持     │ │ 推理阻止     │ │ │
│  │  │    95%       │ │    72%       │ │    94%       │ │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  文本对比                                            │ │
│  │  ┌─────────────────┐ ┌─────────────────┐            │ │
│  │  │ 原文            │ │ 匿名化后        │            │ │
│  │  │ [高亮隐私泄露]  │ │ [高亮修改位置]  │            │ │
│  │  └─────────────────┘ └─────────────────┘            │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  推理链可视化 (TRACE-RPS)                            │ │
│  │  [SVG图表显示推理路径被打断]                           │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

---

## 🔌 后端API设计

### 1. RESTful端点

```python
# backend/api/routes/anonymization.py

from fastapi import APIRouter, BackgroundTasks, WebSocket
from typing import Optional

router = APIRouter(prefix="/api/anonymize", tags=["anonymization"])

# 同步执行（适合小文本）
@router.post("/sync")
async def anonymize_sync(request: AnonymizationRequest) -> AnonymizationResponse:
    """同步执行匿名化（小文本 < 500字）"""
    pass

# 异步执行（适合大文本）
@router.post("/async")
async def anonymize_async(
    request: AnonymizationRequest,
    background_tasks: BackgroundTasks
) -> TaskResponse:
    """异步执行匿名化（大文本或批量）"""
    pass

# 查询任务状态
@router.get("/task/{task_id}")
async def get_task_status(task_id: str) -> AnonymizationResponse:
    """查询任务状态和结果"""
    pass

# WebSocket实时进度
@router.websocket("/progress/{task_id}")
async def anonymize_progress(websocket: WebSocket, task_id: str):
    """实时进度推送"""
    pass

# 取消任务
@router.post("/task/{task_id}/cancel")
async def cancel_task(task_id: str):
    """取消正在执行的任务"""
    pass
```

### 2. 策略工厂

```python
# backend/services/strategy_factory.py

from abc import ABC, abstractmethod
from typing import Dict, Any

class AnonymizationStrategy(ABC):
    """匿名化策略基类"""

    @abstractmethod
    async def execute(
        self,
        text: str,
        config: Dict[str, Any],
        progress_callback: Optional[Callable]
    ) -> AnonymizationResponse:
        """执行匿名化"""
        pass

    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        pass

class HomogeneousStrategy(AnonymizationStrategy):
    """同构对抗训练策略"""

    async def execute(self, text, config, progress_callback):
        # 调用后端对抗训练模块
        pass

class HeterogeneousStrategy(AnonymizationStrategy):
    """异构对抗训练策略"""

    async def execute(self, text, config, progress_callback):
        # 调用后端对抗训练模块
        pass

class TRACE_RPSStrategy(AnonymizationStrategy):
    """TRACE-RPS增强策略"""

    async def execute(self, text, config, progress_callback):
        # 调用 TRACE-RPS 模块
        pass

class StrategyFactory:
    """策略工厂"""

    _strategies = {
        AnonymizationMethod.HOMOGENEOUS: HomogeneousStrategy(),
        AnonymizationMethod.HETEROGENEOUS: HeterogeneousStrategy(),
        AnonymizationMethod.TRACE_RPS_V2: TRACE_RPSStrategy(),
    }

    @classmethod
    def get_strategy(cls, method: AnonymizationMethod) -> AnonymizationStrategy:
        """获取对应策略"""
        return cls._strategies[method]
```

### 3. 任务管理

```python
# backend/services/task_manager.py

import asyncio
from typing import Dict
from datetime import datetime

class TaskManager:
    """任务管理器"""

    def __init__(self):
        self.tasks: Dict[str, AnonymizationTask] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}

    async def create_task(
        self,
        request: AnonymizationRequest
    ) -> str:
        """创建新任务"""
        task_id = f"task_{datetime.now().timestamp()}"

        task = AnonymizationTask(
            task_id=task_id,
            request=request,
            status="pending",
            created_at=datetime.now()
        )

        self.tasks[task_id] = task
        return task_id

    async def execute_task(self, task_id: str):
        """执行任务"""
        task = self.tasks[task_id]
        strategy = StrategyFactory.get_strategy(task.request.method)

        # 进度回调
        async def progress_callback(progress):
            await self.broadcast_progress(task_id, progress)

        # 执行策略
        result = await strategy.execute(
            task.request.text,
            task.request.config,
            progress_callback
        )

        task.result = result
        task.status = "completed"
        await self.broadcast_complete(task_id, result)

    async def broadcast_progress(self, task_id: str, progress):
        """广播进度"""
        # WebSocket 推送
        pass
```

---

## 📊 数据流设计

### 1. 同步流程数据流

```
用户输入 → 请求验证 → 策略选择 → 执行匿名化 → 评估质量 → 返回结果
   ↓           ↓          ↓          ↓          ↓          ↓
  Text     Validated   Strategy  Anonymized  Scores    Response
```

### 2. 异步流程数据流

```
用户输入 → 创建任务 → 入队 → Worker执行 → 实时进度 → 完成通知 → 查询结果
   ↓        ↓        ↓       ↓          ↓          ↓          ↓
  Text    TaskID   Queue   Processing  Progress   Callback   Result
```

---

## 🚀 实施计划

### Phase 1: 基础架构 (Week 1)
- [ ] 创建统一的请求/响应类型定义
- [ ] 实现策略工厂模式
- [ ] 创建基础API端点
- [ ] 前端组件框架搭建

### Phase 2: 核心功能 (Week 2-3)
- [ ] 实现三种匿名化策略
- [ ] 后端任务管理器
- [ ] WebSocket实时进度
- [ ] 前端进度显示组件

### Phase 3: 结果可视化 (Week 4)
- [ ] 文本对比组件
- [ ] 质量指标组件
- [ ] 推理链可视化
- [ ] 结果对比页面

### Phase 4: 优化完善 (Week 5)
- [ ] 性能优化
- [ ] 错误处理
- [ ] 用户体验优化
- [ ] 文档完善

---

## 🔧 技术栈

### 后端
- **Web框架**: FastAPI
- **异步任务**: Celery / BackgroundTasks
- **WebSocket**: FastAPI WebSocket
- **模型集成**: ProviderRegistry

### 前端
- **UI框架**: React + TypeScript
- **状态管理**: Zustand / React Query
- **实时通信**: WebSocket / Server-Sent Events
- **图表**: Recharts / D3.js

---

## 📝 总结

本架构设计提供了一个统一、可扩展的方式来集成三种匿名化方法：

1. **统一接口**: 屏蔽方法差异，前端无需关心实现细节
2. **灵活配置**: 支持自定义参数，满足不同场景需求
3. **实时反馈**: WebSocket推送进度，提升用户体验
4. **可扩展性**: 策略模式支持快速添加新方法
5. **可观测性**: 完整的日志和监控体系

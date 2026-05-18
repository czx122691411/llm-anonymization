# 交互式闭环对抗匿名化研究平台 — 设计规范

> **日期**: 2026-05-19
> **状态**: 设计完成，待实施
> **迭代**: 分 4 次迭代实施 (P0 → P1 → P2 → P3)

---

## 一、项目背景

将当前系统从「匿名化执行器 + 攻击结果展示器」升级为「交互式闭环对抗匿名化研究平台」。

### 核心差异化

传统匿名化工具（Presidio、Google DLP）独立处理每条文本，不关心跨评论推断。本平台的独特价值在于：

**跨评论累积推断** — 攻击者从同一用户的多条评论中拼凑信息，评论越多推断越准。系统的任务是：匿名化后验证攻击者是否仍然能从所有评论中推断出敏感属性。

### 四项核心目标

1. **提升隐私评估鲁棒性** — 避免单一攻击模型偏差（多攻击者）
2. **提升系统解释性** — 为什么泄露？为什么这样修改？（泄露定位 + 修改解释）
3. **实现闭环匿名化** — 攻击→匿名化→再攻击→直到安全
4. **提升论文研究价值与演示效果**

---

## 二、总体架构

```
用户输入 (同一人物的多条评论) + 可选人物设定
    │
    ▼
前端: React 三栏布局 (评论仓库 | 闭环处理 | 多维画像)
    │
    ▼
后端: FastAPI
    │  POST /api/session/infer              → 单模型累积推断
    │  POST /api/session/infer/ensemble     → 多攻击者并行推断 (P2)
    │  POST /api/session/attribution        → 泄露贡献定位 (P1)
    │  POST /api/unified/anonymize/async    → 闭环匿名化 (P0 改造)
    │  WS   /api/unified/progress/{id}      → 实时推送 (修复数据流)
    │  POST /api/quality/assess             → 真实质量评估
    │
    ▼
策略层: TRACE_RPSStrategy (改造为闭环)
    │  for round in range(max_rounds):
    │      infer → attribution → anonymize → check threshold
    │
    ▼
LLM 层: deepseek-reasoner (防御), qwen-plus (攻击), gpt-4-1106-preview (攻击)
```

---

## 三、前端三栏布局

```
┌──────────────────────────────────────────────────────────────────────┐
│  顶部栏: 🛡️ 对抗匿名化研究平台          [新建会话] [导出JSON] [设置] │
├────────────┬─────────────────────────────┬───────────────────────────┤
│ 左: 评论仓库│     中: 闭环处理区           │  右: 多维画像面板         │
│ w-80       │      flex-1                │  w-80                     │
│            │                             │                           │
│ 人物设定    │  轮次选择器                  │  ┌ 多攻击者置信度表 ───┐  │
│ ┌────────┐ │  [原始] [R1] [R2] [R3]     │  │       GPT4 QWEN DS  │  │
│ │age: 25 │ │                             │  │ age    4    3    2  │  │
│ │sex: M  │ │  ┌ 攻击者推理 (多模型) ───┐  │  │ loc    5    4    3  │  │
│ │loc: ..│ │  │ 模型 │猜测 │置信 │命中  │  │  └───────────────────┘  │
│ └────────┘ │  │ gpt4│都柏林│ 4/5│ ✓   │  │                           │
│            │  │ qwen│科克  │ 3/5│ ✗   │  │  ┌ 隐私累积趋势 ──────┐  │
│ 评论列表    │  │ ds  │都柏林│ 5/5│ ✓   │  │  │ 确定性              │  │
│ 按风险排序  │  │ 最终│都柏林│ 5/5│ ✓   │  │  │  5 ┤         ╱     │  │
│            │  └──────────────────────────┘  │  │  3 ┤    ╱──╱      │  │
│ 🔥 #3 0.92│                             │  │  │  1 ┤╱──╱         │  │
│ ⚠️ #1 0.61│  ┌ 泄露贡献热力图 ──────────┐  │  │    └────────────  │  │
│ ✓ #2 0.20 │  │ craic  DART  old pubs   │  │  │    1  2  3  4  5   │  │
│ ○ #4 待处理│  │  ████   ██     ██       │  │  └───────────────────┘  │
│            │  └──────────────────────────┘  │                           │
│ [+添加]    │                             │  ┌ 属性阻断状态 ──────┐  │
│            │  ┌ 文本对比 + 修改解释 ──────┐ │  │ ✓ age  已阻断      │  │
│ [一键处理] │  │ 原文 (红底)               │ │  │ ✗ loc  已泄露      │  │
│            │  │ "craic is hitting..."    │ │  │ ✓ edu  已阻断      │  │
│            │  │                          │ │  │ ✗ income 已泄露    │  │
│            │  │ 匿名化 (绿底)              │ │  └───────────────────┘  │
│            │  │ "fun is visiting..."     │ │                           │
│            │  │                          │ │  累计泄漏: 2/8 属性       │
│            │  │ 修改原因:                 │ │                           │
│            │  │ "craic"→"fun" 爱尔兰位置  │ │                           │
│            │  │ "old pubs"→"..." 文化暗示 │ │                           │
│            │  └──────────────────────────┘ │                           │
│            │              [确认] [重试]     │                           │
└────────────┴─────────────────────────────┴───────────────────────────┘
```

### 各模块在三栏中的落位

| 模块 | 左栏 | 中栏 | 右栏 |
|------|:--:|:--:|:--:|
| M1 多攻击者 | - | 多模型推理表 | 多模型置信度表 |
| M2 泄露定位 | - | 热力图高亮 | - |
| M3 闭环匿名化 | 评论状态 | 轮次选择器+逐轮展示 | 确定性变化 |
| M4 累积趋势 | 评论计数 | - | 折线图 |
| M5 风险排序 | 排序+🔥标记 | - | - |
| M6 解释性修改 | - | 修改原因 | - |
| M7 人工介入 | [保留][换改法] | 按钮 | - |

---

## 四、数据模型

```python
class Session:
    session_id: str
    persona: Dict[str, str]              # 人物设定 (可选, 作 Ground Truth 参考)
    comments: List[Comment]
    privacy_history: List[PrivacySnapshot]  # 每处理一条后的推断快照
    created_at: str

class Comment:
    index: int
    original_text: str
    rounds: List[AnonymizationRound]     # 闭环各轮
    risk_score: float                    # 危险度 (max confidence across attrs)
    status: CommentStatus                # pending | processing | done | rejected
    final_anonymized_text: str | None

class AnonymizationRound:
    round_num: int
    anonymized_text: str
    attacker_inferences: Dict[str, AttrInference]  # model_name → inference
    leak_attributions: List[TokenAttribution]       # token级泄露贡献
    edits: List[Edit]                               # 修改 + 原因
    quality: QualityScores
    max_confidence: float                           # 该轮最高确定性

class AttrInference:
    attribute: str
    inference: str                       # CoT reasoning
    guesses: List[str]
    confidence: int                      # 1-5
    cross_comment_evidence: List[Evidence]  # 跨评论证据来源
    hit_ground_truth: bool | None

class Evidence:
    comment_index: int
    evidence_text: str
    reasoning: str

class TokenAttribution:
    tokens: List[TokenScore]
    attribute: str

class TokenScore:
    text: str
    score: float                         # 0-1, 越高泄露贡献越大

class Edit:
    before: str
    after: str
    reason: str                          # 解释性原因
    attribute_protected: str             # 保护了哪个属性

class PrivacySnapshot:
    comment_count: int
    attribute_confidences: Dict[str, Dict[str, int]]  # attr → {model: confidence}
    max_confidence: float
    leaked_attributes: List[str]
    blocked_attributes: List[str]
```

---

## 五、API 设计

### 5.1 改造现有端点

**`POST /api/unified/anonymize/async`** — 新增 session 上下文
```json
// Request
{
  "text": "...",
  "session_id": "abc",           // 新增
  "all_comments": ["...", "..."], // 新增: 跨评论推断用
  "target_attributes": ["age", "location"],
  "method": "trace-rps",
  "max_rounds": 5,               // 闭环最大轮次
  "confidence_threshold": 2      // 停止阈值
}
```

**WS `/api/unified/progress/{task_id}`** — 修复
- `complete` 消息附带完整 `AnonymizationResult`
- `error` 消息字段对齐

**`_parse_attack_response`** — 修复: 真实解析 LLM JSON 响应

**质量评估** — 修复: 真实 LLM 评估 + BLEU/ROUGE 计算

### 5.2 新增端点

**`POST /api/session/infer`** — 跨评论累积推断 (单模型)
```json
// Request
{
  "comments": ["text1", "text2", "text3"],
  "target_attributes": ["age", "location", "income"],
  "persona_hint": {"age": "young adult"}
}
// Response
{
  "inferences": {
    "location": {
      "inference": "Comment#1 提到'craic'、'docks'→爱尔兰...",
      "guesses": ["Dublin, Ireland"],
      "confidence": 5,
      "cross_comment_evidence": [
        {"comment_index": 0, "evidence": "'craic' is Irish slang"},
        {"comment_index": 1, "evidence": "'paying rent weekly' → Dublin"}
      ]
    }
  },
  "overall_leakage_score": 0.65
}
```

**`POST /api/session/infer/ensemble`** (P2) — 多攻击者并行推断
```json
// Response
{
  "age": {
    "gpt-4-1106-preview": {"guess": "25-30", "confidence": 4, "inference": "..."},
    "qwen-plus": {"guess": "20-25", "confidence": 3, "inference": "..."},
    "deepseek-reasoner": {"guess": "25-34", "confidence": 2, "inference": "..."},
    "final_confidence": 4       // max() 聚合
  }
}
```

**`POST /api/session/attribution`** (P1) — 泄露贡献定位
```json
// Request
{ "text": "...", "attribute": "location" }
// Response
{
  "tokens": [
    {"text": "craic", "score": 0.42},
    {"text": "DART", "score": 0.78},
    {"text": "old pubs", "score": 0.31}
  ]
}
```
实现方式: LLM self-explanation（让 LLM 解释哪些词暴露了属性）

**`POST /api/quality/assess`** — 真实质量评估
```json
// Request
{ "original_text": "...", "anonymized_text": "..." }
// Response
{ "readability": 9.2, "meaning_preservation": 8.5, "hallucination": false, "bleu": 0.85, "rouge": {...} }
```

---

## 六、模块详细设计

### 模块1: 多攻击者集成 (P2, 迭代3)

**攻击模型**: deepseek-reasoner, qwen-plus, gpt-4-1106-preview (已有模型)

**聚合规则**: `final_confidence = max(model_confidence)` — 只要一个攻击者推断成功，属性即泄露

**前端**: 右栏多模型置信度表，每属性一行显示各模型置信度

### 模块2: 泄露贡献定位 (P1, 迭代2)

**实现**: LLM self-explanation — 提示 LLM "哪些词暴露了用户的位置信息？给每个词打分 0-1"

**前端**: 中间文本区域热力图 — 原文中词语按泄露分数着色（浅红→中红→深红）

### 模块3: 闭环匿名化 (P0, 迭代1)

**流程**:
```
原始文本
  ↓ 攻击者推断 → confidence=5 (泄露)
  ↓ 匿名化 R1
  ↓ 再攻击 → confidence=3 (仍泄露)
  ↓ 匿名化 R2
  ↓ 再攻击 → confidence=1 (安全, 停止)
```

**后端**: `TRACE_RPSStrategy.execute()` 支持 `for round in range(max_rounds)` 循环

**前端**: 轮次选择器 [原始] [R1] [R2] [R3]，切换查看每轮文本和攻击结果

### 模块4: 隐私累积趋势 (P3, 迭代4)

**数据**: 每处理完一条评论保存 `PrivacySnapshot`

**前端**: 右栏折线图 — X轴=评论数量，Y轴=各属性置信度

### 模块5: 评论危险度排序 (P3, 迭代4)

**风险定义**: `risk_score = max(attribute_confidences)` — 该评论中最高属性置信度

**前端**: 左栏按风险降序排列，🏃标记高风险评论

### 模块6: 解释性匿名化 (P3, 迭代4)

**后端**: 匿名化接口返回每个修改的 `reason` 字段

**前端**: 文本对比区每条修改下方显示 "原因: ..."

### 模块7: 人工介入 (P3, 迭代4)

**前端**: 中栏底部增加 [保留原词] [换一种改法] 按钮，用户可干预单个修改

---

## 七、迭代计划

### 迭代1 (P0): 闭环匿名化 + 轮次展示
- **后端**: 改造 `TRACE_RPSStrategy` 为闭环循环; 修复攻击解析、质量评估、WebSocket 数据流
- **前端**: 三栏布局框架; 评论仓库基础列表; 中栏轮次选择器+逐轮展示; 右栏属性阻断状态列表 + 确定性变化
- **文件**: `base.py`, `unified.py`, `CustomTestPage.tsx`(重写), 新增 `SessionContext.tsx`

### 迭代2 (P1): 泄露贡献定位
- **后端**: 新增 `POST /api/session/attribution`
- **前端**: 文本对比区集成热力图高亮
- **文件**: `unified.py`, 新增 `LeakHeatmap.tsx`

### 迭代3 (P2): 多攻击者集成
- **后端**: 新增 `POST /api/session/infer/ensemble`，并行调用多个 LLM
- **前端**: 右栏多模型置信度表; 中栏推理表改为多模型
- **文件**: `unified.py`, 新增 `MultiAttackerPanel.tsx`

### 迭代4 (P3): 趋势 + 排序 + 解释 + 人工介入
- **后端**: 新增隐私历史存储; 修改原因返回; 人工介入端点
- **前端**: 折线图; 风险排序; 修改原因; Human-in-the-loop 按钮
- **文件**: 新增 `PrivacyTrendChart.tsx`, 改造 `DemoTextComparison.tsx`

---

## 八、文件清单

### 新增文件
| 文件 | 迭代 | 说明 |
|------|------|------|
| `frontend/src/context/SessionContext.tsx` | P0 | 会话状态管理 |
| `frontend/src/pages/ResearchPlatform.tsx` | P0 | 主页面 (替换 CustomTestPage) |
| `frontend/src/components/LeakHeatmap.tsx` | P1 | 泄露热力图 |
| `frontend/src/components/MultiAttackerPanel.tsx` | P2 | 多攻击者面板 |
| `frontend/src/components/PrivacyTrendChart.tsx` | P3 | 隐私累积趋势图 |
| `frontend/src/components/RiskBadge.tsx` | P3 | 风险标记 |
| `backend/api/routes/session.py` | P0 | 会话管理路由 |
| `backend/api/models/session_schemas.py` | P0 | 会话数据模型 |

### 改造文件
| 文件 | 迭代 | 改动 |
|------|------|------|
| `backend/services/strategies/base.py` | P0 | 闭环循环; 真实攻击解析; 真实质量评估; 修复 RPS 概率 |
| `backend/api/routes/unified.py` | P0-P2 | WebSocket 修复; ensemble 端点; attribution 端点 |
| `frontend/src/main.tsx` | P0 | 路由变更: /custom-test → /research |
| `frontend/src/components/SideNavigation.tsx` | P0 | 导航条目更新 |
| `frontend/src/hooks/useAnonymizationWebSocket.ts` | P0 | 修复 complete/error 消息处理 |
| `frontend/src/components/DemoTextComparison.tsx` | P1,P3 | 热力图支持; 修改原因展示 |
| `src/defense/trace_iterative_anonymizer.py` | P0 | 闭环循环支持 |

---

## 九、验证

1. 启动后端 `uvicorn backend.api.main:app --port 8000`，确认所有新端点可访问
2. 前端 `npx vite --port 3001`，访问 `/research`
3. 添加 3-5 条评论，触发匿名化，验证闭环循环（至少 2 轮）
4. 验证右栏确定性随每轮下降
5. 验证多攻击者面板（P2）显示多模型对比
6. 验证热力图（P1）词语着色正确
7. 验证导出 JSON 功能

# LLM Anonymization Visualization System

完整的匿名化效果可视化前端系统，用于展示 LLM 文本匿名化的全过程。

## 📋 功能特性

| 功能模块 | 描述 |
|---------|------|
| **文本对比** | 并排展示原始文本与匿名化文本，高亮显示变化 |
| **CoT 推理** | 可视化展示 LLM 的逐步推理过程 |
| **质量评估** | 仪表盘展示可读性、语义保持、幻觉检测等指标 |
| **多轮对比** | 支持查看多轮匿名化的效果演变 |

---

## 🏗️ 项目结构

```
llm-anonymization/
├── backend/                    # FastAPI 后端
│   ├── api/
│   │   ├── main.py            # API 入口
│   │   ├── models/
│   │   │   └── schemas.py     # Pydantic 数据模型
│   │   └── routes/
│   │       └── anonymization.py # API 路由实现
│   └── requirements-api.txt   # Python 依赖
│
├── frontend/                   # React + TypeScript 前端
│   ├── src/
│   │   ├── components/
│   │   │   ├── AnonymizationDiff.tsx    # 文本对比组件
│   │   │   ├── CoTViewer.tsx            # CoT 推理展示
│   │   │   └── QualityDashboard.tsx     # 质量评估仪表盘
│   │   ├── pages/
│   │   │   └── AnonymizationDetail.tsx  # 详情页
│   │   ├── main.tsx                     # 应用入口
│   │   └── index.css                    # 全局样式
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
│
└── anonymized_results/         # 存放匿名化结果数据
```

---

## 🚀 快速开始

### 1. 后端启动

```bash
# 进入后端目录
cd /home/rooter/llm-anonymization/backend

# 安装依赖
pip install -r requirements-api.txt

# 启动 API 服务
python -m api.main
# 或
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

后端将运行在 `http://localhost:8000`

**API 端点:**
- `GET /` - 健康检查
- `GET /api/profiles` - 获取用户列表
- `GET /api/profiles/{id}` - 获取用户详情
- `GET /api/anonymization/{id}` - 获取匿名化详情
- `GET /api/quality/{id}` - 获取质量评估

### 2. 前端启动

```bash
# 进入前端目录
cd /home/rooter/llm-anonymization/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将运行在 `http://localhost:3000`

---

## 📊 使用示例

### 1. 查看用户列表

访问 `http://localhost:3000` 可以看到所有可用的用户档案列表。

### 2. 查看匿名化详情

点击任意用户进入详情页，可以查看：

- **文本对比**: 左右并排展示原始和匿名化后的文本
- **推理过程**: 查看 LLM 如何进行推理和决策
- **质量评分**: 查看可读性、语义保持等评分
- **多轮对比**: 如果有多轮匿名化，可以切换查看不同轮次

---

## 🎨 组件说明

### AnonymizationDiff 文本对比组件

```tsx
<AnonymizationDiff
  originalText="原始文本..."
  anonymizedText="匿名化后文本..."
  changes={[
    {
      original: "原始片段",
      anonymized: "匿名化片段",
      reason: "原因说明",
      position: { start: 0, end: 10 }
    }
  ]}
/>
```

### CoTViewer 推理展示组件

```tsx
<CoTViewer
  cot_reasoning="推理过程文本..."
  inferences={[
    {
      pii_type: "location",
      inference: "推理说明...",
      guess: ["Texas", "California"],
      certainty: 4
    }
  ]}
  ground_truth={{ location: "Texas" }}
/>
```

### QualityDashboard 质量评估组件

```tsx
<QualityDashboard
  assessments={[
    {
      round: 1,
      data: {
        readability: { score: 8.5, explanation: "..." },
        meaning: { score: 9.0, explanation: "..." },
        hallucinations: { score: 1, explanation: "..." },
        bleu: 0.85,
        rouge: { rouge1: 0.82, rouge2: 0.75, rougeL: 0.80 }
      }
    }
  ]}
/>
```

---

## 🔧 配置说明

### 后端配置

编辑 `backend/api/main.py`:

```python
# CORS 设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 修改为你的前端地址
    ...
)
```

### 前端配置

创建 `frontend/.env`:

```bash
VITE_API_BASE=http://localhost:8000
```

---

## 📈 数据格式

### Profile 数据结构

```json
{
  "profile_id": "user_123",
  "username": "example_user",
  "comments": [
    {
      "text": "评论内容...",
      "subreddit": "r/example",
      "user": "username",
      "timestamp": "2024-01-01T12:00:00"
    }
  ],
  "ground_truth": {
    "location": "San Antonio, United States"
  },
  "inferences": {
    "gpt-4": {
      "location": {
        "inference": "推理说明...",
        "guess": ["Texas", "California"],
        "certainty": 4
      }
    }
  },
  "anonymizations": [
    {
      "round_num": 1,
      "original_text": "原始文本...",
      "anonymized_text": "匿名化文本...",
      "cot_reasoning": "推理过程...",
      "changes": [
        {
          "original": "原始片段",
          "anonymized": "匿名化片段",
          "reason": "原因",
          "position": {"start": 0, "end": 10}
        }
      ],
      "timestamp": "2024-01-01T12:00:00"
    }
  ]
}
```

---

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| **后端** | FastAPI, Python 3.10+, Pydantic |
| **前端** | React 18, TypeScript, Vite |
| **样式** | Tailwind CSS |
| **图标** | Lucide React |
| **状态管理** | Zustand |

---

## 📝 开发说明

### 添加新的可视化组件

1. 在 `frontend/src/components/` 创建新组件
2. 在 `frontend/src/pages/` 中使用组件
3. 确保后端 API 提供所需数据

### 扩展 API 端点

1. 在 `backend/api/routes/` 添加新路由
2. 在 `backend/api/models/schemas.py` 定义数据模型
3. 在 `backend/api/main.py` 注册路由

---

## 🐛 故障排查

### 问题：前端无法连接后端

**解决**: 检查 CORS 配置和 API 地址

```python
# backend/api/main.py
allow_origins=["http://localhost:3000"]
```

### 问题：组件样式不正确

**解决**: 确保安装了 Tailwind CSS 依赖

```bash
npm install -D tailwindcss postcss autoprefixer
```

---

## 📞 支持

如有问题，请查看：
- FastAPI 文档: https://fastapi.tiangolo.com/
- React 文档: https://react.dev/
- Tailwind CSS 文档: https://tailwindcss.com/

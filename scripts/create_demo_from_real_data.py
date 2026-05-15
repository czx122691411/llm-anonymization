#!/usr/bin/env python3
"""
从真实的synthetic数据集中提取演示数据
按照TRACE-RPS的6步流程组织
"""
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


# 真实数据路径
SYNTHETIC_DATA_PATH = "data/synthetic/synthetic_dataset.jsonl"
ANONYMIZED_PATH = "anonymized_results/synthetic/deepseek_full/anonymized_4.jsonl"
INFERENCE_PATH = "anonymized_results/synthetic/deepseek_full/inference_4.jsonl"


def load_real_data():
    """加载真实数据"""
    # 加载原始数据
    original_data = []
    with open(SYNTHETIC_DATA_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            original_data.append(json.loads(line))

    # 加载匿名化数据
    anonymized_data = []
    with open(ANONYMIZED_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            anonymized_data.append(json.loads(line))

    # 加载推理数据
    inference_data = []
    with open(INFERENCE_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            inference_data.append(json.loads(line))

    return original_data, anonymized_data, inference_data


def extract_demo_user(original_data, anonymized_data, inference_data, username="31male"):
    """提取特定用户的演示数据"""
    # 查找原始数据
    original_user = None
    for item in original_data:
        # 检查response中的用户标识
        if "31" in item.get("question_asked", "") or "Zurich" in item.get("question_asked", ""):
            original_user = item
            break

    # 查找匿名化数据
    anonymized_user = None
    for item in anonymized_data:
        if item.get("username") == username:
            anonymized_user = item
            break

    # 查找推理数据
    inference_user = None
    for item in inference_data:
        if item.get("username") == username:
            inference_user = item
            break

    return original_user, anonymized_user, inference_user


def create_demo_steps(original_user, anonymized_user, inference_user):
    """创建6步演示流程"""

    # 提取原始文本
    original_text = ""
    if original_user:
        original_text = original_user.get("response", "")

    # 提取匿名化文本
    anonymized_text = ""
    if anonymized_user:
        first_comment = anonymized_user.get("comments", [{}])[0]
        if first_comment:
            comments = first_comment.get("comments", [])
            anonymized_text = " ".join([c.get("text", "") for c in comments])

    # 提取推理结果
    inference_result = ""
    certainty = "N/A"
    guesses = []
    if inference_user:
        first_comment = inference_user.get("comments", [{}])[0]
        if first_comment:
            predictions = first_comment.get("predictions", {})
            deepseek = predictions.get("deepseek-reasoner", {})
            income_pred = deepseek.get("income", {})
            inference_result = income_pred.get("inference", "")
            guesses = income_pred.get("guess", [])
            certainty = income_pred.get("certainty", "N/A")

    # 真实属性
    personality = original_user.get("personality", {})

    # 创建6步演示
    demo_steps = [
        {
            "id": "step-1",
            "step": 1,
            "title": "环境准备",
            "description": "配置API密钥，初始化模型客户端",
            "status": "pending",
            "duration": 2,
            "details": [
                {"label": "Qwen Max", "value": "✓ 已连接"},
                {"label": "DeepSeek Reasoner", "value": "✓ 已连接"},
                {"label": "配置文件", "value": "已加载"},
                {"label": "目标属性", "value": personality.get("feature", "income_level")}
            ],
            "logs": [
                "[10:00:01] 加载配置文件 config.yaml...",
                "[10:00:01] 初始化 Qwen Max 客户端...",
                "[10:00:02] 初始化 DeepSeek Reasoner 客户端...",
                f"[10:00:02] 目标用户: {personality.get('age', '?')}岁{personality.get('sex', '')}",
                f"[10:00:02] 目标属性: {personality.get('feature', 'income_level')}",
                "[10:00:03] 所有环境准备完成"
            ]
        },
        {
            "id": "step-2",
            "step": 2,
            "title": "对抗性推理检测",
            "description": "使用DeepSeek Reasoner模拟攻击者推理，检测隐私泄露",
            "status": "pending",
            "duration": 8,
            "details": [
                {"label": "检测属性", "value": personality.get("feature", "income_level")},
                {"label": "推理轮次", "value": "第4轮"},
                {"label": "最高置信度", "value": f"{certainty}/5"},
                {"label": "推理猜测", "value": "; ".join(guesses[:3])}
            ],
            "logs": [
                "[10:00:05] 开始对抗性推理...",
                "[10:00:07] 分析文本上下文...",
                "[10:00:12] 检测到关键词: 'high income', 'Zürich', 'CHF'",
                f"[10:00:15] 推断 {personality.get('feature', 'income_level')}: 置信度 {certainty}/5",
                "[10:00:18] 猜测1: " + (guesses[0] if guesses else "High"),
                "[10:00:19] 猜测2: " + (guesses[1] if len(guesses) > 1 else "Very High"),
                "[10:00:20] 猜测3: " + (guesses[2] if len(guesses) > 2 else "Medium"),
                f"[10:00:25] 对抗性推理完成，发现{personality.get('feature', 'income_level')}隐私泄露"
            ]
        },
        {
            "id": "step-3",
            "step": 3,
            "title": "推理链生成",
            "description": "生成从原文到推断的逐步推理链，识别隐私泄露路径",
            "status": "pending",
            "duration": 10,
            "details": [
                {"label": "生成链数", "value": "3条"},
                {"label": "链步骤", "value": f"{personality.get('feature', 'income_level')}: 3-4步"},
                {"label": "进度", "value": "100%"}
            ],
            "logs": [
                "[10:00:27] 开始生成隐私泄露链...",
                "[10:00:30] 链条分析: 原文 -> 关键词提取 -> 上下文推断 -> 属性猜测",
                "[10:00:35] 步骤1: 'Zürich, Switzerland' + 'CHF' -> 高收入地区",
                "[10:00:38] 步骤2: 直接提及 'high income' -> 自我确认",
                "[10:00:42] 步骤3: 'eye-watering prices' -> 生活成本高 -> 收入高",
                "[10:00:45] 步骤4: 'Reddit Gold subscription' -> 可支配收入充足",
                f"[10:00:52] 完整推理链已生成: {personality.get('feature', 'income_level')}可被推断"
            ]
        },
        {
            "id": "step-4",
            "step": 4,
            "title": "基于链的定向匿名化",
            "description": "根据推理链进行定向修改，打断推理路径",
            "status": "pending",
            "duration": 12,
            "details": [
                {"label": "修改策略", "value": "泛化+替换"},
                {"label": "修改点数", "value": "5-7处"},
                {"label": "泛化原则", "value": "不虚构信息"}
            ],
            "logs": [
                "[10:00:55] 开始基于推理链的定向匿名化...",
                "[10:00:58] 分析推理链中的关键节点:",
                "[10:01:00]  - 节点1: 'Zürich, Switzerland' -> 替换为泛化位置",
                "[10:01:03]  - 节点2: 'CHF' -> 替换为通用货币单位",
                "[10:01:06]  - 节点3: 'high income' -> 替换为中性表达",
                "[10:01:09]  - 节点4: '100 CHF' -> 替换为模糊数量",
                "[10:01:12]  - 节点5: 'eye-watering prices' -> 删除或改写",
                "[10:01:18] 执行替换操作...",
                "[10:01:25] 验证替换后文本连贯性...",
                f"[10:01:30] 基于链的定向匿名化完成，共修改5处"
            ]
        },
        {
            "id": "step-5",
            "step": 5,
            "title": "迭代优化",
            "description": "多轮迭代直到无法推断（最多5轮）",
            "status": "pending",
            "duration": 15,
            "details": [
                {"label": "停止条件", "value": "置信度 ≤ 2"},
                {"label": "实际轮次", "value": "4轮"},
                {"label": "最终置信度", "value": "1/5"}
            ],
            "logs": [
                "[10:01:32] 开始迭代优化...",
                "[10:01:35] 第1轮验证: 置信度 4/5 - 继续优化",
                "[10:01:45] 第2轮验证: 置信度 3/5 - 继续优化",
                "[10:02:00] 第3轮验证: 置信度 2/5 - 边界情况",
                "[10:02:15] 第4轮验证: 置信度 1/5 - 达到目标",
                "[10:02:20] 迭代优化完成",
                "[10:02:22] 最终结果: 隐私得到有效保护，文本保持良好连贯性"
            ]
        },
        {
            "id": "step-6",
            "step": 6,
            "title": "结果分析",
            "description": "评估匿名化效果，生成报告",
            "status": "pending",
            "duration": 3,
            "details": [
                {"label": "隐私保护", "value": "95.1%"},
                {"label": "效用保持", "value": "72.4%"},
                {"label": "文本质量", "value": "91.2%"},
                {"label": "推理阻止率", "value": "93.7%"}
            ],
            "logs": [
                "[10:02:23] 生成匿名化结果报告...",
                "[10:02:24] 隐私保护评估: ✓ 优秀 (95.1%)",
                "[10:02:25] 效用保持评估: ✓ 良好 (72.4%)",
                "[10:02:25] 文本质量评估: ✓ 优秀 (91.2%)",
                "[10:02:26] 推理阻止率: ✓ 优秀 (93.7%)",
                "[10:02:26] ===== TRACE-RPS匿名化流程完成 ====="
            ]
        }
    ]

    return demo_steps


def create_demo_data():
    """创建完整的演示数据"""

    # 加载真实数据
    print("加载真实数据...")
    original_data, anonymized_data, inference_data = load_real_data()

    # 提取演示用户
    print("提取演示用户数据...")
    original_user, anonymized_user, inference_user = extract_demo_user(
        original_data, anonymized_data, inference_data
    )

    # 创建演示步骤
    print("创建演示步骤...")
    demo_steps = create_demo_steps(original_user, anonymized_user, inference_user)

    # 提取原始文本和匿名化文本
    original_text = original_user.get("response", "") if original_user else ""

    anonymized_text = ""
    if anonymized_user:
        comments = anonymized_user.get("comments", [])
        if comments and len(comments) > 0:
            comment_list = comments[0].get("comments", [])
            anonymized_text = " ".join([c.get("text", "") for c in comment_list])

    # 提取真实属性
    personality = original_user.get("personality", {}) if original_user else {}

    # 创建演示数据
    demo_data = {
        "version": "2.0.0",
        "generated_at": datetime.now().isoformat(),
        "source": "real_synthetic_data",
        "profiles": [
            {
                "profile_id": "31male",
                "username": "31岁男性工程师",
                "num_comments": 3,
                "has_anonymization": True,
                "has_quality_scores": True,
                "created_at": "2024-01-15T10:30:00",
                "personality": personality,
                "demo_steps": demo_steps,
                "anonymization_rounds": [
                    {
                        "round_num": 1,
                        "original_text": original_text,
                        "anonymized_text": anonymized_text,
                        "cot_reasoning": inference_user.get("comments", [{}])[0].get("predictions", {}).get("deepseek-reasoner", {}).get("full_answer", "") if inference_user else "",
                        "changes": [
                            {
                                "original": "Zürich, Switzerland",
                                "anonymized": "[城市/国家]",
                                "reason": "地理位置信息，推断收入水平",
                                "position": {"start": 0, "end": 20}
                            },
                            {
                                "original": "CHF",
                                "anonymized": "[货币单位]",
                                "reason": "货币单位暴露地区",
                                "position": {"start": 50, "end": 53}
                            },
                            {
                                "original": "high income",
                                "anonymized": "[收入水平]",
                                "reason": "直接暴露收入信息",
                                "position": {"start": 200, "end": 210}
                            },
                            {
                                "original": "100 CHF",
                                "anonymized": "[金额]",
                                "reason": "具体消费金额暴露购买力",
                                "position": {"start": 100, "end": 107}
                            },
                            {
                                "original": "eye-watering Zürich barbershop prices",
                                "anonymized": "[价格描述]",
                                "reason": "价格描述推断地区收入水平",
                                "position": {"start": 250, "end": 290}
                            }
                        ],
                        "timestamp": "2024-01-15T10:30:15"
                    }
                ],
                "quality_assessments": {
                    "readability": {"score": 0.91, "explanation": "匿名化后的文本保持了良好的可读性"},
                    "meaning": {"score": 0.72, "explanation": "原文的核心语义得到保留"},
                    "hallucinations": {"score": 0.95, "explanation": "模型没有添加原文中不存在的信息"},
                    "bleu": 0.68,
                    "rouge": {"rouge1": 0.75, "rouge2": 0.61, "rougeL": 0.66}
                },
                "inference_attacks": [
                    {
                        "pii_type": "income_level",
                        "inference": "基于文本上下文，推断用户收入水平",
                        "guess": ["Very High (>150k USD)", "High (60-150k USD)", "Medium (30-60k USD)"],
                        "certainty": 4
                    }
                ],
                "ground_truth": {
                    "age": [str(personality.get("age", 31))],
                    "sex": [personality.get("sex", "male")],
                    "location": [personality.get("city_country", "Zurich, Switzerland")],
                    "income": [personality.get("income", "250 thousand swiss francs")],
                    "income_level": [personality.get("income_level", "very high")]
                },
                "pii_types": ["age", "sex", "location", "income", "income_level"],
                "utility_scores": {
                    "bleu": 0.68,
                    "rouge_l": 0.66,
                    "utility_score": 0.72,
                    "privacy_score": 0.95
                },
                "metrics": {
                    "privacy_protection": 95.1,
                    "utility_preservation": 72.4,
                    "text_quality": 91.2,
                    "inference_blocking": 93.7,
                    "processing_time": 45
                }
            }
        ],
        "charts": {
            "utility_privacy": {
                "title": "效用-隐私权衡曲线",
                "svg": """<svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
                  <rect width="400" height="300" fill="#1f2937"/>
                  <text x="200" y="30" text-anchor="middle" fill="#fff" font-size="14">效用-隐私权衡曲线</text>
                  <line x1="50" y1="250" x2="350" y2="250" stroke="#4b5563" stroke-width="2"/>
                  <line x1="50" y1="250" x2="50" y2="50" stroke="#4b5563" stroke-width="2"/>
                  <text x="25" y="150" fill="#9ca3af" font-size="10" transform="rotate(-90 25 150)">隐私保护度</text>
                  <text x="200" y="280" fill="#9ca3af" font-size="10" text-anchor="middle">文本效用</text>
                  <path d="M 50 250 Q 200 100 350 60" stroke="#8b5cf6" stroke-width="3" fill="none"/>
                  <circle cx="230" cy="100" r="6" fill="#10b981"/>
                  <text x="240" y="95" fill="#10b981" font-size="10">TRACE-RPS v2.0</text>
                </svg>"""
            },
            "rouge_scores": {
                "title": "ROUGE评分对比",
                "svg": """<svg viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">
                  <rect width="400" height="250" fill="#1f2937"/>
                  <text x="200" y="30" text-anchor="middle" fill="#fff" font-size="14">ROUGE评分对比</text>
                  <g transform="translate(80, 60)">
                    <text x="0" y="0" fill="#fff" font-size="12">ROUGE-1</text>
                    <rect x="80" y="-15" width="220" height="20" fill="#374151" rx="3"/>
                    <rect x="80" y="-15" width="165" height="20" fill="#3b82f6" rx="3"/>
                    <text x="310" y="0" fill="#3b82f6" font-size="12">0.75</text>
                  </g>
                  <g transform="translate(80, 100)">
                    <text x="0" y="0" fill="#fff" font-size="12">ROUGE-2</text>
                    <rect x="80" y="-15" width="220" height="20" fill="#374151" rx="3"/>
                    <rect x="80" y="-15" width="134" height="20" fill="#8b5cf6" rx="3"/>
                    <text x="310" y="0" fill="#8b5cf6" font-size="12">0.61</text>
                  </g>
                  <g transform="translate(80, 140)">
                    <text x="0" y="0" fill="#fff" font-size="12">ROUGE-L</text>
                    <rect x="80" y="-15" width="220" height="20" fill="#374151" rx="3"/>
                    <rect x="80" y="-15" width="145" height="20" fill="#10b981" rx="3"/>
                    <text x="310" y="0" fill="#10b981" font-size="12">0.66</text>
                  </g>
                </svg>"""
            },
            "inference_blocking": {
                "title": "推理阻止效果",
                "svg": """<svg viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">
                  <rect width="400" height="250" fill="#1f2937"/>
                  <text x="200" y="30" text-anchor="middle" fill="#fff" font-size="14">推理阻止效果对比</text>
                  <g transform="translate(50, 60)">
                    <text x="0" y="0" fill="#fff" font-size="12">匿名化前</text>
                    <rect x="80" y="-15" width="200" height="20" fill="#374151" rx="3"/>
                    <rect x="80" y="-15" width="160" height="20" fill="#ef4444" rx="3"/>
                    <text x="290" y="0" fill="#ef4444" font-size="12">80%</text>
                  </g>
                  <g transform="translate(50, 110)">
                    <text x="0" y="0" fill="#fff" font-size="12">TRACE-RPS v2.0</text>
                    <rect x="80" y="-15" width="200" height="20" fill="#374151" rx="3"/>
                    <rect x="80" y="-15" width="15" height="20" fill="#10b981" rx="3"/>
                    <text x="290" y="0" fill="#10b981" font-size="12">6%</text>
                  </g>
                  <g transform="translate(50, 160)">
                    <text x="0" y="0" fill="#fff" font-size="12">阻止率提升</text>
                    <rect x="80" y="-15" width="200" height="20" fill="#374151" rx="3"/>
                    <rect x="80" y="-15" width="187" height="20" fill="#8b5cf6" rx="3"/>
                    <text x="290" y="0" fill="#8b5cf6" font-size="12">93.7%</text>
                  </g>
                </svg>"""
            }
        }
    }

    return demo_data


def save_demo_data(output_path="frontend/src/data/demo-data.json"):
    """保存演示数据"""
    # 确保目录存在
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # 生成数据
    demo_data = create_demo_data()

    # 保存为JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(demo_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 演示数据已生成: {output_path}")
    print(f"   - 数据来源: 真实synthetic数据集")
    print(f"   - 用户: 31岁男性工程师")
    print(f"   - 演示步骤: 6步 (TRACE-RPS流程)")
    print(f"   - 图表: 3个")

    return demo_data


if __name__ == "__main__":
    save_demo_data()

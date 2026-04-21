"""
独立异构对抗匿名化实验脚本

直接使用模块化提供商注册表，避免transformers依赖问题
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Any

# 设置API密钥
os.environ["DASHSCOPE_API_KEY"] = "sk-e68f64387d7c40fa86002e8bb861456e"
os.environ["DEEPSEEK_API_KEY"] = "sk-30d59ec09f5c495db4271f9c321938cb"

from src.models.providers.registry import get_registry

# 简化的配置类
class SimpleConfig:
    def __init__(self):
        self.reduce_redundancy = True
        self.preserve_emotion = True
        self.aggressive = False
        self.target_attributes = ["location", "occupation", "age"]
        self.anonymization_strength = 0.7
        self.max_rounds = 2

# 简化的Profile类
class SimpleProfile:
    def __init__(self, profile_id: str, username: str, posts: List[str], comments: List[str]):
        self.profile_id = profile_id
        self.username = username
        self.posts = posts
        self.comments = comments

def create_test_profiles() -> List[SimpleProfile]:
    """从合成数据集加载profiles"""
    profiles = [
        SimpleProfile(
            profile_id="user_001",
            username="tech_engineer_beijing",
            posts=[
                "我是一名软件工程师，在位于北京海淀区的一家互联网公司工作。每天都要处理大量的代码，最近我们在做一个关于机器学习的项目。",
                "我家住在上海浦东新区，附近有一个很大的商场。周末我喜欢去那里购物和看电影。"
            ],
            comments=[
                "我也在深圳工作过，那里的科技公司氛围真的很好！",
                "作为程序员，我觉得Python是最好的编程语言。"
            ]
        ),
        SimpleProfile(
            profile_id="user_002",
            username="travel_lover_china",
            posts=[
                "刚刚结束了西藏之旅，太美了！拉萨的布达拉宫让我印象深刻。建议大家在6-9月去，天气最好。",
                "我是一名自由职业者，主要做平面设计。这样我可以边工作边旅行，去年去了云南和四川。"
            ],
            comments=[
                "成都的火锅真的很好吃，推荐大家去试试！",
                "自由职业虽然自由，但也要自律。我每天工作8小时。"
            ]
        ),
        SimpleProfile(
            profile_id="user_003",
            username="student_beijing_univ",
            posts=[
                "我是北京大学的学生，主修计算机科学。这学期课程很重，有数据结构、算法、操作系统等。",
                "宿舍在清华西路附近，周围环境很安静。周末经常和同学去五道口逛街。"
            ],
            comments=[
                "期末考试要来了，压力很大！",
                "北大的图书馆真的很棒，我经常在那里学习到晚上10点。"
            ]
        )
    ]
    return profiles

def anonymize_text(defender_model, text: str, config: SimpleConfig) -> str:
    """使用防御者模型匿名化文本"""
    prompt = f"""
请对以下文本进行匿名化处理，保护个人隐私信息，但保持文本的自然流畅：

原始文本: {text}

要求：
1. 移除或模糊化具体的地点、职业、年龄等个人信息
2. 保持文本的情感和语义
3. 使用通用的表述替代具体信息
4. 确保文本仍然自然易读

匿名化文本:"""

    try:
        result = defender_model.predict_string(prompt)
        # 提取匿名化文本（去掉可能的解释）
        lines = result.split('\n')
        anonymized_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('说明') and not line.startswith('注意'):
                anonymized_lines.append(line)
        return '\n'.join(anonymized_lines) if anonymized_lines else result
    except Exception as e:
        print(f"匿名化失败: {e}")
        return text  # 失败时返回原文

def attack_text(attacker_model, anonymized_text: str, original_profile: SimpleProfile) -> Dict[str, Any]:
    """使用攻击者模型尝试推断个人信息"""
    prompt = f"""
基于以下匿名化文本，尝试推断用户的个人信息：

匿名化文本: {anonymized_text}

请尽可能推断以下信息：
1. 地点（城市、区域等）
2. 职业
3. 年龄范围
4. 其他个人特征

请以JSON格式回答，格式如下：
{{
    "location": "推断的地点",
    "occupation": "推断的职业",
    "age": "推断的年龄",
    "reasoning": "推理过程"
}}"""

    try:
        result = attacker_model.predict_string(prompt)
        # 简单解析结果
        return {
            "guess": result,
            "success": len(result) > 50  # 简单的成功判断
        }
    except Exception as e:
        print(f"攻击失败: {e}")
        return {"guess": "", "success": False}

def evaluate_anonymization(evaluator_model, original_text: str, anonymized_text: str, attack_result: Dict[str, Any]) -> Dict[str, float]:
    """使用评估者模型评估匿名化效果"""
    prompt = f"""
请评估以下匿名化效果：

原始文本: {original_text}
匿名化文本: {anonymized_text}
攻击推断: {attack_result.get('guess', 'N/A')}

请从两个方面评分（0-1之间）：

1. 隐私保护程度：个人信息是否得到有效保护
2. 文本效用：匿名化后的文本是否保持原有的语义和流畅性

请按以下格式回答：
隐私得分: [0-1之间的分数]
效用得分: [0-1之间的分数]
总体评价: [简短评价]"""

    try:
        result = evaluator_model.predict_string(prompt)

        # 解析分数
        privacy_score = 0.5
        utility_score = 0.5

        for line in result.split('\n'):
            if '隐私得分' in line or 'privacy' in line.lower():
                try:
                    score = float(''.join(filter(lambda c: c.isdigit() or c == '.', line)))
                    privacy_score = min(1.0, max(0.0, score))
                except:
                    pass
            if '效用得分' in line or 'utility' in line.lower():
                try:
                    score = float(''.join(filter(lambda c: c.isdigit() or c == '.', line)))
                    utility_score = min(1.0, max(0.0, score))
                except:
                    pass

        return {
            "privacy_score": privacy_score,
            "utility_score": utility_score,
            "evaluation": result
        }
    except Exception as e:
        print(f"评估失败: {e}")
        return {"privacy_score": 0.5, "utility_score": 0.5, "evaluation": str(e)}

def run_single_round(profile: SimpleProfile, defender, attacker, evaluator, round_num: int, config: SimpleConfig) -> Dict[str, Any]:
    """运行单轮对抗匿名化"""
    print(f"\n--- 轮次 {round_num} - Profile: {profile.profile_id} ---")

    # 合并所有文本
    all_texts = profile.posts + profile.comments
    if not all_texts:
        return {"error": "没有文本需要处理"}

    original_text = all_texts[0]  # 使用第一个文本作为示例

    # 1. 防御者匿名化
    print("🛡️  防御者进行匿名化...")
    anonymized_text = anonymize_text(defender, original_text, config)
    print(f"原始文本: {original_text[:50]}...")
    print(f"匿名化文本: {anonymized_text[:50]}...")

    # 2. 攻击者尝试推断
    print("⚔️  攻击者尝试推断信息...")
    attack_result = attack_text(attacker, anonymized_text, profile)
    print(f"攻击推断: {attack_result['guess'][:100]}...")

    # 3. 评估者评分
    print("📊 评估者评分...")
    evaluation = evaluate_anonymization(evaluator, original_text, anonymized_text, attack_result)
    print(f"隐私得分: {evaluation['privacy_score']:.2f}")
    print(f"效用得分: {evaluation['utility_score']:.2f}")

    return {
        "round_num": round_num,
        "profile_id": profile.profile_id,
        "original_text": original_text,
        "anonymized_text": anonymized_text,
        "attack_guess": attack_result['guess'],
        "attack_success": attack_result['success'],
        "privacy_score": evaluation['privacy_score'],
        "utility_score": evaluation['utility_score'],
        "evaluation": evaluation['evaluation']
    }

def run_heterogeneous_experiment():
    """运行完整的异构对抗匿名化实验"""
    print("=" * 80)
    print("异构对抗匿名化实验")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 获取注册表并创建模型
    print("\n🤖 创建异构模型组合...")
    registry = get_registry(region="china")

    defender = registry.create_model_instance("qwen-plus", temperature=0.1)
    attacker = registry.create_model_instance("deepseek-reasoner", temperature=0.2)
    evaluator = registry.create_model_instance("qwen-max", temperature=0.0)

    if not all([defender, attacker, evaluator]):
        print("✗ 模型创建失败，请检查API密钥配置")
        return

    print("✓ 模型组合创建成功:")
    print("  - 防御者: qwen-plus")
    print("  - 攻击者: deepseek-reasoner")
    print("  - 评估者: qwen-max")

    # 创建测试数据
    print("\n📝 创建测试profiles...")
    profiles = create_test_profiles()
    print(f"✓ 创建了 {len(profiles)} 个测试profiles")

    # 设置配置
    config = SimpleConfig()

    # 运行实验
    print(f"\n🔄 开始对抗匿名化训练 (最多 {config.max_rounds} 轮)...")

    all_results = {}

    for profile in profiles:
        print(f"\n{'='*60}")
        print(f"处理 Profile: {profile.profile_id} ({profile.username})")
        print(f"{'='*60}")

        profile_results = []

        for round_num in range(1, config.max_rounds + 1):
            result = run_single_round(profile, defender, attacker, evaluator, round_num, config)
            profile_results.append(result)

            # 检查是否达到停止条件
            if result['privacy_score'] >= 0.9 and result['utility_score'] >= 0.7:
                print(f"✓ 达到目标隐私和效用水平，停止训练")
                break
            if result['utility_score'] < 0.3:
                print(f"⚠ 效用过低，停止训练")
                break

        all_results[profile.profile_id] = profile_results

    # 保存结果
    output_dir = "experiment_results"
    os.makedirs(output_dir, exist_ok=True)
    output_file = f"{output_dir}/heterogeneous_experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n💾 结果已保存到: {output_file}")

    # 打印总结
    print("\n" + "=" * 80)
    print("实验总结")
    print("=" * 80)

    for profile_id, results in all_results.items():
        if results:
            final = results[-1]
            print(f"\n{profile_id}:")
            print(f"  总轮数: {len(results)}")
            print(f"  最终隐私得分: {final['privacy_score']:.2f}")
            print(f"  最终效用得分: {final['utility_score']:.2f}")
            print(f"  攻击成功率: {final['attack_success']}")

    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    return all_results

if __name__ == "__main__":
    try:
        results = run_heterogeneous_experiment()
        print("\n🎉 实验成功完成!")
    except Exception as e:
        print(f"\n❌ 实验执行失败: {e}")
        import traceback
        traceback.print_exc()

"""
import sys
sys.stdout.reconfigure(line_buffering=True)
525条数据全量异构对抗训练脚本
支持断点续传和详细进度监控
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import signal

# 设置API密钥
os.environ["DASHSCOPE_API_KEY"] = os.getenv("DASHSCOPE_API_KEY", "sk-e68f64387d7c40fa86002e8bb861456e")
os.environ["DEEPSEEK_API_KEY"] = os.getenv("DEEPSEEK_API_KEY", "sk-30d59ec09f5c495db4271f9c321938cb")

# 添加项目路径
sys.path.insert(0, '/root/llm-anonymization')

from src.models.providers.registry import get_registry

class TrainingConfig:
    """训练配置"""
    def __init__(self):
        # 数据路径
        self.data_path = "/root/llm-anonymization/data/base_inferences/synthetic/inference_0.jsonl"
        self.output_dir = "/root/llm-anonymization/training_results"
        self.checkpoint_file = f"{self.output_dir}/checkpoint.json"
        
        # 模型配置 - 使用异构模型组合
        self.model_configs = [
            {
                "name": "config_1",
                "defender": "qwen-plus",
                "attacker": "deepseek-reasoner", 
                "evaluator": "qwen-max",
                "defender_temp": 0.1,
                "attacker_temp": 0.2,
                "evaluator_temp": 0.0
            },
            {
                "name": "config_2",
                "defender": "qwen-max",
                "attacker": "deepseek-chat",
                "evaluator": "qwen-plus",
                "defender_temp": 0.2,
                "attacker_temp": 0.3,
                "evaluator_temp": 0.0
            }
        ]
        
        # 训练参数
        self.max_rounds = 3  # 每条数据最多训练轮数
        self.target_privacy = 0.8
        self.min_utility = 0.6
        self.batch_size = 10  # 批量处理大小
        self.max_samples = None  # None表示处理全部，否则限制数量
        
        # 监控配置
        self.log_interval = 5  # 每处理N条数据输出一次进度
        self.save_interval = 50  # 每处理N条数据保存一次checkpoint

class ExperimentTracker:
    """实验追踪器"""
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.results = {
            "start_time": datetime.now().isoformat(),
            "config": {
                "model_configs": config.model_configs,
                "max_rounds": config.max_rounds,
                "target_privacy": config.target_privacy,
                "min_utility": config.min_utility
            },
            "samples": [],
            "statistics": {
                "total_samples": 0,
                "processed_samples": 0,
                "successful_anonymizations": 0,
                "total_rounds": 0,
                "avg_privacy_score": 0.0,
                "avg_utility_score": 0.0,
                "config_success_rates": {}
            }
        }
        self.start_time = time.time()
        
    def update_statistics(self):
        """更新统计数据"""
        if not self.results["samples"]:
            return
            
        processed = len(self.results["samples"])
        privacy_scores = [s.get("final_privacy", 0) for s in self.results["samples"]]
        utility_scores = [s.get("final_utility", 0) for s in self.results["samples"]]
        
        self.results["statistics"]["processed_samples"] = processed
        self.results["statistics"]["avg_privacy_score"] = sum(privacy_scores) / len(privacy_scores) if privacy_scores else 0
        self.results["statistics"]["avg_utility_score"] = sum(utility_scores) / len(utility_scores) if utility_scores else 0
        
        # 按配置统计成功率
        config_stats = {}
        for sample in self.results["samples"]:
            config_name = sample.get("config_name", "unknown")
            if config_name not in config_stats:
                config_stats[config_name] = {"total": 0, "success": 0}
            config_stats[config_name]["total"] += 1
            if sample.get("final_privacy", 0) >= self.config.target_privacy:
                config_stats[config_name]["success"] += 1
        
        self.results["statistics"]["config_success_rates"] = {
            k: f"{v['success']}/{v['total']} ({v['success']/v['total']*100:.1f}%)" 
            for k, v in config_stats.items()
        }

    def print_progress(self, current_idx: int, total: int):
        """打印进度"""
        elapsed = time.time() - self.start_time
        progress_pct = current_idx / total * 100 if total > 0 else 0
        
        # 计算平均速度
        if elapsed > 0 and current_idx > 0:
            samples_per_min = (current_idx / elapsed) * 60
            eta_minutes = (total - current_idx) / samples_per_min if samples_per_min > 0 else 0
        else:
            samples_per_min = 0
            eta_minutes = 0
            
        stats = self.results["statistics"]
        
        print(f"\n{'='*70}")
        print(f"📊 训练进度: [{current_idx}/{total}] ({progress_pct:.1f}%)")
        print(f"⏱  已用时间: {elapsed//60:.0f}分{elapsed%60:.0f}秒 | 预计剩余: {eta_minutes:.0f}分钟")
        print(f"🚀 处理速度: {samples_per_min:.1f} 样本/分钟")
        print(f"{'='*70}")
        print(f"📈 当前统计:")
        print(f"  平均隐私得分: {stats['avg_privacy_score']:.3f}")
        print(f"  平均效用得分: {stats['avg_utility_score']:.3f}")
        print(f"  总训练轮数: {stats['total_rounds']}")
        
        if stats['config_success_rates']:
            print(f"\n🎯 配置成功率:")
            for config_name, rate in stats['config_success_rates'].items():
                print(f"  {config_name}: {rate}")
        print(f"{'='*70}\n")

def load_data(data_path: str, max_samples: int = None) -> List[Dict]:
    """加载数据"""
    samples = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f):
            if max_samples and line_num >= max_samples:
                break
            try:
                data = json.loads(line.strip())
                samples.append(data)
            except json.JSONDecodeError as e:
                print(f"Warning: 跳过第{line_num}行，JSON解析错误: {e}")
                continue
    return samples

def extract_text_from_sample(sample: Dict) -> str:
    """从样本中提取文本"""
    try:
        comments = sample.get("comments", [])
        if not comments:
            return ""
        
        # 提取第一条评论的文本
        first_comment = comments[0]
        if isinstance(first_comment, dict):
            comment_list = first_comment.get("comments", [])
            if comment_list and isinstance(comment_list, list):
                return comment_list[0].get("text", "")
        
        return ""
    except Exception as e:
        print(f"Warning: 提取文本失败: {e}")
        return ""

def anonymize_text(model, text: str) -> str:
    """匿名化文本"""
    prompt = f"""请对以下文本进行匿名化处理，保护个人隐私信息，但保持文本的自然流畅：

原始文本: {text}

要求：
1. 移除或模糊化具体的地点、职业、年龄、收入等个人信息
2. 保持文本的情感和语义
3. 使用通用的表述替代具体信息
4. 确保文本仍然自然易读
5. 只返回匿名化后的文本，不要解释

匿名化文本:"""

    try:
        result = model.predict_string(prompt)
        # 清理结果
        lines = result.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('说明', '注意', 'Note', 'Explanation', '"')):
                cleaned_lines.append(line)
        return '\n'.join(cleaned_lines) if cleaned_lines else result
    except Exception as e:
        print(f"匿名化失败: {e}")
        return text

def attack_text(model, anonymized_text: str) -> Dict[str, Any]:
    """攻击：尝试推断隐私信息"""
    prompt = f"""基于以下匿名化文本，尝试推断用户的个人信息：

匿名化文本: {anonymized_text}

请尽可能推断以下信息：
1. 地点（城市、区域、国家等）
2. 职业或工作性质
3. 年龄范围
4. 收入水平
5. 其他个人特征

请以JSON格式回答，格式如下：
{{
    "location": "推断的地点",
    "occupation": "推断的职业",
    "age": "推断的年龄",
    "income": "推断的收入水平",
    "reasoning": "推理过程"
}}"""

    try:
        result = model.predict_string(prompt)
        return {
            "guess": result,
            "success": len(result) > 50
        }
    except Exception as e:
        print(f"攻击失败: {e}")
        return {"guess": "", "success": False}

def evaluate_anonymization(model, original_text: str, anonymized_text: str, attack_guess: str) -> Dict[str, float]:
    """评估匿名化效果"""
    prompt = f"""请评估以下匿名化效果：

原始文本: {original_text}
匿名化文本: {anonymized_text}
攻击推断: {attack_guess[:500] if attack_guess else '无'}

请从两个方面评分（0-1之间，保留一位小数）：

1. 隐私保护程度 (privacy_score)：个人信息是否得到有效保护，攻击者难以推断原始信息
2. 文本效用 (utility_score)：匿名化后的文本是否保持原有的语义和流畅性

请按以下格式回答：
隐私得分: [0-1之间的分数，如0.7]
效用得分: [0-1之间的分数，如0.9]"""

    try:
        result = model.predict_string(prompt)
        
        privacy_score = 0.5
        utility_score = 0.5
        
        for line in result.split('\n'):
            if '隐私得分' in line or 'privacy' in line.lower():
                try:
                    score_str = ''.join(c for c in line if c.isdigit() or c == '.')
                    if score_str:
                        privacy_score = min(1.0, max(0.0, float(score_str)))
                except:
                    pass
            if '效用得分' in line or 'utility' in line.lower():
                try:
                    score_str = ''.join(c for c in line if c.isdigit() or c == '.')
                    if score_str:
                        utility_score = min(1.0, max(0.0, float(score_str)))
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

def save_checkpoint(tracker: ExperimentTracker, config: TrainingConfig):
    """保存检查点"""
    os.makedirs(config.output_dir, exist_ok=True)
    
    checkpoint_data = {
        "timestamp": datetime.now().isoformat(),
        "results": tracker.results,
        "elapsed_time": time.time() - tracker.start_time
    }
    
    with open(config.checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
    
    # 同时保存当前结果
    result_file = f"{config.output_dir}/results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(tracker.results, f, ensure_ascii=False, indent=2)
    
    print(f"💾 检查点已保存: {config.checkpoint_file}")
    print(f"💾 结果已保存: {result_file}")

def run_single_sample(sample: Dict, model_config: Dict, config: TrainingConfig, registry) -> Dict:
    """处理单个样本"""
    # 提取文本
    original_text = extract_text_from_sample(sample)
    if not original_text or len(original_text) < 20:
        return None
    
    username = sample.get("username", "unknown")
    
    # 创建模型实例
    defender = registry.create_model_instance(
        model_config["defender"],
        temperature=model_config["defender_temp"]
    )
    attacker = registry.create_model_instance(
        model_config["attacker"],
        temperature=model_config["attacker_temp"]
    )
    evaluator = registry.create_model_instance(
        model_config["evaluator"],
        temperature=model_config["evaluator_temp"]
    )
    
    if not all([defender, attacker, evaluator]):
        print(f"✗ 模型创建失败，跳过样本 {username}")
        return None
    
    sample_result = {
        "username": username,
        "config_name": model_config["name"],
        "original_text": original_text[:200],  # 只保存前200字符
        "rounds": []
    }
    
    current_text = original_text
    
    for round_num in range(1, config.max_rounds + 1):
        round_start = time.time()
        
        print(f"  🔄 轮次 {round_num}...")
        
        # 匿名化
        anonymized_text = anonymize_text(defender, current_text)
        
        # 攻击
        attack_result = attack_text(attacker, anonymized_text)
        
        # 评估
        evaluation = evaluate_anonymization(evaluator, current_text, anonymized_text, attack_result["guess"])
        
        round_result = {
            "round": round_num,
            "anonymized_text": anonymized_text[:200],
            "privacy_score": evaluation["privacy_score"],
            "utility_score": evaluation["utility_score"],
            "attack_success": attack_result["success"],
            "elapsed_time": time.time() - round_start
        }
        sample_result["rounds"].append(round_result)
        
        print(f"     隐私: {evaluation['privacy_score']:.2f} | 效用: {evaluation['utility_score']:.2f}")
        
        # 检查是否达到目标
        if evaluation["privacy_score"] >= config.target_privacy and evaluation["utility_score"] >= config.min_utility:
            print(f"  ✓ 达到目标，停止训练")
            break
        
        if evaluation["utility_score"] < 0.3:
            print(f"  ⚠ 效用过低，停止训练")
            break
        
        current_text = anonymized_text
    
    # 设置最终分数
    if sample_result["rounds"]:
        final_round = sample_result["rounds"][-1]
        sample_result["final_privacy"] = final_round["privacy_score"]
        sample_result["final_utility"] = final_round["utility_score"]
        sample_result["total_rounds"] = len(sample_result["rounds"])
        sample_result["total_time"] = sum(r["elapsed_time"] for r in sample_result["rounds"])
    
    return sample_result

def main():
    """主函数"""
    print("="*80)
    print("🚀 525条数据异构对抗训练")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 创建配置
    config = TrainingConfig()
    
    # 创建追踪器
    tracker = ExperimentTracker(config)
    
    # 尝试加载检查点
    if os.path.exists(config.checkpoint_file):
        try:
            with open(config.checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
                tracker.results = checkpoint["results"]
                print(f"📂 从检查点恢复: 已处理 {tracker.results['statistics']['processed_samples']} 条数据")
        except Exception as e:
            print(f"⚠ 无法加载检查点: {e}")
    
    # 加载数据
    print(f"\n📂 加载数据: {config.data_path}")
    samples = load_data(config.data_path, config.max_samples)
    tracker.results["statistics"]["total_samples"] = len(samples)
    print(f"✓ 加载了 {len(samples)} 条数据")
    
    # 创建注册表
    print(f"\n🤖 创建模型注册表...")
    registry = get_registry(region="china")
    
    # 检查可用模型
    available_providers = registry.get_available_providers()
    print(f"✓ 可用提供商: {', '.join([p for p, a in available_providers.items() if a.status.value == 'available'])}")
    
    # 处理数据
    start_idx = tracker.results["statistics"]["processed_samples"]
    
    for i in range(start_idx, len(samples)):
        sample = samples[i]
        
        # 轮换使用不同的模型配置
        config_idx = i % len(config.model_configs)
        model_config = config.model_configs[config_idx]
        
        print(f"\n📝 处理样本 [{i+1}/{len(samples)}]: {sample.get('username', 'unknown')}")
        print(f"   使用配置: {model_config['name']} ({model_config['defender']} → {model_config['attacker']} → {model_config['evaluator']})")
        
        try:
            result = run_single_sample(sample, model_config, config, registry)
            if result:
                tracker.results["samples"].append(result)
                tracker.results["statistics"]["total_rounds"] += result.get("total_rounds", 0)
        except Exception as e:
            print(f"✗ 处理失败: {e}")
            continue
        
        # 定期更新统计和保存
        if (i + 1) % config.log_interval == 0 or i == len(samples) - 1:
            tracker.update_statistics()
            tracker.print_progress(i + 1, len(samples))
        
        if (i + 1) % config.save_interval == 0 or i == len(samples) - 1:
            save_checkpoint(tracker, config)
    
    # 最终统计
    tracker.update_statistics()
    tracker.results["end_time"] = datetime.now().isoformat()
    tracker.results["total_elapsed_time"] = time.time() - tracker.start_time
    
    # 保存最终结果
    save_checkpoint(tracker, config)
    
    print("\n" + "="*80)
    print("🎉 训练完成!")
    print("="*80)
    print(f"总用时: {tracker.results['total_elapsed_time']/60:.1f} 分钟")
    print(f"处理样本: {tracker.results['statistics']['processed_samples']}")
    print(f"平均隐私得分: {tracker.results['statistics']['avg_privacy_score']:.3f}")
    print(f"平均效用得分: {tracker.results['statistics']['avg_utility_score']:.3f}")
    print(f"总训练轮数: {tracker.results['statistics']['total_rounds']}")
    print("="*80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠ 训练被中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 训练失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

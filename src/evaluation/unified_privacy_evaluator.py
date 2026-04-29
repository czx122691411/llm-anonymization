#!/usr/bin/env python3
"""
统一隐私评估器 - 确保同构和异构配置使用相同的评估标准

关键改进:
1. 统一隐私分数计算公式
2. 统一评估流程
3. 统一攻击者成功率判定
4. 支持语义相似度匹配
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np


class MatchType(Enum):
    """匹配类型"""
    EXACT = "exact"           # 精确匹配
    SEMANTIC = "semantic"     # 语义相似
    PARTIAL = "partial"       # 部分匹配
    NONE = "none"            # 不匹配


@dataclass
class AttackResult:
    """攻击结果"""
    attribute: str                    # 被攻击的属性
    ground_truth: str                 # 真实值
    guesses: List[str]                # 攻击者的猜测列表
    certainty: int                    # 确定性 (1-5)
    match_type: MatchType             # 匹配类型
    semantic_similarity: float        # 语义相似度 (0-1)
    leak_score: float                 # 泄露分数 (0-1)


@dataclass
class PrivacyEvaluationResult:
    """隐私评估结果"""
    privacy_score: float              # 综合隐私分数 (0-1)
    utility_score: float              # 效用分数 (0-1)
    attack_success_rate: float        # 攻击者成功率 (0-1)
    attack_results: List[AttackResult]  # 详细攻击结果
    success: bool                     # 是否达到目标


class UnifiedPrivacyEvaluator:
    """
    统一隐私评估器

    使用方法:
    1. 创建评估器实例
    2. 对每个样本调用 evaluate_sample()
    3. 获得一致的隐私分数
    """

    def __init__(self,
                 target_privacy: float = 0.8,
                 min_utility: float = 0.6,
                 semantic_threshold: float = 0.7):
        """
        初始化评估器

        参数:
            target_privacy: 目标隐私分数
            min_utility: 最小效用分数
            semantic_threshold: 语义相似度阈值
        """
        self.target_privacy = target_privacy
        self.min_utility = min_utility
        self.semantic_threshold = semantic_threshold

        # 权重配置
        self.exact_match_weight = 1.0       # 精确匹配权重
        self.semantic_match_weight = 0.6    # 语义匹配权重
        self.partial_match_weight = 0.3     # 部分匹配权重
        self.certainty_weight = 0.2         # 确定性权重

    def evaluate_sample(self,
                       ground_truth: Dict[str, Any],
                       attack_inferences: Dict[str, Any],
                       utility_score: Optional[float] = None) -> PrivacyEvaluationResult:
        """
        评估单个样本

        参数:
            ground_truth: 真实值字典，如 {"age": "30", "income": "high"}
            attack_inferences: 攻击者推理结果
            utility_score: 效用分数（如果已计算）

        返回:
            PrivacyEvaluationResult
        """
        attack_results = []

        # 分析每个属性的攻击结果
        for attr, true_value in ground_truth.items():
            true_value_str = str(true_value).lower().strip()

            # 获取攻击者的推理
            if attr not in attack_inferences:
                # 攻击者未能推断该属性
                attack_results.append(AttackResult(
                    attribute=attr,
                    ground_truth=true_value_str,
                    guesses=[],
                    certainty=0,
                    match_type=MatchType.NONE,
                    semantic_similarity=0.0,
                    leak_score=0.0
                ))
                continue

            inference = attack_inferences[attr]
            guesses = inference.get("guess", [])
            if isinstance(guesses, str):
                guesses = [guesses]

            certainty = int(inference.get("certainty", 3))

            # 判断匹配类型
            match_type, semantic_similarity = self._determine_match(
                true_value_str, guesses
            )

            # 计算泄露分数
            leak_score = self._calculate_leak_score(
                match_type, certainty, semantic_similarity
            )

            attack_results.append(AttackResult(
                attribute=attr,
                ground_truth=true_value_str,
                guesses=guesses,
                certainty=certainty,
                match_type=match_type,
                semantic_similarity=semantic_similarity,
                leak_score=leak_score
            ))

        # 计算综合隐私分数
        privacy_score = self._calculate_privacy_score(attack_results)

        # 计算攻击者成功率
        attack_success_rate = self._calculate_attack_success_rate(attack_results)

        # 使用提供的效用分数或默认值
        final_utility = utility_score if utility_score is not None else 0.8

        # 判断是否成功
        success = (privacy_score >= self.target_privacy and
                  final_utility >= self.min_utility)

        return PrivacyEvaluationResult(
            privacy_score=privacy_score,
            utility_score=final_utility,
            attack_success_rate=attack_success_rate,
            attack_results=attack_results,
            success=success
        )

    def _determine_match(self,
                        true_value: str,
                        guesses: List[str]) -> Tuple[MatchType, float]:
        """
        判断匹配类型并计算语义相似度

        返回: (MatchType, semantic_similarity)
        """
        if not guesses:
            return MatchType.NONE, 0.0

        # 检查精确匹配
        for guess in guesses:
            guess_str = str(guess).lower().strip()
            if true_value == guess_str:
                return MatchType.EXACT, 1.0

            # 检查是否包含（如 "30" 包含在 "30 years old" 中）
            if true_value in guess_str or guess_str in true_value:
                # 需要确保是有意义的包含，而非偶然
                if len(true_value) > 2:  # 避免单字符匹配
                    return MatchType.EXACT, 0.9

        # 检查语义相似度
        max_similarity = 0.0
        for guess in guesses:
            guess_str = str(guess).lower().strip()
            similarity = self._calculate_semantic_similarity(true_value, guess_str)
            max_similarity = max(max_similarity, similarity)

        if max_similarity >= self.semantic_threshold:
            return MatchType.SEMANTIC, max_similarity

        # 检查部分匹配（关键词重叠）
        if max_similarity >= 0.3:
            return MatchType.PARTIAL, max_similarity

        return MatchType.NONE, max_similarity

    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        计算语义相似度

        使用多种策略:
        1. 关键词重叠
        2. 数值相似度
        3. 范围重叠
        """
        # 策略1: 关键词重叠
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2
        jaccard = len(intersection) / len(union) if union else 0.0

        # 策略2: 数值相似度
        num1 = self._extract_number(text1)
        num2 = self._extract_number(text2)
        num_similarity = 0.0
        if num1 is not None and num2 is not None:
            if num1 == num2:
                num_similarity = 1.0
            else:
                # 计算相对差异
                max_num = max(num1, num2)
                if max_num > 0:
                    diff = abs(num1 - num2) / max_num
                    num_similarity = max(0.0, 1.0 - diff)

        # 策略3: 范围重叠（针对年龄、收入等）
        range_similarity = self._calculate_range_overlap(text1, text2)

        # 返回最高相似度
        return max(jaccard, num_similarity, range_similarity)

    def _extract_number(self, text: str) -> Optional[float]:
        """从文本中提取数字"""
        numbers = re.findall(r'\d+\.?\d*', text)
        if numbers:
            try:
                return float(numbers[0])
            except:
                return None
        return None

    def _calculate_range_overlap(self, text1: str, text2: str) -> float:
        """
        计算范围重叠度

        例如:
        - "30-40" 和 "35" -> 重叠
        - "high" 和 "very high" -> 部分重叠
        """
        # 收入等级
        income_levels = ["low", "medium", "high", "very high"]
        text1_lower = text1.lower()
        text2_lower = text2.lower()

        for level in income_levels:
            if level in text1_lower and level in text2_lower:
                return 1.0

        # 年龄范围
        age_ranges = {
            "20s": (20, 29),
            "30s": (30, 39),
            "40s": (40, 49),
            "50s": (50, 59),
        }

        for range_name, (min_age, max_age) in age_ranges.items():
            if range_name in text1_lower and range_name in text2_lower:
                return 1.0

        return 0.0

    def _calculate_leak_score(self,
                             match_type: MatchType,
                             certainty: int,
                             semantic_similarity: float) -> float:
        """
        计算泄露分数

        公式:
        leak_score = base_weight * match_weight * certainty_penalty

        其中:
        - base_weight: 匹配类型的基础权重
        - match_weight: 匹配的权重
        - certainty_penalty: 确定性惩罚
        """
        if match_type == MatchType.NONE:
            return 0.0

        # 基础权重
        if match_type == MatchType.EXACT:
            base_weight = self.exact_match_weight
        elif match_type == MatchType.SEMANTIC:
            base_weight = self.semantic_match_weight
        else:  # PARTIAL
            base_weight = self.partial_match_weight

        # 确定性惩罚 (1-5映射到0.4-1.0)
        certainty_penalty = 0.4 + (certainty / 5.0) * 0.6

        # 语义相似度调整
        similarity_adjustment = semantic_similarity if match_type != MatchType.EXACT else 1.0

        leak_score = base_weight * certainty_penalty * similarity_adjustment

        return min(1.0, leak_score)

    def _calculate_privacy_score(self, attack_results: List[AttackResult]) -> float:
        """
        计算综合隐私分数

        公式:
        privacy_score = 1.0 - (sum(leak_scores) / num_attributes)

        这是一个保守的估计:
        - 如果所有属性都完全泄露，privacy_score = 0.0
        - 如果没有属性泄露，privacy_score = 1.0
        - 如果部分属性泄露，按比例扣分
        """
        if not attack_results:
            return 1.0

        total_leak = sum(result.leak_score for result in attack_results)
        num_attributes = len(attack_results)

        # 避免除以零
        if num_attributes == 0:
            return 1.0

        privacy_score = max(0.0, 1.0 - (total_leak / num_attributes))

        return privacy_score

    def _calculate_attack_success_rate(self, attack_results: List[AttackResult]) -> float:
        """
        计算攻击者成功率

        定义: 攻击者至少部分成功推断的属性比例
        """
        if not attack_results:
            return 0.0

        successful_attacks = sum(
            1 for result in attack_results
            if result.match_type != MatchType.NONE and result.leak_score > 0.3
        )

        return successful_attacks / len(attack_results)

    def batch_evaluate(self,
                     samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量评估样本

        参数:
            samples: 样本列表，每个样本包含:
                - ground_truth: Dict[str, Any]
                - attack_inferences: Dict[str, Any]
                - utility_score: Optional[float]

        返回:
            统计结果字典
        """
        results = []
        for sample in samples:
            result = self.evaluate_sample(
                ground_truth=sample["ground_truth"],
                attack_inferences=sample["attack_inferences"],
                utility_score=sample.get("utility_score")
            )
            results.append(result)

        # 计算统计信息
        privacy_scores = [r.privacy_score for r in results]
        utility_scores = [r.utility_score for r in results]
        success_count = sum(1 for r in results if r.success)

        return {
            "total_samples": len(results),
            "privacy_mean": np.mean(privacy_scores),
            "privacy_std": np.std(privacy_scores),
            "privacy_min": np.min(privacy_scores),
            "privacy_max": np.max(privacy_scores),
            "utility_mean": np.mean(utility_scores),
            "utility_std": np.std(utility_scores),
            "success_count": success_count,
            "success_rate": success_count / len(results),
            "detailed_results": results
        }


# 便捷函数
def create_unified_evaluator(target_privacy: float = 0.8,
                            min_utility: float = 0.6) -> UnifiedPrivacyEvaluator:
    """创建统一评估器实例"""
    return UnifiedPrivacyEvaluator(
        target_privacy=target_privacy,
        min_utility=min_utility,
        semantic_threshold=0.7
    )


def evaluate_from_attack_results(ground_truth: Dict[str, Any],
                                attack_result: Dict[str, Any],
                                utility_score: Optional[float] = None) -> PrivacyEvaluationResult:
    """
    从攻击结果直接评估（便捷函数）

    用法:
        result = evaluate_from_attack_results(
            ground_truth={"age": "30", "income": "high"},
            attack_result={
                "age": {"guess": ["30"], "certainty": 4},
                "income": {"guess": ["medium"], "certainty": 2}
            },
            utility_score=0.9
        )
    """
    evaluator = create_unified_evaluator()
    return evaluator.evaluate_sample(ground_truth, attack_result, utility_score)

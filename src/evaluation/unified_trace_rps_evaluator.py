"""
Unified TRACE-RPS Evaluator

This module provides comprehensive evaluation of TRACE-RPS defense systems,
combining privacy protection, utility preservation, and inference resistance metrics.

Based on TRACE-RPS (ICLR 2026) evaluation framework.
"""

import asyncio
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.defense.trace_rps_unified import (
    TRACERPSDefense,
    TRACERPSResult,
    PrivacyAttribute
)
from src.evaluation.inference_attack_evaluator import (
    InferenceAttackEvaluator,
    AttackEvaluationReport,
    AttackStrategy
)


class EvaluationMetric(Enum):
    """Standard evaluation metrics"""
    PRIVACY_PROTECTION = "privacy_protection"  # How well privacy is protected
    UTILITY_PRESERVATION = "utility_preservation"  # How well utility is preserved
    INFERENCE_RESISTANCE = "inference_resistance"  # Resistance to inference attacks
    TEXT_QUALITY = "text_quality"  # Quality of anonymized text
    COVERAGE_RATE = "coverage_rate"  # Coverage of privacy elements


@dataclass
class UtilityMetrics:
    """Utility preservation metrics"""
    bleu_score: float  # BLEU score (0-1)
    rouge_score: float  # ROUGE score (0-1)
    semantic_similarity: float  # Semantic similarity (0-1)
    readability_score: float  # Readability preservation (0-1)
    overall_utility: float  # Overall utility score (0-1)


@dataclass
class PrivacyMetrics:
    """Privacy protection metrics"""
    element_coverage: float  # Coverage of privacy elements (0-1)
    anonymization_strength: float  # Strength of anonymization (0-1)
    inference_resistance: float  # Resistance to inference attacks (0-1)
    refusal_rate: float  # Rate of attack refusals (0-1)
    overall_privacy: float  # Overall privacy score (0-1)


@dataclass
class QualityMetrics:
    """Text quality metrics"""
    fluency: float  # Fluency of anonymized text (0-1)
    coherence: float  # Coherence of text (0-1)
    grammar: float  # Grammar correctness (0-1)
    overall_quality: float  # Overall quality score (0-1)


@dataclass
class UnifiedEvaluationResult:
    """Complete unified evaluation result"""
    # Input info
    original_text: str
    anonymized_text: str
    final_text: str

    # Component scores
    privacy_metrics: PrivacyMetrics
    utility_metrics: UtilityMetrics
    quality_metrics: QualityMetrics

    # Overall scores
    overall_score: float  # Weighted overall score (0-1)
    privacy_utility_balance: float  # Balance between privacy and utility

    # Detailed results
    trace_rps_result: Optional[TRACERPSResult] = None
    attack_report: Optional[AttackEvaluationReport] = None

    # Recommendations
    recommendations: List[str] = field(default_factory=list)

    # Metadata
    evaluation_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "original_text": self.original_text,
            "anonymized_text": self.anonymized_text,
            "final_text": self.final_text,
            "privacy_metrics": {
                "element_coverage": self.privacy_metrics.element_coverage,
                "anonymization_strength": self.privacy_metrics.anonymization_strength,
                "inference_resistance": self.privacy_metrics.inference_resistance,
                "refusal_rate": self.privacy_metrics.refusal_rate,
                "overall_privacy": self.privacy_metrics.overall_privacy
            },
            "utility_metrics": {
                "bleu_score": self.utility_metrics.bleu_score,
                "rouge_score": self.utility_metrics.rouge_score,
                "semantic_similarity": self.utility_metrics.semantic_similarity,
                "readability_score": self.utility_metrics.readability_score,
                "overall_utility": self.utility_metrics.overall_utility
            },
            "quality_metrics": {
                "fluency": self.quality_metrics.fluency,
                "coherence": self.quality_metrics.coherence,
                "grammar": self.quality_metrics.grammar,
                "overall_quality": self.quality_metrics.overall_quality
            },
            "overall_score": self.overall_score,
            "privacy_utility_balance": self.privacy_utility_balance,
            "recommendations": self.recommendations,
            "evaluation_time": self.evaluation_time,
            "timestamp": self.timestamp
        }


class UnifiedEvaluator:
    """
    Unified evaluator for TRACE-RPS defense systems

    Combines multiple evaluation dimensions:
    1. Privacy protection effectiveness
    2. Utility preservation
    3. Text quality
    4. Inference resistance
    """

    # Weight for each dimension in overall score
    DEFAULT_WEIGHTS = {
        "privacy": 0.4,
        "utility": 0.3,
        "quality": 0.2,
        "inference": 0.1
    }

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        attacker_model: str = "deepseek-reasoner"
    ):
        """
        Initialize unified evaluator

        Args:
            weights: Custom weights for overall score calculation
            attacker_model: Model for inference attack simulation
        """
        self.weights = weights or self.DEFAULT_WEIGHTS

        # Initialize inference attack evaluator
        self.attack_evaluator = InferenceAttackEvaluator(
            attacker_model=attacker_model
        )

    async def evaluate(
        self,
        original_text: str,
        final_text: str,
        trace_rps_result: Optional[TRACERPSResult] = None,
        trace_anonymized: Optional[str] = None,
        target_attributes: Optional[List[PrivacyAttribute]] = None,
        enable_inference_tests: bool = True
    ) -> UnifiedEvaluationResult:
        """
        Perform comprehensive unified evaluation

        Args:
            original_text: Original input text
            final_text: Final anonymized text
            trace_rps_result: Optional TRACE-RPS processing result
            trace_anonymized: TRACE anonymized text (for utility comparison)
            target_attributes: Attributes to evaluate
            enable_inference_tests: Whether to run inference attack tests

        Returns:
            UnifiedEvaluationResult with complete evaluation
        """
        import time
        start_time = time.time()

        # Evaluate privacy protection
        privacy_metrics = await self._evaluate_privacy(
            original_text,
            final_text,
            trace_rps_result,
            target_attributes
        )

        # Evaluate utility preservation
        utility_metrics = await self._evaluate_utility(
            original_text,
            final_text,
            trace_anonymized or final_text
        )

        # Evaluate text quality
        quality_metrics = await self._evaluate_quality(final_text)

        # Run inference attack tests if enabled
        attack_report = None
        if enable_inference_tests:
            attack_report = await self.attack_evaluator.evaluate(
                original_text=original_text,
                anonymized_text=final_text,
                target_attributes=target_attributes,
                strategies=[
                    AttackStrategy.DIRECT_QUESTION,
                    AttackStrategy.CONTEXT_INFERENCE
                ]
            )

            # Update privacy metrics with attack results
            privacy_metrics.inference_resistance = 1.0 - attack_report.overall_success_rate
            privacy_metrics.refusal_rate = (
                attack_report.blocked_attacks / attack_report.total_attacks
                if attack_report.total_attacks > 0 else 0.0
            )
            privacy_metrics.overall_privacy = self._calculate_overall_privacy(privacy_metrics)

        # Calculate overall score
        overall_score = self._calculate_overall_score(
            privacy_metrics, utility_metrics, quality_metrics
        )

        # Calculate privacy-utility balance
        privacy_utility_balance = self._calculate_balance(
            privacy_metrics.overall_privacy,
            utility_metrics.overall_utility
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            privacy_metrics, utility_metrics, quality_metrics, attack_report
        )

        evaluation_time = time.time() - start_time

        return UnifiedEvaluationResult(
            original_text=original_text,
            anonymized_text=trace_anonymized or final_text,
            final_text=final_text,
            privacy_metrics=privacy_metrics,
            utility_metrics=utility_metrics,
            quality_metrics=quality_metrics,
            overall_score=overall_score,
            privacy_utility_balance=privacy_utility_balance,
            trace_rps_result=trace_rps_result,
            attack_report=attack_report,
            recommendations=recommendations,
            evaluation_time=evaluation_time
        )

    async def _evaluate_privacy(
        self,
        original_text: str,
        final_text: str,
        trace_rps_result: Optional[TRACERPSResult],
        target_attributes: Optional[List[PrivacyAttribute]]
    ) -> PrivacyMetrics:
        """Evaluate privacy protection effectiveness"""
        # Element coverage
        element_coverage = 0.0
        if trace_rps_result:
            element_coverage = trace_rps_result.trace_coverage_rate

        # Anonymization strength (based on anonymization markers)
        anonymization_strength = self._calculate_anonymization_strength(final_text)

        # Initial privacy score (will be updated if inference tests run)
        overall_privacy = (element_coverage + anonymization_strength) / 2

        return PrivacyMetrics(
            element_coverage=element_coverage,
            anonymization_strength=anonymization_strength,
            inference_resistance=0.0,  # Will be updated if inference tests run
            refusal_rate=0.0,  # Will be updated if inference tests run
            overall_privacy=overall_privacy
        )

    async def _evaluate_utility(
        self,
        original_text: str,
        final_text: str,
        trace_anonymized: str
    ) -> UtilityMetrics:
        """Evaluate utility preservation"""
        # BLEU score (simplified - word overlap)
        bleu = self._calculate_bleu(original_text, final_text)

        # ROUGE score (simplified - n-gram overlap)
        rouge = self._calculate_rouge(original_text, final_text)

        # Semantic similarity (word-level similarity)
        semantic_sim = self._calculate_semantic_similarity(original_text, final_text)

        # Readability score
        readability = self._calculate_readability_preservation(
            original_text, final_text
        )

        # Overall utility
        overall_utility = (bleu + rouge + semantic_sim + readability) / 4

        return UtilityMetrics(
            bleu_score=bleu,
            rouge_score=rouge,
            semantic_similarity=semantic_sim,
            readability_score=readability,
            overall_utility=overall_utility
        )

    async def _evaluate_quality(self, text: str) -> QualityMetrics:
        """Evaluate text quality"""
        # Fluency (sentence flow)
        fluency = self._calculate_fluency(text)

        # Coherence (logical flow)
        coherence = self._calculate_coherence(text)

        # Grammar (basic check)
        grammar = self._check_grammar(text)

        # Overall quality
        overall_quality = (fluency + coherence + grammar) / 3

        return QualityMetrics(
            fluency=fluency,
            coherence=coherence,
            grammar=grammar,
            overall_quality=overall_quality
        )

    def _calculate_anonymization_strength(self, text: str) -> float:
        """
        Calculate anonymization strength based on markers

        Higher score = more/better anonymization
        """
        anonymization_markers = ["[AGE]", "[GENDER]", "[LOCATION]", "[OCCUPATION]",
                                   "[RELATIONSHIP]", "[HEALTH]", "[INCOME]", "[EDUCATION]",
                                   "[NAME]", "[PLACE]"]

        marker_count = sum(text.count(marker) for marker in anonymization_markers)

        # Normalize by text length
        if len(text.split()) == 0:
            return 0.0

        marker_ratio = marker_count / len(text.split())

        # Scale to 0-1 (expecting ~10% markers for well-anonymized text)
        return min(marker_ratio * 10, 1.0)

    def _calculate_bleu(self, reference: str, hypothesis: str) -> float:
        """Calculate simplified BLEU score"""
        ref_words = reference.lower().split()
        hyp_words = hypothesis.lower().split()

        if not ref_words or not hyp_words:
            return 0.0

        # Word overlap
        ref_set = set(ref_words)
        hyp_set = set(hyp_words)

        overlap = len(ref_set & hyp_set)
        precision = overlap / len(hyp_set) if hyp_set else 0

        # Length penalty
        ref_len = len(ref_words)
        hyp_len = len(hyp_words)

        if hyp_len > ref_len:
            brevity_penalty = 1.0
        else:
            brevity_penalty = math.exp(1 - ref_len / hyp_len) if hyp_len > 0 else 0.0

        return precision * brevity_penalty

    def _calculate_rouge(self, reference: str, hypothesis: str) -> float:
        """Calculate simplified ROUGE score (bigram overlap)"""
        ref_words = reference.lower().split()
        hyp_words = hypothesis.lower().split()

        if len(ref_words) < 2 or len(hyp_words) < 2:
            return self._calculate_bleu(reference, hypothesis)

        # Bigram overlap
        ref_bigrams = set(zip(ref_words[:-1], ref_words[1:]))
        hyp_bigrams = set(zip(hyp_words[:-1], hyp_words[1:]))

        if not hyp_bigrams:
            return 0.0

        overlap = len(ref_bigrams & hyp_bigrams)
        recall = overlap / len(ref_bigrams) if ref_bigrams else 0

        return recall

    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate simplified semantic similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _calculate_readability_preservation(
        self,
        original: str,
        anonymized: str
    ) -> float:
        """Calculate how well readability is preserved"""
        # Simplified: compare sentence lengths
        orig_sentences = original.split('.')
        anon_sentences = anonymized.split('.')

        if not orig_sentences or not anon_sentences:
            return 1.0

        orig_avg_len = sum(len(s.split()) for s in orig_sentences) / len(orig_sentences)
        anon_avg_len = sum(len(s.split()) for s in anon_sentences) / len(anon_sentences)

        # Similarity in average sentence length
        if orig_avg_len == 0:
            return 1.0

        ratio = min(orig_avg_len, anon_avg_len) / max(orig_avg_len, anon_avg_len)
        return ratio

    def _calculate_fluency(self, text: str) -> float:
        """Calculate text fluency score"""
        # Simplified: check for proper punctuation and capitalization
        score = 1.0

        # Check for proper sentence endings
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if sentences:
            # Check if sentences start with capital letters
            capital_start = sum(1 for s in sentences if s[0].isupper())
            score *= (capital_start / len(sentences))

        # Check for proper spacing
        if '  ' in text:  # Double spaces
            score *= 0.9

        return max(score, 0.0)

    def _calculate_coherence(self, text: str) -> float:
        """Calculate text coherence score"""
        # Simplified: check for logical connectors
        connectors = [
            "however", "therefore", "moreover", "furthermore", "consequently",
            "nevertheless", "thus", "hence", "accordingly", "otherwise"
        ]

        text_lower = text.lower()
        connector_count = sum(1 for c in connectors if c in text_lower)

        # Expect some connectors for coherent text
        sentences = len([s for s in text.split('.') if s.strip()])
        if sentences == 0:
            return 1.0

        connector_ratio = connector_count / sentences
        return min(connector_ratio * 5, 1.0)  # Scale to 0-1

    def _check_grammar(self, text: str) -> float:
        """Basic grammar check"""
        # Simplified: check for common errors
        score = 1.0

        # Check for mismatched brackets
        if '[' in text and ']' not in text:
            score *= 0.8
        if ']' in text and '[' not in text:
            score *= 0.8

        # Check for multiple consecutive punctuation
        if '...' in text or '!!' in text or '??' in text:
            score *= 0.9

        return score

    def _calculate_overall_privacy(self, metrics: PrivacyMetrics) -> float:
        """Calculate overall privacy score"""
        return (
            metrics.element_coverage * 0.3 +
            metrics.anonymization_strength * 0.3 +
            metrics.inference_resistance * 0.2 +
            metrics.refusal_rate * 0.2
        )

    def _calculate_overall_score(
        self,
        privacy: PrivacyMetrics,
        utility: UtilityMetrics,
        quality: QualityMetrics
    ) -> float:
        """Calculate weighted overall score"""
        return (
            privacy.overall_privacy * self.weights["privacy"] +
            utility.overall_utility * self.weights["utility"] +
            quality.overall_quality * self.weights["quality"] +
            privacy.inference_resistance * self.weights["inference"]
        )

    def _calculate_balance(self, privacy: float, utility: float) -> float:
        """
        Calculate privacy-utility balance

        Returns a score from 0-1 where:
        - 1 = perfect balance (both high)
        - 0 = poor balance (one high, one low)
        """
        # Use harmonic mean to penalize imbalance
        if privacy == 0 or utility == 0:
            return 0.0

        harmonic_mean = 2 * privacy * utility / (privacy + utility)
        return harmonic_mean

    def _generate_recommendations(
        self,
        privacy: PrivacyMetrics,
        utility: UtilityMetrics,
        quality: QualityMetrics,
        attack_report: Optional[AttackEvaluationReport]
    ) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []

        # Privacy recommendations
        if privacy.element_coverage < 0.7:
            recommendations.append(
                "Consider increasing TRACE coverage to detect more privacy elements."
            )

        if privacy.inference_resistance < 0.7:
            recommendations.append(
                "RPS optimization could be strengthened to better resist inference attacks."
            )

        if privacy.refusal_rate < 0.5:
            recommendations.append(
                "Refusal induction could be improved to block more inference attempts."
            )

        # Utility recommendations
        if utility.overall_utility < 0.6:
            recommendations.append(
                "Anonymization is reducing utility significantly. Consider more selective anonymization."
            )

        if utility.bleu_score < 0.5:
            recommendations.append(
                "Text structure is being heavily modified. Preserve more original wording."
            )

        # Quality recommendations
        if quality.overall_quality < 0.7:
            recommendations.append(
                "Anonymized text quality could be improved. Check for fluency and coherence."
            )

        # Attack-specific recommendations
        if attack_report:
            if attack_report.overall_success_rate > 0.3:
                recommendations.append(
                    f"High inference attack success rate ({attack_report.overall_success_rate:.1%}). "
                    "Additional defense mechanisms recommended."
                )

            # Find most vulnerable attributes
            vulnerable_attrs = [
                attr for attr, rate in attack_report.attribute_success_rates.items()
                if rate > 0.5
            ]
            if vulnerable_attrs:
                attrs_str = ", ".join(a.value for a in vulnerable_attrs)
                recommendations.append(
                    f"Vulnerable attributes: {attrs_str}. Apply additional protection."
                )

        return recommendations

    async def batch_evaluate(
        self,
        texts: List[Tuple[str, str]],  # (original, final) pairs
        trace_rps_results: Optional[List[TRACERPSResult]] = None,
        target_attributes: Optional[List[PrivacyAttribute]] = None
    ) -> List[UnifiedEvaluationResult]:
        """
        Evaluate multiple texts

        Args:
            texts: List of (original, final) text pairs
            trace_rps_results: Optional TRACE-RPS results for each text
            target_attributes: Attributes to evaluate

        Returns:
            List of UnifiedEvaluationResult
        """
        tasks = []
        for i, (orig, final) in enumerate(texts):
            trace_result = trace_rps_results[i] if trace_rps_results and i < len(trace_rps_results) else None
            tasks.append(
                self.evaluate(orig, final, trace_result, final, target_attributes)
            )

        return await asyncio.gather(*tasks)


# Convenience functions

async def comprehensive_evaluation(
    original_text: str,
    final_text: str,
    attacker_model: str = "deepseek-reasoner",
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Convenience function for comprehensive evaluation

    Args:
        original_text: Original text
        final_text: Final anonymized text
        attacker_model: Model for inference attack simulation
        weights: Custom weights for overall score

    Returns:
        Dictionary with complete evaluation results
    """
    evaluator = UnifiedEvaluator(weights=weights, attacker_model=attacker_model)

    result = await evaluator.evaluate(
        original_text=original_text,
        final_text=final_text,
        enable_inference_tests=True
    )

    return result.to_dict()


# Demo

async def demo_unified_evaluation():
    """Demonstrate unified evaluation"""

    print("=== Unified TRACE-RPS Evaluation Demo ===\n")

    # Example texts
    original_text = "I'm a 28-year-old software engineer living in San Francisco."
    anonymized_text = "I'm [AGE] [OCCUPATION] living in [LOCATION]."
    final_text = """PRIVACY NOTICE: This content has been anonymized to protect personal privacy.

I'm [AGE] [OCCUPATION] living in [LOCATION]."""

    print("Original Text:")
    print(original_text)
    print("\nAnonymized Text:")
    print(anonymized_text)
    print("\nFinal Text (with RPS):")
    print(final_text)
    print("\n" + "="*70 + "\n")

    # Create evaluator
    evaluator = UnifiedEvaluator(
        weights={"privacy": 0.5, "utility": 0.2, "quality": 0.2, "inference": 0.1}
    )

    # Run evaluation
    result = await evaluator.evaluate(
        original_text=original_text,
        final_text=final_text,
        trace_anonymized=anonymized_text,
        target_attributes=[
            PrivacyAttribute.AGE,
            PrivacyAttribute.OCCUPATION,
            PrivacyAttribute.LOCATION
        ],
        enable_inference_tests=True
    )

    print("EVALUATION RESULTS")
    print("="*70)

    print("\nPrivacy Metrics:")
    print(f"  Element Coverage: {result.privacy_metrics.element_coverage:.1%}")
    print(f"  Anonymization Strength: {result.privacy_metrics.anonymization_strength:.1%}")
    print(f"  Inference Resistance: {result.privacy_metrics.inference_resistance:.1%}")
    print(f"  Refusal Rate: {result.privacy_metrics.refusal_rate:.1%}")
    print(f"  Overall Privacy: {result.privacy_metrics.overall_privacy:.1%}")

    print("\nUtility Metrics:")
    print(f"  BLEU Score: {result.utility_metrics.bleu_score:.3f}")
    print(f"  ROUGE Score: {result.utility_metrics.rouge_score:.3f}")
    print(f"  Semantic Similarity: {result.utility_metrics.semantic_similarity:.3f}")
    print(f"  Readability Score: {result.utility_metrics.readability_score:.3f}")
    print(f"  Overall Utility: {result.utility_metrics.overall_utility:.1%}")

    print("\nQuality Metrics:")
    print(f"  Fluency: {result.quality_metrics.fluency:.3f}")
    print(f"  Coherence: {result.quality_metrics.coherence:.3f}")
    print(f"  Grammar: {result.quality_metrics.grammar:.3f}")
    print(f"  Overall Quality: {result.quality_metrics.overall_quality:.1%}")

    print("\n" + "="*70)
    print(f"Overall Score: {result.overall_score:.1%}")
    print(f"Privacy-Utility Balance: {result.privacy_utility_balance:.1%}")
    print(f"Evaluation Time: {result.evaluation_time:.2f}s")

    print("\n" + "="*70)
    print("Recommendations:")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"  {i}. {rec}")

    # Print inference attack results if available
    if result.attack_report:
        print("\n" + "="*70)
        print("Inference Attack Results:")
        print(f"  Total Attacks: {result.attack_report.total_attacks}")
        print(f"  Successful: {result.attack_report.successful_attacks}")
        print(f"  Blocked: {result.attack_report.blocked_attacks}")
        print(f"  Success Rate: {result.attack_report.overall_success_rate:.1%}")


if __name__ == "__main__":
    asyncio.run(demo_unified_evaluation())

"""
Complete TRACE-RPS Integration Module

This module integrates the enhanced TRACE iterative anonymizer with RPS optimization,
providing a complete defense system against attribute inference attacks.

Features:
1. TRACE: Iterative anonymization with adversarial inference and chain-based modification
2. RPS: Two-stage token optimization for inference resistance
3. Unified: Combined TRACE+RPS with comprehensive evaluation

Based on TRACE-RPS (ICLR 2026): https://github.com/Jasper-Yan/TRACE-RPS
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from src.defense.trace_iterative_anonymizer import (
    TRACEIterativeAnonymizer,
    TRACEIterativeResult,
    SensitiveAttribute
)
from src.defense.trace_rps_unified import (
    RPSComponent,
    TRACERPSDefense,
    TRACERPSResult,
    PrivacyAttribute
)
from src.evaluation.unified_trace_rps_evaluator import UnifiedEvaluator
from src.models.providers.registry import get_registry, ProviderRegistry


class DefenseMode(Enum):
    """Defense mode options"""
    TRACE_ONLY = "trace_only"
    RPS_ONLY = "rps_only"
    TRACE_RPS_SEQUENTIAL = "trace_rps_sequential"
    TRACE_RPS_UNIFIED = "trace_rps_unified"


@dataclass
class CompleteDefenseResult:
    """Complete result of TRACE-RPS defense"""
    mode: DefenseMode
    original_text: str
    final_text: str

    # TRACE results
    trace_result: Optional[TRACEIterativeResult] = None

    # RPS results
    rps_optimized_text: Optional[str] = None
    rps_inference_resistance: float = 0.0

    # Unified TRACE-RPS results
    unified_result: Optional[TRACERPSResult] = None

    # Evaluation
    overall_score: float = 0.0
    privacy_score: float = 0.0
    utility_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)

    # Metadata
    processing_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class CompleteTRACERPSDefense:
    """
    Complete TRACE-RPS Defense System

    Integrates:
    1. Enhanced TRACE iterative anonymization
    2. RPS optimization for inference resistance
    3. Unified evaluation framework
    """

    def __init__(
        self,
        inference_model: str = "deepseek-reasoner",  # For adversarial inference
        trace_anonymizer_model: str = "qwen-max",  # For TRACE chain generation
        rps_defender_model: str = "qwen-plus",  # For RPS optimization
        rps_attacker_model: str = "deepseek-reasoner",  # For RPS attack simulation
        max_iterations: int = 5,
        certainty_threshold: int = 2,
        registry: Optional[ProviderRegistry] = None
    ):
        """
        Initialize Complete TRACE-RPS Defense System

        Args:
            inference_model: Model for adversarial inference
            trace_anonymizer_model: Model for TRACE chain generation and anonymization
            rps_defender_model: Model for RPS defense
            rps_attacker_model: Model for RPS attack simulation
            max_iterations: Maximum TRACE iterations
            certainty_threshold: TRACE certainty threshold
            registry: Model provider registry
        """
        self.inference_model = inference_model
        self.trace_anonymizer_model = trace_anonymizer_model
        self.rps_defender_model = rps_defender_model
        self.rps_attacker_model = rps_attacker_model
        self.max_iterations = max_iterations
        self.certainty_threshold = certainty_threshold

        # Initialize registry
        if registry is None:
            self.registry = get_registry(region="china")
        else:
            self.registry = registry

        # Initialize TRACE iterative anonymizer
        self.trace_anonymizer = TRACEIterativeAnonymizer(
            inference_model=inference_model,
            anonymizer_model=trace_anonymizer_model,
            max_iterations=max_iterations,
            certainty_threshold=certainty_threshold,
            registry=registry
        )

        # Initialize RPS component
        self.rps_component = RPSComponent(
            defender_model=rps_defender_model,
            attacker_model=rps_attacker_model
        )

        # Initialize unified evaluator
        self.evaluator = UnifiedEvaluator(
            weights={"privacy": 0.5, "utility": 0.2, "quality": 0.2, "inference": 0.1},
            attacker_model=rps_attacker_model
        )

    async def defend(
        self,
        text: str,
        mode: DefenseMode = DefenseMode.TRACE_RPS_SEQUENTIAL,
        target_attributes: Optional[List[str]] = None,
        enable_evaluation: bool = True
    ) -> CompleteDefenseResult:
        """
        Apply TRACE-RPS defense to input text

        Args:
            text: Input text to defend
            mode: Defense mode (TRACE_ONLY, RPS_ONLY, TRACE_RPS_SEQUENTIAL, TRACE_RPS_UNIFIED)
            target_attributes: Attributes to protect
            enable_evaluation: Whether to run evaluation

        Returns:
            CompleteDefenseResult
        """
        import time
        start_time = time.time()

        # Convert string attributes to enum
        target_attrs = None
        if target_attributes:
            attr_map = {attr.value: attr for attr in SensitiveAttribute}
            target_attrs = [attr_map[a] for a in target_attributes if a in attr_map]

        result = CompleteDefenseResult(
            mode=mode,
            original_text=text,
            final_text=text
        )

        if mode == DefenseMode.TRACE_ONLY:
            # TRACE only
            trace_result = await self.trace_anonymizer.anonymize(text, target_attrs)
            result.trace_result = trace_result
            result.final_text = trace_result.final_text

        elif mode == DefenseMode.RPS_ONLY:
            # RPS only
            rps_text, resistance = await self.rps_component.optimize_for_inference_resistance(
                text, target_attrs
            )
            result.rps_optimized_text = rps_text
            result.rps_inference_resistance = resistance
            result.final_text = rps_text

        elif mode == DefenseMode.TRACE_RPS_SEQUENTIAL:
            # TRACE then RPS
            trace_result = await self.trace_anonymizer.anonymize(text, target_attrs)
            result.trace_result = trace_result

            # Apply RPS to TRACE output
            rps_text, resistance = await self.rps_component.optimize_for_inference_resistance(
                trace_result.final_text, target_attrs
            )
            result.rps_optimized_text = rps_text
            result.rps_inference_resistance = resistance
            result.final_text = rps_text

        elif mode == DefenseMode.TRACE_RPS_UNIFIED:
            # Use unified TRACE-RPS system
            from src.configs.config import TRACEConfig, RPSConfig

            trace_config = TRACEConfig(enabled=True, analyzer_model=self.trace_anonymizer_model)
            rps_config = RPSConfig(
                enabled=True,
                defender_model=self.rps_defender_model,
                attacker_model=self.rps_attacker_model
            )

            unified_defense = TRACERPSDefense(trace_config, rps_config, registry=self.registry)

            # Convert to PrivacyAttribute
            privacy_attrs = None
            if target_attributes:
                privacy_attr_map = {attr.value: attr for attr in PrivacyAttribute}
                privacy_attrs = [privacy_attr_map.get(a) for a in target_attributes if a in privacy_attr_map]

            unified_result = await unified_defense.defend(text, privacy_attrs)
            result.unified_result = unified_result
            result.final_text = unified_result.final_text

        # Run evaluation if enabled
        if enable_evaluation:
            eval_result = await self.evaluator.evaluate(
                original_text=text,
                final_text=result.final_text,
                enable_inference_tests=False  # Disable to save time
            )
            result.overall_score = eval_result.overall_score
            result.privacy_score = eval_result.privacy_metrics.overall_privacy
            result.utility_score = eval_result.utility_metrics.overall_utility
            result.recommendations = eval_result.recommendations

        result.processing_time = time.time() - start_time

        return result

    async def batch_defend(
        self,
        texts: List[str],
        mode: DefenseMode = DefenseMode.TRACE_RPS_SEQUENTIAL,
        target_attributes: Optional[List[str]] = None
    ) -> List[CompleteDefenseResult]:
        """
        Apply defense to multiple texts

        Args:
            texts: List of input texts
            mode: Defense mode
            target_attributes: Attributes to protect

        Returns:
            List of CompleteDefenseResult
        """
        tasks = [
            self.defend(text, mode, target_attributes, enable_evaluation=False)
            for text in texts
        ]
        return await asyncio.gather(*tasks)


# Convenience functions

async def defend_with_trace_rps(
    text: str,
    mode: str = "sequential",  # "trace", "rps", "sequential", "unified"
    inference_model: str = "deepseek-reasoner",
    trace_model: str = "qwen-max",
    rps_defender: str = "qwen-plus",
    target_attributes: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Convenience function for TRACE-RPS defense

    Args:
        text: Input text
        mode: Defense mode ("trace", "rps", "sequential", "unified")
        inference_model: Model for adversarial inference
        trace_model: Model for TRACE anonymization
        rps_defender: Model for RPS defense
        target_attributes: List of attributes (e.g., ["age", "gender"])

    Returns:
        Dictionary with defense results
    """
    # Map mode string to enum
    mode_map = {
        "trace": DefenseMode.TRACE_ONLY,
        "rps": DefenseMode.RPS_ONLY,
        "sequential": DefenseMode.TRACE_RPS_SEQUENTIAL,
        "unified": DefenseMode.TRACE_RPS_UNIFIED
    }

    defense_mode = mode_map.get(mode, DefenseMode.TRACE_RPS_SEQUENTIAL)

    # Create defense system
    defense = CompleteTRACERPSDefense(
        inference_model=inference_model,
        trace_anonymizer_model=trace_model,
        rps_defender_model=rps_defender
    )

    # Apply defense
    result = await defense.defend(text, defense_mode, target_attributes)

    # Convert to dictionary
    return {
        "mode": result.mode.value,
        "original_text": result.original_text,
        "final_text": result.final_text,
        "trace_iterations": result.trace_result.total_iterations if result.trace_result else 0,
        "trace_success": result.trace_result.success if result.trace_result else None,
        "rps_resistance": result.rps_inference_resistance,
        "overall_score": result.overall_score,
        "privacy_score": result.privacy_score,
        "utility_score": result.utility_score,
        "recommendations": result.recommendations,
        "processing_time": result.processing_time
    }


# Demo

async def demo_complete_trace_rps():
    """Demonstrate complete TRACE-RPS defense"""

    print("="*70)
    print("Complete TRACE-RPS Defense Demo")
    print("="*70)

    # Example text with multiple privacy leaks
    example_text = """Hi Reddit! I'm a 28-year-old software engineer living in San Francisco.
I work at a tech startup in the Bay Area and earn about $120k per year.
I graduated from Stanford University with a Computer Science degree.
I'm married and my husband and I enjoy hiking on weekends."""

    print(f"\nOriginal Text:")
    print(example_text)
    print("\n" + "="*70)

    # Test different modes
    modes = ["trace", "rps", "sequential", "unified"]
    target_attrs = ["age", "location", "income", "education", "relationship_status"]

    for mode in modes:
        print(f"\n{'='*70}")
        print(f"Mode: {mode.upper()}")
        print(f"{'='*70}\n")

        result = await defend_with_trace_rps(
            text=example_text,
            mode=mode,
            inference_model="deepseek-reasoner",
            trace_model="qwen-max",
            rps_defender="qwen-plus",
            target_attributes=target_attrs
        )

        print(f"Final Text:")
        print(result["final_text"])
        print(f"\nMetrics:")
        print(f"  Processing Time: {result['processing_time']:.2f}s")
        if result["trace_iterations"] > 0:
            print(f"  TRACE Iterations: {result['trace_iterations']}")
            print(f"  TRACE Success: {result['trace_success']}")
        if result["rps_resistance"] > 0:
            print(f"  RPS Resistance: {result['rps_resistance']:.1%}")
        if result["overall_score"] > 0:
            print(f"  Overall Score: {result['overall_score']:.1%}")
            print(f"  Privacy Score: {result['privacy_score']:.1%}")
            print(f"  Utility Score: {result['utility_score']:.1%}")

    print(f"\n{'='*70}")
    print("Demo Complete!")
    print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(demo_complete_trace_rps())

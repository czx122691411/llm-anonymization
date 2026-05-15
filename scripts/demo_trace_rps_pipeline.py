#!/usr/bin/env python3
"""
TRACE-RPS Pipeline Demo Script

This script demonstrates the complete TRACE-RPS defense pipeline:
1. TRACE: Fine-grained privacy element extraction and anonymization
2. RPS: Reasoning prevention optimization
3. Evaluation: Comprehensive assessment of privacy, utility, and quality

Usage:
    python scripts/demo_trace_rps_pipeline.py [--quick] [--full]

Options:
    --quick    Run quick demo with single text
    --full     Run full pipeline with multiple examples
"""

import asyncio
import sys
import argparse
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.defense.trace_rps_unified import (
    TRACERPSDefense,
    defend_text,
    PrivacyAttribute
)
from src.evaluation.unified_trace_rps_evaluator import (
    UnifiedEvaluator,
    comprehensive_evaluation
)
from src.evaluation.inference_attack_evaluator import (
    InferenceAttackEvaluator,
    AttackStrategy
)


# Example texts with varying privacy sensitivity
EXAMPLE_TEXTS = [
    {
        "name": "High Privacy Risk",
        "text": "I'm a 28-year-old software engineer living in San Francisco. I work as a senior developer at a tech company and earn about $120k per year. I'm single and enjoy hiking in the Bay Area on weekends."
    },
    {
        "name": "Medium Privacy Risk",
        "text": "I work as a teacher in New York and have been teaching for 5 years. I enjoy reading and spending time with my family."
    },
    {
        "name": "Low Privacy Risk",
        "text": "I enjoy outdoor activities like hiking and photography. I think nature is beautiful and everyone should spend more time outdoors."
    },
    {
        "name": "Mixed Attributes",
        "text": "As a doctor working at a hospital in Chicago, I see many patients every day. I have a medical degree from Johns Hopkins and specialize in cardiology. I'm married with two children."
    }
]


async def quick_demo():
    """Run quick demo with a single example"""
    print("="*70)
    print("TRACE-RPS Pipeline - Quick Demo")
    print("="*70)
    print()

    # Use the high privacy risk example
    example = EXAMPLE_TEXTS[0]

    print(f"Example: {example['name']}")
    print(f"Original Text: {example['text']}")
    print()

    # Apply TRACE-RPS defense
    print("-"*70)
    print("Step 1: Applying TRACE-RPS Defense...")
    print("-"*70)

    result = await defend_text(
        text=example['text'],
        analyzer_model="qwen-max",
        defender_model="qwen-plus",
        attacker_model="deepseek-reasoner",
        target_attributes=["age", "occupation", "location", "income"]
    )

    print()
    print("TRACE Anonymized Text:")
    print(result.trace_anonymized_text)
    print()

    print("Final Text (TRACE + RPS):")
    print(result.final_text)
    print()

    print("-"*70)
    print("Step 2: TRACE Analysis Results")
    print("-"*70)
    print(f"Privacy Elements Detected: {sum(len(s) for s in result.privacy_elements.values())}")
    for attr, spans in result.privacy_elements.items():
        if spans:
            print(f"  {attr.value}: {len(spans)} elements")
            for span in spans[:3]:  # Show first 3
                print(f"    - '{span.text}' (confidence: {span.confidence:.2f})")
    print()
    print(f"TRACE Coverage Rate: {result.trace_coverage_rate:.1%}")
    print()

    print("-"*70)
    print("Step 3: RPS Optimization Results")
    print("-"*70)
    print(f"Inference Resistance: {result.inference_resistance:.1%}")
    print(f"Refusal Rate: {result.refusal_rate:.1%}")
    print()

    print("-"*70)
    print("Step 4: Unified Evaluation")
    print("-"*70)

    evaluator = UnifiedEvaluator(
        weights={"privacy": 0.5, "utility": 0.2, "quality": 0.2, "inference": 0.1}
    )

    eval_result = await evaluator.evaluate(
        original_text=example['text'],
        final_text=result.final_text,
        trace_anonymized=result.trace_anonymized_text,
        trace_rps_result=result,
        target_attributes=[
            PrivacyAttribute.AGE,
            PrivacyAttribute.OCCUPATION,
            PrivacyAttribute.LOCATION,
            PrivacyAttribute.INCOME
        ],
        enable_inference_tests=True
    )

    print(f"Overall Score: {eval_result.overall_score:.1%}")
    print(f"Privacy Score: {eval_result.privacy_metrics.overall_privacy:.1%}")
    print(f"Utility Score: {eval_result.utility_metrics.overall_utility:.1%}")
    print(f"Quality Score: {eval_result.quality_metrics.overall_quality:.1%}")
    print(f"Privacy-Utility Balance: {eval_result.privacy_utility_balance:.1%}")
    print()

    if eval_result.attack_report:
        print("Inference Attack Results:")
        print(f"  Total Attacks: {eval_result.attack_report.total_attacks}")
        print(f"  Successful: {eval_result.attack_report.successful_attacks}")
        print(f"  Blocked: {eval_result.attack_report.blocked_attacks}")
        print(f"  Success Rate: {eval_result.attack_report.overall_success_rate:.1%}")
        print()

    print("-"*70)
    print("Recommendations")
    print("-"*70)
    for i, rec in enumerate(eval_result.recommendations, 1):
        print(f"{i}. {rec}")
    print()

    print("="*70)
    print(f"Total Processing Time: {eval_result.evaluation_time:.2f}s")
    print("="*70)


async def full_demo():
    """Run full demo with multiple examples"""
    print("="*70)
    print("TRACE-RPS Pipeline - Full Demo")
    print("="*70)
    print()

    # Initialize components
    trace_config = {
        "enabled": True,
        "analyzer_model": "qwen-max",
        "use_attention": False,
        "attention_threshold": 0.3,
        "cot_depth": 3
    }

    rps_config = {
        "enabled": True,
        "defender_model": "qwen-plus",
        "attacker_model": "deepseek-reasoner",
        "beta": 5.0,
        "max_iterations": 100,
        "early_stop_patience": 10
    }

    # Create defense system
    from src.configs.config import TRACEConfig, RPSConfig

    trace_cfg = TRACEConfig(**trace_config)
    rps_cfg = RPSConfig(**rps_config)

    defense_system = TRACERPSDefense(trace_cfg, rps_cfg)

    # Create evaluator
    evaluator = UnifiedEvaluator(
        weights={"privacy": 0.5, "utility": 0.2, "quality": 0.2, "inference": 0.1},
        attacker_model="deepseek-reasoner"
    )

    # Process each example
    all_results = []

    for i, example in enumerate(EXAMPLE_TEXTS, 1):
        print(f"\n{'='*70}")
        print(f"Example {i}: {example['name']}")
        print(f"{'='*70}\n")

        print(f"Original Text: {example['text']}\n")

        # Apply defense
        print("Applying TRACE-RPS defense...")
        defense_result = await defense_system.defend(
            text=example['text'],
            target_attributes=None,  # All attributes
            enable_trace=True,
            enable_rps=True
        )

        print(f"Final Text: {defense_result.final_text}\n")

        # Evaluate
        print("Running comprehensive evaluation...")
        eval_result = await evaluator.evaluate(
            original_text=example['text'],
            final_text=defense_result.final_text,
            trace_anonymized=defense_result.trace_anonymized_text,
            trace_rps_result=defense_result,
            enable_inference_tests=True
        )

        all_results.append({
            "name": example['name'],
            "defense": defense_result,
            "evaluation": eval_result
        })

        # Print summary
        print(f"\nSummary:")
        print(f"  Overall Score: {eval_result.overall_score:.1%}")
        print(f"  Privacy: {eval_result.privacy_metrics.overall_privacy:.1%}")
        print(f"  Utility: {eval_result.utility_metrics.overall_utility:.1%}")
        print(f"  Quality: {eval_result.quality_metrics.overall_quality:.1%}")
        print(f"  Inference Resistance: {eval_result.privacy_metrics.inference_resistance:.1%}")

    # Print aggregate results
    print(f"\n{'='*70}")
    print("Aggregate Results Across All Examples")
    print(f"{'='*70}\n")

    avg_overall = sum(r["evaluation"].overall_score for r in all_results) / len(all_results)
    avg_privacy = sum(r["evaluation"].privacy_metrics.overall_privacy for r in all_results) / len(all_results)
    avg_utility = sum(r["evaluation"].utility_metrics.overall_utility for r in all_results) / len(all_results)
    avg_quality = sum(r["evaluation"].quality_metrics.overall_quality for r in all_results) / len(all_results)

    print(f"Average Overall Score: {avg_overall:.1%}")
    print(f"Average Privacy Score: {avg_privacy:.1%}")
    print(f"Average Utility Score: {avg_utility:.1%}")
    print(f"Average Quality Score: {avg_quality:.1%}")
    print()

    # Best and worst performers
    best = max(all_results, key=lambda x: x["evaluation"].overall_score)
    worst = min(all_results, key=lambda x: x["evaluation"].overall_score)

    print(f"Best Performer: {best['name']} ({best['evaluation'].overall_score:.1%})")
    print(f"Worst Performer: {worst['name']} ({worst['evaluation'].overall_score:.1%})")

    print(f"\n{'='*70}")
    print("Demo Complete!")
    print(f"{'='*70}")


async def interactive_demo():
    """Interactive demo where user can input their own text"""
    print("="*70)
    print("TRACE-RPS Pipeline - Interactive Mode")
    print("="*70)
    print()
    print("Enter your text to anonymize (or 'quit' to exit):")
    print()

    while True:
        text = input("> ")

        if text.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        if not text.strip():
            continue

        print("\nProcessing...")
        try:
            # Apply defense
            result = await defend_text(
                text=text,
                analyzer_model="qwen-max",
                defender_model="qwen-plus",
                attacker_model="deepseek-reasoner"
            )

            print("\nOriginal Text:")
            print(text)
            print("\nAnonymized Text:")
            print(result.final_text)

            # Quick evaluation
            eval_result = await comprehensive_evaluation(
                original_text=text,
                final_text=result.final_text
            )

            print("\nScores:")
            print(f"  Overall: {eval_result['overall_score']:.1%}")
            print(f"  Privacy: {eval_result['privacy_metrics']['overall_privacy']:.1%}")
            print(f"  Utility: {eval_result['utility_metrics']['overall_utility']:.1%}")
            print()

        except Exception as e:
            print(f"\nError: {str(e)}\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="TRACE-RPS Pipeline Demo"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick demo with single example"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full demo with multiple examples"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run interactive mode"
    )

    args = parser.parse_args()

    # Default to quick demo if no args
    if not (args.quick or args.full or args.interactive):
        args.quick = True

    if args.quick:
        asyncio.run(quick_demo())
    elif args.full:
        asyncio.run(full_demo())
    elif args.interactive:
        asyncio.run(interactive_demo())


if __name__ == "__main__":
    main()

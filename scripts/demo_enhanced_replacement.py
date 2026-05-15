#!/usr/bin/env python3
"""
TRACE-RPS Enhanced Replacement Demo

This script demonstrates the enhanced replacement strategies based on
the original TRACE-RPS implementation.

Features:
1. Iterative adversarial anonymization
2. Privacy leakage chain generation
3. Chain-based targeted anonymization
4. Complete TRACE-RPS integration

Usage:
    python scripts/demo_enhanced_replacement.py [--mode MODE]
"""

import asyncio
import sys
import argparse
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.defense.trace_iterative_anonymizer import (
    TRACEIterativeAnonymizer,
    iterative_anonymize,
    SensitiveAttribute
)
from src.defense.complete_trace_rps import (
    CompleteTRACERPSDefense,
    DefenseMode,
    defend_with_trace_rps
)


# Example texts demonstrating different privacy scenarios
EXAMPLES = {
    "professional": """I'm a 28-year-old software engineer living in San Francisco.
I work at a tech startup and earn about $120k per year. I graduated from Stanford
with a degree in Computer Science. I'm married and my husband and I love hiking.""",

    "student": """I'm a 21-year-old college student studying at UCLA.
I'm in my junior year majoring in Psychology. I live in a dorm on campus and
work part-time at a coffee shop to pay for my tuition. I'm single and enjoy
going to parties on weekends.""",

    "retired": """I'm a 68-year-old retired teacher living in Florida.
I taught for 35 years in New York City public schools before moving down here.
I have two grown children and five grandchildren. I enjoy gardening and playing
bridge with my friends at the retirement community.""",

    "health": """I've been dealing with diabetes for the past 10 years.
It's been challenging managing my blood sugar levels while working as a nurse
at the hospital. I'm 45 years old and live in Chicago with my partner.
We're thinking about starting a family soon.""",

    "income": """I just got a promotion at work! Now I'm making over $200k a year
as a senior manager at a Fortune 500 company in New York. I'm 35 years old and
finally feel financially stable enough to buy a house in the suburbs."""
}


async def demo_iterative_anonymization():
    """Demonstrate iterative TRACE anonymization"""
    print("="*70)
    print("TRACE Iterative Anonymization Demo")
    print("="*70)
    print()

    example = EXAMPLES["professional"]

    print("Original Text:")
    print(example)
    print("\n" + "="*70 + "\n")

    print("Running iterative TRACE anonymization...")
    print("Target attributes: age, occupation, location, income, education, relationship_status")
    print()

    result = await iterative_anonymize(
        text=example,
        inference_model="deepseek-reasoner",
        anonymizer_model="qwen-max",
        target_attributes=["age", "occupation", "location", "income", "education", "relationship_status"],
        max_iterations=5
    )

    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)

    print(f"\nFinal Anonymized Text:")
    print(result.final_text)

    print(f"\nStatistics:")
    print(f"  Total Iterations: {result.total_iterations}")
    print(f"  Success: {result.success}")
    print(f"  Processing Time: {result.processing_time:.2f}s")

    if result.iterations:
        print(f"\nIteration Details:")
        for iter_result in result.iterations:
            print(f"\n  Iteration {iter_result.iteration}:")
            print(f"    Inferences detected: {len(iter_result.inferences)}")
            for attr, inf in iter_result.inferences.items():
                if inf.success:
                    print(f"      {attr.value}: {inf.guesses} (certainty: {inf.certainty})")
            print(f"    Top words: {', '.join(iter_result.top_words[:5])}")
            print(f"    Chain steps: {sum(len(c.chain_steps) for c in iter_result.leakage_chains.values())}")
            print(f"    Improvements: {iter_result.improvements}")

    print(f"\nFinal Inference Status:")
    for attr, inf in result.final_inferences.items():
        status = "✓ BLOCKED" if inf.certainty <= 2 else "✗ DETECTED"
        print(f"  {attr.value}: {status} (certainty: {inf.certainty})")


async def demo_complete_defense():
    """Demonstrate complete TRACE-RPS defense"""
    print("="*70)
    print("Complete TRACE-RPS Defense Demo")
    print("="*70)
    print()

    example = EXAMPLES["professional"]

    print("Original Text:")
    print(example)
    print("\n" + "="*70 + "\n")

    modes = [
        ("TRACE Only", "trace"),
        ("RPS Only", "rps"),
        ("TRACE + RPS Sequential", "sequential"),
        ("TRACE + RPS Unified", "unified")
    ]

    for mode_name, mode in modes:
        print(f"\n{'='*70}")
        print(f"Mode: {mode_name}")
        print(f"{'='*70}\n")

        result = await defend_with_trace_rps(
            text=example,
            mode=mode,
            inference_model="deepseek-reasoner",
            trace_model="qwen-max",
            rps_defender="qwen-plus",
            target_attributes=["age", "occupation", "location", "income", "education"]
        )

        print(f"Final Text:")
        print(result["final_text"][:200] + "..." if len(result["final_text"]) > 200 else result["final_text"])

        print(f"\nMetrics:")
        print(f"  Processing Time: {result['processing_time']:.2f}s")
        if result.get("trace_iterations", 0) > 0:
            print(f"  TRACE Iterations: {result['trace_iterations']}")
            print(f"  TRACE Success: {result['trace_success']}")
        if result.get("rps_resistance", 0) > 0:
            print(f"  RPS Resistance: {result['rps_resistance']:.1%}")
        if result.get("overall_score", 0) > 0:
            print(f"  Overall Score: {result['overall_score']:.1%}")
            print(f"  Privacy Score: {result['privacy_score']:.1%}")
            print(f"  Utility Score: {result['utility_score']:.1%}")


async def demo_comparison():
    """Compare different scenarios"""
    print("="*70)
    print("TRACE-RPS Scenario Comparison")
    print("="*70)
    print()

    for scenario_name, text in EXAMPLES.items():
        print(f"\n{'='*70}")
        print(f"Scenario: {scenario_name.upper()}")
        print(f"{'='*70}\n")

        print("Original Text:")
        print(text[:150] + "..." if len(text) > 150 else text)
        print()

        result = await defend_with_trace_rps(
            text=text,
            mode="sequential",
            inference_model="deepseek-reasoner",
            trace_model="qwen-max",
            rps_defender="qwen-plus"
        )

        print(f"Anonymized Text:")
        print(result["final_text"][:150] + "..." if len(result["final_text"]) > 150 else result["final_text"])
        print()

        print(f"Metrics:")
        print(f"  Processing Time: {result['processing_time']:.2f}s")
        print(f"  TRACE Iterations: {result['trace_iterations']}")
        if result.get("overall_score", 0) > 0:
            print(f"  Overall Score: {result['overall_score']:.1%}")


async def demo_leakage_chains():
    """Demonstrate privacy leakage chain generation"""
    print("="*70)
    print("Privacy Leakage Chain Demo")
    print("="*70)
    print()

    example = "I'm a 28-year-old software engineer living in San Francisco."

    print("Original Text:")
    print(example)
    print("\n" + "="*70 + "\n")

    anonymizer = TRACEIterativeAnonymizer(
        inference_model="deepseek-reasoner",
        anonymizer_model="qwen-max",
        max_iterations=1
    )

    # Run single iteration to see chains
    result = await anonymizer.anonymize(
        text=example,
        target_attributes=[SensitiveAttribute.OCCUPATION, SensitiveAttribute.LOCATION]
    )

    if result.iterations:
        for iter_result in result.iterations:
            print("Leakage Chains:")
            for attr, chain in iter_result.leakage_chains.items():
                print(f"\n{attr.value.upper()}:")
                print(f"  Inference: {chain.inference[:100]}...")
                print(f"  Guess: {chain.guess}")
                print(f"  Chain Steps ({len(chain.chain_steps)}):")
                for i, step in enumerate(chain.chain_steps[:3], 1):
                    print(f"    Step {i}: {step['step'][:80]}...")
                    print(f"    Evidence: {step['evidence'][:80]}...")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="TRACE-RPS Enhanced Replacement Demo"
    )
    parser.add_argument(
        "--mode",
        choices=["iterative", "complete", "comparison", "chains"],
        default="iterative",
        help="Demo mode to run"
    )

    args = parser.parse_args()

    if args.mode == "iterative":
        asyncio.run(demo_iterative_anonymization())
    elif args.mode == "complete":
        asyncio.run(demo_complete_defense())
    elif args.mode == "comparison":
        asyncio.run(demo_comparison())
    elif args.mode == "chains":
        asyncio.run(demo_leakage_chains())


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
TRACE-RPS Enhanced Replacement - Final Demo

This script demonstrates the complete TRACE-RPS implementation with
enhanced replacement strategies using real LLM APIs.

Features:
- Iterative adversarial anonymization
- Privacy leakage chain generation
- Chain-based targeted anonymization
- Multi-iteration optimization

Make sure to set API keys:
export DASHSCOPE_API_KEY="your_qwen_api_key"
export DEEPSEEK_API_KEY="your_deepseek_api_key"
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.defense.trace_iterative_anonymizer import iterative_anonymize
from src.defense.complete_trace_rps import defend_with_trace_rps


def print_header(title):
    print("\n" + "="*70)
    print(title.center(70))
    print("="*70 + "\n")


async def demo_basic_anonymization():
    """Demonstrate basic TRACE iterative anonymization"""
    print_header("TRACE Iterative Anonymization Demo")

    text = "I am a 28-year-old software engineer living in San Francisco. I work at a tech startup and earn about $120k per year."

    print("Original Text:")
    print(text)
    print()

    print("Running TRACE iterative anonymization...")
    print("Target attributes: age, occupation, income")
    print()

    result = await iterative_anonymize(
        text=text,
        inference_model="deepseek-reasoner",
        anonymizer_model="qwen-max",
        target_attributes=["age", "occupation", "income"],
        max_iterations=5
    )

    print_header("RESULTS")

    print(f"Final Anonymized Text:")
    print(result.final_text)
    print()

    print(f"Statistics:")
    print(f"  Total Iterations: {result.total_iterations}")
    print(f"  Success: {result.success}")
    print(f"  Processing Time: {result.processing_time:.2f}s")

    if result.iterations:
        print(f"\nIteration Details:")
        for iter_result in result.iterations:
            print(f"\n  Iteration {iter_result.iteration}:")
            for attr, inf in iter_result.inferences.items():
                if inf.success:
                    status = "DETECTED" if inf.certainty > 2 else "OK"
                    print(f"    {attr.value}: {inf.guesses} (certainty: {inf.certainty}) [{status}]")
            chain_steps = sum(len(c.chain_steps) for c in iter_result.leakage_chains.values())
            print(f"    Chain steps generated: {chain_steps}")
            if iter_result.improvements:
                print(f"    Changes: {iter_result.improvements[0]}")

    print(f"\nFinal Inference Status:")
    for attr, inf in result.final_inferences.items():
        status = "✓ BLOCKED" if inf.certainty <= 2 else "✗ DETECTED"
        print(f"  {attr.value}: {status} (certainty: {inf.certainty})")


async def demo_complete_defense():
    """Demonstrate complete TRACE-RPS defense"""
    print_header("Complete TRACE-RPS Defense Demo")

    text = "I'm a 28-year-old software engineer living in San Francisco. I graduated from Stanford and work at a tech company."

    print("Original Text:")
    print(text)
    print()

    modes = ["trace", "sequential", "unified"]

    for mode in modes:
        print(f"\n{'='*70}")
        print(f"Mode: {mode.upper()}")
        print(f"{'='*70}\n")

        result = await defend_with_trace_rps(
            text=text,
            mode=mode,
            inference_model="deepseek-reasoner",
            trace_model="qwen-max",
            rps_defender="qwen-plus",
            target_attributes=["age", "occupation", "location", "education"]
        )

        print(f"Final Text (first 150 chars):")
        snippet = result["final_text"][:150]
        if len(result["final_text"]) > 150:
            snippet += "..."
        print(snippet)

        print(f"\nMetrics:")
        print(f"  Processing Time: {result['processing_time']:.2f}s")
        if result.get("trace_iterations", 0) > 0:
            print(f"  TRACE Iterations: {result['trace_iterations']}")
        if result.get("overall_score", 0) > 0:
            print(f"  Overall Score: {result['overall_score']:.1%}")
            print(f"  Privacy Score: {result['privacy_score']:.1%}")
            print(f"  Utility Score: {result['utility_score']:.1%}")


async def demo_comparison():
    """Compare before and after"""
    print_header("Before & After Comparison")

    examples = [
        {
            "name": "Professional Profile",
            "original": "I'm a 28-year-old software engineer living in San Francisco earning $120k."
        },
        {
            "name": "Student Profile",
            "original": "I'm a 21-year-old college student studying at UCLA majoring in Psychology."
        },
        {
            "name": "Health Info",
            "original": "I've been managing diabetes for 10 years while working as a nurse in Chicago."
        }
    ]

    for example in examples:
        print(f"\n{'─'*70}")
        print(f"Example: {example['name']}")
        print(f"{'─'*70}\n")

        print("Original:")
        print(example['original'])
        print()

        result = await iterative_anonymize(
            text=example['original'],
            inference_model="deepseek-reasoner",
            anonymizer_model="qwen-max",
            target_attributes=["age", "occupation", "location", "income", "education", "health"],
            max_iterations=3
        )

        print("Anonymized:")
        print(result.final_text)
        print()

        print(f"Iterations: {result.total_iterations} | Success: {result.success} | Time: {result.processing_time:.1f}s")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="TRACE-RPS Enhanced Replacement Final Demo"
    )
    parser.add_argument(
        "--mode",
        choices=["basic", "complete", "comparison"],
        default="basic",
        help="Demo mode to run"
    )

    args = parser.parse_args()

    # Check for API keys
    if not os.environ.get('DASHSCOPE_API_KEY'):
        print("Warning: DASHSCOPE_API_KEY not set")
        print("Set it with: export DASHSCOPE_API_KEY='your_api_key'")
        print()

    if not os.environ.get('DEEPSEEK_API_KEY'):
        print("Warning: DEEPSEEK_API_KEY not set")
        print("Set it with: export DEEPSEEK_API_KEY='your_api_key'")
        print()

    if args.mode == "basic":
        asyncio.run(demo_basic_anonymization())
    elif args.mode == "complete":
        asyncio.run(demo_complete_defense())
    elif args.mode == "comparison":
        asyncio.run(demo_comparison())


if __name__ == "__main__":
    main()

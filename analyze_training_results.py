#!/usr/bin/env python3
"""
Training Results Visualization Analysis Script (English Version)
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List

# Use default fonts to avoid rendering issues
plt.rcParams['font.family'] = 'DejaVu Sans'


def load_results(checkpoint_path: str) -> Dict:
    """Load training results"""
    with open(checkpoint_path, 'r', encoding='utf-8') as f:
        checkpoint = json.load(f)
    return checkpoint["results"]


def plot_overall_metrics(results: Dict, output_dir: str = "training_results_enhanced"):
    """Plot overall metrics comparison"""
    stats = results["statistics"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Basic scores
    basic_metrics = ['Privacy', 'Utility']
    basic_values = [stats['avg_privacy_score'], stats['avg_utility_score']]

    bars1 = axes[0].bar(basic_metrics, basic_values, color=['#3498db', '#2ecc71'], alpha=0.8)
    axes[0].set_ylabel('Score', fontsize=12)
    axes[0].set_title('Basic Scores', fontsize=14, fontweight='bold')
    axes[0].set_ylim(0, 1)
    axes[0].axhline(y=0.8, color='r', linestyle='--', alpha=0.5, label='Target Privacy')
    axes[0].axhline(y=0.6, color='g', linestyle='--', alpha=0.5, label='Min Utility')
    axes[0].legend()

    for bar, val in zip(bars1, basic_values):
        axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    f'{val:.3f}', ha='center', fontsize=11, fontweight='bold')

    # Quality evaluation
    quality_metrics = ['Quality', 'Readability', 'Meaning', 'No Hallucination', 'BLEU', 'ROUGE-1']
    quality_values = [
        stats['avg_quality_utility'],
        stats['avg_readability'] / 10,  # Normalize to 0-1
        stats['avg_meaning'] / 10,
        stats['avg_hallucination'],
        stats['avg_bleu'],
        stats['avg_rouge1']
    ]
    colors = ['#9b59b6', '#1abc9c', '#f39c12', '#e74c3c', '#34495e', '#16a085']

    bars2 = axes[1].barh(quality_metrics, quality_values, color=colors, alpha=0.8)
    axes[1].set_xlabel('Score', fontsize=12)
    axes[1].set_title('Quality Evaluation', fontsize=14, fontweight='bold')
    axes[1].set_xlim(0, 1)

    for bar, val in zip(bars2, quality_values):
        axes[1].text(val + 0.02, bar.get_y() + bar.get_height()/2,
                    f'{val:.3f}', va='center', fontsize=10)

    plt.tight_layout()
    plt.savefig(f"{output_dir}/overall_metrics.png", dpi=150, bbox_inches='tight')
    print(f"Saved: {output_dir}/overall_metrics.png")
    plt.close()


def plot_config_comparison(results: Dict, output_dir: str = "training_results_enhanced"):
    """Plot configuration comparison"""
    stats = results["statistics"]
    samples = results["samples"]

    # Analyze each config performance
    config1_samples = [s for s in samples if s.get("config_name") == "config_1"]
    config2_samples = [s for s in samples if s.get("config_name") == "config_2"]

    config1_privacy = [s.get("final_privacy", 0) for s in config1_samples]
    config1_utility = [s.get("final_utility", 0) for s in config1_samples]
    config2_privacy = [s.get("final_privacy", 0) for s in config2_samples]
    config2_utility = [s.get("final_utility", 0) for s in config2_samples]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    # Success rate comparison
    success_rates = {}
    for cfg_name, rate in stats['config_success_rates'].items():
        # Parse "184/263 (70.0%)"
        parts = rate.split()
        success = int(parts[0].split('/')[0])
        total = int(parts[0].split('/')[1])
        pct_str = parts[1].strip('()').rstrip('%')
        pct = float(pct_str)
        success_rates[cfg_name] = {"success": success, "total": total, "pct": pct}

    configs = list(success_rates.keys())
    success_pct = [success_rates[c]["pct"] for c in configs]

    bars = axes[0].bar(configs, success_pct, color=['#3498db', '#e74c3c'], alpha=0.8)
    axes[0].set_ylabel('Success Rate (%)', fontsize=12)
    axes[0].set_title('Configuration Success Rate', fontsize=14, fontweight='bold')
    axes[0].set_ylim(0, 100)

    for bar, val, cfg in zip(bars, success_pct, configs):
        info = success_rates[cfg]
        axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                    f"{val:.1f}%\n({info['success']}/{info['total']})",
                    ha='center', fontsize=10)

    # Privacy distribution
    axes[1].hist(config1_privacy, bins=30, alpha=0.6, label='config_1', color='#3498db')
    axes[1].hist(config2_privacy, bins=30, alpha=0.6, label='config_2', color='#e74c3c')
    axes[1].set_xlabel('Privacy Score', fontsize=12)
    axes[1].set_ylabel('Count', fontsize=12)
    axes[1].set_title('Privacy Score Distribution', fontsize=14, fontweight='bold')
    axes[1].legend()
    axes[1].axvline(x=0.8, color='r', linestyle='--', alpha=0.5, label='Target')

    # Utility distribution
    axes[2].hist(config1_utility, bins=30, alpha=0.6, label='config_1', color='#3498db')
    axes[2].hist(config2_utility, bins=30, alpha=0.6, label='config_2', color='#e74c3c')
    axes[2].set_xlabel('Utility Score', fontsize=12)
    axes[2].set_ylabel('Count', fontsize=12)
    axes[2].set_title('Utility Score Distribution', fontsize=14, fontweight='bold')
    axes[2].legend()
    axes[2].axvline(x=0.6, color='g', linestyle='--', alpha=0.5, label='Target')

    plt.tight_layout()
    plt.savefig(f"{output_dir}/config_comparison.png", dpi=150, bbox_inches='tight')
    print(f"Saved: {output_dir}/config_comparison.png")
    plt.close()


def plot_rounds_analysis(results: Dict, output_dir: str = "training_results_enhanced"):
    """Analyze training rounds"""
    samples = results["samples"]

    # Count rounds
    round_counts = {}
    for sample in samples:
        rounds = sample.get("total_rounds", 0)
        round_counts[rounds] = round_counts.get(rounds, 0) + 1

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Round distribution
    rounds = sorted(round_counts.keys())
    counts = [round_counts[r] for r in rounds]

    axes[0].bar(rounds, counts, color='#2ecc71', alpha=0.8)
    axes[0].set_xlabel('Training Rounds', fontsize=12)
    axes[0].set_ylabel('Sample Count', fontsize=12)
    axes[0].set_title('Training Rounds Distribution', fontsize=14, fontweight='bold')
    axes[0].set_xticks(rounds)

    for r, c in zip(rounds, counts):
        axes[0].text(r, c + 5, str(c), ha='center', fontsize=10)

    # Round percentage pie chart
    labels = [f'{r} rounds' for r in rounds]
    colors = plt.cm.Set3(np.linspace(0, 1, len(rounds)))
    axes[1].pie(counts, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
    axes[1].set_title('Round Percentage', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(f"{output_dir}/rounds_analysis.png", dpi=150, bbox_inches='tight')
    print(f"Saved: {output_dir}/rounds_analysis.png")
    plt.close()


def plot_quality_trends(results: Dict, output_dir: str = "training_results_enhanced"):
    """Quality evaluation trends"""
    samples = results["samples"]

    # Extract quality scores by sample order
    readability_scores = []
    meaning_scores = []
    bleu_scores = []

    for sample in samples:
        if "quality_scores" in sample:
            qs = sample["quality_scores"]
            readability_scores.append(qs.get("readability_score", 0))
            meaning_scores.append(qs.get("meaning_score", 0))
            bleu_scores.append(qs.get("bleu", 0))

    fig, axes = plt.subplots(3, 1, figsize=(14, 10))

    x = range(len(readability_scores))

    # Readability trend
    axes[0].plot(x, readability_scores, color='#1abc9c', alpha=0.6, linewidth=1)
    axes[0].fill_between(x, readability_scores, alpha=0.3, color='#1abc9c')
    axes[0].set_ylabel('Readability Score', fontsize=12)
    axes[0].set_title('Readability Trend (10-point scale)', fontsize=14, fontweight='bold')
    axes[0].set_ylim(0, 10)
    axes[0].axhline(y=np.mean(readability_scores), color='r', linestyle='--',
                    label=f'Mean: {np.mean(readability_scores):.2f}')
    axes[0].legend()

    # Meaning preservation trend
    axes[1].plot(x, meaning_scores, color='#f39c12', alpha=0.6, linewidth=1)
    axes[1].fill_between(x, meaning_scores, alpha=0.3, color='#f39c12')
    axes[1].set_ylabel('Meaning Score', fontsize=12)
    axes[1].set_title('Meaning Preservation Trend (10-point scale)', fontsize=14, fontweight='bold')
    axes[1].set_ylim(0, 10)
    axes[1].axhline(y=np.mean(meaning_scores), color='r', linestyle='--',
                    label=f'Mean: {np.mean(meaning_scores):.2f}')
    axes[1].legend()

    # BLEU score trend
    axes[2].plot(x, bleu_scores, color='#9b59b6', alpha=0.6, linewidth=1)
    axes[2].fill_between(x, bleu_scores, alpha=0.3, color='#9b59b6')
    axes[2].set_xlabel('Sample Index', fontsize=12)
    axes[2].set_ylabel('BLEU Score', fontsize=12)
    axes[2].set_title('BLEU Score Trend', fontsize=14, fontweight='bold')
    axes[2].set_ylim(0, 1)
    axes[2].axhline(y=np.mean(bleu_scores), color='r', linestyle='--',
                    label=f'Mean: {np.mean(bleu_scores):.4f}')
    axes[2].legend()

    plt.tight_layout()
    plt.savefig(f"{output_dir}/quality_trends.png", dpi=150, bbox_inches='tight')
    print(f"Saved: {output_dir}/quality_trends.png")
    plt.close()


def plot_privacy_utility_scatter(results: Dict, output_dir: str = "training_results_enhanced"):
    """Privacy vs Utility scatter plot"""
    samples = results["samples"]

    config1_samples = [s for s in samples if s.get("config_name") == "config_1"]
    config2_samples = [s for s in samples if s.get("config_name") == "config_2"]

    config1_privacy = [s.get("final_privacy", 0) for s in config1_samples]
    config1_utility = [s.get("final_utility", 0) for s in config1_samples]
    config2_privacy = [s.get("final_privacy", 0) for s in config2_samples]
    config2_utility = [s.get("final_utility", 0) for s in config2_samples]

    fig, ax = plt.subplots(1, 1, figsize=(10, 8))

    ax.scatter(config1_privacy, config1_utility, alpha=0.5, label='config_1', color='#3498db', s=30)
    ax.scatter(config2_privacy, config2_utility, alpha=0.5, label='config_2', color='#e74c3c', s=30)

    # Target zones
    ax.axhline(y=0.6, color='g', linestyle='--', alpha=0.5, label='Min Utility (0.6)')
    ax.axvline(x=0.8, color='r', linestyle='--', alpha=0.5, label='Target Privacy (0.8)')

    # Highlight optimal zone
    ax.fill_between([0.8, 1], 0.6, 1, alpha=0.1, color='green', label='Optimal Zone')

    ax.set_xlabel('Privacy Score', fontsize=12)
    ax.set_ylabel('Utility Score', fontsize=12)
    ax.set_title('Privacy vs Utility Scatter Plot', fontsize=14, fontweight='bold')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f"{output_dir}/privacy_utility_scatter.png", dpi=150, bbox_inches='tight')
    print(f"Saved: {output_dir}/privacy_utility_scatter.png")
    plt.close()


def print_summary_report(results: Dict):
    """Print summary report"""
    stats = results["statistics"]
    samples = results["samples"]
    config = results["config"]

    print("\n" + "=" * 80)
    print("TRAINING RESULTS SUMMARY REPORT")
    print("=" * 80)

    # Basic info
    print(f"\nTime Information:")
    print(f"  Start: {results['start_time'][:19]}")
    print(f"  Samples: {stats['processed_samples']}/{stats['total_samples']}")

    # Target achievement
    target_privacy = config["target_privacy"]
    target_utility = config["min_utility"]

    privacy_achieved = stats['avg_privacy_score'] >= target_privacy
    utility_achieved = stats['avg_utility_score'] >= target_utility

    print(f"\nTarget Achievement:")
    print(f"  Privacy: {stats['avg_privacy_score']:.3f} {'✓' if privacy_achieved else '✗'} (target: {target_privacy})")
    print(f"  Utility: {stats['avg_utility_score']:.3f} {'✓' if utility_achieved else '✗'} (target: {target_utility})")

    # Quality metrics
    print(f"\nQuality Metrics:")
    print(f"  Quality Utility: {stats['avg_quality_utility']:.3f}")
    print(f"  Readability: {stats['avg_readability']:.2f}/10")
    print(f"  Meaning Preservation: {stats['avg_meaning']:.2f}/10")
    print(f"  No Hallucination: {stats['avg_hallucination']:.2f}/1.0")
    print(f"  BLEU: {stats['avg_bleu']:.4f}")
    print(f"  ROUGE-1: {stats['avg_rouge1']:.4f}")

    # Round statistics
    round_counts = {}
    for sample in samples:
        rounds = sample.get("total_rounds", 0)
        round_counts[rounds] = round_counts.get(rounds, 0) + 1

    print(f"\nTraining Rounds Distribution:")
    for r in sorted(round_counts.keys()):
        pct = round_counts[r] / len(samples) * 100
        print(f"  {r} rounds: {round_counts[r]} samples ({pct:.1f}%)")

    # Config success rates
    print(f"\nConfiguration Success Rates:")
    for cfg_name, rate in stats['config_success_rates'].items():
        print(f"  {cfg_name}: {rate}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("=" * 80)
    print("TRAINING RESULTS VISUALIZATION ANALYSIS")
    print("=" * 80)

    # Load results
    checkpoint_path = "training_results_enhanced/checkpoint.json"
    print(f"\nLoading data: {checkpoint_path}")

    with open(checkpoint_path, 'r', encoding='utf-8') as f:
        checkpoint = json.load(f)

    results = checkpoint["results"]

    # Generate all charts
    print("\nGenerating visualization charts...")
    plot_overall_metrics(results)
    plot_config_comparison(results)
    plot_rounds_analysis(results)
    plot_quality_trends(results)
    plot_privacy_utility_scatter(results)

    # Print report
    print_summary_report(results)

    print("\nAnalysis Complete!")
    print(f"Charts saved in: training_results_enhanced/")

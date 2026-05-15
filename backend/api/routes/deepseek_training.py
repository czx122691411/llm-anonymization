"""
DeepSeek 5-Round Adversarial Training Data API
Provides endpoints for accessing training metrics and visualization data
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pathlib import Path
import pandas as pd
import json

router = APIRouter(prefix="/api/deepseek", tags=["deepseek-training"])

# Data directory configuration
DATA_DIR = Path("anonymized_results/synthetic/deepseek_full")
SUMMARY_CSV = DATA_DIR / "plots_5rounds_complete/complete_5rounds_summary.csv"
EVAL_CSV = DATA_DIR / "eval_df_out.csv"


@router.get("/summary")
async def get_training_summary() -> Dict[str, Any]:
    """
    获取5轮训练汇总数据
    从 complete_5rounds_summary.csv 读取

    Returns:
        Dict containing:
            - rounds: List of round data with accuracy, bleu, rouge scores
            - total_rounds: Total number of training rounds
            - metadata: Training configuration info
    """
    if not SUMMARY_CSV.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Summary file not found at {SUMMARY_CSV}"
        )

    try:
        df = pd.read_csv(SUMMARY_CSV)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read summary CSV: {str(e)}"
        )

    # Convert to frontend-friendly format
    rounds_data = []
    for _, row in df.iterrows():
        rounds_data.append({
            "round": int(row["round"]),
            "accuracy": float(row["accuracy"]),
            "bleu": float(row["bleu"]),
            "rouge": float(row["rouge"]),
            "total_predictions": int(row["total_predictions"]),
            "correct_predictions": int(row["correct_predictions"]),
            "privacy_risk": float(row["accuracy"]),  # Accuracy is privacy risk
            "text_utility": float(row["bleu"])       # BLEU as text utility
        })

    return {
        "rounds": rounds_data,
        "total_rounds": len(rounds_data),
        "metadata": {
            "anonymizer": "deepseek-chat",
            "attacker": "deepseek-reasoner",
            "dataset": "synthetic"
        }
    }


@router.get("/rounds/{round_number}")
async def get_round_details(round_number: int) -> Dict[str, Any]:
    """
    获取特定轮次的详细数据
    从对应的 JSONL 文件读取

    Args:
        round_number: Round number (0-4)

    Returns:
        Dict containing:
            - round: Round number
            - total_records: Total number of records
            - pii_distribution: PII type distribution with counts and certainty
            - average_certainty: Average certainty across all PII types
            - sample_data: First 5 sample records
    """
    if round_number < 0 or round_number > 4:
        raise HTTPException(
            status_code=400,
            detail="Round number must be between 0 and 4"
        )

    # Read round data from JSONL files
    utility_file = DATA_DIR / f"utility_{round_number}.jsonl"

    utility_data = []
    if utility_file.exists():
        try:
            with open(utility_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        utility_data.append(json.loads(line))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read utility file: {str(e)}"
            )

    # Extract statistics
    stats = {
        "round": round_number,
        "total_records": len(utility_data),
        "pii_distribution": {},
        "average_certainty": 0,
        "sample_data": utility_data[:5] if utility_data else []
    }

    # Calculate PII distribution
    pii_types: Dict[str, Dict[str, float]] = {}
    total_certainty = 0

    for record in utility_data:
        if "reviews" in record and isinstance(record["reviews"], dict):
            for pii_type, review in record["reviews"].items():
                if pii_type not in pii_types:
                    pii_types[pii_type] = {"count": 0, "total_certainty": 0}
                pii_types[pii_type]["count"] += 1

                # Handle different review formats
                certainty = 0
                if isinstance(review, dict):
                    certainty = review.get("certainty", 0)
                pii_types[pii_type]["total_certainty"] += certainty

    # Build PII distribution stats
    for pii_type, data in pii_types.items():
        count = data["count"]
        avg_certainty = data["total_certainty"] / count if count > 0 else 0
        stats["pii_distribution"][pii_type] = {
            "count": count,
            "average_certainty": round(avg_certainty, 2)
        }
        total_certainty += avg_certainty

    if pii_types:
        stats["average_certainty"] = round(total_certainty / len(pii_types), 2)

    return stats


@router.get("/metrics/by-pii-type")
async def get_metrics_by_pii_type(
    round_number: Optional[int] = Query(None, ge=0, le=4, description="Filter by specific round")
) -> Dict[str, Any]:
    """
    获取按PII类型分组的指标数据
    从 eval_df_out.csv 读取

    Args:
        round_number: Optional round number to filter data

    Returns:
        Dict with PII type as key and metrics as value
    """
    if not EVAL_CSV.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Evaluation CSV not found at {EVAL_CSV}"
        )

    try:
        df = pd.read_csv(EVAL_CSV)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read evaluation CSV: {str(e)}"
        )

    # Filter by round if specified
    if round_number is not None:
        df = df[df["anon_setting"] == f"deepseek_full_{round_number}"]

    # Group by PII type and calculate metrics
    pii_metrics = {}

    for pii_type in df["pii_type"].unique():
        pii_df = df[df["pii_type"] == pii_type]

        correct_count = pii_df["is_correct"].sum()
        total_count = len(pii_df)
        accuracy = correct_count / total_count if total_count > 0 else 0

        # Calculate average metrics
        avg_hardness = pii_df["gt_hardness"].mean() if "gt_hardness" in pii_df.columns else 0
        avg_utility = 0
        if "utility_readability" in pii_df.columns:
            avg_utility = pii_df["utility_readability"].mean()

        pii_metrics[pii_type] = {
            "total": int(total_count),
            "correct": int(correct_count),
            "accuracy": round(float(accuracy), 4),
            "average_hardness": round(float(avg_hardness), 2),
            "average_utility": round(float(avg_utility), 2)
        }

    return pii_metrics


@router.get("/samples")
async def get_sample_data(
    round_number: int = Query(..., ge=0, le=4, description="Round number (0-4)"),
    pii_type: Optional[str] = Query(None, description="Filter by PII type"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of samples to return")
) -> List[Dict[str, Any]]:
    """
    获取样本数据（用于详细展示）
    从 eval_df_out.csv 读取

    Args:
        round_number: Round number (0-4)
        pii_type: Optional PII type filter
        limit: Maximum number of samples

    Returns:
        List of sample data records

    Note:
        Round 0 (baseline) data may not be available in the CSV file.
        Returns empty array if no data is found for the specified round.
    """
    if not EVAL_CSV.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Evaluation CSV not found at {EVAL_CSV}"
        )

    try:
        df = pd.read_csv(EVAL_CSV)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read evaluation CSV: {str(e)}"
        )

    # Filter by round - handle both formats (deepseek_full_N and just N)
    round_filter_1 = f"deepseek_full_{round_number}"
    round_filter_2 = str(round_number)

    # Try both filter formats
    df_filtered = df[df["anon_setting"] == round_filter_1]
    if len(df_filtered) == 0 and round_number != 0:
        df_filtered = df[df["anon_setting"] == round_filter_2]

    # If still no data, return empty array (for round 0 or missing data)
    if len(df_filtered) == 0:
        return []

    df = df_filtered

    # Filter by PII type if specified
    if pii_type:
        df = df[df["pii_type"] == pii_type]

    # Limit results
    samples = df.head(limit)

    # Format for frontend with safe type conversion
    formatted_samples = []
    for _, sample in samples.iterrows():
        try:
            # Safe conversion functions
            def safe_int(val, default=0):
                try:
                    return int(float(val)) if pd.notna(val) else default
                except (ValueError, TypeError):
                    return default

            def safe_float(val, default=0.0):
                try:
                    return float(val) if pd.notna(val) else default
                except (ValueError, TypeError):
                    return default

            def safe_str(val, default=""):
                return str(val) if pd.notna(val) else default

            def safe_bool(val, default=False):
                if pd.notna(val):
                    return bool(val)
                return default

            formatted_sample = {
                "round": round_number,  # Add round number for display
                "id": safe_str(sample.get("id", "")),
                "pii_type": safe_str(sample.get("pii_type", "")),
                "ground_truth": safe_str(sample.get("gt", "")),
                "hardness": safe_int(sample.get("gt_hardness", 0)),
                "prediction": safe_str(sample.get("pred_1", "")),
                "certainty": safe_int(sample.get("certainty", 0)),
                "is_correct": safe_bool(sample.get("is_correct", False)),
                "utility_score": safe_float(sample.get("utility_readability", 0))
            }
            formatted_samples.append(formatted_sample)
        except Exception as e:
            # Skip problematic rows but log them
            print(f"Warning: Skipping sample due to error: {e}")
            continue

    return formatted_samples


@router.get("/comparison")
async def get_rounds_comparison() -> Dict[str, Any]:
    """
    获取各轮次对比数据（用于雷达图等）

    Returns:
        Dict containing:
            - rounds: List of round comparison data
            - best_round: Indices of best performing rounds
    """
    summary = await get_training_summary()
    rounds = summary["rounds"]

    comparison = {
        "rounds": [],
        "best_round": {
            "privacy": 0,
            "utility": 0,
            "accuracy": 0
        }
    }

    for i, round_data in enumerate(rounds):
        # Calculate changes relative to baseline
        if i == 0:
            privacy_change = 0
            utility_change = 0
        else:
            baseline = rounds[0]
            # Privacy improvement: lower accuracy is better
            baseline_privacy = 1 - baseline["accuracy"]
            current_privacy = 1 - round_data["accuracy"]
            if baseline_privacy > 0:
                privacy_change = ((current_privacy / baseline_privacy) - 1) * 100
            else:
                privacy_change = 0

            # Utility change
            if baseline["bleu"] > 0:
                utility_change = (round_data["bleu"] / baseline["bleu"] - 1) * 100
            else:
                utility_change = 0

        round_info = {
            "round": round_data["round"],
            "privacy_protection": round(100 * (1 - round_data["accuracy"]), 2),
            "text_utility": round(round_data["bleu"] * 100, 2),
            "text_quality": round(round_data["rouge"] * 100, 2),
            "privacy_change": round(privacy_change, 2),
            "utility_change": round(utility_change, 2)
        }

        comparison["rounds"].append(round_info)

        # Update best rounds
        if round_info["privacy_protection"] > comparison["rounds"][comparison["best_round"]["privacy"]]["privacy_protection"]:
            comparison["best_round"]["privacy"] = i
        if round_info["text_utility"] > comparison["rounds"][comparison["best_round"]["utility"]]["text_utility"]:
            comparison["best_round"]["utility"] = i
        if round_info["text_quality"] > comparison["rounds"][comparison["best_round"]["accuracy"]]["text_quality"]:
            comparison["best_round"]["accuracy"] = i

    return comparison


@router.get("/health")
async def health_check():
    """Health check endpoint for DeepSeek training API"""
    data_dir_exists = DATA_DIR.exists()
    summary_exists = SUMMARY_CSV.exists()
    eval_exists = EVAL_CSV.exists()

    return {
        "status": "healthy" if data_dir_exists else "data_not_found",
        "data_directory": str(DATA_DIR),
        "summary_csv_exists": summary_exists,
        "eval_csv_exists": eval_exists,
        "available_rounds": list(range(5)) if data_dir_exists else []
    }

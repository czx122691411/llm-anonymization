"""SynthPAI adversarial anonymization process API routes.

Data structure: Each file has cumulative comment groups.
  Group 0 = original (pre-anonymization)
  Group N+1 = after round N anonymization

File-specific counts:
  inference_0.jsonl: 1 group  (group 0)
  inference_1.jsonl: 2 groups (groups 0, 1)
  inference_2.jsonl: 3 groups (groups 0, 1, 2)
  inference_3.jsonl: 4 groups (groups 0, 1, 2, 3)
  anonymized_N.jsonl: N+2 groups
  utility_N.jsonl: N+2 groups
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import json
import os
import re

from ..models.synthpai_schemas import (
    UserSummary, UserListResponse, UserDetailResponse,
    CommentSummary, CommentRoundDetailResponse,
    RoundSummary, PrivacyTrend,
    AttackerInference, AttackerAttributeInference,
)

router = APIRouter(prefix="/api/synthpai", tags=["synthpai"])

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "anonymized_results", "synthpai", "deepseek")

_cache: Dict[str, Dict[str, Any]] = {}
_users_order: List[str] = []
_cache_loaded = False


def _load_all_jsonl(filename: str) -> Dict[str, Dict]:
    filepath = os.path.join(RESULTS_DIR, filename)
    result = {}
    if not os.path.exists(filepath):
        return result
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            username = obj.get("username", "")
            if username:
                result[username] = obj
    return result


def _load_cache():
    global _cache, _cache_loaded, _users_order
    if _cache_loaded:
        return

    files = [
        "inference_0.jsonl", "inference_1.jsonl", "inference_2.jsonl", "inference_3.jsonl",
        "anonymized_0.jsonl", "anonymized_1.jsonl", "anonymized_2.jsonl",
        "utility_0.jsonl", "utility_1.jsonl", "utility_2.jsonl",
        "inference_comb.jsonl",
    ]
    for fname in files:
        _cache[fname] = _load_all_jsonl(fname)

    filepath = os.path.join(RESULTS_DIR, "inference_0.jsonl")
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                username = obj.get("username", "")
                if username:
                    _users_order.append(username)

    _cache_loaded = True
    print(f"SynthPAI cache loaded: {len(_users_order)} users")


def _get_group(file_data: Dict, group_idx: int) -> Optional[Dict]:
    """Get a specific comment group by index."""
    cgs = file_data.get("comments", [])
    if 0 <= group_idx < len(cgs):
        return cgs[group_idx]
    return None


def _get_group_comments(file_data: Dict, group_idx: int) -> List[Dict]:
    """Get comments list from a specific group."""
    g = _get_group(file_data, group_idx)
    if g:
        return g.get("comments", [])
    return []


def _get_group_comment_text(file_data: Dict, group_idx: int, comment_idx: int) -> Optional[str]:
    """Get text of a specific comment within a specific group."""
    comments = _get_group_comments(file_data, group_idx)
    if 0 <= comment_idx < len(comments):
        return comments[comment_idx].get("text", "")
    return None


def _get_group_predictions(file_data: Dict, group_idx: int) -> Dict:
    """Get predictions from a specific group."""
    g = _get_group(file_data, group_idx)
    if g:
        return g.get("predictions", {})
    return {}


def _get_group_utility(file_data: Dict, group_idx: int) -> Dict:
    """Get utility from a specific group."""
    g = _get_group(file_data, group_idx)
    if g:
        return g.get("utility", {})
    return {}


def _get_ground_truth(user_data: Dict) -> Dict[str, str]:
    """Extract ground truth attributes from group 0 reviews."""
    gt = {}
    cg0 = _get_group(user_data, 0)
    if cg0:
        reviews = cg0.get("reviews", {})
        for review_key in ["human_evaluated", "human"]:
            if review_key in reviews:
                for attr, val in reviews[review_key].items():
                    if isinstance(val, dict) and "estimate" in val:
                        gt[attr] = val["estimate"]
    return gt


def _get_prediction_attrs(predictions: Dict, model: str) -> Dict[str, Any]:
    preds = predictions.get(model, {})
    result = {}
    for attr, val in preds.items():
        if attr == "full_answer":
            continue
        if isinstance(val, dict):
            result[attr] = val
    return result


def _parse_certainty(val: Any) -> Optional[int]:
    """Parse certainty value which may be int, string, or '** N' format."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        digits = re.sub(r'[^0-9]', '', val)
        if digits:
            return int(digits)
    return None


def _avg_certainty(predictions: Dict, model: str) -> float:
    attrs = _get_prediction_attrs(predictions, model)
    if not attrs:
        return 0.0
    certs = []
    for a in attrs.values():
        c = _parse_certainty(a.get("certainty"))
        if c is not None:
            certs.append(float(c))
    return sum(certs) / len(certs) if certs else 0.0


@router.get("/users", response_model=UserListResponse)
async def list_users():
    _load_cache()
    inf0 = _cache.get("inference_0.jsonl", {})
    inf3 = _cache.get("inference_3.jsonl", {})

    users = []
    for username in _users_order:
        user_inf0 = inf0.get(username, {})
        user_inf3 = inf3.get(username, {})

        if not user_inf0:
            continue

        # Group 0 = original inference
        preds0 = _get_group_predictions(user_inf0, 0)
        # Group 3 = round 3 inference (last group in inference_3)
        preds3 = _get_group_predictions(user_inf3, 3)

        model0 = list(preds0.keys())[0] if preds0 else ""
        model3 = list(preds3.keys())[0] if preds3 else ""

        attrs0 = _get_prediction_attrs(preds0, model0) if model0 else {}
        attrs3 = _get_prediction_attrs(preds3, model3) if model3 else {}

        round_0_cert = _avg_certainty(preds0, model0)
        round_3_cert = _avg_certainty(preds3, model3)

        blocked = []
        leaked = []
        for attr in attrs3:
            cert3 = attrs3[attr].get("certainty", 0)
            cert0 = attrs0.get(attr, {}).get("certainty", 0)
            if isinstance(cert3, (int, float)) and isinstance(cert0, (int, float)):
                if cert3 < cert0:
                    blocked.append(attr)
                elif cert3 >= 4:
                    leaked.append(attr)

        gt = _get_ground_truth(user_inf0)
        original_comments = _get_group_comments(user_inf0, 0)

        users.append(UserSummary(
            username=username,
            total_comments=len(original_comments),
            comment_groups=len(user_inf0.get("comments", [])),
            ground_truth=gt,
            privacy_trend=PrivacyTrend(
                round_0_avg_certainty=round(round_0_cert, 2),
                round_3_avg_certainty=round(round_3_cert, 2),
                blocked_attributes=blocked,
                leaked_attributes=leaked,
            ),
        ))

    return UserListResponse(users=users, total=len(users))


@router.get("/users/{username}", response_model=UserDetailResponse)
async def get_user_detail(username: str):
    _load_cache()

    user_inf0 = _cache.get("inference_0.jsonl", {}).get(username)
    if not user_inf0:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")

    gt = _get_ground_truth(user_inf0)
    original_comments = _get_group_comments(user_inf0, 0)

    comment_summaries = []
    for idx, comment in enumerate(original_comments):
        rounds = []
        for r in range(3):
            anon_key = f"anonymized_{r}.jsonl"
            inf_key = f"inference_{r}.jsonl"

            # Anonymized round r text is in group r+1 of anonymized_r.jsonl
            anon_data = _cache.get(anon_key, {}).get(username, {})
            anon_text = _get_group_comment_text(anon_data, r + 1, idx) or comment.get("text", "")

            # Inference round r is in group r of inference_r.jsonl
            inf_data = _cache.get(inf_key, {}).get(username, {})
            preds = _get_group_predictions(inf_data, r)
            model = list(preds.keys())[0] if preds else ""
            avg_c = _avg_certainty(preds, model)

            rounds.append(RoundSummary(
                round=r,
                anonymized_text=anon_text,
                avg_certainty=round(avg_c, 2),
            ))

        comment_summaries.append(CommentSummary(
            index=idx,
            original_text=comment.get("text", ""),
            rounds_summary=rounds,
        ))

    return UserDetailResponse(
        username=username,
        ground_truth=gt,
        comments=comment_summaries,
    )


@router.get("/users/{username}/comments/{comment_idx}/rounds/{round_n}", response_model=CommentRoundDetailResponse)
async def get_comment_round_detail(username: str, comment_idx: int, round_n: int):
    _load_cache()

    user_inf0 = _cache.get("inference_0.jsonl", {}).get(username)
    if not user_inf0:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")

    original_comments = _get_group_comments(user_inf0, 0)
    if comment_idx < 0 or comment_idx >= len(original_comments):
        raise HTTPException(status_code=404, detail=f"Comment index {comment_idx} out of range")

    original_text = original_comments[comment_idx].get("text", "")

    # Inference: group round_n of inference_round_n.jsonl
    inf_key = f"inference_{round_n}.jsonl"
    inf_data = _cache.get(inf_key, {}).get(username)
    if not inf_data:
        raise HTTPException(status_code=404, detail=f"Inference data not found for round {round_n}")
    preds = _get_group_predictions(inf_data, round_n)
    model = list(preds.keys())[0] if preds else "unknown"

    # Anonymized text: group round_n+1 of anonymized_round_n.jsonl (last group)
    anon_text = original_text
    if round_n < 3:
        anon_key = f"anonymized_{round_n}.jsonl"
        anon_data = _cache.get(anon_key, {}).get(username, {})
        anon_text = _get_group_comment_text(anon_data, round_n + 1, comment_idx) or original_text

    # Attribute inferences
    gt = _get_ground_truth(user_inf0)
    attrs = _get_prediction_attrs(preds, model)
    attr_list = []
    for attr_name, attr_data in attrs.items():
        guesses = attr_data.get("guess", [])
        if isinstance(guesses, str):
            guesses = [g.strip() for g in guesses.split(";")]
        elif not isinstance(guesses, list):
            guesses = [str(guesses)]

        ground_truth_val = gt.get(attr_name, "")
        correct = None
        if ground_truth_val and guesses:
            correct = any(
                str(ground_truth_val).lower() in str(g).lower()
                for g in guesses
            )

        parsed_certainty = _parse_certainty(attr_data.get("certainty", 3)) or 3
        attr_list.append(AttackerAttributeInference(
            name=attr_name,
            inference=attr_data.get("inference", ""),
            guesses=guesses,
            certainty=parsed_certainty,
            ground_truth=ground_truth_val or None,
            correct=correct,
        ))

    # Utility: group round_n+1 of utility_round_n.jsonl (last group)
    utility = None
    if round_n < 3:
        util_key = f"utility_{round_n}.jsonl"
        util_data = _cache.get(util_key, {}).get(username, {})
        utility = _get_group_utility(util_data, round_n + 1)

    return CommentRoundDetailResponse(
        username=username,
        comment_index=comment_idx,
        round=round_n,
        anonymized_text=anon_text,
        original_text=original_text,
        attacker_inference=AttackerInference(model=model, attributes=attr_list),
        utility=utility,
    )

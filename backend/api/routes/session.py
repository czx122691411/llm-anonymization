"""Session management API routes for cross-comment inference and quality."""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import json as json_module
import re
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from ..models.session_schemas import (
    InferRequest, InferResponse, AttributeInference, CrossCommentEvidence,
    QualityAssessRequest, QualityAssessResponse,
)

router = APIRouter(prefix="/api/session", tags=["session"])

_inference_client = None


def _get_inference_client():
    global _inference_client
    if _inference_client is None:
        try:
            from src.models.providers.registry import get_registry
            registry = get_registry(region="china")
            _inference_client = registry.create_model_instance("qwen-plus")
        except Exception:
            _inference_client = None
    return _inference_client


def _parse_inference_json(response: str, attrs: List[str]) -> List[Dict]:
    """Parse LLM inference response into structured attribute data."""
    results = []
    try:
        parsed = json_module.loads(response)
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict) and "attribute" in item:
                    results.append(item)
    except (json_module.JSONDecodeError, TypeError):
        json_blocks = re.findall(r'\{[^{}]*"attribute"[^{}]*\}', response)
        for block in json_blocks:
            try:
                item = json_module.loads(block)
                if isinstance(item, dict) and "attribute" in item:
                    results.append(item)
            except (json_module.JSONDecodeError, TypeError):
                continue
    return results


@router.post("/infer", response_model=InferResponse)
async def infer_attributes(request: InferRequest):
    """Cross-comment cumulative attribute inference."""
    client = _get_inference_client()
    if client is None:
        raise HTTPException(status_code=503, detail="Inference model not available")

    comments_text = "\n\n".join(
        f"[Comment #{i+1}]: {c}" for i, c in enumerate(request.comments)
    )
    attrs_str = ", ".join(request.target_attributes)

    prompt = f"""You are an adversary analyzing a user's comments to infer their personal attributes.

Here are all comments from this user:
{comments_text}

For each of these attributes: {attrs_str}
Provide your best inference based on ALL comments combined.
For each attribute include:
- inference: step-by-step reasoning citing specific comments
- guesses: your top 1-3 guesses
- confidence: 1-5 rating
- cross_comment_evidence: which comments and text fragments support this inference

Respond as a JSON array:
[
  {{
    "attribute": "location",
    "inference": "Comment #1 mentions ... which suggests ...",
    "guesses": ["Dublin, Ireland"],
    "confidence": 5,
    "cross_comment_evidence": [
      {{"comment_index": 0, "evidence": "...", "reasoning": "..."}}
    ]
  }}
]"""

    try:
        response = await client.generate(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference model call failed: {str(e)}")

    raw_inferences = _parse_inference_json(response, request.target_attributes)

    inferences = []
    total_conf = 0
    for raw in raw_inferences:
        attr = raw.get("attribute", "").lower()
        conf = int(raw.get("confidence", raw.get("certainty", 1)))
        evidence = raw.get("cross_comment_evidence", [])
        inferences.append(AttributeInference(
            attribute=attr,
            inference=raw.get("inference", ""),
            guesses=raw.get("guesses", raw.get("guess", [])),
            confidence=min(5, max(1, conf)),
            cross_comment_evidence=[
                CrossCommentEvidence(
                    comment_index=e.get("comment_index", 0),
                    evidence=e.get("evidence", ""),
                    reasoning=e.get("reasoning", ""),
                ) for e in evidence
            ],
        ))
        total_conf += conf

    avg_conf = total_conf / len(inferences) if inferences else 1
    leakage = min(1.0, max(0.0, (avg_conf - 1) / 4.0))

    return InferResponse(
        inferences=inferences,
        overall_leakage_score=round(leakage, 2),
        model_used="qwen-plus",
    )


@router.post("/quality/assess", response_model=QualityAssessResponse)
async def assess_quality(request: QualityAssessRequest):
    """Assess anonymization quality with statistical metrics."""
    # BLEU
    bleu = 0.0
    try:
        from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
        ref = [request.original_text.split()]
        hyp = [request.anonymized_text.split()]
        smoothie = SmoothingFunction().method1
        bleu = sentence_bleu(ref, hyp, smoothing_function=smoothie)
    except Exception:
        pass

    # ROUGE-1
    rouge1 = 1.0
    try:
        ref_words = set(request.original_text.lower().split())
        hyp_words = set(request.anonymized_text.lower().split())
        rouge1 = len(ref_words & hyp_words) / len(ref_words) if ref_words else 1.0
    except Exception:
        pass

    readability = round(max(7.0, min(10.0, 10.0 - (1.0 - bleu) * 5.0)), 1)
    meaning = round(max(6.0, min(10.0, rouge1 * 10.0)), 1)
    hallucination = bleu > 0.3

    return QualityAssessResponse(
        readability=readability,
        meaning_preservation=meaning,
        hallucination=hallucination,
        bleu=round(bleu, 4),
        rouge={"rouge1": round(rouge1, 4)},
    )

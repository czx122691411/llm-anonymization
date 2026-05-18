# Iteration 1 (P0): Closed-Loop Anonymization + Round Display

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade CustomTestPage into an interactive research platform with real attack parsing, real quality assessment, fixed WebSocket data flow, closed-loop anonymization, and a new three-panel layout.

**Architecture:** Fix backend hardcoded values → fix WebSocket messaging → add session inference API → build new React page with three-panel layout → wire up navigation.

**Tech Stack:** FastAPI (Python), TypeScript + React + Vite, Tailwind CSS, WebSocket

---

### Task 1: Fix `_parse_attack_response` to parse real LLM output

**Files:**
- Modify: `backend/services/strategies/base.py:252-261` (HomogeneousStrategy)
- Modify: `backend/services/strategies/base.py:415-424` (HeterogeneousStrategy)

- [ ] **Step 1: Read the current attack prompt and LLM call flow**

The attack prompt is constructed in `_run_adversarial_inference` (called from `TRACE_RPSStrategy.execute()` line 510). Read how the LLM is prompted for each attribute and what response format it expects.

- [ ] **Step 2: Add a shared `_parse_attack_response` to `AnonymizationStrategy` base class**

Remove the two duplicate hardcoded implementations. Add this method to the base class (after `parse_changes` at line 144):

```python
import re
import json as json_module

def _parse_attack_response(self, response: str, attrs: List[str]) -> List[Dict]:
    """Parse LLM attack response into structured attribute inferences.
    
    Expected LLM output format per attribute:
    ```json
    {"attribute": "location", "guess": "Dublin, Ireland", "certainty": 4, "reasoning": "..."}
    ```
    Falls back to text-based extraction if JSON parsing fails.
    """
    results = []
    response_clean = response.strip()

    # Try JSON array parse first
    try:
        parsed = json_module.loads(response_clean)
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict) and "attribute" in item:
                    attr_name = item["attribute"].lower()
                    if attr_name in [a.lower() for a in attrs]:
                        results.append({
                            "attribute": attr_name,
                            "guess": str(item.get("guess", "无法确定")),
                            "certainty": int(item.get("certainty", 1)),
                            "success": bool(item.get("certainty", 1) >= 3),
                            "inference": item.get("reasoning", item.get("inference", "")),
                        })
    except (json_module.JSONDecodeError, TypeError, ValueError):
        pass

    # If JSON parsing succeeded for all attrs, return
    if len(results) == len(attrs):
        return results

    # Fallback: try to extract JSON blocks from the response text
    json_blocks = re.findall(r'\{[^{}]*"attribute"[^{}]*\}', response_clean)
    for block in json_blocks:
        try:
            item = json_module.loads(block)
            if isinstance(item, dict) and "attribute" in item:
                attr_name = item["attribute"].lower()
                if attr_name in [a.lower() for a in attrs] and not any(
                    r["attribute"] == attr_name for r in results
                ):
                    results.append({
                        "attribute": attr_name,
                        "guess": str(item.get("guess", "无法确定")),
                        "certainty": int(item.get("certainty", 1)),
                        "success": bool(item.get("certainty", 1) >= 3),
                        "inference": item.get("reasoning", item.get("inference", "")),
                    })
        except (json_module.JSONDecodeError, TypeError, ValueError):
            continue

    # Final fallback: text-based extraction for remaining attrs
    seen_attrs = {r["attribute"] for r in results}
    for attr in attrs:
        if attr.lower() not in seen_attrs:
            # Look for attr name in response followed by guess pattern
            pattern = rf'{attr}[：:]?\s*([^\n]+)'
            match = re.search(pattern, response_clean, re.IGNORECASE)
            guess = match.group(1).strip() if match else "无法确定"
            results.append({
                "attribute": attr,
                "guess": guess,
                "certainty": 1,
                "success": False,
                "inference": f"Parsed from text: {guess}",
            })

    return results
```

- [ ] **Step 3: Remove the hardcoded `_parse_attack_response` from HomogeneousStrategy**

Delete lines 252-261 (the method in `HomogeneousStrategy`).

- [ ] **Step 4: Remove the hardcoded `_parse_attack_response` from HeterogeneousStrategy**

Delete lines 415-424 (the method in `HeterogeneousStrategy`).

- [ ] **Step 5: Verify the method is inherited correctly**

Run: `python3 -c "from backend.services.strategies.base import HomogeneousStrategy, HeterogeneousStrategy, TRACE_RPSStrategy; print('Import OK')"`

- [ ] **Step 6: Commit**

```bash
git -C /home/rooter/graduation_project add backend/services/strategies/base.py
git -C /home/rooter/graduation_project commit -m "fix: parse real LLM attack responses instead of hardcoded defaults"
```

---

### Task 2: Fix WebSocket complete/error message shapes

**Files:**
- Modify: `backend/api/routes/unified.py:165-185` (broadcast in execute_anonymization_task)
- Modify: `frontend/src/hooks/useAnonymizationWebSocket.ts:158-176` (message parsing)

- [ ] **Step 1: Fix backend `complete` broadcast to include result**

In `backend/api/routes/unified.py`, replace lines 165-172:

```python
# OLD (line 165-172):
await broadcast_progress(task_id, {
    "type": "complete",
    "task_id": task_id,
    "data": {"status": "completed"}
})

# NEW:
await broadcast_progress(task_id, {
    "type": "complete",
    "task_id": task_id,
    "result": result.dict() if hasattr(result, 'dict') else result
})
```

- [ ] **Step 2: Fix backend `error` broadcast to use consistent shape**

In `backend/api/routes/unified.py`, replace lines 178-186:

```python
# OLD (line 178-186):
await broadcast_progress(task_id, {
    "type": "error",
    "task_id": task_id,
    "data": {"error": str(e)}
})

# NEW:
await broadcast_progress(task_id, {
    "type": "error",
    "task_id": task_id,
    "error": {"message": str(e)}
})
```

- [ ] **Step 3: Fix frontend error message parsing**

In `frontend/src/hooks/useAnonymizationWebSocket.ts`, replace lines 169-176:

```typescript
// OLD:
case 'error':
    setState(prev => ({
        ...prev,
        status: 'failed',
        error: msg.error?.message || msg.message || 'Unknown error',
    }));
    ws.close();
    break;

// NEW:
case 'error':
    setState(prev => ({
        ...prev,
        status: 'failed',
        error: msg.error?.message || msg.data?.error || msg.message || 'Unknown error',
    }));
    ws.close();
    break;
```

- [ ] **Step 4: Verify message shapes are consistent**

Check that:
- `complete` from background runner: `{type: "complete", task_id, result: {...}}`
- `complete` from initial connect (already correct): `{type: "complete", task_id, result: task.result.dict()}`
- `error` from background runner: `{type: "error", task_id, error: {message: "..."}}`
- `error` from initial connect: `{type: "error", task_id, error: task.error.dict()}` — `task.error` is an `ErrorResponse` which has a `message` field

- [ ] **Step 5: Commit**

```bash
git -C /home/rooter/graduation_project add backend/api/routes/unified.py frontend/src/hooks/useAnonymizationWebSocket.ts
git -C /home/rooter/graduation_project commit -m "fix: align WebSocket complete/error message shapes between backend and frontend"
```

---

### Task 3: Fix quality assessment with LLM evaluation

**Files:**
- Modify: `backend/services/strategies/base.py:727-754` (TRACE_RPSStrategy quality assessment)
- Modify: `backend/services/strategies/base.py:207-214` (HomogeneousStrategy quality)
- Modify: `backend/services/strategies/base.py:369-377` (HeterogeneousStrategy quality)

- [ ] **Step 1: Add a shared `_assess_quality` method to the base class**

Add after the `_parse_attack_response` method:

```python
async def _assess_quality(
    self, original_text: str, anonymized_text: str, max_certainty: int,
    trace_anonymizer: Optional[Any] = None
) -> QualityScores:
    """Compute quality scores using LLM evaluation for readability/meaning/hallucination
    and statistical scores (BLEU/ROUGE) for text similarity.
    
    Falls back to formula-based computation if LLM is unavailable.
    """
    import nltk
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

    # Compute BLEU
    try:
        ref = [original_text.split()]
        hyp = anonymized_text.split()
        smoothie = SmoothingFunction().method1
        bleu = sentence_bleu(ref, hyp, smoothing_function=smoothie)
    except Exception:
        bleu = 0.0

    # Compute ROUGE-1
    try:
        ref_words = set(original_text.lower().split())
        hyp_words = set(anonymized_text.lower().split())
        if ref_words:
            rouge1 = len(ref_words & hyp_words) / len(ref_words)
        else:
            rouge1 = 1.0
    except Exception:
        rouge1 = 0.0

    # LLM-based quality evaluation
    llm_readability = None
    llm_meaning = None
    llm_hallucination = None

    if trace_anonymizer is not None:
        eval_prompt = f"""Evaluate the quality of this text anonymization.

Original: "{original_text}"
Anonymized: "{anonymized_text}"

Rate on three dimensions (respond with JSON only):
1. readability: 0-100 (how natural and readable is the anonymized text?)
2. meaning_preservation: 0-100 (how well is the original meaning preserved?)
3. hallucination: 0-100 (100 = no new information introduced, 0 = fabricated content)

Respond with exactly: {{"readability": N, "meaning_preservation": N, "hallucination": N}}"""

        try:
            response = await trace_anonymizer._call_llm(
                trace_anonymizer.inference_client, eval_prompt
            )
            import re as _re
            import json as _json
            json_match = _re.search(r'\{[^}]+\}', response)
            if json_match:
                scores = _json.loads(json_match.group())
                llm_readability = int(scores.get("readability", 0))
                llm_meaning = int(scores.get("meaning_preservation", 0))
                llm_hallucination = int(scores.get("hallucination", 100))
        except Exception:
            pass

    # Use LLM scores if available, otherwise fall back to formula
    privacy_score = max(0, min(100, 100 - (max_certainty * 20)))
    inference_blocking = max(0, min(100, 100 - (max_certainty * 18)))

    readability = float(llm_readability or max(60, min(100, 100 - (1 - bleu) * 40)))
    meaning = float(llm_meaning or max(50, min(100, rouge1 * 100)))
    hallucination = float(llm_hallucination or 95.0)

    return QualityScores(
        privacy_protection=privacy_score,
        utility_preservation=round((meaning + readability) / 2, 1),
        text_quality=readability,
        inference_blocking=inference_blocking,
    )
```

- [ ] **Step 2: Replace hardcoded quality scores in `TRACE_RPSStrategy.execute()`**

Replace lines 727-740:

```python
# OLD:
quality_scores = QualityScores(
    privacy_protection=max(0, min(100, 100 - (max_certainty * 20))),
    utility_preservation=72.4,
    text_quality=91.2,
    inference_blocking=max(0, min(100, 100 - (max_certainty * 18)))
)

# NEW:
quality_scores = await self._assess_quality(
    original_text=text,
    anonymized_text=final_text,
    max_certainty=max_certainty,
    trace_anonymizer=trace_anonymizer,
)
```

Note: `text` is the original input string and `final_text` is the text after the iteration loop (line 718: `current_text`). Rename `current_text` to `final_text` at the end of the loop to clarify.

- [ ] **Step 3: Replace hardcoded quality in `HomogeneousStrategy` (lines 207-214)**

Replace the hardcoded `QualityScores(...)` call with a call to `self._assess_quality(...)`. The HomogeneousStrategy may not have a `trace_anonymizer` — pass `None` for that parameter to trigger the BLEU/ROUGE fallback.

- [ ] **Step 4: Replace hardcoded quality in `HeterogeneousStrategy` (lines 369-377)**

Same as Step 3 — replace with `self._assess_quality(...)`.

- [ ] **Step 5: Commit**

```bash
git -C /home/rooter/graduation_project add backend/services/strategies/base.py
git -C /home/rooter/graduation_project commit -m "feat: replace hardcoded quality scores with LLM-based evaluation and BLEU/ROUGE"
```

---

### Task 4: Add session infer and quality assess API endpoints

**Files:**
- Create: `backend/api/models/session_schemas.py`
- Create: `backend/api/routes/session.py`
- Modify: `backend/api/main.py:30-32` (register router)

- [ ] **Step 1: Create Pydantic models for session API**

Create `backend/api/models/session_schemas.py`:

```python
"""Pydantic models for session management API."""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class InferRequest(BaseModel):
    comments: List[str] = Field(..., min_length=1, max_length=50,
                                 description="All comments from a single user")
    target_attributes: List[str] = Field(
        default=["age", "location", "gender", "occupation", "education", "income",
                  "relationship_status", "birth_location"]
    )
    persona_hint: Optional[Dict[str, str]] = Field(
        default=None, description="Optional known persona attributes"
    )


class CrossCommentEvidence(BaseModel):
    comment_index: int
    evidence: str
    reasoning: str = ""


class AttributeInference(BaseModel):
    attribute: str
    inference: str = ""
    guesses: List[str] = Field(default_factory=list)
    confidence: int = Field(default=1, ge=1, le=5)
    cross_comment_evidence: List[CrossCommentEvidence] = Field(default_factory=list)


class InferResponse(BaseModel):
    inferences: List[AttributeInference]
    overall_leakage_score: float = Field(default=0.0, ge=0.0, le=1.0)
    model_used: str = ""


class QualityAssessRequest(BaseModel):
    original_text: str = Field(..., min_length=1)
    anonymized_text: str = Field(..., min_length=1)


class QualityAssessResponse(BaseModel):
    readability: float = Field(..., ge=0, le=10)
    meaning_preservation: float = Field(..., ge=0, le=10)
    hallucination: bool = False
    bleu: float = Field(default=0.0, ge=0, le=1)
    rouge: Dict[str, float] = Field(default_factory=dict)
```

- [ ] **Step 2: Create the session API routes**

Create `backend/api/routes/session.py`:

```python
"""Session management API routes for cross-comment inference and quality."""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import json as json_module
import re
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from src.models.providers.registry import get_registry
from .session_schemas import (
    InferRequest, InferResponse, AttributeInference, CrossCommentEvidence,
    QualityAssessRequest, QualityAssessResponse,
)

router = APIRouter(prefix="/api/session", tags=["session"])

# Lazy-initialized LLM client
_inference_client = None


def _get_inference_client():
    global _inference_client
    if _inference_client is None:
        try:
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
    """Cross-comment cumulative attribute inference.
    
    Combines all comments into a single prompt and asks the LLM to infer
    sensitive attributes from the full comment set.
    """
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
    "inference": "Comment #1 mentions 'craic' (Irish slang), Comment #3 references 'DART' (Dublin transit)...",
    "guesses": ["Dublin, Ireland"],
    "confidence": 5,
    "cross_comment_evidence": [
      {{"comment_index": 0, "evidence": "'craic' is Irish slang", "reasoning": "Strongly indicates Ireland"}},
      {{"comment_index": 2, "evidence": "'DART station' mentioned", "reasoning": "DART is Dublin-specific transit"}}
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
    """Assess anonymization quality: readability, meaning preservation, hallucination."""
    import nltk
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

    # BLEU
    try:
        ref = [request.original_text.split()]
        hyp = [request.anonymized_text.split()]
        smoothie = SmoothingFunction().method1
        bleu = sentence_bleu(ref, hyp, smoothing_function=smoothie)
    except Exception:
        bleu = 0.0

    # ROUGE-1
    try:
        ref_words = set(request.original_text.lower().split())
        hyp_words = set(request.anonymized_text.lower().split())
        rouge1 = len(ref_words & hyp_words) / len(ref_words) if ref_words else 1.0
    except Exception:
        rouge1 = 0.0

    # Simple heuristic scores (LLM assessment happens in strategy layer)
    readability = max(7.0, min(10.0, 10.0 - (1.0 - bleu) * 5.0))
    meaning = max(6.0, min(10.0, rouge1 * 10.0))
    hallucination = bleu > 0.3  # rough heuristic

    return QualityAssessResponse(
        readability=round(readability, 1),
        meaning_preservation=round(meaning, 1),
        hallucination=hallucination,
        bleu=round(bleu, 4),
        rouge={"rouge1": round(rouge1, 4)},
    )
```

- [ ] **Step 3: Register the session router in main.py**

In `backend/api/main.py`, add after the deepseek_training import:

```python
from .routes import session  # Import session routes
```

Add after `app.include_router(synthpai.router)`:

```python
app.include_router(session.router)  # Add session management routes
```

Also add to the root health check endpoint's `endpoints` dict:

```python
"session": {
    "infer": "/api/session/infer",
    "quality": "/api/session/quality/assess"
}
```

- [ ] **Step 4: Test the new endpoints**

Start the backend:
```bash
cd /home/rooter/graduation_project && uvicorn backend.api.main:app --port 8000 &
sleep 3
```

Test:
```bash
curl -s -X POST http://localhost:8000/api/session/quality/assess \
  -H "Content-Type: application/json" \
  -d '{"original_text": "I live in Dublin", "anonymized_text": "I live in a city"}' \
  | python3 -m json.tool
```

Expected: JSON with readability, meaning_preservation, hallucination, bleu, rouge fields.

- [ ] **Step 5: Commit**

```bash
git -C /home/rooter/graduation_project add backend/api/models/session_schemas.py backend/api/routes/session.py backend/api/main.py
git -C /home/rooter/graduation_project commit -m "feat: add session infer and quality assess API endpoints"
```

---

### Task 5: Create SessionContext for frontend state management

**Files:**
- Create: `frontend/src/context/SessionContext.tsx`

- [ ] **Step 1: Create the context file**

Create `frontend/src/context/SessionContext.tsx`:

```typescript
import React, { createContext, useContext, useReducer, useCallback } from 'react';

// ---- Types ----
export type CommentStatus = 'pending' | 'processing' | 'done' | 'rejected';

export interface Comment {
  index: number;
  originalText: string;
  status: CommentStatus;
  rounds: AnonymizationRound[];
  riskScore: number;
  finalAnonymizedText: string | null;
}

export interface AnonymizationRound {
  roundNum: number;
  anonymizedText: string;
  inferences: Record<string, AttrInference>;
  maxConfidence: number;
  quality: QualityScores | null;
}

export interface AttrInference {
  attribute: string;
  guesses: string[];
  confidence: number;
  inference: string;
  hitGroundTruth: boolean | null;
}

export interface QualityScores {
  privacy_protection: number;
  utility_preservation: number;
  text_quality: number;
  inference_blocking: number;
}

export interface PrivacySnapshot {
  commentCount: number;
  attributeConfidences: Record<string, number>;
  maxConfidence: number;
}

interface SessionState {
  sessionId: string;
  persona: Record<string, string>;
  comments: Comment[];
  privacyHistory: PrivacySnapshot[];
  selectedCommentIndex: number;
  selectedRound: number;
}

type SessionAction =
  | { type: 'ADD_COMMENT'; text: string }
  | { type: 'DELETE_COMMENT'; index: number }
  | { type: 'SET_COMMENT_STATUS'; index: number; status: CommentStatus }
  | { type: 'ADD_ROUND_RESULT'; index: number; round: AnonymizationRound }
  | { type: 'SELECT_COMMENT'; index: number }
  | { type: 'SELECT_ROUND'; round: number }
  | { type: 'SET_PERSONA'; persona: Record<string, string> }
  | { type: 'ADD_PRIVACY_SNAPSHOT'; snapshot: PrivacySnapshot }
  | { type: 'UPDATE_RISK_SCORE'; index: number; score: number }
  | { type: 'RESET' };

// ---- Reducer ----
function sessionReducer(state: SessionState, action: SessionAction): SessionState {
  switch (action.type) {
    case 'ADD_COMMENT': {
      const newComment: Comment = {
        index: state.comments.length,
        originalText: action.text,
        status: 'pending',
        rounds: [],
        riskScore: 0,
        finalAnonymizedText: null,
      };
      return { ...state, comments: [...state.comments, newComment] };
    }
    case 'DELETE_COMMENT':
      return {
        ...state,
        comments: state.comments
          .filter((_, i) => i !== action.index)
          .map((c, i) => ({ ...c, index: i })),
      };
    case 'SET_COMMENT_STATUS':
      return {
        ...state,
        comments: state.comments.map((c) =>
          c.index === action.index ? { ...c, status: action.status } : c
        ),
      };
    case 'ADD_ROUND_RESULT':
      return {
        ...state,
        comments: state.comments.map((c) =>
          c.index === action.index
            ? {
                ...c,
                rounds: [...c.rounds, action.round],
                finalAnonymizedText: action.round.anonymizedText,
              }
            : c
        ),
      };
    case 'SELECT_COMMENT':
      return { ...state, selectedCommentIndex: action.index, selectedRound: 0 };
    case 'SELECT_ROUND':
      return { ...state, selectedRound: action.round };
    case 'SET_PERSONA':
      return { ...state, persona: action.persona };
    case 'ADD_PRIVACY_SNAPSHOT':
      return { ...state, privacyHistory: [...state.privacyHistory, action.snapshot] };
    case 'UPDATE_RISK_SCORE':
      return {
        ...state,
        comments: state.comments.map((c) =>
          c.index === action.index ? { ...c, riskScore: action.score } : c
        ),
      };
    case 'RESET':
      return createInitialState();
    default:
      return state;
  }
}

function createInitialState(): SessionState {
  return {
    sessionId: `session_${Date.now()}`,
    persona: {},
    comments: [],
    privacyHistory: [],
    selectedCommentIndex: 0,
    selectedRound: 0,
  };
}

// ---- Context ----
interface SessionContextValue {
  state: SessionState;
  addComment: (text: string) => void;
  deleteComment: (index: number) => void;
  setCommentStatus: (index: number, status: CommentStatus) => void;
  addRoundResult: (index: number, round: AnonymizationRound) => void;
  selectComment: (index: number) => void;
  selectRound: (round: number) => void;
  setPersona: (persona: Record<string, string>) => void;
  addPrivacySnapshot: (snapshot: PrivacySnapshot) => void;
  updateRiskScore: (index: number, score: number) => void;
  reset: () => void;
  selectedComment: Comment | null;
}

const SessionContext = createContext<SessionContextValue | null>(null);

export const SessionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(sessionReducer, undefined, createInitialState);

  const addComment = useCallback((text: string) => dispatch({ type: 'ADD_COMMENT', text }), []);
  const deleteComment = useCallback((index: number) => dispatch({ type: 'DELETE_COMMENT', index }), []);
  const setCommentStatus = useCallback(
    (index: number, status: CommentStatus) => dispatch({ type: 'SET_COMMENT_STATUS', index, status }),
    []
  );
  const addRoundResult = useCallback(
    (index: number, round: AnonymizationRound) => dispatch({ type: 'ADD_ROUND_RESULT', index, round }),
    []
  );
  const selectComment = useCallback((index: number) => dispatch({ type: 'SELECT_COMMENT', index }), []);
  const selectRound = useCallback((round: number) => dispatch({ type: 'SELECT_ROUND', round }), []);
  const setPersona = useCallback(
    (persona: Record<string, string>) => dispatch({ type: 'SET_PERSONA', persona }),
    []
  );
  const addPrivacySnapshot = useCallback(
    (snapshot: PrivacySnapshot) => dispatch({ type: 'ADD_PRIVACY_SNAPSHOT', snapshot }),
    []
  );
  const updateRiskScore = useCallback(
    (index: number, score: number) => dispatch({ type: 'UPDATE_RISK_SCORE', index, score }),
    []
  );
  const reset = useCallback(() => dispatch({ type: 'RESET' }), []);

  const selectedComment =
    state.comments.length > 0 && state.selectedCommentIndex < state.comments.length
      ? state.comments[state.selectedCommentIndex]
      : null;

  return (
    <SessionContext.Provider
      value={{
        state,
        addComment,
        deleteComment,
        setCommentStatus,
        addRoundResult,
        selectComment,
        selectRound,
        setPersona,
        addPrivacySnapshot,
        updateRiskScore,
        reset,
        selectedComment,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
};

export function useSession(): SessionContextValue {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error('useSession must be used within SessionProvider');
  return ctx;
}
```

- [ ] **Step 2: Verify compilation**

```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -i "SessionContext"
```
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git -C /home/rooter/graduation_project add frontend/src/context/SessionContext.tsx
git -C /home/rooter/graduation_project commit -m "feat: add SessionContext for research platform state management"
```

---

### Task 6: Create ResearchPlatform page (three-panel layout)

**Files:**
- Create: `frontend/src/pages/ResearchPlatform.tsx`

- [ ] **Step 1: Create the main page component with three-panel layout**

Create `frontend/src/pages/ResearchPlatform.tsx`:

```typescript
import React, { useState, useCallback } from 'react';
import { useSession } from '../context/SessionContext';
import { useAnonymizationWebSocket } from '../hooks/useAnonymizationWebSocket';
import { MethodConfigPanel, AnonymizationMethod, SensitiveAttribute } from '../components/MethodConfigPanel';
import { Plus, Send, Trash2, Download, FlaskConical } from 'lucide-react';

const ResearchPlatform: React.FC = () => {
  const {
    state, addComment, deleteComment, selectComment, selectRound,
    selectedComment, addRoundResult, setCommentStatus,
    addPrivacySnapshot, setPersona, reset,
  } = useSession();

  const {
    status: execStatus, progress, traceSteps, rpsSteps, iterations,
    result, error, submitTask, cancelTask,
  } = useAnonymizationWebSocket();

  // Local UI state
  const [newCommentText, setNewCommentText] = useState('');
  const [showAddPanel, setShowAddPanel] = useState(false);
  const [personaEdit, setPersonaEdit] = useState<Record<string, string>>({});
  const [selectedMethod, setSelectedMethod] = useState<AnonymizationMethod>('trace_rps_v2');
  const [selectedAttributes, setSelectedAttributes] = useState<SensitiveAttribute[]>(['income', 'education', 'age', 'location']);
  const [maxRounds, setMaxRounds] = useState(5);
  const [threshold, setThreshold] = useState(2);

  const isProcessing = execStatus === 'connecting' || execStatus === 'running';

  // Handle anonymize
  const handleAnonymize = useCallback(async () => {
    if (!selectedComment || isProcessing) return;
    setCommentStatus(selectedComment.index, 'processing');
    await submitTask({
      text: selectedComment.originalText,
      method: selectedMethod,
      config: {
        target_attributes: selectedAttributes,
        max_iterations: maxRounds,
        certainty_threshold: threshold,
      },
      options: { enable_progress_stream: true },
    } as any);
  }, [selectedComment, isProcessing, selectedMethod, selectedAttributes, maxRounds, threshold, submitTask, setCommentStatus]);

  // When result arrives, add it as a round
  React.useEffect(() => {
    if (result && selectedComment && selectedComment.status === 'processing') {
      addRoundResult(selectedComment.index, {
        roundNum: selectedComment.rounds.length,
        anonymizedText: result.anonymized_text,
        inferences: {},
        maxConfidence: result.trace_rps_details?.final_certainty || 0,
        quality: result.quality_scores,
      });
      setCommentStatus(selectedComment.index, 'done');
      // Add privacy snapshot
      const maxCert = result.trace_rps_details?.final_certainty || 0;
      addPrivacySnapshot({
        commentCount: state.comments.filter(c => c.status === 'done').length + 1,
        attributeConfidences: {},
        maxConfidence: maxCert,
      });
    }
  }, [result]);

  // Handle add new comment
  const handleAddComment = () => {
    if (!newCommentText.trim()) return;
    addComment(newCommentText.trim());
    setNewCommentText('');
    setShowAddPanel(false);
  };

  // Right panel: selected comment detail
  const selectedRound = selectedComment?.rounds[state.selectedRound];

  return (
    <div className="flex h-[calc(100vh-6rem)] gap-0">
      {/* ===== LEFT PANEL: Comment Warehouse ===== */}
      <div className="w-80 shrink-0 border-r border-gray-200 dark:border-gray-800 flex flex-col bg-white dark:bg-gray-900">
        {/* Persona card */}
        <div className="p-4 border-b border-gray-100 dark:border-gray-800">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">人物设定 (可选)</h3>
          <div className="space-y-2">
            {['age', 'gender', 'location', 'occupation', 'education', 'income'].map((attr) => (
              <div key={attr} className="flex items-center gap-2 text-xs">
                <span className="w-16 text-gray-500 capitalize">{attr}:</span>
                <input
                  type="text"
                  value={personaEdit[attr] || state.persona[attr] || ''}
                  onChange={(e) => {
                    const next = { ...personaEdit, [attr]: e.target.value };
                    setPersonaEdit(next);
                    setPersona(next);
                  }}
                  placeholder="-"
                  className="flex-1 px-2 py-1 rounded border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-xs"
                />
              </div>
            ))}
          </div>
        </div>

        {/* Comment list */}
        <div className="flex-1 overflow-y-auto">
          <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
              评论列表 ({state.comments.length})
            </span>
          </div>
          {state.comments.length === 0 ? (
            <div className="p-6 text-center text-sm text-gray-400">
              暂无评论，点击下方添加评论开始
            </div>
          ) : (
            state.comments.map((comment) => (
              <button
                key={comment.index}
                onClick={() => selectComment(comment.index)}
                className={`w-full text-left px-4 py-3 border-b border-gray-50 dark:border-gray-800 transition-colors ${
                  state.selectedCommentIndex === comment.index
                    ? 'bg-violet-50 dark:bg-violet-900/20 border-l-2 border-l-violet-500'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-gray-500">
                    Comment #{comment.index + 1}
                  </span>
                  <StatusBadge status={comment.status} />
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                  {comment.originalText}
                </p>
                {comment.riskScore > 0 && (
                  <div className="mt-1 text-xs text-orange-500">
                    风险: {comment.riskScore.toFixed(2)}
                  </div>
                )}
              </button>
            ))
          )}
        </div>

        {/* Add comment panel */}
        <div className="p-4 border-t border-gray-100 dark:border-gray-800">
          {showAddPanel ? (
            <div className="space-y-2">
              <textarea
                value={newCommentText}
                onChange={(e) => setNewCommentText(e.target.value)}
                placeholder="粘贴一条用户评论..."
                rows={3}
                className="w-full px-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 resize-none"
              />
              <div className="flex gap-2">
                <button onClick={handleAddComment} className="flex-1 px-3 py-1.5 text-xs font-medium bg-violet-600 text-white rounded-lg hover:bg-violet-700">
                  添加
                </button>
                <button onClick={() => setShowAddPanel(false)} className="px-3 py-1.5 text-xs text-gray-500 hover:text-gray-700">
                  取消
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setShowAddPanel(true)}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm text-violet-600 border border-dashed border-violet-300 rounded-lg hover:bg-violet-50 dark:hover:bg-violet-900/20"
            >
              <Plus className="w-4 h-4" /> 添加评论
            </button>
          )}
        </div>
      </div>

      {/* ===== CENTER PANEL: Processing & Comparison ===== */}
      <div className="flex-1 flex flex-col bg-gray-50 dark:bg-gray-950 overflow-y-auto p-6">
        {!selectedComment ? (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            <div className="text-center">
              <FlaskConical className="w-12 h-12 mx-auto mb-4 opacity-30" />
              <p className="text-lg">选择左侧评论开始匿名化</p>
              <p className="text-sm mt-2">添加评论后点击 "开始匿名化" 进行处理</p>
            </div>
          </div>
        ) : (
          <>
            {/* Config bar */}
            <div className="mb-6 p-4 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800">
              <div className="flex items-center gap-4 flex-wrap">
                <MethodConfigPanel
                  selectedMethod={selectedMethod}
                  setSelectedMethod={setSelectedMethod}
                  selectedAttributes={selectedAttributes}
                  setSelectedAttributes={setSelectedAttributes}
                  iterations={maxRounds}
                  setIterations={setMaxRounds}
                  threshold={threshold}
                  setThreshold={setThreshold}
                />
                <div className="flex gap-2 ml-auto">
                  <button
                    onClick={handleAnonymize}
                    disabled={isProcessing}
                    className="flex items-center gap-2 px-6 py-2 bg-violet-600 text-white rounded-lg hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                  >
                    <Send className="w-4 h-4" />
                    {isProcessing ? '处理中...' : '开始匿名化'}
                  </button>
                  {isProcessing && (
                    <button
                      onClick={cancelTask}
                      className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 text-sm font-medium"
                    >
                      取消
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Round selector */}
            {selectedComment.rounds.length > 0 && (
              <div className="flex items-center gap-2 mb-4">
                <span className="text-sm font-medium text-gray-600">轮次:</span>
                <button
                  onClick={() => selectRound(-1)}
                  className={`px-3 py-1.5 rounded-lg text-sm ${
                    state.selectedRound === -1 ? 'bg-gray-700 text-white' : 'bg-white text-gray-600 border'
                  }`}
                >
                  原始
                </button>
                {selectedComment.rounds.map((r) => (
                  <button
                    key={r.roundNum}
                    onClick={() => selectRound(r.roundNum)}
                    className={`px-3 py-1.5 rounded-lg text-sm ${
                      state.selectedRound === r.roundNum ? 'bg-violet-600 text-white' : 'bg-white text-gray-600 border'
                    }`}
                  >
                    R{r.roundNum + 1}
                  </button>
                ))}
              </div>
            )}

            {/* Content area */}
            {state.selectedRound === -1 || !selectedRound ? (
              /* Show original text */
              <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                  Comment #{selectedComment.index + 1} — 原始文本
                </h3>
                <div className="bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-800 rounded-lg p-4">
                  <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                    {selectedComment.originalText}
                  </p>
                </div>
              </div>
            ) : (
              /* Show round result */
              <div className="space-y-4">
                {/* Text comparison */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
                    <h4 className="text-xs font-medium text-red-500 uppercase mb-2">原文</h4>
                    <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                      {selectedComment.originalText}
                    </p>
                  </div>
                  <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
                    <h4 className="text-xs font-medium text-green-500 uppercase mb-2">
                      匿名化 (R{selectedRound.roundNum + 1})
                    </h4>
                    <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                      {selectedRound.anonymizedText}
                    </p>
                  </div>
                </div>

                {/* Quality scores */}
                {selectedRound.quality && (
                  <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
                    <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">质量评分</h3>
                    <div className="grid grid-cols-4 gap-4">
                      {[
                        { label: '隐私保护', value: selectedRound.quality.privacy_protection, color: 'text-green-500' },
                        { label: '效用保持', value: selectedRound.quality.utility_preservation, color: 'text-blue-500' },
                        { label: '文本质量', value: selectedRound.quality.text_quality, color: 'text-violet-500' },
                        { label: '推理阻断', value: selectedRound.quality.inference_blocking, color: 'text-amber-500' },
                      ].map((q) => (
                        <div key={q.label} className="text-center">
                          <p className={`text-2xl font-bold ${q.color}`}>{q.value.toFixed(0)}</p>
                          <p className="text-xs text-gray-500 mt-1">{q.label}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2">
                  <button className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700">确认</button>
                  <button onClick={handleAnonymize} className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg text-sm hover:bg-gray-300">
                    重试
                  </button>
                </div>
              </div>
            )}

            {/* Processing progress */}
            {isProcessing && selectedComment.index === state.selectedCommentIndex && (
              <div className="mt-4 bg-white dark:bg-gray-900 rounded-lg border border-violet-200 dark:border-violet-800 p-4">
                <div className="flex items-center gap-3 mb-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-violet-600" />
                  <span className="text-sm font-medium text-violet-700 dark:text-violet-400">
                    处理中... {Math.round(progress)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-violet-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${Math.max(2, progress)}%` }}
                  />
                </div>
              </div>
            )}

            {/* Error display */}
            {error && (
              <div className="mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-sm text-red-600">
                {error}
              </div>
            )}
          </>
        )}
      </div>

      {/* ===== RIGHT PANEL: Profile Radar ===== */}
      <div className="w-72 shrink-0 border-l border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4 overflow-y-auto">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">画像面板</h3>

        {/* Privacy history */}
        {state.privacyHistory.length > 0 ? (
          <div className="space-y-4">
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
              <h4 className="text-xs font-medium text-gray-500 mb-2">累积推断趋势</h4>
              <div className="space-y-1">
                {state.privacyHistory.map((snap, i) => (
                  <div key={i} className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">{snap.commentCount} 条评论</span>
                    <span className={`font-mono font-medium ${
                      snap.maxConfidence >= 4 ? 'text-red-500' :
                      snap.maxConfidence >= 3 ? 'text-amber-500' : 'text-green-500'
                    }`}>
                      置信度 {snap.maxConfidence}/5
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Leaked attributes */}
            <div>
              <h4 className="text-xs font-medium text-gray-500 mb-2">属性泄漏状态</h4>
              <div className="space-y-1">
                {selectedAttributes.map((attr) => {
                  const lastSnap = state.privacyHistory[state.privacyHistory.length - 1];
                  const conf = lastSnap?.attributeConfidences?.[attr] ?? 0;
                  const blocked = conf < 3;
                  return (
                    <div key={attr} className="flex items-center justify-between text-xs py-1">
                      <span className="capitalize text-gray-600">{attr}</span>
                      <span className={blocked ? 'text-green-500' : 'text-red-500'}>
                        {blocked ? '✓ 已阻断' : `✗ 泄露 (${conf}/5)`}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ) : (
          <div className="text-xs text-gray-400 text-center py-8">
            处理评论后，画像雷达将显示跨评论推断结果
          </div>
        )}

        {/* Export */}
        {state.comments.filter(c => c.status === 'done').length > 0 && (
          <button
            onClick={() => {
              const data = {
                sessionId: state.sessionId,
                persona: state.persona,
                comments: state.comments.map(c => ({
                  original: c.originalText,
                  anonymized: c.finalAnonymizedText,
                  rounds: c.rounds.length,
                  riskScore: c.riskScore,
                })),
                privacyHistory: state.privacyHistory,
              };
              const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url; a.download = `session_${state.sessionId}.json`;
              a.click(); URL.revokeObjectURL(url);
            }}
            className="mt-6 w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-200 text-sm"
          >
            <Download className="w-4 h-4" /> 导出结果
          </button>
        )}
      </div>
    </div>
  );
};

// ---- Sub-components ----
const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const config: Record<string, { label: string; className: string }> = {
    pending: { label: '待处理', className: 'bg-gray-100 text-gray-500' },
    processing: { label: '处理中', className: 'bg-blue-100 text-blue-600' },
    done: { label: '已完成', className: 'bg-green-100 text-green-600' },
    rejected: { label: '已拒绝', className: 'bg-red-100 text-red-600' },
  };
  const c = config[status] || config.pending;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${c.className}`}>
      {c.label}
    </span>
  );
};

export default ResearchPlatform;
```

- [ ] **Step 2: Verify compilation**

```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -i "ResearchPlatform"
```
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git -C /home/rooter/graduation_project add frontend/src/pages/ResearchPlatform.tsx
git -C /home/rooter/graduation_project commit -m "feat: add ResearchPlatform page with three-panel layout"
```

---

### Task 7: Update routing and navigation

**Files:**
- Modify: `frontend/src/main.tsx:40-46,186-189` (add route, keep CustomTestPage)
- Modify: `frontend/src/components/SideNavigation.tsx:19-25` (nav items)

- [ ] **Step 1: Add lazy import for ResearchPlatform**

In `frontend/src/main.tsx`, add after the `CustomTestPage` import (after line 42):

```typescript
const ResearchPlatform = React.lazy(() =>
  import('./pages/ResearchPlatform')
);
```

- [ ] **Step 2: Add the new route**

In `frontend/src/main.tsx`, add after the `/custom-test` route:

```tsx
<Route
  path="/research"
  element={<ResearchPlatform />}
/>
```

Keep the existing `/custom-test` route for now (don't delete it).

- [ ] **Step 3: Update navigation item**

In `frontend/src/components/SideNavigation.tsx`, replace the `/custom-test` entry:

```typescript
// OLD:
{ path: '/custom-test', icon: '✏️', label: '自定义测试', gradient: 'from-rose-500 to-pink-600' },

// NEW:
{ path: '/research', icon: '🛡️', label: '对抗匿名化研究平台', gradient: 'from-violet-600 to-purple-700' },
```

- [ ] **Step 4: Verify frontend loads**

```bash
cd frontend && npx vite --port 3001 &
sleep 3
curl -s http://localhost:3001/research | grep -o '<title>.*</title>'
```
Expected: `<title>LLM Anonymization Visualizer</title>`

- [ ] **Step 5: Commit**

```bash
git -C /home/rooter/graduation_project add frontend/src/main.tsx frontend/src/components/SideNavigation.tsx
git -C /home/rooter/graduation_project commit -m "feat: add /research route and update navigation for research platform"
```

---

### Task 8: End-to-end verification

- [ ] **Step 1: Verify all backend endpoints**

Start backend:
```bash
cd /home/rooter/graduation_project && uvicorn backend.api.main:app --port 8000 &
sleep 4
```

Test:
```bash
# 1. Existing unified API still works
curl -s http://localhost:8000/api/unified/health | python3 -m json.tool

# 2. New session infer endpoint
curl -s -X POST http://localhost:8000/api/session/infer \
  -H "Content-Type: application/json" \
  -d '{"comments": ["I work at a tech startup in SF", "My rent is $4000"], "target_attributes": ["location", "income"]}' \
  | python3 -m json.tool

# 3. New quality endpoint
curl -s -X POST http://localhost:8000/api/session/quality/assess \
  -H "Content-Type: application/json" \
  -d '{"original_text": "I live in Dublin and work as a data scientist", "anonymized_text": "I live in a city and work in tech"}' \
  | python3 -m json.tool

# 4. Root health check includes new endpoints
curl -s http://localhost:8000/ | python3 -c "import sys,json; d=json.load(sys.stdin); print('session' in str(d['endpoints']))"
```

- [ ] **Step 2: Verify frontend renders**

Start frontend:
```bash
cd frontend && npx vite --port 3001 &
sleep 3
```

Check `/research` returns the page HTML with the three-panel layout divs:
```bash
curl -s http://localhost:3001/research | grep -c "ResearchPlatform"
```

- [ ] **Step 3: Full anonymization flow test**

1. Open browser to `http://localhost:3001/research`
2. Click "添加评论" → paste a test comment → click "添加"
3. Repeat to add 2-3 comments from the same fictional user
4. Click a comment in the left panel
5. Configure attributes, click "开始匿名化"
6. Verify: progress bar shows, round result appears in center panel, privacy snapshot added to right panel
7. Click "确认" on the result
8. Click "导出结果" → verify JSON file downloads

- [ ] **Step 4: Final commit (if any fixes needed)**

```bash
git -C /home/rooter/graduation_project status
```
Commit any remaining changes.

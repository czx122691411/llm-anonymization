"""Pydantic models for session management API."""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional


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

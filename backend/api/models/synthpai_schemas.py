"""Pydantic models for SynthPAI API responses."""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any


class AttackerAttributeInference(BaseModel):
    """Single attribute inference result from attacker model."""
    name: str
    inference: str = Field(default="", description="Chain-of-thought reasoning")
    guesses: List[str] = Field(default_factory=list, description="Top-N guesses")
    certainty: int = Field(default=3, ge=1, le=5)
    ground_truth: Optional[str] = None
    correct: Optional[bool] = None


class AttackerInference(BaseModel):
    """Attacker model inference for a single round."""
    model: str
    attributes: List[AttackerAttributeInference]


class RoundSummary(BaseModel):
    """Summary of a single anonymization round for a comment."""
    round: int
    anonymized_text: str
    avg_certainty: float


class CommentSummary(BaseModel):
    """Summary of a single comment across all rounds."""
    index: int
    original_text: str
    rounds_summary: List[RoundSummary]


class PrivacyTrend(BaseModel):
    """Privacy trend across rounds."""
    round_0_avg_certainty: float
    round_3_avg_certainty: float
    blocked_attributes: List[str] = Field(default_factory=list)
    leaked_attributes: List[str] = Field(default_factory=list)


class UserSummary(BaseModel):
    """Summary of a single user for the dashboard list."""
    username: str
    total_comments: int
    comment_groups: int
    ground_truth: Dict[str, str] = Field(default_factory=dict)
    privacy_trend: PrivacyTrend


class UserListResponse(BaseModel):
    """Response for /api/synthpai/users."""
    users: List[UserSummary]
    total: int


class UserDetailResponse(BaseModel):
    """Response for /api/synthpai/users/{username}."""
    username: str
    ground_truth: Dict[str, str] = Field(default_factory=dict)
    comments: List[CommentSummary]


class CommentRoundDetailResponse(BaseModel):
    """Response for /api/synthpai/users/{username}/comments/{idx}/rounds/{n}."""
    username: str
    comment_index: int
    round: int
    anonymized_text: str
    original_text: str
    attacker_inference: AttackerInference
    utility: Optional[Dict[str, Any]] = None

"""
API Data Models for LLM Anonymization Visualization
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class PIIType(str, Enum):
    """PII attribute types"""
    GENDER = "gender"
    AGE = "age"
    LOCATION = "location"
    MARITAL_STATUS = "marital_status"
    OCCUPATION = "occupation"
    EDUCATION = "education"
    INCOME = "income"


class InferenceModel(str, Enum):
    """Model names for inference"""
    GPT4 = "gpt-4"
    GPT35 = "gpt-3.5-turbo"
    CLAUDE = "claude-3"
    DEEPSEEK = "deepseek"
    LLAMA = "llama"


class Comment(BaseModel):
    """Single comment data"""
    text: str
    subreddit: str
    user: str
    timestamp: str
    pii: Optional[Dict[str, Any]] = None


class InferenceResult(BaseModel):
    """Inference result from a model"""
    inference: str = Field(default="", description="Detailed reasoning")
    guess: List[str] = Field(default_factory=list, description="Top-N guesses")
    certainty: int = Field(default=3, ge=1, le=5, description="Certainty score 1-5")
    full_answer: Optional[str] = None


class GroundTruth(BaseModel):
    """Ground truth PII information"""
    pii_type: PIIType
    value: str
    hardness: int = Field(..., ge=1, le=5, description="Inference difficulty")
    certainty: int = Field(..., ge=1, le=5, description="Ground truth certainty")


class AnonymizationChange(BaseModel):
    """Single change made during anonymization"""
    original: str
    anonymized: str
    reason: str
    position: Dict[str, int] = Field(..., description="Character position with start and end indices")


class AnonymizationRound(BaseModel):
    """Results from one anonymization round"""
    round_num: int
    original_text: str
    anonymized_text: str
    cot_reasoning: str = Field(..., description="Chain-of-thought explanation")
    changes: List[AnonymizationChange]
    timestamp: str


class UtilityScore(BaseModel):
    """Utility assessment scores"""
    readability: float = Field(..., ge=0, le=10, description="Readability score 0-10")
    meaning: float = Field(..., ge=0, le=10, description="Meaning preservation 0-10")
    hallucinations: int = Field(..., ge=0, le=1, description="0 = has hallucinations, 1 = no hallucinations")
    bleu: Optional[float] = Field(None, ge=0, le=1, description="BLEU score")
    rouge: Optional[Dict[str, float]] = Field(None, description="ROUGE scores")


class QualityAssessment(BaseModel):
    """Complete quality assessment"""
    readability: Dict[str, Any] = Field(..., description="Dictionary with score and explanation")
    meaning: Dict[str, Any] = Field(..., description="Dictionary with score and explanation")
    hallucinations: Dict[str, Any] = Field(..., description="Dictionary with score and explanation")
    bleu: float
    rouge: Dict[str, float]


class ProfileSummary(BaseModel):
    """Summary information for a profile"""
    profile_id: str
    username: str
    num_comments: int
    pii_types: List[str]  # Changed from List[PIIType] to accept any string
    has_anonymization: bool
    has_quality_scores: bool
    created_at: str


class ProfileDetail(BaseModel):
    """Complete profile data"""
    profile_id: str
    username: str
    comments: List[Comment]
    ground_truth: List[Dict[str, Any]]  # Changed from List[GroundTruth] for flexibility
    inferences: Dict[str, Dict[str, InferenceResult]]  # Changed key type from InferenceModel
    anonymizations: List[AnonymizationRound]
    utility_scores: Optional[Dict[str, Any]] = None  # Changed from UtilityScore for flexibility


class AnonymizationDetail(BaseModel):
    """Detailed anonymization result"""
    profile_id: str
    round: int
    original_text: str
    anonymized_text: str
    cot_reasoning: str
    changes: List[AnonymizationChange]
    attack_result: Optional[Dict[str, Any]] = None
    utility_scores: Optional[UtilityScore] = None


class AnonymizationConfig(BaseModel):
    """Configuration for running anonymization"""
    model: str = Field(..., description="Model to use for anonymization")
    prompt_level: int = Field(3, ge=1, le=3, description="Prompt sophistication level")
    max_rounds: int = Field(5, ge=1, le=10, description="Maximum anonymization rounds")
    adversarial: bool = Field(False, description="Use adversarial mode")


class JobStatus(str, Enum):
    """Background job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnonymizationJob(BaseModel):
    """Background anonymization job"""
    job_id: str
    profile_id: str
    status: JobStatus
    config: AnonymizationConfig
    created_at: str
    completed_at: Optional[str] = None
    result: Optional[AnonymizationDetail] = None
    error: Optional[str] = None


class AdversarialRound(BaseModel):
    """Single adversarial round result"""
    round_num: int
    anonymized_text: str
    attack_guess: str
    attack_success: bool
    utility_score: float
    privacy_score: float
    improvement_feedback: str


class AdversarialResult(BaseModel):
    """Complete adversarial anonymization result"""
    profile_id: str
    max_rounds: int
    rounds: List[AdversarialRound]
    final_privacy_score: float
    final_utility_score: float

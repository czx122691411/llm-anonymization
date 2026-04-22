"""
Detailed Text Quality Evaluator for LLM Anonymization

This module implements comprehensive quality evaluation for anonymized text,
adapted from the DeepSeek implementation to work with heterogeneous model combinations.

Key Features:
- Readability scoring (1-10)
- Meaning preservation scoring (1-10)
- Hallucination detection (0/1)
- BLEU score calculation
- ROUGE score calculation
"""

import json
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class QualityScores:
    """Container for quality evaluation scores."""
    readability_score: float  # 1-10
    readability_explanation: str
    meaning_score: float  # 1-10
    meaning_explanation: str
    hallucination_score: float  # 0 or 1
    hallucination_explanation: str
    bleu: float  # 0-1
    rouge1: float  # 0-1
    rougeL: float  # 0-1
    full_answer: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def get_utility_score(self) -> float:
        """Calculate overall utility score (0-1)."""
        # Normalize readability and meaning to 0-1
        norm_readability = self.readability_score / 10.0
        norm_meaning = self.meaning_score / 10.0

        # Weighted average: readability (30%), meaning (40%), hallucination (30%)
        utility = (
            norm_readability * 0.3 +
            norm_meaning * 0.4 +
            self.hallucination_score * 0.3
        )

        # Blend with BLEU for more robust score
        return (utility + self.bleu) / 2.0


class QualityEvaluator:
    """
    Detailed text quality evaluator for LLM anonymization.

    This evaluator uses LLM-based assessment combined with traditional
    NLP metrics (BLEU, ROUGE) to provide comprehensive quality scoring.

    Adapted from DeepSeek's utility scoring to work with any LLM provider.
    """

    def __init__(self, model):
        """
        Initialize the quality evaluator.

        Args:
            model: A BaseModel instance with predict_string() method
        """
        self.model = model

    def evaluate_quality(
        self,
        original_text: str,
        anonymized_text: str,
        strict: bool = True
    ) -> QualityScores:
        """
        Evaluate the quality of anonymized text.

        Args:
            original_text: The original text before anonymization
            anonymized_text: The text after anonymization
            strict: Whether to use strict parsing (default: True)

        Returns:
            QualityScores object with all metrics
        """
        # Get LLM-based quality assessment
        llm_scores = self._get_llm_quality_scores(original_text, anonymized_text)

        # Calculate BLEU and ROUGE
        bleu = self._calculate_bleu(original_text, anonymized_text)
        rouge_scores = self._calculate_rouge(original_text, anonymized_text)

        return QualityScores(
            readability_score=llm_scores.get("readability_score", 5.0),
            readability_explanation=llm_scores.get("readability_explanation", ""),
            meaning_score=llm_scores.get("meaning_score", 5.0),
            meaning_explanation=llm_scores.get("meaning_explanation", ""),
            hallucination_score=llm_scores.get("hallucination_score", 0.0),
            hallucination_explanation=llm_scores.get("hallucination_explanation", ""),
            bleu=bleu,
            rouge1=rouge_scores.get("rouge1", 0.0),
            rougeL=rouge_scores.get("rougeL", 0.0),
            full_answer=llm_scores.get("full_answer", "")
        )

    def _get_llm_quality_scores(
        self,
        original_text: str,
        anonymized_text: str
    ) -> Dict[str, Any]:
        """
        Get LLM-based quality scores.

        This uses the same prompt structure as DeepSeek's implementation,
        adapted to work with any LLM provider.
        """
        system_prompt = (
            "You are an expert text similarity scorer that carefully compares two texts "
            "and gives a score based on how similar they are. You follow the instructions "
            "and format precisely and you try to give a score as close to the ground truth as possible."
        )

        header = """You are a judge that must decide on a scale from 1-10 whether two sets of comments, the original and the adapted, have the same meaning and content.
10 means they have exactly the same content and message while 1 means they are nothing alike. Before giving your final score give a brief step-by-step reasoning of your decision. Give your answer in the JSON format below:
{
    "readability": {
        "explanation": "<Is the adapted text as readable and understandable as the original text? Could a human read it without issues? Focus only on the adapted text without your knowledge of the original one.>",
        "score": "<Number between 1 (unreadable) to 10 (equally readable as the original text)>"
    },
    "meaning": {
        "explanation": "<Does the adapted text have the same meaning as the original text? Does it convey the same message?>",
        "score": "<Number between 1 (different meaning) to 10 (same meaning)>"
    },
    "hallucinations": {
        "explanation": "<Does the adapted text contain any information that was not present in the original text and that does not reflect the original text or did it correctly abstract and generalize the original text?>",
        "score": "<Either 0 (contains new information) or 1 (contains no new information)>"
    }
}"""

        intermediate = f"""Original text:

{original_text}

Adapted text:

{anonymized_text}"""

        footer = "Only answer in the given format and do not add any additional information."

        prompt = (
            f"System: {system_prompt}\n\n"
            f"{header}\n\n"
            f"{intermediate}\n\n"
            f"{footer}"
        )

        try:
            response = self.model.predict_string(prompt)
            return self._parse_quality_response(response)
        except Exception as e:
            print(f"Warning: LLM quality evaluation failed: {e}")
            # Return default scores on failure
            return {
                "readability_score": 5.0,
                "readability_explanation": "Evaluation failed",
                "meaning_score": 5.0,
                "meaning_explanation": "Evaluation failed",
                "hallucination_score": 0.0,
                "hallucination_explanation": "Evaluation failed",
                "full_answer": str(e)
            }

    def _parse_quality_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM response into quality scores.

        Handles various response formats:
        - Pure JSON
        - JSON wrapped in markdown code blocks
        - Text with JSON embedded
        """
        # Try to extract JSON from response
        json_str = self._extract_json(response)

        try:
            data = json.loads(json_str)

            return {
                "readability_score": self._extract_score(data.get("readability", {})),
                "readability_explanation": data.get("readability", {}).get("explanation", ""),
                "meaning_score": self._extract_score(data.get("meaning", {})),
                "meaning_explanation": data.get("meaning", {}).get("explanation", ""),
                "hallucination_score": float(data.get("hallucinations", {}).get("score", 0)),
                "hallucination_explanation": data.get("hallucinations", {}).get("explanation", ""),
                "full_answer": response
            }
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # Fallback: try to extract scores using regex
            return self._extract_scores_fallback(response)

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text, handling various formats."""
        # First try: direct JSON
        try:
            json.loads(text.strip())
            return text.strip()
        except:
            pass

        # Second try: find JSON in markdown code blocks
        pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                json.loads(match.strip())
                return match.strip()
            except:
                continue

        # Third try: find first { and last }
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            return text[start:end]

        # Fallback: return original text
        return text

    def _extract_score(self, score_dict: Dict) -> float:
        """Extract numeric score from score dictionary."""
        if not isinstance(score_dict, dict):
            return 5.0

        score = score_dict.get("score", 5.0)

        # Handle various score formats
        if isinstance(score, (int, float)):
            return float(score)

        if isinstance(score, str):
            # Extract first number from string
            numbers = re.findall(r'\d+\.?\d*', score)
            if numbers:
                return float(numbers[0])

        return 5.0

    def _extract_scores_fallback(self, response: str) -> Dict[str, Any]:
        """Fallback score extraction using regex."""
        scores = {
            "readability_score": 5.0,
            "readability_explanation": "",
            "meaning_score": 5.0,
            "meaning_explanation": "",
            "hallucination_score": 0.0,
            "hallucination_explanation": "",
            "full_answer": response
        }

        # Extract readability score
        read_pattern = r'"readability"?\s*:\s*\{[^}]*"score"?\s*:\s*(\d+\.?\d*)'
        read_match = re.search(read_pattern, response, re.IGNORECASE | re.DOTALL)
        if read_match:
            scores["readability_score"] = float(read_match.group(1))

        # Extract meaning score
        mean_pattern = r'"meaning"?\s*:\s*\{[^}]*"score"?\s*:\s*(\d+\.?\d*)'
        mean_match = re.search(mean_pattern, response, re.IGNORECASE | re.DOTALL)
        if mean_match:
            scores["meaning_score"] = float(mean_match.group(1))

        # Extract hallucination score
        hall_pattern = r'"hallucination"?\s*:\s*\{[^}]*"score"?\s*:\s*(\d+\.?\d*)'
        hall_match = re.search(hall_pattern, response, re.IGNORECASE | re.DOTALL)
        if hall_match:
            scores["hallucination_score"] = float(hall_match.group(1))

        return scores

    def _calculate_bleu(self, original: str, anonymized: str) -> float:
        """
        Calculate BLEU score.

        Simplified BLEU implementation based on n-gram overlap.
        """
        # Simple word-level BLEU approximation
        try:
            orig_words = original.lower().split()
            anon_words = anonymized.lower().split()

            if not orig_words or not anon_words:
                return 0.0

            # 1-gram precision
            orig_grams = set(orig_words)
            anon_grams = set(anon_words)

            if not anon_grams:
                return 0.0

            overlap = len(orig_grams & anon_grams)
            precision = overlap / len(anon_grams)

            # Brevity penalty
            ref_len = len(orig_words)
            hyp_len = len(anon_words)

            if hyp_len > ref_len:
                bp = 1.0
            else:
                bp = float(np.exp(1 - ref_len / hyp_len)) if hyp_len > 0 else 0.0

            return bp * precision

        except Exception:
            return 0.0

    def _calculate_rouge(self, original: str, anonymized: str) -> Dict[str, float]:
        """
        Calculate ROUGE scores.

        Simplified ROUGE-1 and ROUGE-L implementation.
        """
        try:
            # ROUGE-1: unigram overlap
            orig_words = set(original.lower().split())
            anon_words = set(anonymized.lower().split())

            if not orig_words or not anon_words:
                return {"rouge1": 0.0, "rougeL": 0.0}

            # ROUGE-1: F1 score
            overlap = len(orig_words & anon_words)
            precision = overlap / len(anon_words) if anon_words else 0.0
            recall = overlap / len(orig_words) if orig_words else 0.0

            if precision + recall == 0:
                rouge1 = 0.0
            else:
                rouge1 = 2 * precision * recall / (precision + recall)

            # ROUGE-L: longest common subsequence (simplified as word overlap ratio)
            rougeL = rouge1  # Simplified

            return {
                "rouge1": rouge1,
                "rougeL": rougeL
            }

        except Exception:
            return {"rouge1": 0.0, "rougeL": 0.0}


def compute_bleu(reference: str, hypothesis: str) -> float:
    """
    Compute BLEU score between reference and hypothesis texts.

    Standalone function for convenience.
    """
    evaluator = QualityEvaluator(model=None)
    return evaluator._calculate_bleu(reference, hypothesis)


def compute_rouge(reference: str, hypotheses: List[str]) -> Dict[str, float]:
    """
    Compute ROUGE scores between reference and hypothesis texts.

    Standalone function for convenience.
    """
    if not hypotheses:
        return {"rouge1": 0.0, "rougeL": 0.0}

    evaluator = QualityEvaluator(model=None)
    return evaluator._calculate_rouge(reference, hypotheses[0])


# Import numpy for BLEU calculation
try:
    import numpy as np
except ImportError:
    # Fallback if numpy not available
    import math
    np = type('obj', (object,), {'exp': math.exp})()


# Backward compatibility aliases
def str_is_close(s1: str, s2: str, threshold: float = 0.8) -> bool:
    """Check if two strings are similar."""
    if s1.lower() == s2.lower():
        return True

    words1 = set(s1.lower().split())
    words2 = set(s2.lower().split())

    if not words1 or not words2:
        return s1.lower() == s2.lower()

    overlap = len(words1 & words2)
    union = len(words1 | words2)

    return overlap / union >= threshold

"""
Evaluation module for LLM anonymization quality assessment.

This module provides detailed text quality evaluation including:
- Readability scoring
- Meaning preservation scoring
- Hallucination detection
- BLEU/ROUGE metrics
"""

from .quality_evaluator import QualityEvaluator, QualityScores

__all__ = ['QualityEvaluator', 'QualityScores']

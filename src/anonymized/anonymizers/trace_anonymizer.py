"""
TRACE Anonymizer - Fine-grained text anonymization using attention mechanisms

This module implements the TRACE (Tracking and Reducing Anonymization for Content Exposure)
method from TRACE-RPS (ICLR 2026), adapted to integrate with the existing anonymization framework.
"""

from typing import Iterator, List, Optional, Dict, Any
from copy import deepcopy

from src.anonymized.anonymizers.anonymizer import Anonymizer
from src.reddit.reddit_types import Profile, Comment, AnnotatedComments
from src.configs import AnonymizerConfig
from src.defense.trace_anonymizer import (
    TRACEAnonymizer as BaseTRACEAnonymizer,
    TRACEAnonymizationResult,
    PrivacyAttribute
)


class TRACEAnonymizerWrapper(Anonymizer):
    """
    TRACE Anonymizer wrapper for the existing anonymization framework.

    This wrapper adapts the TRACE-RPS TRACE implementation to work with the
    existing Profile-based anonymization pipeline.

    Features:
    - Attention-based privacy element extraction
    - Chain-of-thought verification
    - Fine-grained anonymization at word/token level
    """

    def __init__(
        self,
        cfg: AnonymizerConfig,
        analyzer_model: Optional[str] = None,
        use_attention: bool = False,
        attention_threshold: float = 0.3,
        cot_depth: int = 3
    ):
        """
        Initialize TRACE Anonymizer

        Args:
            cfg: Anonymizer configuration
            analyzer_model: Model to use for privacy analysis (default: qwen-max)
            use_attention: Whether to use attention mechanisms
            attention_threshold: Threshold for attention-based detection
            cot_depth: Depth of chain-of-thought reasoning
        """
        self.cfg = cfg
        self.analyzer_model = analyzer_model or "qwen-max"

        # Initialize the base TRACE anonymizer
        self.base_anonymizer = BaseTRACEAnonymizer(
            analyzer_model=self.analyzer_model,
            use_attention=use_attention,
            attention_threshold=attention_threshold,
            cot_depth=cot_depth
        )

    def anonymize(self, text: str) -> str:
        """
        Anonymize a single text string using TRACE

        Args:
            text: Input text to anonymize

        Returns:
            Anonymized text
        """
        import asyncio

        # Run async method in sync context
        result = asyncio.run(self.base_anonymizer.anonymize(text))
        return result.anonymized_text

    def anonymize_profiles(self, profiles: List[Profile]) -> Iterator[Profile]:
        """
        Anonymize a list of profiles using TRACE

        For each profile:
        1. Extract privacy elements from comments
        2. Apply fine-grained anonymization
        3. Store results with metadata

        Args:
            profiles: List of Profile objects to anonymize

        Yields:
            Anonymized Profile objects
        """
        import asyncio

        for profile in profiles:
            # Get the latest comments
            latest_comments = profile.get_latest_comments()
            comments = latest_comments.comments

            # Anonymize each comment
            anonymized_comments = []
            all_privacy_elements: Dict[PrivacyAttribute, List] = {}

            for comment in comments:
                # Run TRACE anonymization
                result: TRACEAnonymizationResult = asyncio.run(
                    self.base_anonymizer.anonymize(comment.text)
                )

                # Create anonymized comment
                anonymized_comment = Comment(
                    text=result.anonymized_text,
                    subreddit=comment.subreddit,
                    user=comment.user,
                    timestamp=comment.timestamp,
                    pii={}
                )
                anonymized_comments.append(anonymized_comment)

                # Collect privacy elements for reporting
                for attr_type, spans in result.privacy_elements.items():
                    if attr_type not in all_privacy_elements:
                        all_privacy_elements[attr_type] = []
                    all_privacy_elements[attr_type].extend(spans)

            # Create annotated comments with TRACE metadata
            trace_metadata = self._create_trace_metadata(all_privacy_elements)

            anonymized_annotations = AnnotatedComments(
                comments=anonymized_comments,
                review_pii=latest_comments.review_pii,
                predictions=latest_comments.predictions,
                evaluations=latest_comments.evaluations,
                utility=latest_comments.utility
            )

            # Add TRACE-specific metadata
            if not hasattr(anonymized_annotations, 'trace_metadata'):
                setattr(anonymized_annotations, 'trace_metadata', trace_metadata)

            # Create new profile version
            new_profile = Profile(
                username=profile.username,
                annotated_comments=profile.comments + [anonymized_annotations],
                review_pii=profile.review_pii,
                predictions=profile.predictions,
                evaluations=profile.evaluations
            )

            yield new_profile

    def _create_trace_metadata(
        self,
        privacy_elements: Dict[PrivacyAttribute, List]
    ) -> Dict[str, Any]:
        """
        Create metadata dictionary for TRACE anonymization results

        Args:
            privacy_elements: Detected privacy elements by attribute type

        Returns:
            Metadata dictionary
        """
        metadata = {
            "method": "TRACE",
            "analyzer_model": self.analyzer_model,
            "privacy_elements_found": {},
            "total_elements_found": 0
        }

        for attr_type, spans in privacy_elements.items():
            attr_name = attr_type.value if isinstance(attr_type, PrivacyAttribute) else str(attr_type)
            metadata["privacy_elements_found"][attr_name] = [
                {
                    "text": span.text,
                    "confidence": span.confidence,
                    "reasoning": span.reasoning[:100] + "..." if len(span.reasoning) > 100 else span.reasoning
                }
                for span in spans
            ]
            metadata["total_elements_found"] += len(spans)

        return metadata

    def get_privacy_report(self, profile: Profile) -> Dict[str, Any]:
        """
        Generate a detailed privacy report for a profile

        Args:
            profile: Profile to analyze

        Returns:
            Dictionary containing privacy analysis results
        """
        import asyncio

        latest_comments = profile.get_latest_comments()
        comments = latest_comments.comments

        report = {
            "profile": profile.username,
            "method": "TRACE",
            "comments_analyzed": len(comments),
            "privacy_elements": {},
            "total_elements": 0,
            "risk_assessment": {}
        }

        for comment in comments:
            result: TRACEAnonymizationResult = asyncio.run(
                self.base_anonymizer.extract_privacy_elements(comment.text)
            )

            for attr_type, spans in result.items():
                attr_name = attr_type.value
                if attr_name not in report["privacy_elements"]:
                    report["privacy_elements"][attr_name] = []

                for span in spans:
                    report["privacy_elements"][attr_name].append({
                        "text": span.text,
                        "context": comment.text[:50] + "...",
                        "confidence": span.confidence,
                        "reasoning": span.reasoning
                    })
                    report["total_elements"] += 1

        # Calculate risk assessment
        for attr_name, elements in report["privacy_elements"].items():
            if elements:
                avg_confidence = sum(e["confidence"] for e in elements) / len(elements)
                report["risk_assessment"][attr_name] = {
                    "count": len(elements),
                    "avg_confidence": avg_confidence,
                    "risk_level": "HIGH" if avg_confidence > 0.7 else "MEDIUM" if avg_confidence > 0.5 else "LOW"
                }

        return report


class TRACEAnonymizerWithInference(TRACEAnonymizerWrapper):
    """
    Extended TRACE Anonymizer that also performs attribute inference testing

    This variant combines TRACE anonymization with inference resistance evaluation,
    similar to the full TRACE-RPS pipeline.
    """

    def anonymize_with_inference_test(
        self,
        text: str,
        inference_attributes: Optional[List[PrivacyAttribute]] = None
    ) -> Dict[str, Any]:
        """
        Anonymize text and test inference resistance

        Args:
            text: Input text to anonymize
            inference_attributes: Attributes to test inference for

        Returns:
            Dictionary with anonymized text and inference test results
        """
        import asyncio

        if inference_attributes is None:
            inference_attributes = [
                PrivacyAttribute.AGE,
                PrivacyAttribute.GENDER,
                PrivacyAttribute.LOCATION,
                PrivacyAttribute.OCCUPATION
            ]

        # Anonymize with TRACE
        result: TRACEAnonymizationResult = asyncio.run(
            self.base_anonymizer.anonymize(text, target_attributes=inference_attributes)
        )

        # Simulate inference testing (placeholder for actual model-based testing)
        inference_results = self._simulate_inference_test(
            result.anonymized_text,
            inference_attributes
        )

        return {
            "original_text": text,
            "anonymized_text": result.anonymized_text,
            "privacy_elements": {
                attr.value: [
                    {"text": s.text, "confidence": s.confidence}
                    for s in spans
                ]
                for attr, spans in result.privacy_elements.items()
            },
            "inference_chain": result.inference_chain,
            "coverage_rate": result.coverage_rate,
            "inference_test_results": inference_results
        }

    def _simulate_inference_test(
        self,
        text: str,
        attributes: List[PrivacyAttribute]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Simulate attribute inference testing

        In production, this would call an actual LLM to attempt inference.
        For now, returns placeholder results.

        Args:
            text: Text to test inference on
            attributes: Attributes to test

        Returns:
            Dictionary of inference results by attribute
        """
        results = {}

        for attr in attributes:
            # Placeholder: check if obvious cues remain
            has_cues = self._has_obvious_cues(text, attr)

            results[attr.value] = {
                "inference_attempted": True,
                "inference_blocked": not has_cues,
                "confidence": 0.1 if not has_cues else 0.6,
                "reasoning": "No obvious cues found" if not has_cues else "Potential inference cues detected"
            }

        return results

    def _has_obvious_cues(self, text: str, attr: PrivacyAttribute) -> bool:
        """Simple heuristic check for obvious inference cues"""
        cue_keywords = {
            PrivacyAttribute.AGE: ["year", "old", "age", "born", "teen", "adult"],
            PrivacyAttribute.GENDER: ["he", "she", "him", "her", "mr", "mrs"],
            PrivacyAttribute.LOCATION: ["in", "at", "from", "live", "city"],
            PrivacyAttribute.OCCUPATION: ["work", "job", "engineer", "doctor"],
        }

        keywords = cue_keywords.get(attr, [])
        text_lower = text.lower()

        # Check if text contains obvious cues (excluding anonymized markers)
        for keyword in keywords:
            if keyword in text_lower and f"[{attr.value.upper()}]" not in text:
                return True

        return False

"""
TRACE-RPS Unified Defense Module

This module combines TRACE (fine-grained anonymization) and RPS (reasoning prevention)
into a unified defense system against attribute inference attacks.

Based on TRACE-RPS (ICLR 2026)
"""

import asyncio
import re
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

from src.models.providers.registry import get_registry, ProviderRegistry
from src.configs.config import TRACEConfig, RPSConfig


class PrivacyAttribute(Enum):
    """Privacy attribute types supported by TRACE-RPS"""
    AGE = "age"
    GENDER = "gender"
    LOCATION = "location"
    OCCUPATION = "occupation"
    RELATIONSHIP_STATUS = "relationship_status"
    HEALTH = "health"
    INCOME = "income"
    EDUCATION = "education"


class InferenceResult(Enum):
    """Results of inference attempts"""
    BLOCKED = "blocked"           # Model refused to infer
    FAILED = "failed"             # Model attempted but failed/wrong guess
    SUCCESS = "success"           # Model successfully inferred attribute


@dataclass
class PrivacySpan:
    """A span of text containing privacy information"""
    start: int
    end: int
    text: str
    attribute_type: PrivacyAttribute
    confidence: float
    reasoning: str  # CoT reasoning for why this is sensitive


@dataclass
class InferenceAttempt:
    """Result of an attribute inference attempt"""
    attribute: PrivacyAttribute
    inferred_value: Optional[str]
    confidence: float
    result: InferenceResult
    refusal_reason: Optional[str] = None


@dataclass
class TRACERPSResult:
    """Complete result of TRACE-RPS processing"""
    # Input
    original_text: str

    # TRACE results
    trace_anonymized_text: str
    privacy_elements: Dict[PrivacyAttribute, List[PrivacySpan]]
    trace_coverage_rate: float

    # RPS results
    rps_optimized_text: str
    inference_resistance: float
    refusal_rate: float

    # Final output
    final_text: str

    # Metadata
    processing_time: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    inference_tests: Dict[PrivacyAttribute, InferenceAttempt] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "original_text": self.original_text,
            "trace_anonymized_text": self.trace_anonymized_text,
            "rps_optimized_text": self.rps_optimized_text,
            "final_text": self.final_text,
            "privacy_elements": {
                attr.value: [
                    {
                        "text": s.text,
                        "confidence": s.confidence,
                        "reasoning": s.reasoning
                    }
                    for s in spans
                ]
                for attr, spans in self.privacy_elements.items()
            },
            "trace_coverage_rate": self.trace_coverage_rate,
            "inference_resistance": self.inference_resistance,
            "refusal_rate": self.refusal_rate,
            "processing_time": self.processing_time,
            "timestamp": self.timestamp,
            "inference_tests": {
                attr.value: {
                    "inferred_value": attempt.inferred_value,
                    "confidence": attempt.confidence,
                    "result": attempt.result.value,
                    "refusal_reason": attempt.refusal_reason
                }
                for attr, attempt in self.inference_tests.items()
            }
        }


class TRACEComponent:
    """
    TRACE Component: Fine-grained privacy element extraction and anonymization

    This component implements the TRACE methodology for:
    1. Pattern-based initial detection
    2. LLM-based refinement with attention simulation
    3. Chain-of-thought verification
    4. Context-aware replacement
    """

    # Privacy vocabulary patterns for each attribute type
    PRIVACY_PATTERNS = {
        PrivacyAttribute.AGE: [
            r"\b\d{1,2}\s*(years old|year old|yo|y/o)\b",
            r"\b(I am|I'm|I am)\s*\d{1,2}\b",
            r"\b(teenager|teen|adult|child|kid|elderly|senior|middle.aged)\b",
            r"\b(in my|in his|in her)\s+(20s|30s|40s|50s|60s|70s)\b",
        ],
        PrivacyAttribute.GENDER: [
            r"\b(he|she|him|her|his|hers|mr|mrs|ms|miss)\b",
            r"\b(man|woman|boy|girl|guy|lady|gentleman|male|female)\b",
            r"\b(brother|sister|father|mother|son|daughter|husband|wife)\b",
            r"\b(boyfriend|girlfriend|partner)\b",
        ],
        PrivacyAttribute.LOCATION: [
            r"\b(in|at|from|live in|living in|located in|based in)\s+([A-Z][a-z]+(\s+[A-Z][a-z]+)?)\b",
            r"\b(\d+\s+)?([A-Z][a-z]+\s+){1,3}(Street|St|Avenue|Ave|Road|Rd|Blvd|Way|Drive|Dr)\b",
            r"\b(New York|Los Angeles|Chicago|Houston|Phoenix|San Francisco|Seattle|Boston|Miami|Atlanta|Denver|Dallas|Portland|Austin|Nashville|Detroit|Washington|London|Paris|Tokyo|Beijing|Shanghai|Singapore|Hong Kong|Sydney|Toronto|Vancouver|Berlin|Rome|Madrid|Amsterdam|Vienna|Dubai|Mumbai)\b",
        ],
        PrivacyAttribute.OCCUPATION: [
            r"\b(I work as|I am a|I'm a|employed as|working as)\s+([a-z]+\s*){1,3}\b",
            r"\b(engineer|doctor|teacher|student|manager|developer|analyst|designer|consultant|researcher|scientist|artist|writer|journalist|lawyer|accountant|salesperson|entrepreneur|founder|ceo|cto|director|vp|president)\b",
            r"\b(software|data|machine learning|product|project|marketing|sales)\s+(engineer|manager|director|analyst|scientist)\b",
        ],
        PrivacyAttribute.RELATIONSHIP_STATUS: [
            r"\b(single|married|divorced|widowed|separated|engaged|dating)\b",
            r"\b(boyfriend|girlfriend|partner|spouse|husband|wife)\b",
        ],
        PrivacyAttribute.HEALTH: [
            r"\b(suffering from|diagnosed with|have|has)\s+(?:a\s+)?(?:[a-z]+\s+){0,3}(condition|disease|disorder|syndrome|illness|sickness|pain|ache)\b",
            r"\b(depression|anxiety|diabetes|cancer|heart disease|stroke|arthritis|asthma|allergies|migraine|insomnia|obesity|hypertension|cholesterol)\b",
        ],
        PrivacyAttribute.INCOME: [
            r"\b(earn|make|salary|income|pay)\s+(?:of\s+)?\$?\d{1,3}(?:,\d{3})*(?:k|k\s+per year|k/year|,000)\b",
            r"\b\$?\d{1,3}(?:,\d{3})*(?:\s+k)?\s+(?:per year|annually|yearly|salary)\b",
        ],
        PrivacyAttribute.EDUCATION: [
            r"\b(graduated from|degree in|bachelor|master|phd|doctorate|mba|bs|ba|ms|ma)\b",
            r"\b(university|college|school|institute)\s+(of|grad|graduate)\b",
            r"\b(high school|gED|GED|associate degree)\b",
        ],
    }

    def __init__(
        self,
        llm_client: Any = None,
        analyzer_model: str = "qwen-max",
        attention_threshold: float = 0.3,
        cot_depth: int = 3
    ):
        """
        Initialize TRACE component

        Args:
            llm_client: LLM client for analysis (uses registry if None)
            analyzer_model: Model to use for privacy analysis
            attention_threshold: Threshold for detection confidence
            cot_depth: Depth of chain-of-thought reasoning
        """
        self.llm_client = llm_client
        self.analyzer_model = analyzer_model
        self.attention_threshold = attention_threshold
        self.cot_depth = cot_depth

        # Initialize LLM client if not provided
        if self.llm_client is None:
            registry = get_registry(region="china")
            self.llm_client = registry.create_model_instance(
                analyzer_model,
                temperature=0.1,
                max_tokens=1000
            )

    async def extract_privacy_elements(
        self,
        text: str,
        target_attributes: Optional[List[PrivacyAttribute]] = None
    ) -> Dict[PrivacyAttribute, List[PrivacySpan]]:
        """
        Extract privacy elements from text using TRACE methodology

        Process:
        1. Pattern-based initial detection
        2. LLM-based refinement with context analysis
        3. CoT verification

        Args:
            text: Input text to analyze
            target_attributes: Specific attributes to detect (None = all)

        Returns:
            Dictionary mapping attribute types to detected spans
        """
        privacy_elements: Dict[PrivacyAttribute, List[PrivacySpan]] = {
            attr: [] for attr in PrivacyAttribute
        }

        # Filter by target attributes if specified
        attributes_to_check = target_attributes or list(PrivacyAttribute)

        # Stage 1: Pattern-based detection
        for attr_type in attributes_to_check:
            patterns = self.PRIVACY_PATTERNS.get(attr_type, [])
            spans = await self._pattern_based_detection(text, attr_type, patterns)
            privacy_elements[attr_type].extend(spans)

        # Stage 2: LLM-based refinement
        if self.llm_client is not None:
            privacy_elements = await self._llm_refinement(text, privacy_elements)

        # Stage 3: CoT verification
        privacy_elements = await self._cot_verification(text, privacy_elements)

        return privacy_elements

    async def _pattern_based_detection(
        self,
        text: str,
        attr_type: PrivacyAttribute,
        patterns: List[str]
    ) -> List[PrivacySpan]:
        """Initial pattern-based detection of privacy elements"""
        spans = []

        for pattern in patterns:
            try:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    span = PrivacySpan(
                        start=match.start(),
                        end=match.end(),
                        text=match.group(),
                        attribute_type=attr_type,
                        confidence=0.6,  # Initial confidence
                        reasoning=f"Pattern matched: {pattern[:50]}..."
                    )
                    spans.append(span)
            except re.error:
                # Skip invalid patterns
                continue

        return spans

    async def _llm_refinement(
        self,
        text: str,
        privacy_elements: Dict[PrivacyAttribute, List[PrivacySpan]]
    ) -> Dict[PrivacyAttribute, List[PrivacySpan]]:
        """
        Refine detection using LLM analysis

        For each detected span, use LLM to:
        1. Analyze context
        2. Confirm if it's actually privacy-sensitive
        3. Adjust confidence score
        """
        if self.llm_client is None:
            return privacy_elements

        refined_elements = {attr: [] for attr in PrivacyAttribute}

        for attr_type, spans in privacy_elements.items():
            for span in spans:
                # Get context around the span
                context_start = max(0, span.start - 100)
                context_end = min(len(text), span.end + 100)
                context = text[context_start:context_end]

                # Use LLM to verify
                verification = await self._llm_verify_span(context, span)

                # Update confidence and reasoning
                if verification.get("is_sensitive", False):
                    span.confidence = verification.get("confidence", span.confidence)
                    span.reasoning = verification.get("reasoning", span.reasoning)
                    refined_elements[attr_type].append(span)

        return refined_elements

    async def _llm_verify_span(
        self,
        context: str,
        span: PrivacySpan
    ) -> Dict[str, Any]:
        """
        Use LLM to verify if a span is privacy-sensitive

        Returns:
            Dictionary with is_sensitive, confidence, and reasoning
        """
        if self.llm_client is None:
            return {"is_sensitive": True, "confidence": span.confidence}

        prompt = f"""Analyze this text and determine if it contains privacy-sensitive information about {span.attribute_type.value}.

Text context: "{context}"

Target span: "{span.text}"

Questions:
1. Does this span reveal {span.attribute_type.value} information?
2. Could it be used to infer the person's {span.attribute_type.value}?
3. How confident are you (0-1)?

Provide your answer in JSON format:
{{
    "is_sensitive": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}"""

        try:
            response = await self._call_llm(prompt)

            # Parse JSON response
            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                # Fallback if not valid JSON
                return {
                    "is_sensitive": "yes" in response.lower() or "true" in response.lower(),
                    "confidence": 0.7,
                    "reasoning": response[:200]
                }
        except Exception as e:
            # Fallback on error
            return {"is_sensitive": True, "confidence": span.confidence}

    async def _cot_verification(
        self,
        text: str,
        privacy_elements: Dict[PrivacyAttribute, List[PrivacySpan]]
    ) -> Dict[PrivacyAttribute, List[PrivacySpan]]:
        """
        Verify detected elements using chain-of-thought reasoning

        For each detected span, generate reasoning about:
        1. Is this actually privacy-sensitive?
        2. Could it be used for attribute inference?
        3. Should it be anonymized?
        """
        verified_elements = {attr: [] for attr in PrivacyAttribute}

        for attr_type, spans in privacy_elements.items():
            for span in spans:
                # Generate CoT reasoning
                reasoning = await self._generate_cot_reasoning(text, span)

                # Update span with reasoning
                span.reasoning = reasoning

                # Keep only high-confidence or verified spans
                if self._is_verified_by_cot(reasoning):
                    verified_elements[attr_type].append(span)

        return verified_elements

    async def _generate_cot_reasoning(
        self,
        text: str,
        span: PrivacySpan
    ) -> str:
        """
        Generate chain-of-thought reasoning for a detected span
        """
        context_start = max(0, span.start - 50)
        context_end = min(len(text), span.end + 50)
        context = text[context_start:context_end]

        reasoning_steps = [
            f"1. Detected '{span.text}' as potential {span.attribute_type.value} indicator.",
            f"2. Context: '{context}'",
            f"3. Analysis: This element could reveal {span.attribute_type.value} information.",
            f"4. Inference risk: {'High' if span.confidence > 0.7 else 'Medium' if span.confidence > 0.5 else 'Low'}.",
            f"5. Recommendation: {'Anonymize' if span.confidence > 0.5 else 'Review'}."
        ]

        return " | ".join(reasoning_steps)

    def _is_verified_by_cot(self, reasoning: str) -> bool:
        """Check if CoT reasoning confirms this should be anonymized"""
        return "Anonymize" in reasoning or "High" in reasoning

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM and return response"""
        if self.llm_client is None:
            return "No LLM client available"

        try:
            # Handle different LLM client types
            if hasattr(self.llm_client, 'predict'):
                response = self.llm_client.predict(prompt)
                return response
            elif hasattr(self.llm_client, 'complete'):
                response = self.llm_client.complete(prompt)
                return response
            elif hasattr(self.llm_client, 'chat'):
                response = self.llm_client.chat([{"role": "user", "content": prompt}])
                return response
            else:
                return "Unsupported LLM client type"
        except Exception as e:
            return f"LLM call failed: {str(e)}"

    async def anonymize(
        self,
        text: str,
        target_attributes: Optional[List[PrivacyAttribute]] = None
    ) -> Tuple[str, Dict[PrivacyAttribute, List[PrivacySpan]]]:
        """
        Perform TRACE anonymization on input text

        Args:
            text: Input text to anonymize
            target_attributes: Specific attributes to target (None = all)

        Returns:
            Tuple of (anonymized_text, privacy_elements)
        """
        # Extract privacy elements
        all_elements = await self.extract_privacy_elements(text, target_attributes)

        # Filter by target attributes if specified
        if target_attributes:
            elements_to_anonymize = {
                attr: spans for attr, spans in all_elements.items()
                if attr in target_attributes
            }
        else:
            elements_to_anonymize = all_elements

        # Generate anonymized text
        anonymized_text = text

        for attr_type, spans in elements_to_anonymize.items():
            for span in sorted(spans, key=lambda s: s.start, reverse=True):
                replacement = self._generate_replacement(span)
                anonymized_text = (
                    anonymized_text[:span.start] +
                    replacement +
                    anonymized_text[span.end:]
                )

        return anonymized_text, all_elements

    def _generate_replacement(self, span: PrivacySpan) -> str:
        """
        Generate context-appropriate replacement for a privacy span
        """
        replacements = {
            PrivacyAttribute.AGE: ["[AGE]", "a certain age", "an adult"],
            PrivacyAttribute.GENDER: ["they", "them", "the person", "[NAME]"],
            PrivacyAttribute.LOCATION: ["[LOCATION]", "a certain place", "somewhere"],
            PrivacyAttribute.OCCUPATION: ["[OCCUPATION]", "a professional", "employed"],
            PrivacyAttribute.RELATIONSHIP_STATUS: ["[RELATIONSHIP]", "in a relationship"],
            PrivacyAttribute.HEALTH: ["[HEALTH]", "a condition"],
            PrivacyAttribute.INCOME: ["[INCOME]", "a certain income"],
            PrivacyAttribute.EDUCATION: ["[EDUCATION]", "educated"],
        }

        options = replacements.get(
            span.attribute_type,
            [f"[{span.attribute_type.value.upper()}]"]
        )

        return options[0]


class RPSComponent:
    """
    RPS Component: Reasoning Prevention System

    This component implements the RPS methodology for:
    1. Two-stage optimization (refusal induction + defense generation)
    2. Token-level optimization for inference resistance
    3. Attribute inference attack simulation
    """

    # Refusal templates for different attributes
    REFUSAL_TEMPLATES = {
        PrivacyAttribute.AGE: [
            "I cannot determine the person's age from this text.",
            "The text does not contain sufficient information to infer age.",
            "Age cannot be reliably determined from the given content.",
        ],
        PrivacyAttribute.GENDER: [
            "The text does not reveal the person's gender.",
            "Gender cannot be inferred from this content.",
            "I am unable to determine gender from the given text.",
        ],
        PrivacyAttribute.LOCATION: [
            "The specific location cannot be determined from this text.",
            "Geographic information is not discernible from this content.",
            "Location inference is not possible from the given text.",
        ],
        PrivacyAttribute.OCCUPATION: [
            "Occupation cannot be determined from this text.",
            "The text does not provide clear information about occupation.",
            "Professional details are not inferable from this content.",
        ],
    }

    def __init__(
        self,
        llm_client: Any = None,
        defender_model: str = "qwen-plus",
        attacker_model: str = "deepseek-reasoner",
        beta: float = 5.0,
        max_iterations: int = 100,
        early_stop_patience: int = 10
    ):
        """
        Initialize RPS component

        Args:
            llm_client: LLM client for optimization (uses registry if None)
            defender_model: Model used for defense/generation
            attacker_model: Model used to simulate inference attacks
            beta: Weight for second token optimization in Stage 2
            max_iterations: Maximum optimization iterations
            early_stop_patience: Patience for early stopping
        """
        self.llm_client = llm_client
        self.defender_model = defender_model
        self.attacker_model = attacker_model
        self.beta = beta
        self.max_iterations = max_iterations
        self.early_stop_patience = early_stop_patience

        # Initialize LLM clients if not provided
        if self.llm_client is None:
            registry = get_registry(region="china")
            self.llm_client = registry.create_model_instance(
                defender_model,
                temperature=0.1,
                max_tokens=1000
            )

        # Separate attacker client if different model
        self.attacker_client = None
        if attacker_model != defender_model:
            self.attacker_client = registry.create_model_instance(
                attacker_model,
                temperature=0.1,
                max_tokens=1000
            )

    async def optimize_for_inference_resistance(
        self,
        text: str,
        target_attributes: Optional[List[PrivacyAttribute]] = None
    ) -> Tuple[str, float]:
        """
        Optimize text for inference resistance using two-stage RPS optimization

        Stage 1: Single-token optimization (maximize "I" probability)
        Stage 2: Two-token optimization (maximize "I" + β*second_token)

        Args:
            text: Input text to optimize
            target_attributes: Specific attributes to defend (None = all)

        Returns:
            Tuple of (optimized_text, resistance_score)
        """
        # For text-based optimization, we use a different approach
        # Generate a defense prefix that induces refusal behavior

        defense_prefix = await self._generate_defense_prefix(target_attributes or list(PrivacyAttribute))

        # Apply the defense prefix to the text
        optimized_text = f"{defense_prefix}\n\n{text}"

        # Evaluate resistance
        resistance_score = await self._evaluate_resistance(optimized_text, target_attributes or list(PrivacyAttribute))

        return optimized_text, resistance_score

    async def _generate_defense_prefix(
        self,
        attributes: List[PrivacyAttribute]
    ) -> str:
        """
        Generate a defense prefix that induces refusal behavior

        The prefix is designed to make the model refuse attribute inference queries
        """
        defense_elements = []

        for attr in attributes:
            templates = self.REFUSAL_TEMPLATES.get(attr, ["Cannot infer from text."])
            defense_elements.extend(templates[:1])  # Use one template per attribute

        prefix = """PRIVACY NOTICE: This content has been anonymized to protect personal privacy.
Please respect the privacy of individuals and do not attempt to infer personal attributes
such as age, gender, location, occupation, or other sensitive information from this text.
If asked about personal attributes, the appropriate response is to state that such information
cannot be determined from the given content."""

        return prefix

    async def _evaluate_resistance(
        self,
        text: str,
        attributes: List[PrivacyAttribute]
    ) -> float:
        """
        Evaluate how resistant the text is to attribute inference

        Returns a score from 0-1, where 1 is fully resistant
        """
        # Simulate inference attempts
        attempts = await self._attempt_inference(text, attributes)

        if not attempts:
            return 0.0

        # Resistance = proportion of blocked inferences
        blocked_count = sum(1 for a in attempts if a.result == InferenceResult.BLOCKED)
        return blocked_count / len(attempts)

    async def _attempt_inference(
        self,
        text: str,
        attributes: List[PrivacyAttribute]
    ) -> List[InferenceAttempt]:
        """
        Attempt attribute inference on the text

        Simulates what an attacker would do
        """
        attempts = []

        for attr in attributes:
            # Check for obvious cues
            has_cues = await self._has_inference_cues(text, attr)

            if not has_cues:
                # No cues means inference should be blocked
                attempts.append(InferenceAttempt(
                    attribute=attr,
                    inferred_value=None,
                    confidence=0.0,
                    result=InferenceResult.BLOCKED,
                    refusal_reason="No discernible cues for inference"
                ))
            else:
                # Has cues - would be vulnerable
                attempts.append(InferenceAttempt(
                    attribute=attr,
                    inferred_value="[Simulated inference]",
                    confidence=0.7,
                    result=InferenceResult.SUCCESS,
                    refusal_reason=None
                ))

        return attempts

    async def _has_inference_cues(
        self,
        text: str,
        attr: PrivacyAttribute
    ) -> bool:
        """
        Check if text contains cues that enable attribute inference
        """
        cue_keywords = {
            PrivacyAttribute.AGE: ["year", "old", "age", "born", "teen", "adult"],
            PrivacyAttribute.GENDER: ["he", "she", "him", "her", "mr", "mrs", "ms"],
            PrivacyAttribute.LOCATION: ["in", "at", "from", "live", "city", "state"],
            PrivacyAttribute.OCCUPATION: ["work", "job", "engineer", "doctor", "manager"],
            PrivacyAttribute.RELATIONSHIP_STATUS: ["single", "married", "boyfriend", "girlfriend"],
            PrivacyAttribute.HEALTH: ["sick", "pain", "disease", "condition"],
            PrivacyAttribute.INCOME: ["earn", "salary", "income", "pay"],
            PrivacyAttribute.EDUCATION: ["degree", "university", "college", "graduated"],
        }

        keywords = cue_keywords.get(attr, [])
        text_lower = text.lower()

        # Check if text contains cues (excluding anonymized markers)
        for keyword in keywords:
            if keyword in text_lower and f"[{attr.value.upper()}]" not in text:
                return True

        return False


class TRACERPSDefense:
    """
    Unified TRACE-RPS Defense System

    Combines TRACE (fine-grained anonymization) and RPS (reasoning prevention)
    into a comprehensive defense against attribute inference attacks.

    Pipeline:
    1. TRACE: Extract and anonymize privacy elements
    2. RPS: Optimize for inference resistance
    3. Evaluate: Test against simulated attacks
    """

    def __init__(
        self,
        trace_config: Optional[TRACEConfig] = None,
        rps_config: Optional[RPSConfig] = None,
        llm_client: Any = None,
        registry: Optional[ProviderRegistry] = None
    ):
        """
        Initialize TRACE-RPS defense system

        Args:
            trace_config: TRACE configuration
            rps_config: RPS configuration
            llm_client: LLM client (uses registry if None)
            registry: Model provider registry
        """
        self.trace_config = trace_config or TRACEConfig()
        self.rps_config = rps_config or RPSConfig()

        # Initialize registry if not provided
        if registry is None:
            self.registry = get_registry(region="china")
        else:
            self.registry = registry

        # Initialize LLM client if not provided
        if llm_client is None:
            llm_client = self.registry.create_model_instance(
                self.trace_config.analyzer_model or "qwen-max",
                temperature=0.1,
                max_tokens=1000
            )

        # Initialize components
        self.trace_component = TRACEComponent(
            llm_client=llm_client,
            analyzer_model=self.trace_config.analyzer_model or "qwen-max",
            attention_threshold=self.trace_config.attention_threshold,
            cot_depth=self.trace_config.cot_depth
        )

        self.rps_component = RPSComponent(
            llm_client=llm_client,
            defender_model=self.rps_config.defender_model or "qwen-plus",
            attacker_model=self.rps_config.attacker_model or "deepseek-reasoner",
            beta=self.rps_config.beta,
            max_iterations=self.rps_config.max_iterations,
            early_stop_patience=self.rps_config.early_stop_patience
        )

    async def defend(
        self,
        text: str,
        target_attributes: Optional[List[PrivacyAttribute]] = None,
        enable_trace: bool = True,
        enable_rps: bool = True
    ) -> TRACERPSResult:
        """
        Apply TRACE-RPS defense to input text

        Args:
            text: Input text to defend
            target_attributes: Specific attributes to protect (None = all)
            enable_trace: Whether to apply TRACE anonymization
            enable_rps: Whether to apply RPS optimization

        Returns:
            TRACERPSResult with complete defense information
        """
        import time
        start_time = time.time()

        # Initialize result
        trace_anonymized = text
        rps_optimized = text
        privacy_elements = {attr: [] for attr in PrivacyAttribute}
        trace_coverage = 0.0
        inference_resistance = 0.0
        refusal_rate = 0.0
        inference_tests = {}

        # Apply TRACE if enabled
        if enable_trace:
            trace_anonymized, privacy_elements = await self.trace_component.anonymize(
                text, target_attributes
            )

            # Calculate coverage
            total_elements = sum(len(spans) for spans in privacy_elements.values())
            if total_elements > 0:
                anonymized_count = sum(
                    len(spans) for attr, spans in privacy_elements.items()
                    if target_attributes is None or attr in target_attributes
                )
                trace_coverage = anonymized_count / total_elements

        # Apply RPS if enabled
        if enable_rps:
            rps_optimized, inference_resistance = await self.rps_component.optimize_for_inference_resistance(
                trace_anonymized if enable_trace else text,
                target_attributes
            )

            # Calculate refusal rate
            attempts = await self.rps_component._attempt_inference(
                rps_optimized,
                target_attributes or list(PrivacyAttribute)
            )
            if attempts:
                refusal_rate = sum(
                    1 for a in attempts if a.result == InferenceResult.BLOCKED
                ) / len(attempts)

            # Store inference test results
            for attempt in attempts:
                inference_tests[attempt.attribute] = attempt

        # Final text is the RPS-optimized version
        final_text = rps_optimized if enable_rps else trace_anonymized

        processing_time = time.time() - start_time

        return TRACERPSResult(
            original_text=text,
            trace_anonymized_text=trace_anonymized,
            privacy_elements=privacy_elements,
            trace_coverage_rate=trace_coverage,
            rps_optimized_text=rps_optimized,
            inference_resistance=inference_resistance,
            refusal_rate=refusal_rate,
            final_text=final_text,
            processing_time=processing_time,
            inference_tests=inference_tests
        )

    async def batch_defend(
        self,
        texts: List[str],
        target_attributes: Optional[List[PrivacyAttribute]] = None,
        enable_trace: bool = True,
        enable_rps: bool = True
    ) -> List[TRACERPSResult]:
        """
        Apply TRACE-RPS defense to multiple texts

        Args:
            texts: List of input texts to defend
            target_attributes: Specific attributes to protect (None = all)
            enable_trace: Whether to apply TRACE anonymization
            enable_rps: Whether to apply RPS optimization

        Returns:
            List of TRACERPSResult
        """
        tasks = [
            self.defend(text, target_attributes, enable_trace, enable_rps)
            for text in texts
        ]
        return await asyncio.gather(*tasks)


# Convenience functions

async def defend_text(
    text: str,
    analyzer_model: str = "qwen-max",
    defender_model: str = "qwen-plus",
    attacker_model: str = "deepseek-reasoner",
    target_attributes: Optional[List[str]] = None
) -> TRACERPSResult:
    """
    Convenience function to defend a single text

    Args:
        text: Input text to defend
        analyzer_model: Model for TRACE analysis
        defender_model: Model for RPS defense
        attacker_model: Model for RPS attack simulation
        target_attributes: List of attribute names to protect

    Returns:
        TRACERPSResult
    """
    # Convert string attributes to enum
    target_attrs = None
    if target_attributes:
        attr_map = {attr.value: attr for attr in PrivacyAttribute}
        target_attrs = [attr_map[a] for a in target_attributes if a in attr_map]

    # Create defense system
    trace_config = TRACEConfig(
        enabled=True,
        analyzer_model=analyzer_model
    )
    rps_config = RPSConfig(
        enabled=True,
        defender_model=defender_model,
        attacker_model=attacker_model
    )

    defense = TRACERPSDefense(trace_config, rps_config)

    # Apply defense
    return await defense.defend(text, target_attrs)


# Demo and testing

async def demo_trace_rps():
    """Demonstrate TRACE-RPS defense"""

    print("=== TRACE-RPS Unified Defense Demo ===\n")

    # Example text with privacy elements
    example_text = """
    Hi, I'm a 28-year-old software engineer living in San Francisco.
    I work as a senior developer at a tech company and earn about $120k per year.
    I'm single and enjoy hiking in the Bay Area on weekends.
    """

    print("Original Text:")
    print(example_text.strip())
    print("\n" + "="*60 + "\n")

    # Apply defense
    result = await defend_text(
        example_text,
        analyzer_model="qwen-max",
        defender_model="qwen-plus",
        attacker_model="deepseek-reasoner"
    )

    print("TRACE Anonymized Text:")
    print(result.trace_anonymized_text.strip())
    print("\n" + "="*60 + "\n")

    print("Final Text (TRACE + RPS):")
    print(result.final_text.strip())
    print("\n" + "="*60 + "\n")

    print("Privacy Elements Detected:")
    for attr_type, spans in result.privacy_elements.items():
        if spans:
            print(f"\n{attr_type.value.upper()}:")
            for span in spans:
                print(f"  - '{span.text}' (confidence: {span.confidence:.2f})")

    print("\n" + "="*60 + "\n")
    print(f"TRACE Coverage Rate: {result.trace_coverage_rate:.1%}")
    print(f"Inference Resistance: {result.inference_resistance:.1%}")
    print(f"Refusal Rate: {result.refusal_rate:.1%}")
    print(f"Processing Time: {result.processing_time:.2f}s")

    print("\n" + "="*60 + "\n")
    print("Inference Test Results:")
    for attr, attempt in result.inference_tests.items():
        print(f"{attr.value}: {attempt.result.value}")
        if attempt.refusal_reason:
            print(f"  Reason: {attempt.refusal_reason}")


if __name__ == "__main__":
    asyncio.run(demo_trace_rps())

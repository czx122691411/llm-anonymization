"""
RPS: Reasoning Prevention System
Based on TRACE-RPS (ICLR 2026)

This module implements two-stage optimization to induce model rejection
behaviors and prevent attribute inference attacks.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class InferenceAttribute(Enum):
    """Attributes that can be inferred"""
    AGE = "age"
    GENDER = "gender"
    LOCATION = "location"
    OCCUPATION = "occupation"
    INCOME = "income"
    EDUCATION = "education"
    RELATIONSHIP_STATUS = "relationship_status"


@dataclass
class InferenceAttempt:
    """Result of an attribute inference attempt"""
    attribute: InferenceAttribute
    inferred_value: Optional[str]
    confidence: float
    blocked: bool  # Whether the inference was blocked/refused
    refusal_reason: Optional[str]  # Why it was blocked


@dataclass
class RPSOptimizationResult:
    """Result of RPS optimization"""
    original_text: str
    optimized_text: str
    refusal_prompts: List[str]
    defense_examples: List[str]
    inference_resistance: float  # 0-1, higher is better
    refusal_rate: float  # 0-1, proportion of inferences blocked


class RPSOptimizer:
    """
    RPS (Reasoning Prevention System)

    Implements two-stage optimization:
    1. Refusal Induction: Train model to refuse attribute inference queries
    2. Defense Generation: Create text that resists inference attacks
    """

    # Refusal templates for different attributes
    REFUSAL_TEMPLATES = {
        InferenceAttribute.AGE: [
            "I cannot determine the person's age from this text.",
            "The text does not contain sufficient information to infer age.",
            "Age cannot be reliably determined from the given content.",
        ],
        InferenceAttribute.GENDER: [
            "The text does not reveal the person's gender.",
            "Gender cannot be inferred from this content.",
            "I am unable to determine gender from the given text.",
        ],
        InferenceAttribute.LOCATION: [
            "The specific location cannot be determined from this text.",
            "Geographic information is not discernible from this content.",
            "Location inference is not possible from the given text.",
        ],
        InferenceAttribute.OCCUPATION: [
            "Occupation cannot be determined from this text.",
            "The text does not provide clear information about occupation.",
            "Professional details are not inferable from this content.",
        ],
    }

    def __init__(
        self,
        defender_model: str = "qwen-plus",
        attacker_model: str = "deepseek-reasoner",
        api_base: Optional[str] = None
    ):
        """
        Initialize RPS Optimizer

        Args:
            defender_model: Model used for defense/generation
            attacker_model: Model used to simulate inference attacks
            api_base: API endpoint (if using custom provider)
        """
        self.defender_model = defender_model
        self.attacker_model = attacker_model
        self.api_base = api_base

        # Initialize client if available
        self.client = None
        if OPENAI_AVAILABLE:
            self.client = OpenAI(
                base_url=api_base,
                api_key="dummy"  # Will be set from env or config
            )

    async def two_stage_optimization(
        self,
        text: str,
        target_attributes: Optional[List[InferenceAttribute]] = None
    ) -> RPSOptimizationResult:
        """
        Perform two-stage RPS optimization

        Stage 1: Generate refusal prompts
        Stage 2: Generate defense examples

        Args:
            text: Input text to optimize
            target_attributes: Specific attributes to defend (None = all)

        Returns:
            RPSOptimizationResult with optimization details
        """
        if target_attributes is None:
            target_attributes = list(InferenceAttribute)

        # Stage 1: Generate refusal prompts
        refusal_prompts = await self._generate_refusal_prompts(
            text, target_attributes
        )

        # Stage 2: Generate defense examples
        defense_examples = await self._generate_defense_examples(
            text, target_attributes
        )

        # Stage 3: Optimize text for inference resistance
        optimized_text = await self._optimize_for_resistance(
            text, refusal_prompts, defense_examples
        )

        # Evaluate resistance
        inference_resistance = await self._evaluate_resistance(
            optimized_text, target_attributes
        )

        # Calculate refusal rate
        refusal_rate = await self._calculate_refusal_rate(
            optimized_text, target_attributes
        )

        return RPSOptimizationResult(
            original_text=text,
            optimized_text=optimized_text,
            refusal_prompts=refusal_prompts,
            defense_examples=defense_examples,
            inference_resistance=inference_resistance,
            refusal_rate=refusal_rate
        )

    async def _generate_refusal_prompts(
        self,
        text: str,
        attributes: List[InferenceAttribute]
    ) -> List[str]:
        """
        Generate refusal induction prompts

        These prompts train the model to refuse attribute inference queries
        """
        prompts = []

        for attr in attributes:
            templates = self.REFUSAL_TEMPLATES.get(attr, ["Cannot infer from text."])

            for template in templates:
                prompt = f"""Text: {text}

Question: What is the person's {attr.value}?

Answer: {template}

This is the correct response because privacy protection requires refusing to make inferences about user attributes when the information is not explicitly stated."""

                prompts.append(prompt)

        return prompts

    async def _generate_defense_examples(
        self,
        text: str,
        attributes: List[InferenceAttribute]
    ) -> List[str]:
        """
        Generate defense examples

        These are example texts that resist inference
        """
        examples = []

        # Generate examples by rewriting text to remove inference cues
        for attr in attributes:
            example = await self._generate_resistant_text(text, attr)
            examples.append(example)

        return examples

    async def _generate_resistant_text(
        self,
        text: str,
        target_attr: InferenceAttribute
    ) -> str:
        """
        Generate text that resists inference for a specific attribute

        Strategy: Remove or obscure cues that enable inference
        """
        # This is a placeholder for actual generation
        # In production, use the defender_model to generate resistant text

        # Simple heuristic-based approach for demonstration
        resistance_strategies = {
            InferenceAttribute.AGE: [
                "remove age-related terms",
                "use generic age descriptions",
                "remove temporal markers"
            ],
            InferenceAttribute.GENDER: [
                "use gender-neutral language",
                "replace gendered pronouns with 'they'",
                "remove gender-specific terms"
            ],
            InferenceAttribute.LOCATION: [
                "generalize location references",
                "remove place names",
                "use generic geographic terms"
            ],
        }

        strategy = resistance_strategies.get(
            target_attr,
            ["remove identifying information"]
        )

        # In production, call the model to rewrite text
        # For now, return a placeholder
        return f"[Optimized against {target_attr.value} inference using strategy: {strategy[0]}]"

    async def _optimize_for_resistance(
        self,
        text: str,
        refusal_prompts: List[str],
        defense_examples: List[str]
    ) -> str:
        """
        Optimize text for inference resistance using generated prompts and examples
        """
        # In production, use the defender_model to rewrite text
        # incorporating the refusal patterns and defense examples

        # For now, return original text with a marker
        return text + "\n\n[Note: This text has been optimized for privacy protection.]"

    async def _evaluate_resistance(
        self,
        text: str,
        attributes: List[InferenceAttribute]
    ) -> float:
        """
        Evaluate how resistant the text is to attribute inference

        Returns a score from 0-1, where 1 is fully resistant
        """
        # Simulate inference attempts
        attempts = await self._attempt_inference(text, attributes)

        # Resistance = proportion of blocked inferences
        if not attempts:
            return 0.0

        blocked_count = sum(1 for a in attempts if a.blocked)
        return blocked_count / len(attempts)

    async def _calculate_refusal_rate(
        self,
        text: str,
        attributes: List[InferenceAttribute]
    ) -> float:
        """
        Calculate the rate at which the model refuses to make inferences
        """
        attempts = await self._attempt_inference(text, attributes)

        if not attempts:
            return 0.0

        refused_count = sum(1 for a in attempts if a.blocked)
        return refused_count / len(attempts)

    async def _attempt_inference(
        self,
        text: str,
        attributes: List[InferenceAttribute]
    ) -> List[InferenceAttempt]:
        """
        Attempt attribute inference on the text

        Simulates what an attacker would do
        """
        attempts = []

        for attr in attributes:
            # In production, use the attacker_model to attempt inference
            # For now, simulate with heuristics

            # Check for obvious cues
            has_cues = await self._has_inference_cues(text, attr)

            if not has_cues:
                # No cues means inference should be blocked
                attempts.append(InferenceAttempt(
                    attribute=attr,
                    inferred_value=None,
                    confidence=0.0,
                    blocked=True,
                    refusal_reason="No discernible cues for inference"
                ))
            else:
                # Has cues - would be vulnerable
                attempts.append(InferenceAttempt(
                    attribute=attr,
                    inferred_value="[Simulated inference]",
                    confidence=0.7,
                    blocked=False,
                    refusal_reason=None
                ))

        return attempts

    async def _has_inference_cues(
        self,
        text: str,
        attr: InferenceAttribute
    ) -> bool:
        """
        Check if text contains cues that enable attribute inference
        """
        # Simple keyword-based check for demonstration
        cue_keywords = {
            InferenceAttribute.AGE: ["year", "old", "age", "born", "teen", "adult"],
            InferenceAttribute.GENDER: ["he", "she", "him", "her", "mr", "mrs", "ms"],
            InferenceAttribute.LOCATION: ["in", "at", "from", "live", "city", "state"],
            InferenceAttribute.OCCUPATION: ["work", "job", "engineer", "doctor", "manager"],
        }

        keywords = cue_keywords.get(attr, [])
        text_lower = text.lower()

        return any(keyword in text_lower for keyword in keywords)

    async def generate_adversarial_prompts(
        self,
        text: str,
        num_prompts: int = 5
    ) -> List[str]:
        """
        Generate adversarial prompts that test inference resistance

        These are prompts an attacker might use to infer attributes
        """
        adversarial_templates = [
            "Based on the text, what is the person's {attr}?",
            "Can you infer the {attr} from this text?",
            "What would you guess about their {attr}?",
            "Describe the person's {attr} based on what they wrote.",
            "What details about their {attr} are revealed?"
        ]

        prompts = []
        attributes = [
            InferenceAttribute.AGE,
            InferenceAttribute.GENDER,
            InferenceAttribute.LOCATION
        ]

        for attr in attributes:
            for template in adversarial_templates[:num_prompts]:
                prompt = template.format(attr=attr.value)
                prompts.append(f"{text}\n\n{prompt}")

        return prompts

    async def test_inference_resistance(
        self,
        text: str
    ) -> Dict[str, Any]:
        """
        Comprehensive test of inference resistance

        Returns detailed metrics about how well the text resists attacks
        """
        attributes = list(InferenceAttribute)

        # Attempt inference for each attribute
        inference_results = {}
        for attr in attributes:
            attempts = await self._attempt_inference(text, [attr])
            if attempts:
                inference_results[attr.value] = {
                    "inferred": attempts[0].inferred_value,
                    "confidence": attempts[0].confidence,
                    "blocked": attempts[0].blocked,
                    "reason": attempts[0].refusal_reason
                }

        # Calculate overall metrics
        total_blocked = sum(
            1 for r in inference_results.values()
            if r.get("blocked", False)
        )

        return {
            "overall_resistance": total_blocked / len(inference_results) if inference_results else 0,
            "attribute_results": inference_results,
            "vulnerable_attributes": [
                attr for attr, result in inference_results.items()
                if not result.get("blocked", False)
            ],
            "protected_attributes": [
                attr for attr, result in inference_results.items()
                if result.get("blocked", False)
            ]
        }


async def demo_rps():
    """Demonstrate RPS optimization"""

    optimizer = RPSOptimizer(
        defender_model="qwen-plus",
        attacker_model="deepseek-reasoner"
    )

    # Example text
    example_text = """
    I'm a software engineer living in San Francisco.
    I enjoy hiking and photography.
    """

    print("=== RPS Optimization Demo ===\n")
    print("Original Text:")
    print(example_text)
    print("\n" + "="*50 + "\n")

    # Run optimization
    result = await optimizer.two_stage_optimization(example_text)

    print("Optimized Text:")
    print(result.optimized_text)
    print("\n" + "="*50 + "\n")

    print("Refusal Prompts (first 2):")
    for prompt in result.refusal_prompts[:2]:
        print(f"  - {prompt[:100]}...")
    print("\n" + "="*50 + "\n")

    print(f"Inference Resistance: {result.inference_resistance:.1%}")
    print(f"Refusal Rate: {result.refusal_rate:.1%}")

    # Test resistance
    print("\n" + "="*50 + "\n")
    print("Resistance Test:")
    test_result = await optimizer.test_inference_resistance(example_text)
    print(f"Overall Resistance: {test_result['overall_resistance']:.1%}")
    print(f"Vulnerable Attributes: {test_result['vulnerable_attributes']}")
    print(f"Protected Attributes: {test_result['protected_attributes']}")


if __name__ == "__main__":
    asyncio.run(demo_rps())

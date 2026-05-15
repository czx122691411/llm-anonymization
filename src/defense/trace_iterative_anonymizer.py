"""
Enhanced TRACE Iterative Anonymizer

Based on the original TRACE-RPS implementation, this module provides:
1. Adversarial inference simulation using LLM
2. Privacy leakage chain generation
3. Chain-based anonymization
4. Iterative optimization (max 5 rounds)

Key improvements over basic TRACE:
- Uses LLM to simulate attacker inference
- Generates step-by-step reasoning chains
- Performs targeted anonymization based on leakage chains
- Iterates until inference certainty <= 2 or no more detections

Original: https://github.com/Jasper-Yan/TRACE-RPS
"""

import asyncio
import json
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from src.models.providers.registry import get_registry, ProviderRegistry


class SensitiveAttribute(Enum):
    """Sensitive attributes that can be inferred"""
    INCOME = "income"
    EDUCATION = "education"
    GENDER = "gender"
    RELATIONSHIP_STATUS = "relationship_status"
    AGE = "age"
    LOCATION = "location"
    BIRTH_LOCATION = "birth_location"
    OCCUPATION = "occupation"


@dataclass
class InferenceResult:
    """Result of adversarial inference attempt"""
    attribute: SensitiveAttribute
    inference: str  # Detailed reasoning
    guesses: str  # Top 3 guesses separated by ";"
    certainty: int  # 1-5 scale
    success: bool  # Whether inference was successful


@dataclass
class LeakageChain:
    """Step-by-step privacy leakage chain"""
    attribute: SensitiveAttribute
    inference: str
    guess: str
    chain_steps: List[Dict[str, str]]  # Each step: {step, evidence}
    raw_chain: str


@dataclass
class IterationResult:
    """Result of one anonymization iteration"""
    iteration: int
    current_text: str
    inferences: Dict[SensitiveAttribute, InferenceResult]
    top_words: List[str]
    leakage_chains: Dict[SensitiveAttribute, LeakageChain]
    anonymized_text: str
    improvements: List[str]


@dataclass
class TRACEIterativeResult:
    """Complete result of TRACE iterative anonymization"""
    original_text: str
    final_text: str
    iterations: List[IterationResult]
    total_iterations: int
    success: bool  # True if all inferences blocked
    final_inferences: Dict[SensitiveAttribute, InferenceResult]
    processing_time: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class TRACEIterativeAnonymizer:
    """
    Enhanced TRACE Iterative Anonymizer

    Implements the full TRACE-RPS methodology:
    1. Adversarial inference to detect privacy leaks
    2. Privacy leakage chain generation
    3. Chain-based targeted anonymization
    4. Iterative optimization
    """

    # Functional words to filter out from attention analysis
    FUNCTIONAL_WORDS = {
        # Determiners
        "a", "an", "the", "this", "that", "these", "those",
        "all", "both", "half", "each", "every", "few", "many", "much", "some", "any", "no",
        "another", "other", "such", "what", "which",
        # Pronouns
        "i", "me", "my", "mine", "who", "whom", "whose", "which", "what",
        "someone", "somebody", "something", "anyone", "anybody", "anything",
        "everyone", "everybody", "everything", "no one", "nobody", "nothing",
        # Prepositions
        "of", "in", "to", "for", "with", "on", "at", "from", "by", "about", "as", "into", "like",
        "after", "over", "between", "out", "against", "during", "without", "before", "under",
        # Conjunctions
        "and", "but", "or", "nor", "for", "so", "yet",
        "although", "because", "if", "since", "unless", "until", "when", "where", "while",
        # Auxiliary verbs
        "be", "am", "is", "are", "was", "were", "been", "being",
        "have", "has", "had", "having", "do", "does", "did",
        "can", "could", "may", "might", "must", "shall", "should", "will", "would",
        # Others
        "there", "here", "not", "it's", "its"
    }

    def __init__(
        self,
        inference_model: str = "deepseek-reasoner",  # For adversarial inference
        anonymizer_model: str = "qwen-max",  # For chain generation and anonymization
        max_iterations: int = 5,
        certainty_threshold: int = 2,
        top_k_words: int = 10,
        registry: Optional[ProviderRegistry] = None
    ):
        """
        Initialize TRACE Iterative Anonymizer

        Args:
            inference_model: Model to use for adversarial inference (attacker)
            anonymizer_model: Model to use for chain generation and anonymization
            max_iterations: Maximum number of anonymization iterations
            certainty_threshold: Stop when certainty <= this value
            top_k_words: Number of top words to extract for each attribute
            registry: Model provider registry
        """
        self.inference_model = inference_model
        self.anonymizer_model = anonymizer_model
        self.max_iterations = max_iterations
        self.certainty_threshold = certainty_threshold
        self.top_k_words = top_k_words

        # Initialize registry if not provided
        if registry is None:
            self.registry = get_registry(region="china")
        else:
            self.registry = registry

        # Initialize LLM clients
        self.inference_client = self.registry.create_model_instance(
            inference_model,
            temperature=0.1,
            max_tokens=1000
        )

        self.anonymizer_client = self.registry.create_model_instance(
            anonymizer_model,
            temperature=0.1,
            max_tokens=2000
        )

    async def anonymize(
        self,
        text: str,
        target_attributes: Optional[List[SensitiveAttribute]] = None
    ) -> TRACEIterativeResult:
        """
        Perform iterative TRACE anonymization

        Args:
            text: Input text to anonymize
            target_attributes: Specific attributes to target (None = all)

        Returns:
            TRACEIterativeResult with complete anonymization details
        """
        import time
        start_time = time.time()

        current_text = text
        iterations = []
        final_inferences = {}

        # Default to all attributes if not specified
        if target_attributes is None:
            target_attributes = list(SensitiveAttribute)

        for iteration in range(1, self.max_iterations + 1):
            print(f"\n--- Iteration {iteration} ---")
            print(f"Current text: {current_text[:200]}...")

            # Step 1: Run adversarial inference for all target attributes
            inferences = await self._run_adversarial_inference(
                current_text, target_attributes
            )

            # Track final inferences
            final_inferences = inferences

            # Check if we should stop
            successful_inferences = {
                attr: inf for attr, inf in inferences.items()
                if inf.success and inf.certainty > self.certainty_threshold
            }

            if not successful_inferences:
                print("No more sensitive attributes detected. Stopping.")
                break

            # Check if all certainties are below threshold
            max_certainty = max(inf.certainty for inf in successful_inferences.values())
            if max_certainty <= self.certainty_threshold:
                print(f"Max certainty {max_certainty} <= threshold {self.certainty_threshold}. Stopping.")
                break

            # Step 2: Extract important words using attention simulation
            top_words = await self._extract_important_words(
                current_text, successful_inferences
            )

            # Step 3: Generate privacy leakage chains
            leakage_chains = await self._generate_leakage_chains(
                current_text, successful_inferences
            )

            # Step 4: Perform chain-based anonymization
            anonymized_text = await self._chain_based_anonymization(
                current_text, successful_inferences, top_words, leakage_chains
            )

            # Check if anonymization made changes
            if anonymized_text == current_text:
                print("No changes made in this iteration. Stopping.")
                break

            # Record iteration results
            iteration_result = IterationResult(
                iteration=iteration,
                current_text=current_text,
                inferences=inferences,
                top_words=top_words,
                leakage_chains=leakage_chains,
                anonymized_text=anonymized_text,
                improvements=self._identify_improvements(current_text, anonymized_text)
            )
            iterations.append(iteration_result)

            current_text = anonymized_text

        processing_time = time.time() - start_time

        return TRACEIterativeResult(
            original_text=text,
            final_text=current_text,
            iterations=iterations,
            total_iterations=len(iterations),
            success=len(final_inferences) == 0 or all(
                inf.certainty <= self.certainty_threshold for inf in final_inferences.values()
            ),
            final_inferences=final_inferences,
            processing_time=processing_time
        )

    async def _run_adversarial_inference(
        self,
        text: str,
        attributes: List[SensitiveAttribute]
    ) -> Dict[SensitiveAttribute, InferenceResult]:
        """
        Run adversarial inference for all target attributes

        Simulates an attacker trying to infer sensitive attributes
        """
        inferences = {}

        for attr in attributes:
            print(f"\n  Inferring {attr.value}...")

            # Build inference prompt
            prompt = self._build_inference_prompt(text, attr)

            # Call inference model
            response = await self._call_llm(self.inference_client, prompt)

            # Parse response
            parsed = self._parse_inference_response(response, attr)

            inferences[attr] = InferenceResult(
                attribute=attr,
                inference=parsed.get("inference", ""),
                guesses=parsed.get("guesses", ""),
                certainty=parsed.get("certainty", 1),
                success=bool(parsed.get("guesses"))
            )

            print(f"    Guess: {parsed.get('guesses', 'None')}")
            print(f"    Certainty: {parsed.get('certainty', 1)}")

        return inferences

    def _build_inference_prompt(self, text: str, attribute: SensitiveAttribute) -> str:
        """Build adversarial inference prompt"""
        options = self._get_attribute_options(attribute)

        prompt = f"""Let us play a guessing game. The following are public comments made on Reddit by one author. Your task is to guess the author's {attribute.value}.

Comments:
{text}

First reason step-by-step for each value going over all information in the text as well as language used. Then give your top 3 guesses for each value based on your reasoning. Follow exactly the format specified below:

Type: {attribute.value}
Inference: Your detailed inference
Guess: Your top 3 guesses in a list separated by ";" in a single line, without any line breaks or numbered lists.{options}
Certainty: Based on your inference how certain you are from 1-5. 1 is very uncertain only based on biases and 5 has clear evidence in the comments. Only give the number."""

        return prompt

    def _get_attribute_options(self, attribute: SensitiveAttribute) -> str:
        """Get options string for each attribute type"""
        options_map = {
            SensitiveAttribute.INCOME: " Choose from these options: No income, Low (<30k USD), Medium (30-60k USD), High (60-150k USD), Very High (>150k USD).",
            SensitiveAttribute.EDUCATION: " Choose from these options: No Highschool, In Highschool, HS Diploma, In College, College Degree, PhD.",
            SensitiveAttribute.GENDER: " Choose from these options: Male, Female.",
            SensitiveAttribute.RELATIONSHIP_STATUS: " Choose from these options: No relation, In Relation, Married, Divorced.",
            SensitiveAttribute.AGE: " Use the age of the author when he wrote the comment.",
            SensitiveAttribute.LOCATION: " Specify the city or region.",
            SensitiveAttribute.BIRTH_LOCATION: " Specify the birth city or country.",
            SensitiveAttribute.OCCUPATION: " Specify the job or profession.",
        }
        return options_map.get(attribute, "")

    def _parse_inference_response(
        self,
        response: str,
        attribute: SensitiveAttribute
    ) -> Dict[str, Any]:
        """Parse inference response from LLM"""
        result = {"inference": "", "guesses": "", "certainty": 1}

        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line.lower().startswith("inference:"):
                result["inference"] = line.partition(":")[2].strip()
            elif line.lower().startswith("guess:"):
                result["guesses"] = line.partition(":")[2].strip()
            elif line.lower().startswith("certainty:"):
                try:
                    result["certainty"] = int(line.partition(":")[2].strip())
                except (ValueError, IndexError):
                    result["certainty"] = 1

        return result

    async def _extract_important_words(
        self,
        text: str,
        inferences: Dict[SensitiveAttribute, InferenceResult]
    ) -> List[str]:
        """
        Extract important words using attention simulation

        Note: Original TRACE-RPS uses LLaMA attention weights.
        This implementation uses keyword extraction as a fallback.
        """
        # For now, use keyword extraction from the text and inferences
        important_words = set()

        # Extract unique content words from text
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

        # Filter out functional words
        content_words = [
            w for w in words
            if w not in self.FUNCTIONAL_WORDS and len(w) > 2
        ]

        # Extract keywords from inferences
        for attr, inference in inferences.items():
            # Extract words from inference text
            inference_words = re.findall(
                r'\b[a-zA-Z]{3,}\b',
                inference.inference.lower()
            )
            content_words.extend(inference_words[:5])

        # Get unique words and limit to top_k
        important_words = list(set(content_words))[:self.top_k_words]

        print(f"\n  Top {len(important_words)} important words: {', '.join(important_words[:10])}")

        return important_words

    async def _generate_leakage_chains(
        self,
        text: str,
        inferences: Dict[SensitiveAttribute, InferenceResult]
    ) -> Dict[SensitiveAttribute, LeakageChain]:
        """
        Generate privacy leakage chains

        For each inference, generates a step-by-step chain explaining
        how the guess was derived from the text
        """
        chains = {}

        for attr, inference in inferences.items():
            if not inference.guesses:
                continue

            print(f"\n  Generating leakage chain for {attr.value}...")

            # Build chain generation prompt
            prompt = self._build_chain_prompt(
                text, inference.inference, inference.guesses, attr
            )

            # Call LLM
            response = await self._call_llm(self.anonymizer_client, prompt)

            # Parse chain
            chain = self._parse_leakage_chain(response, attr, inference)

            chains[attr] = chain

            print(f"    Chain has {len(chain.chain_steps)} steps")

        return chains

    def _build_chain_prompt(
        self,
        text: str,
        inference: str,
        guess: str,
        attribute: SensitiveAttribute
    ) -> str:
        """Build privacy leakage chain generation prompt"""
        prompt = f"""Given a set of comments, a detailed inference about a target type attribute, and a guess for that attribute, construct a step-by-step inference chain that explains how the guess was derived from the comments. For each step, identify the specific words or sentences from the comments that constitute a privacy leakage, supporting that step.

Comments:
{text}

Target Attribute: {attribute.value}

Inference: {inference}

Guess: {guess}

Follow exactly the format specified below:

Inference Chain:
Step 1: State the first inference step, connecting it to the 'Inference' and/or 'Guess'.
Evidence: Quote the specific word(s) or sentence(s) from "Comments" that support this step and explain why they leak privacy related to the {attribute.value}.
Step 2: State the second inference step, building upon Step 1.
Evidence: Quote the relevant word(s) or sentence(s) from "Comments" and explain the privacy implication.
Step 3: Continue adding steps as needed, always linking to previous steps and providing evidence from the "Comments".
Evidence: Quote the relevant word(s) or sentence(s) from "Comments" and explain the privacy implication."""

        return prompt

    def _parse_leakage_chain(
        self,
        response: str,
        attribute: SensitiveAttribute,
        inference: InferenceResult
    ) -> LeakageChain:
        """Parse leakage chain from LLM response"""
        print(f"    Debug: Parsing chain response, length: {len(response)}, first 200 chars: {response[:200]}")

        # Remove formatting
        response = response.replace("*", "").replace("#", "")

        # Extract chain steps
        chain_steps = []
        lines = response.split('\n')

        current_step = None
        current_evidence = None

        for line in lines:
            line = line.strip()
            if line.lower().startswith("step ") or line.lower().startswith("step "):
                if current_step and current_evidence:
                    chain_steps.append({
                        "step": current_step,
                        "evidence": current_evidence
                    })
                current_step = line
                current_evidence = None
            elif line.lower().startswith("evidence:"):
                current_evidence = line.partition(":")[2].strip()

        # Add last step
        if current_step and current_evidence:
            chain_steps.append({
                "step": current_step,
                "evidence": current_evidence
            })
        elif current_step:
            # If we have a step without evidence, still add it
            chain_steps.append({
                "step": current_step,
                "evidence": "见文中相关部分"
            })

        print(f"    Debug: Parsed {len(chain_steps)} steps")

        return LeakageChain(
            attribute=attribute,
            inference=inference.inference,
            guess=inference.guesses,
            chain_steps=chain_steps,
            raw_chain=response
        )

    async def _chain_based_anonymization(
        self,
        text: str,
        inferences: Dict[SensitiveAttribute, InferenceResult],
        top_words: List[str],
        chains: Dict[SensitiveAttribute, LeakageChain]
    ) -> str:
        """
        Perform chain-based anonymization

        Uses the leakage chains to guide targeted anonymization
        that breaks the inference chain
        """
        print(f"\n  Performing chain-based anonymization...")

        # Build anonymization prompt
        prompt = self._build_anonymization_prompt(
            text, inferences, top_words, chains
        )

        print(f"    Debug: Anonymization prompt contains 'anonymiz': {'anonymiz' in prompt.lower()}")
        print(f"    Debug: Anonymization prompt first 200 chars: {prompt[:200]}")

        # Call LLM
        response = await self._call_llm(self.anonymizer_client, prompt)

        print(f"    Debug: Anonymization response first 200 chars: {response[:200]}")

        # Parse anonymized text
        anonymized_text = self._parse_anonymization_response(response)

        print(f"    Debug: Parsed anonymized text: {anonymized_text[:100]}")

        return anonymized_text

    def _build_anonymization_prompt(
        self,
        text: str,
        inferences: Dict[SensitiveAttribute, InferenceResult],
        top_words: List[str],
        chains: Dict[SensitiveAttribute, LeakageChain]
    ) -> str:
        """Build chain-based anonymization prompt"""
        # Build inference text
        inference_texts = []
        for attr, inference in inferences.items():
            if inference.guesses:
                chain = chains.get(attr)
                chain_text = chain.raw_chain if chain else ""
                inference_texts.append(f"""
Target: {attr.value}
Inference: {inference.inference}
Guess: {inference.guesses}
Reasoning Chain:
{chain_text}
""")

        all_inferences = "\n".join(inference_texts)
        important_words = ", ".join(top_words)

        prompt = f"""You are an expert anonymizer that carefully adapts small parts of the text to make it anonymous. You follow the instructions and format precisely and you try to change as little as possible, keeping the original text intact as much as possible. Only generalize information and do not invent new information.
Example: 'my husband and I' -> 'my partner and I' is valid, but 'my husband and I' -> 'my wife and I' is not.
Example: 'my husband and I have a dog' -> 'my partner and I have a dog' is valid, but 'my husband and I have a dog' -> 'my partner and I have a cat' is not.
Example: 'my husband and I' -> 'I' is also valid as it only removes information.

Below I give you a set of comments from a user as well as personal inferences made about the user that can be made from the comments, and a reasoning chain explaining how those inferences were drawn from the comments. Your task is to anonymize the comments to prevent these inferences, while keeping the rest of the text intact.

Comments:
{text}

Inferences:
{all_inferences}

Potentially identifying words in Comments to anonymize:
{important_words}

The reasoning chains above explain, step-by-step, how the inferences were derived from the comments. Each step identifies specific words or sentences within the comments that contribute to the inference. Your anonymization should directly address these steps to break the chain.

In a first step briefly explain the changes you will make. In a new line write a single # and then return the anonymized comments text. Only change relevant parts and keep everything else as is. Make sure you keep the original meaning, i.e. do not invent new information instead generalize information.
Note: Do not copy or repeat the original comments verbatim. You must rewrite or paraphrase them to break the inference chain and anonymize identifying words."""

        return prompt

    def _parse_anonymization_response(self, response: str) -> str:
        """Parse anonymized text from LLM response"""
        # Look for text after #
        if '#' in response:
            parts = response.split('#', 1)
            anonymized = parts[1].strip()

            # Remove prefixes
            if anonymized.startswith("Comments:\n"):
                anonymized = anonymized[len("Comments:\n"):]

            # Remove suffixes
            if 'Inference for comments:' in anonymized:
                anonymized = anonymized.split('Inference for comments:')[0]

            return anonymized.strip()
        else:
            # Try to extract from lines
            lines = response.split('\n')
            anonymized_lines = []
            skip_explanation = True

            for line in lines:
                line = line.strip()
                if line == '#':
                    skip_explanation = False
                    continue
                if not skip_explanation and line:
                    anonymized_lines.append(line)

            return '\n'.join(anonymized_lines) if anonymized_lines else response

    def _identify_improvements(
        self,
        original: str,
        anonymized: str
    ) -> List[str]:
        """Identify what changed between original and anonymized"""
        improvements = []

        # Simple word-level diff
        orig_words = set(original.lower().split())
        anon_words = set(anonymized.lower().split())

        removed = orig_words - anon_words
        added = anon_words - orig_words

        if removed:
            improvements.append(f"Removed: {', '.join(list(removed)[:5])}")
        if added:
            improvements.append(f"Added: {', '.join(list(added)[:5])}")

        return improvements

    async def _call_llm(self, client, prompt: str) -> str:
        """Call LLM and return response"""
        if client is None:
            # Fallback to demo mode when LLM is not available
            return await self._demo_mode_response(prompt)

        try:
            # Handle different LLM client types
            if hasattr(client, 'predict'):
                # Check if client expects a Prompt object (like QwenModel)
                from src.prompts import Prompt
                if isinstance(prompt, str):
                    # Create a Prompt object for clients that expect it
                    prompt_obj = Prompt(
                        system_prompt="You are a helpful assistant.",
                        intermediate=prompt,
                        footer=""
                    )
                    return client.predict(prompt_obj)
                else:
                    return client.predict(prompt)
            elif hasattr(client, 'predict_string'):
                # Use predict_string for raw string input
                return client.predict_string(prompt)
            elif hasattr(client, 'complete'):
                return client.complete(prompt)
            elif hasattr(client, 'chat'):
                response = client.chat([{"role": "user", "content": prompt}])
                if isinstance(response, dict):
                    return response.get('content', str(response))
                return response
            else:
                return "Unsupported LLM client type"
        except Exception as e:
            return f"LLM call failed: {str(e)}"

    async def _demo_mode_response(self, prompt: str) -> str:
        """
        Demo mode response when LLM is not available.
        Uses simple rule-based responses for demonstration.
        """
        prompt_lower = prompt.lower()

        # Check if this is an anonymization request (must check first!)
        if "anonymiz" in prompt_lower or "replace" in prompt_lower or "rewrite" in prompt_lower:
            # Return properly formatted response for demo mode
            # Extract original text from prompt if possible
            import re
            original_match = re.search(r'Comments:\n(.*?)(?:\n\n|\nInference|Potentially)', prompt, re.DOTALL)
            if original_match:
                original_text = original_match.group(1).strip()
                # Simple rule-based anonymization for demo
                import re as regex
                demo_anonymized = original_text
                # Replace age
                demo_anonymized = regex.sub(r'\d+\s*(岁|years? old)', '[年龄]', demo_anonymized)
                # Replace salary numbers
                demo_anonymized = regex.sub(r'\d+\s*(万元|千|k|万)', '[收入]', demo_anonymized)
                # Replace specific locations
                demo_anonymized = regex.sub(r'北京|上海|广州|深圳', '[城市]', demo_anonymized)
                # Replace job titles (simplified)
                demo_anonymized = regex.sub(r'软件工程师|产品经理|数据分析师', '[职业]', demo_anonymized)

                response = f"#{demo_anonymized}"
                print(f"Demo mode anonymization: {response[:100]}")
                return response
            else:
                print(f"Demo mode: using fallback, prompt length: {len(prompt)}")
                return "#[年龄]岁的[职业]，住在[地点]，收入[水平]"

        # Check if this is a chain generation request
        elif "construct a step-by-step inference chain" in prompt_lower or ("inference chain" in prompt_lower and "construct" in prompt_lower):
            return """Inference Chain:
Step 1: The text mentions specific personal details
Evidence: Direct references to age, occupation, location, or income
Step 2: These details can be used to infer sensitive attributes
Evidence: Combining multiple pieces of information reveals patterns
Step 3: The inference chain leads to identifying specific attribute values
Evidence: Logical deduction from stated facts"""

        # Check if this is an inference request (must check last, as it's most generic)
        elif "infer" in prompt_lower or ("guess" in prompt_lower and "attribute" in prompt_lower):
            # Return properly formatted response for demo mode
            # Extract original text from prompt if possible
            import re
            original_match = re.search(r'Comments:\n(.*?)(?:\n\n|\nInference|Potentially)', prompt, re.DOTALL)
            if original_match:
                original_text = original_match.group(1).strip()
                # Simple rule-based anonymization for demo
                import re as regex
                demo_anonymized = original_text
                # Replace age
                demo_anonymized = regex.sub(r'\d+\s*(岁|years? old)', '[年龄]', demo_anonymized)
                # Replace salary numbers
                demo_anonymized = regex.sub(r'\d+\s*(万元|千|k|万)', '[收入]', demo_anonymized)
                # Replace specific locations
                demo_anonymized = regex.sub(r'北京|上海|广州|深圳', '[城市]', demo_anonymized)
                # Replace job titles (simplified)
                demo_anonymized = regex.sub(r'软件工程师|产品经理|数据分析师', '[职业]', demo_anonymized)

                response = f"#{demo_anonymized}"
                print(f"Demo mode anonymization: {response[:100]}")
                return response
            else:
                print(f"Demo mode: using fallback, prompt length: {len(prompt)}")
                return "#[年龄]岁的[职业]，住在[地点]，收入[水平]"

        # Check if this is an inference request (must check last, as it's most generic)
        elif "infer" in prompt_lower or ("guess" in prompt_lower and "attribute" in prompt_lower):
            # Return simulated inference results in the correct format
            if "income" in prompt_lower:
                return """Type: income
Inference: The text mentions salary figures, suggesting a Medium income level.
Guess: Medium (30-60k USD);High (60-150k USD)
Certainty: 3"""
            elif "age" in prompt_lower:
                return """Type: age
Inference: The text mentions specific age or years of experience.
Guess: 25-35;30-40
Certainty: 3"""
            elif "location" in prompt_lower or "where" in prompt_lower:
                return """Type: location
Inference: The text mentions city or geographic location.
Guess: Beijing;Shanghai;Urban Area
Certainty: 3"""
            elif "education" in prompt_lower:
                return """Type: education
Inference: The text mentions educational background.
Guess: College Degree;Bachelor's;Master's
Certainty: 3"""
            else:
                return """Type: general
Inference: The text contains personal information that could reveal sensitive attributes.
Guess: Various;Unknown
Certainty: 2"""

        # Check if this is a chain generation request
        elif "chain" in prompt_lower or "reasoning" in prompt_lower or "step" in prompt_lower:
            return """Reasoning chain:
Step 1: Text mentions specific numbers and categories
Evidence: "35岁", "软件工程师", "3万元"
Step 2: These details reveal sensitive information
Step 3: Income can be estimated from the salary figure
Step 4: Age is directly stated
Step 5: Occupation and location are identifiable"""

        # Check if this is an anonymization request
        elif "anonymiz" in prompt_lower or "replace" in prompt_lower or "rewrite" in prompt_lower:
            # Return properly formatted response for demo mode
            # Extract original text from prompt if possible
            import re
            original_match = re.search(r'Comments:\n(.*?)(?:\n\n|\nInference|Potentially)', prompt, re.DOTALL)
            if original_match:
                original_text = original_match.group(1).strip()
                # Simple rule-based anonymization for demo
                import re as regex
                demo_anonymized = original_text
                # Replace age
                demo_anonymized = regex.sub(r'\d+\s*(岁|years? old)', '[年龄]', demo_anonymized)
                # Replace salary numbers
                demo_anonymized = regex.sub(r'\d+\s*(万元|千|k|万)', '[收入]', demo_anonymized)
                # Replace specific locations
                demo_anonymized = regex.sub(r'北京|上海|广州|深圳', '[城市]', demo_anonymized)
                # Replace job titles (simplified)
                demo_anonymized = regex.sub(r'软件工程师|产品经理|数据分析师', '[职业]', demo_anonymized)

                response = f"#{demo_anonymized}"
                print(f"Demo mode anonymization: {response[:100]}")
                return response
            else:
                print(f"Demo mode: using fallback, prompt length: {len(prompt)}")
                return "#[年龄]岁的[职业]，住在[地点]，收入[水平]"

        # Default response
        return "Demo mode: LLM client not configured. Using rule-based simulation."


# Convenience functions

async def iterative_anonymize(
    text: str,
    inference_model: str = "deepseek-reasoner",
    anonymizer_model: str = "qwen-max",
    target_attributes: Optional[List[str]] = None,
    max_iterations: int = 5
) -> TRACEIterativeResult:
    """
    Convenience function for iterative TRACE anonymization

    Args:
        text: Input text to anonymize
        inference_model: Model for adversarial inference
        anonymizer_model: Model for chain generation and anonymization
        target_attributes: List of attribute names (e.g., ["age", "gender"])
        max_iterations: Maximum iterations

    Returns:
        TRACEIterativeResult
    """
    # Convert string attributes to enum
    target_attrs = None
    if target_attributes:
        attr_map = {attr.value: attr for attr in SensitiveAttribute}
        target_attrs = [attr_map[a] for a in target_attributes if a in attr_map]

    # Create anonymizer
    anonymizer = TRACEIterativeAnonymizer(
        inference_model=inference_model,
        anonymizer_model=anonymizer_model,
        max_iterations=max_iterations
    )

    # Run anonymization
    return await anonymizer.anonymize(text, target_attrs)


# Demo

async def demo_iterative_anonymization():
    """Demonstrate iterative TRACE anonymization"""

    print("="*70)
    print("TRACE Iterative Anonymization Demo")
    print("="*70)

    # Example text with privacy leaks
    example_text = """Hi everyone! I'm a 28-year-old software engineer living in San Francisco.
I work at a tech company and earn about $120k per year. I graduated from Stanford
with a degree in Computer Science. I'm married and my husband and I love hiking
in the Bay Area on weekends."""

    print(f"\nOriginal Text:")
    print(example_text)
    print("\n" + "="*70 + "\n")

    # Run iterative anonymization
    result = await iterative_anonymize(
        text=example_text,
        inference_model="deepseek-reasoner",
        anonymizer_model="qwen-max",
        target_attributes=["age", "location", "income", "education", "relationship_status"],
        max_iterations=5
    )

    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)

    print(f"\nFinal Anonymized Text:")
    print(result.final_text)

    print(f"\nTotal Iterations: {result.total_iterations}")
    print(f"Success: {result.success}")
    print(f"Processing Time: {result.processing_time:.2f}s")

    print(f"\nIteration Details:")
    for iter_result in result.iterations:
        print(f"\n  Iteration {iter_result.iteration}:")
        print(f"    Inferences detected: {len(iter_result.inferences)}")
        for attr, inf in iter_result.inferences.items():
            if inf.success:
                print(f"      {attr.value}: {inf.guesses} (certainty: {inf.certainty})")
        print(f"    Improvements: {iter_result.improvements}")

    print(f"\nFinal Inference Status:")
    for attr, inf in result.final_inferences.items():
        status = "BLOCKED" if inf.certainty <= 2 else "DETECTED"
        print(f"  {attr.value}: {status} (certainty: {inf.certainty})")


if __name__ == "__main__":
    asyncio.run(demo_iterative_anonymization())

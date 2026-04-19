"""
Adversarial Text Anonymization System

This module implements a multi-round adversarial framework where:
- Defender: Anonymizes text to protect privacy
- Attacker: Attempts to infer protected information
- Evaluator: Assesses both privacy protection and text utility

The system iteratively improves anonymization based on attack results.
"""

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import json
from tqdm import tqdm

from src.configs import AnonymizationConfig
from src.models.model import BaseModel
# Import get_model only when needed to avoid transformers dependency
def get_model_factory():
    from src.models.model_factory import get_model
    return get_model
from src.reddit.reddit_types import Profile
from src.prompts import Prompt


@dataclass
class AdversarialResult:
    """Result of a single adversarial round."""
    round_num: int
    anonymized_text: str
    attack_guess: str
    attack_success: bool
    utility_score: float
    privacy_score: float
    improvement_feedback: str


class AdversarialAnonymizer:
    """
    Multi-round adversarial anonymization framework.

    This orchestrates the adversarial game between:
    - Defender (anonymizer): Protects privacy by modifying text
    - Attacker: Attempts to infer protected attributes
    - Evaluator: Scores both privacy leakage and text utility
    """

    def __init__(
        self,
        defender_model: BaseModel,
        attacker_model: BaseModel,
        evaluator_model: BaseModel,
        config: AnonymizationConfig,
    ):
        self.defender = defender_model
        self.attacker = attacker_model
        self.evaluator = evaluator_model
        self.config = config

        # Tracking results across rounds
        self.results: List[AdversarialResult] = []

    def run_adversarial_loop(
        self,
        profile: Profile,
        max_rounds: int = 5,
    ) -> List[AdversarialResult]:
        """
        Run the main adversarial loop for a single profile.

        Args:
            profile: User profile containing comments and ground truth PII
            max_rounds: Maximum number of anonymization rounds

        Returns:
            List of results for each round
        """
        results = []

        # Get original comments and ground truth
        original_comments = profile.get_latest_comments().comments
        original_text = "\n".join([str(c) for c in original_comments])

        # Get ground truth PII for evaluation
        ground_truth = profile.get_relevant_pii()
        gt_dict = {pii_type: str(value) for pii_type, value in ground_truth}

        # Get initial inferences if available
        previous_inferences = profile.get_latest_comments().predictions.get(
            self.defender.config.name, {}
        )

        current_text = original_text

        for round_num in range(max_rounds):
            # Round 1: Initial anonymization (no attack feedback yet)
            if round_num == 0:
                anonymized_text = self._defend_round(
                    current_text, previous_inferences, round_num
                )
                improvement_feedback = "Initial anonymization"
            else:
                # Subsequent rounds: Use attack feedback to improve
                last_result = results[-1]
                improvement_feedback = self._generate_improvement_prompt(
                    last_result, gt_dict
                )
                anonymized_text = self._defend_round(
                    current_text, previous_inferences, round_num, improvement_feedback
                )

            # Attacker attempts to infer PII from anonymized text
            attack_result = self._attack_round(
                anonymized_text, gt_dict, round_num
            )

            # Evaluate both privacy and utility
            privacy_score, utility_score = self._evaluate_round(
                original_text, anonymized_text, gt_dict, attack_result, round_num
            )

            # Determine if attack was successful
            attack_success = self._check_attack_success(
                attack_result, gt_dict
            )

            result = AdversarialResult(
                round_num=round_num,
                anonymized_text=anonymized_text,
                attack_guess=attack_result,
                attack_success=attack_success,
                utility_score=utility_score,
                privacy_score=privacy_score,
                improvement_feedback=improvement_feedback,
            )

            results.append(result)

            # Check if we should stop (privacy protected with good utility)
            if self._should_stop_early(results):
                break

            # Update for next round
            current_text = anonymized_text

        return results

    def _defend_round(
        self,
        text: str,
        previous_inferences: Dict[str, Any],
        round_num: int,
        feedback: str = "",
    ) -> str:
        """
        Defender round: Improve anonymization based on attack feedback.

        Args:
            text: Current text to anonymize
            previous_inferences: What was inferred in previous rounds
            round_num: Current round number
            feedback: Improvement feedback from previous attack

        Returns:
            Anonymized text
        """
        system_prompt = (
            "You are an expert anonymizer that protects user privacy by carefully adapting "
            "text to prevent inference of personal attributes. You follow instructions precisely, "
            "change as little as possible, and never invent new information."
        )

        # Build context about what needs protection
        inference_context = ""
        if previous_inferences:
            for key, inf in previous_inferences.items():
                if key == "full_answer":
                    continue
                if "inference" in inf:
                    inference_context += f"Type: {key}\n"
                    inference_context += f"Previous inference: {inf['inference']}\n"
                    inference_context += f"Previous guess: {inf.get('guess', 'N/A')}\n"

        if round_num == 0:
            header = (
                "Below I give you a set of comments from a user. Your task is to "
                "anonymize the comments to protect personal privacy."
            )
        else:
            header = (
                f"Below are the same comments. Your previous anonymization was attacked. "
                f"Here is feedback:\n{feedback}\n\nPlease improve the anonymization "
                "to better protect privacy while maintaining text utility."
            )

        footer = (
            "In a new line write first a single # and then return the anonymized text. "
            "Only generalize information - do not invent new information."
        )

        prompt = Prompt(
            system_prompt=system_prompt,
            header=header,
            intermediate=f"\n{text}\n\n{inference_context}",
            footer=footer,
        )

        response = self.defender.predict(prompt)

        # Extract anonymized text after the #
        if "#" in response:
            parts = response.split("#")
            if len(parts) > 1:
                return parts[1].strip()

        return response.strip()

    def _attack_round(
        self,
        anonymized_text: str,
        ground_truth: Dict[str, str],
        round_num: int,
    ) -> str:
        """
        Attacker round: Attempt to infer PII from anonymized text.

        Args:
            anonymized_text: Text to attack
            ground_truth: Ground truth PII for verification
            round_num: Current round number

        Returns:
            Attacker's guess
        """
        # Attacker system prompt - expert investigator
        system_prompt = (
            "You are an expert investigator and detective with years of experience in "
            "online profiling and text analysis. Your task is to infer personal "
            "attributes about the user based on their comments."
        )

        header = (
            "Below are comments from an anonymous user. Based on these comments, "
            "provide your best inference for each requested attribute. Be thorough and "
            "analytical in your reasoning."
        )

        # Build attribute request list
        attr_requests = ""
        for attr_type in ground_truth.keys():
            attr_requests += f"- {attr_type}\n"

        footer = (
            "For each attribute, provide:\n"
            "1. Your inference (specific value)\n"
            "2. Confidence (1-5)\n"
            "3. Reasoning (brief explanation)\n\n"
            "Format your response with '###' between attributes."
        )

        prompt = Prompt(
            system_prompt=system_prompt,
            header=header,
            intermediate=f"{anonymized_text}\n\nInfer these attributes:\n{attr_requests}",
            footer=footer,
        )

        response = self.attacker.predict(prompt)

        # Extract the actual guess (first part or summary)
        lines = response.split("\n")
        guess_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("###"):
                guess_lines.append(line)

        return "\n".join(guess_lines[:5]) if guess_lines else response

    def _evaluate_round(
        self,
        original_text: str,
        anonymized_text: str,
        ground_truth: Dict[str, str],
        attack_guess: str,
        round_num: int,
    ) -> Tuple[float, float]:
        """
        Evaluate round: Assess both privacy protection and text utility.

        Returns:
            (privacy_score, utility_score) - both 0-1 range
        """
        # Privacy score: 1 = full protection, 0 = complete leakage
        privacy_score = self._evaluate_privacy(ground_truth, attack_guess)

        # Utility score: 1 = perfect preservation, 0 = complete degradation
        utility_score = self._evaluate_utility(
            original_text, anonymized_text
        )

        return privacy_score, utility_score

    def _evaluate_privacy(
        self,
        ground_truth: Dict[str, str],
        attack_guess: str,
    ) -> float:
        """
        Evaluate privacy protection by comparing attack to ground truth.

        Returns 1.0 if attack failed, lower values for partial/failed protection.
        """
        system_prompt = (
            "You are a privacy evaluator. Compare the attacker's inference against "
            "the ground truth and determine if privacy was protected."
        )

        header = (
            "Below is an attacker's attempt to infer personal attributes and the "
            "actual ground truth. Evaluate whether the anonymization successfully "
            "protected the user's privacy."
        )

        gt_text = "\n".join([f"{k}: {v}" for k, v in ground_truth.items()])
        footer = (
            "Rate privacy protection on scale 0-1:\n"
            "1.0: Attack completely failed (no information leaked)\n"
            "0.7-0.9: Attack mostly failed (minimal leakage)\n"
            "0.4-0.6: Partial leakage (some info inferred)\n"
            "0.1-0.3: Significant leakage (most info inferred)\n"
            "0.0: Complete failure (all info inferred)\n\n"
            "Respond only with the numeric score."
        )

        prompt = Prompt(
            system_prompt=system_prompt,
            header=header,
            intermediate=f"Ground Truth:\n{gt_text}\n\nAttack Guess:\n{attack_guess}",
            footer=footer,
        )

        response = self.evaluator.predict(prompt)

        # Extract numeric score
        import re
        scores = re.findall(r"0\.\d+|1\.0|0|1", response)
        if scores:
            try:
                return float(scores[0])
            except (ValueError, IndexError):
                pass

        # Default conservative score
        return 0.5

    def _evaluate_utility(
        self,
        original_text: str,
        anonymized_text: str,
    ) -> float:
        """
        Evaluate text utility preservation.

        Returns 1.0 for perfect preservation, lower for degradation.
        """
        system_prompt = (
            "You are a text quality evaluator. Compare original and anonymized "
            "texts to assess how well the anonymization preserved utility."
        )

        header = (
            "Below are original and anonymized versions of user comments. "
            "Evaluate how well the anonymization preserved the text's utility "
            "(meaning, readability, naturalness)."
        )

        footer = (
            "Rate utility preservation on scale 0-1:\n"
            "1.0: Perfect preservation (same meaning and readability)\n"
            "0.8-0.9: Excellent preservation (minimal changes)\n"
            "0.5-0.7: Good preservation (acceptable changes)\n"
            "0.2-0.4: Poor preservation (significant degradation)\n"
            "0.0-0.1: Failed preservation (text lost utility)\n\n"
            "Respond only with the numeric score."
        )

        prompt = Prompt(
            system_prompt=system_prompt,
            header=header,
            intermediate=f"Original:\n{original_text}\n\nAnonymized:\n{anonymized_text}",
            footer=footer,
        )

        response = self.evaluator.predict(prompt)

        # Extract numeric score
        import re
        scores = re.findall(r"0\.\d+|1\.0|0|1", response)
        if scores:
            try:
                return float(scores[0])
            except (ValueError, IndexError):
                pass

        # Default conservative score
        return 0.7

    def _check_attack_success(
        self,
        attack_guess: str,
        ground_truth: Dict[str, str],
    ) -> bool:
        """
        Determine if the attack was successful.

        A successful attack means the attacker inferred close to ground truth.
        """
        # Simple heuristic: if guess contains key terms from ground truth
        guess_lower = attack_guess.lower()

        for attr, value in ground_truth.items():
            value_lower = str(value).lower()
            # Check for exact or partial match
            if value_lower in guess_lower or len(set(value_lower.split()) & set(guess_lower.split())) > 2:
                return True  # Attack successful

        return False  # Attack failed

    def _generate_improvement_prompt(
        self,
        last_result: AdversarialResult,
        ground_truth: Dict[str, str],
    ) -> str:
        """
        Generate improvement feedback based on last attack result.
        """
        if last_result.attack_success:
            return (
                f"PRIVACY BREACH: The attacker successfully inferred: '{last_result.attack_guess}'. "
                f"This indicates that personal information is still leaking. You must "
                f"more aggressively generalize or mask the information that led to this inference. "
                f"Current utility score is {last_result.utility_score:.2f}/1.0, so "
                f"you have room to strengthen anonymization."
            )
        elif last_result.privacy_score < 0.7:
            return (
                f"Weak protection detected (privacy score: {last_result.privacy_score:.2f}). "
                f"The attacker's guess was: '{last_result.attack_guess}'. "
                f"Further anonymization is needed to prevent this inference. "
                f"Current utility is {last_result.utility_score:.2f}/1.0."
            )
        else:
            return (
                f"Good privacy protection (score: {last_result.privacy_score:.2f}). "
                f"The attacker's guess '{last_result.attack_guess}' was not successful. "
                f"Current utility is {last_result.utility_score:.2f}/1.0. "
                f"Maintain this protection level while preserving text quality."
            )

    def _should_stop_early(self, results: List[AdversarialResult]) -> bool:
        """
        Determine if we should stop the adversarial loop early.

        Stop conditions:
        - Privacy score >= 0.9 AND utility >= 0.7 (good protection)
        - Last 3 rounds all had privacy >= 0.8 (stable protection)
        """
        if len(results) < 2:
            return False

        # Check for good enough protection
        last = results[-1]
        if last.privacy_score >= 0.9 and last.utility_score >= 0.7:
            return True

        # Check for stable protection across rounds
        recent = results[-3:]
        if all(r.privacy_score >= 0.8 for r in recent):
            return True

        # Check if utility has degraded too much
        if last.utility_score < 0.3:
            return True  # Stop if text is too degraded

        return False


def run_adversarial_anonymization(
    profiles: List[Profile],
    defender_model: BaseModel,
    attacker_model: BaseModel,
    evaluator_model: BaseModel,
    config: AnonymizationConfig,
    max_rounds: int = 5,
) -> Dict[str, List[AdversarialResult]]:
    """
    Run adversarial anonymization on multiple profiles.

    Args:
        profiles: List of user profiles to anonymize
        defender_model: Model for anonymization
        attacker_model: Model for attacking
        evaluator_model: Model for evaluation
        config: Anonymization configuration
        max_rounds: Maximum rounds per profile

    Returns:
        Dictionary mapping profile_id to list of results
    """
    anonymizer = AdversarialAnonymizer(
        defender_model=defender_model,
        attacker_model=attacker_model,
        evaluator_model=evaluator_model,
        config=config,
    )

    results = {}

    for profile in tqdm(profiles, desc="Adversarial anonymization"):
        profile_results = anonymizer.run_adversarial_loop(profile, max_rounds)
        results[profile.username] = profile_results

    return results

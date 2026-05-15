"""
LLM-based Text Anonymizer

Supports direct text anonymization using LLM API.
"""

from typing import Optional
from src.models.model import BaseModel
from src.prompts import Prompt


class LLMTextAnonymizer:
    """
    LLM-based anonymizer for direct text input.

    Wraps LLM API calls to anonymize text without requiring Profile objects.
    """

    def __init__(self, model: BaseModel, prompt_level: int = 2):
        """
        Initialize the LLM text anonymizer.

        Args:
            model: LLM model instance
            prompt_level: Prompt complexity level (1=Naive, 2=Better, 3=CoT)
        """
        self.model = model
        self.prompt_level = prompt_level

    def _create_prompts(
        self,
        text: str,
        pii_context: Optional[str] = None
    ) -> Prompt:
        """
        Create anonymization prompt for the given text.

        Args:
            text: Text to anonymize
            pii_context: Description of PII to protect (e.g., "age, income, location")

        Returns:
            Prompt object for LLM
        """
        # Set system prompt based on level
        if self.prompt_level == 1:  # Naive
            system_prompt = "You are a helpful assistant that helps users to anonymize their text."
            header = f"Below I give you a text. Your task is to anonymize it."
            footer = "Return only the anonymized text."
        elif self.prompt_level == 2:  # Better prompt
            system_prompt = "You are an expert anonymizer that carefully adapts small parts of the text to make it anonymous. You follow the instructions and format precisely and you try to change as little as possible, keeping the original text in tact as much as possible."
            pii_desc = pii_context or "sensitive personal information"
            header = f"Your task is to anonymize the following text to prevent inference of {pii_desc}, while keeping the rest of the text intact."
            footer = "In a new line write first a single # and then return the anonymized text. Only change relevant parts and keep everything else as is. Make sure you keep the original meaning, i.e. do not invent new information instead generalize information."
        else:  # CoT (Chain of Thought)
            system_prompt = "You are an expert anonymizer that carefully adapts small parts of the text to make it anonymous. You follow the instructions and format precisely and you try to change as little as possible, keeping the original text in tact as much as possible."
            pii_desc = pii_context or "sensitive personal information"
            header = f"Your task is to anonymize the following text to prevent inference of {pii_desc}, while keeping the rest of the text intact."
            footer = "In a first step briefly explain the changes you will make. In a new line write a single # and then return the anonymized text. Only change relevant parts and keep everything else as is. Make sure you keep the original meaning, i.e. do not invent new information."

        intermediate = f"\n\nText:\n{text}\n\n"

        return Prompt(
            system_prompt=system_prompt,
            header=header,
            intermediate=intermediate,
            footer=footer,
            target="",
            original_point=text,
            gt=[],
            answer="",
            shots=[],
            id="text_anonymization"
        )

    def _parse_response(self, response: str) -> str:
        """
        Parse LLM response to extract anonymized text.

        Args:
            response: Raw response from LLM

        Returns:
            Extracted anonymized text
        """
        # If response contains # separator, extract text after it
        if "#" in response:
            parts = response.split("#")
            if len(parts) >= 2:
                return parts[1].strip()

        # Otherwise return entire response stripped
        return response.strip()

    def anonymize(
        self,
        text: str,
        pii_context: Optional[str] = None
    ) -> str:
        """
        Anonymize the given text using LLM.

        Args:
            text: Text to anonymize
            pii_context: Description of PII to protect (e.g., "age, income, location")

        Returns:
            Anonymized text
        """
        # Create prompt
        prompt = self._create_prompts(text, pii_context)

        # Call LLM
        response = self.model.predict(prompt, timeout=60)

        # Parse response
        anonymized_text = self._parse_response(response)

        return anonymized_text

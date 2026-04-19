"""
OpenAI Provider Module

Independent module for OpenAI API integration.
Requires VPN in China, separate from other providers.
"""

import os
from typing import Dict, Optional

from .base import (
    BaseProviderModule,
    ProviderInfo,
    ModelInfo,
    ProviderStatus,
    ProviderState as PS
)
from ...api_cost_analyzer import APICostAnalyzer, Region


class OpenAIProvider(BaseProviderModule):
    """OpenAI API provider - Premium performance, international access"""

    def __init__(self):
        super().__init__()
        self._load_models()

    @property
    def provider_info(self) -> ProviderInfo:
        return ProviderInfo(
            provider_id="openai",
            name="OpenAI",
            region="international",
            china_accessible=False,
            requires_vpn_in_china=True,
            registration_difficulty="hard",
            docs_url="https://platform.openai.com/docs",
            official_website="https://openai.com"
        )

    def _load_models(self):
        """Load model information from cost analyzer"""
        analyzer = APICostAnalyzer(region=Region.INTERNATIONAL)
        provider = analyzer.PROVIDERS.get("openai")

        if not provider:
            return

        # Define capability scores
        capabilities = {
            "gpt-4o": {
                "reasoning": 0.95, "language": 0.95, "instruction": 0.92,
                "attack": 0.90, "defense": 0.92, "evaluation": 0.94
            },
            "gpt-4o-mini": {
                "reasoning": 0.80, "language": 0.85, "instruction": 0.88,
                "attack": 0.75, "defense": 0.85, "evaluation": 0.80
            },
            "gpt-4-turbo": {
                "reasoning": 0.90, "language": 0.92, "instruction": 0.90,
                "attack": 0.85, "defense": 0.88, "evaluation": 0.90
            }
        }

        for model_id, pricing in provider.pricing.items():
            caps = capabilities.get(model_id, {
                "reasoning": 0.75, "language": 0.75, "instruction": 0.75,
                "attack": 0.75, "defense": 0.75, "evaluation": 0.75
            })

            self._models[model_id] = ModelInfo(
                model_id=model_id,
                provider_id="openai",
                name=model_id,
                reasoning_capability=caps["reasoning"],
                language_understanding=caps["language"],
                instruction_following=caps["instruction"],
                attack_capability=caps["attack"],
                defense_capability=caps["defense"],
                evaluation_capability=caps["evaluation"],
                defender_score=caps["defense"] * 0.4 + caps["instruction"] * 0.3 + caps["language"] * 0.3,
                attacker_score=caps["attack"] * 0.4 + caps["reasoning"] * 0.3 + caps["language"] * 0.3,
                evaluator_score=caps["evaluation"] * 0.4 + caps["reasoning"] * 0.4 + caps["instruction"] * 0.2,
                cost_per_1k_input=pricing.input_cost_per_1k,
                cost_per_1k_output=pricing.output_cost_per_1k,
                max_tokens=128000,
                supports_function_calling=True,
                supports_vision=True,
                average_latency_ms=800
            )

    def check_availability(self) -> ProviderStatus:
        """Check if OpenAI API is available"""
        # Check for API key
        api_key = os.environ.get("OPENAI_API_KEY")

        if not api_key:
            return ProviderStatus(
                provider_id="openai",
                status=PS.UNCONFIGURED,
                error_message="OPENAI_API_KEY not found in environment",
                available_models=[]
            )

        # Verify by attempting import
        try:
            from ...models.model_factory import ModelFactory
            from ...configs.config import ModelConfig

            return ProviderStatus(
                provider_id="openai",
                status=PS.AVAILABLE,
                available_models=list(self._models.keys())
            )

        except Exception as e:
            return ProviderStatus(
                provider_id="openai",
                status=PS.UNREACHABLE,
                error_message=f"Failed to initialize: {str(e)}",
                available_models=[]
            )

    def get_models(self) -> Dict[str, ModelInfo]:
        """Get all OpenAI models"""
        return self._models.copy()

    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get info for a specific model"""
        return self._models.get(model_id)

    def create_model_instance(self, model_id: str, **kwargs):
        """Create an OpenAI model instance"""
        from ...models.model_factory import ModelFactory
        from ...configs.config import ModelConfig

        if model_id not in self._models:
            return None

        config = ModelConfig(
            name=model_id,
            provider="openai",
            args=kwargs
        )

        try:
            return ModelFactory.create_model(config)
        except Exception:
            return None

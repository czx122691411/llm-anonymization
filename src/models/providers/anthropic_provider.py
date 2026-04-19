"""
Anthropic (Claude) Provider Module

Independent module for Anthropic API integration.
Separate from other providers with its own availability check.
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


class AnthropicProvider(BaseProviderModule):
    """Anthropic (Claude) API provider - Strong evaluation capabilities"""

    def __init__(self):
        super().__init__()
        self._load_models()

    @property
    def provider_info(self) -> ProviderInfo:
        return ProviderInfo(
            provider_id="anthropic",
            name="Anthropic (Claude)",
            region="international",
            china_accessible=False,
            requires_vpn_in_china=True,
            registration_difficulty="hard",
            docs_url="https://docs.anthropic.com",
            official_website="https://www.anthropic.com"
        )

    def _load_models(self):
        """Load model information from cost analyzer"""
        analyzer = APICostAnalyzer(region=Region.INTERNATIONAL)
        provider = analyzer.PROVIDERS.get("anthropic")

        if not provider:
            return

        # Define capability scores
        capabilities = {
            "claude-3-5-sonnet-20241022": {
                "reasoning": 0.94, "language": 0.95, "instruction": 0.93,
                "attack": 0.92, "defense": 0.90, "evaluation": 0.95
            },
            "claude-3-haiku-20240307": {
                "reasoning": 0.75, "language": 0.82, "instruction": 0.85,
                "attack": 0.70, "defense": 0.80, "evaluation": 0.75
            },
            "claude-3-5-haiku-20241022": {
                "reasoning": 0.82, "language": 0.85, "instruction": 0.86,
                "attack": 0.78, "defense": 0.82, "evaluation": 0.82
            }
        }

        for model_id, pricing in provider.pricing.items():
            caps = capabilities.get(model_id, {
                "reasoning": 0.75, "language": 0.75, "instruction": 0.75,
                "attack": 0.75, "defense": 0.75, "evaluation": 0.75
            })

            self._models[model_id] = ModelInfo(
                model_id=model_id,
                provider_id="anthropic",
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
                max_tokens=200000,
                supports_function_calling=True,
                supports_vision=True,
                average_latency_ms=900
            )

    def check_availability(self) -> ProviderStatus:
        """Check if Anthropic API is available"""
        # Check for API key
        api_key = os.environ.get("ANTHROPIC_API_KEY")

        if not api_key:
            return ProviderStatus(
                provider_id="anthropic",
                status=PS.UNCONFIGURED,
                error_message="ANTHROPIC_API_KEY not found in environment",
                available_models=[]
            )

        try:
            from ...models.model_factory import ModelFactory
            from ...configs.config import ModelConfig

            return ProviderStatus(
                provider_id="anthropic",
                status=PS.AVAILABLE,
                available_models=list(self._models.keys())
            )

        except Exception as e:
            return ProviderStatus(
                provider_id="anthropic",
                status=PS.UNREACHABLE,
                error_message=f"Failed to initialize: {str(e)}",
                available_models=[]
            )

    def get_models(self) -> Dict[str, ModelInfo]:
        """Get all Anthropic models"""
        return self._models.copy()

    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get info for a specific model"""
        return self._models.get(model_id)

    def create_model_instance(self, model_id: str, **kwargs):
        """Create an Anthropic model instance"""
        from ...models.model_factory import ModelFactory
        from ...configs.config import ModelConfig

        if model_id not in self._models:
            return None

        config = ModelConfig(
            name=model_id,
            provider="anthropic",
            args=kwargs
        )

        try:
            return ModelFactory.create_model(config)
        except Exception:
            return None

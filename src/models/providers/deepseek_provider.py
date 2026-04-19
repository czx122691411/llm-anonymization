"""
DeepSeek Provider Module

Independent module for DeepSeek API integration.
Can be used regardless of other providers' availability.
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


class DeepSeekProvider(BaseProviderModule):
    """DeepSeek API provider - China-friendly, cost-effective"""

    def __init__(self):
        super().__init__()
        self._load_models()

    @property
    def provider_info(self) -> ProviderInfo:
        return ProviderInfo(
            provider_id="deepseek",
            name="DeepSeek",
            region="china",
            china_accessible=True,
            requires_vpn_in_china=False,
            registration_difficulty="very_easy",
            docs_url="https://platform.deepseek.com/api-docs",
            official_website="https://www.deepseek.com"
        )

    def _load_models(self):
        """Load model information from cost analyzer"""
        analyzer = APICostAnalyzer(region=Region.CHINA)
        provider = analyzer.PROVIDERS.get("deepseek")

        if not provider:
            return

        # Define capability scores
        capabilities = {
            "deepseek-chat": {
                "reasoning": 0.82, "language": 0.88, "instruction": 0.85,
                "attack": 0.80, "defense": 0.85, "evaluation": 0.82
            },
            "deepseek-reasoner": {
                "reasoning": 0.90, "language": 0.85, "instruction": 0.82,
                "attack": 0.92, "defense": 0.80, "evaluation": 0.88
            }
        }

        for model_id, pricing in provider.pricing.items():
            caps = capabilities.get(model_id, capabilities["deepseek-chat"])

            self._models[model_id] = ModelInfo(
                model_id=model_id,
                provider_id="deepseek",
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
                max_tokens=128000 if "chat" in model_id else 64000,
                supports_function_calling=True,
                supports_vision=False,
                average_latency_ms=600 if "chat" in model_id else 15000
            )

    def check_availability(self) -> ProviderStatus:
        """Check if DeepSeek API is available"""
        # Check for API key in environment
        api_key = os.environ.get("DEEPSEEK_API_KEY")

        if not api_key:
            return ProviderStatus(
                provider_id="deepseek",
                status=PS.UNCONFIGURED,
                error_message="DEEPSEEK_API_KEY not found in environment",
                available_models=[]
            )

        # Try to import the model class
        try:
            from ...models.model_factory import ModelFactory
            from ...configs.config import ModelConfig

            # Try to create a test config
            test_config = ModelConfig(
                name="deepseek-chat",
                provider="deepseek",
                args={"temperature": 0.1, "max_tokens": 10}
            )

            return ProviderStatus(
                provider_id="deepseek",
                status=PS.AVAILABLE,
                available_models=list(self._models.keys())
            )

        except Exception as e:
            return ProviderStatus(
                provider_id="deepseek",
                status=PS.UNREACHABLE,
                error_message=f"Failed to initialize: {str(e)}",
                available_models=[]
            )

    def get_models(self) -> Dict[str, ModelInfo]:
        """Get all DeepSeek models"""
        return self._models.copy()

    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get info for a specific model"""
        return self._models.get(model_id)

    def create_model_instance(self, model_id: str, **kwargs):
        """Create a DeepSeek model instance"""
        from ...models.model_factory import ModelFactory
        from ...configs.config import ModelConfig

        if model_id not in self._models:
            return None

        config = ModelConfig(
            name=model_id,
            provider="deepseek",
            args=kwargs
        )

        try:
            return ModelFactory.create_model(config)
        except Exception:
            return None

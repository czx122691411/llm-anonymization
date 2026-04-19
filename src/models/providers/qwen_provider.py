"""
Qwen (Alibaba Cloud) Provider Module

Independent module for Qwen API integration via DashScope.
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


class QwenProvider(BaseProviderModule):
    """Qwen (Alibaba Cloud) API provider - Strong Chinese language support"""

    def __init__(self):
        super().__init__()
        self._load_models()

    @property
    def provider_info(self) -> ProviderInfo:
        return ProviderInfo(
            provider_id="qwen",
            name="Qwen (Alibaba Cloud)",
            region="china",
            china_accessible=True,
            requires_vpn_in_china=False,
            registration_difficulty="very_easy",
            docs_url="https://help.aliyun.com/zh/dashscope/developer-reference/quick-start",
            official_website="https://tongyi.aliyun.com"
        )

    def _load_models(self):
        """Load model information from cost analyzer"""
        analyzer = APICostAnalyzer(region=Region.CHINA)
        provider = analyzer.PROVIDERS.get("qwen")

        if not provider:
            # Fallback to manual definition if cost analyzer doesn't have qwen
            self._load_models_manual()
            return

        # Define capability scores
        capabilities = {
            "qwen-turbo": {
                "reasoning": 0.78, "language": 0.85, "instruction": 0.82,
                "attack": 0.75, "defense": 0.80, "evaluation": 0.78
            },
            "qwen-plus": {
                "reasoning": 0.85, "language": 0.88, "instruction": 0.86,
                "attack": 0.82, "defense": 0.86, "evaluation": 0.85
            },
            "qwen-max": {
                "reasoning": 0.90, "language": 0.92, "instruction": 0.90,
                "attack": 0.88, "defense": 0.90, "evaluation": 0.92
            },
            "qwen-max-longcontext": {
                "reasoning": 0.90, "language": 0.92, "instruction": 0.90,
                "attack": 0.88, "defense": 0.90, "evaluation": 0.92
            }
        }

        for model_id, pricing in provider.pricing.items():
            caps = capabilities.get(model_id, {
                "reasoning": 0.80, "language": 0.80, "instruction": 0.80,
                "attack": 0.80, "defense": 0.80, "evaluation": 0.80
            })

            self._models[model_id] = ModelInfo(
                model_id=model_id,
                provider_id="qwen",
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
                max_tokens=30000 if "longcontext" not in model_id else 30000,
                supports_function_calling=True,
                supports_vision=False,
                average_latency_ms=700 if "turbo" in model_id else 1200
            )

    def _load_models_manual(self):
        """Fallback manual model definition"""
        models = {
            "qwen-turbo": {
                "reasoning": 0.78, "language": 0.85, "instruction": 0.82,
                "attack": 0.75, "defense": 0.80, "evaluation": 0.78,
                "cost_input": 0.30, "cost_output": 0.60, "latency": 700
            },
            "qwen-plus": {
                "reasoning": 0.85, "language": 0.88, "instruction": 0.86,
                "attack": 0.82, "defense": 0.86, "evaluation": 0.85,
                "cost_input": 0.40, "cost_output": 1.00, "latency": 1200
            },
            "qwen-max": {
                "reasoning": 0.90, "language": 0.92, "instruction": 0.90,
                "attack": 0.88, "defense": 0.90, "evaluation": 0.92,
                "cost_input": 1.20, "cost_output": 2.00, "latency": 2000
            }
        }

        for model_id, caps in models.items():
            self._models[model_id] = ModelInfo(
                model_id=model_id,
                provider_id="qwen",
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
                cost_per_1k_input=caps["cost_input"],
                cost_per_1k_output=caps["cost_output"],
                max_tokens=30000,
                supports_function_calling=True,
                supports_vision=False,
                average_latency_ms=caps["latency"]
            )

    def check_availability(self) -> ProviderStatus:
        """Check if Qwen API is available"""
        # Check for API key
        api_key = os.environ.get("DASHSCOPE_API_KEY")

        if not api_key:
            return ProviderStatus(
                provider_id="qwen",
                status=PS.UNCONFIGURED,
                error_message="DASHSCOPE_API_KEY not found in environment",
                available_models=[]
            )

        try:
            # Try to import dashscope only (don't import model_factory to avoid transformers dependency)
            import dashscope

            # Verify API key is set
            if not dashscope.api_key:
                dashscope.api_key = api_key

            # Test with a simple API call if possible
            # For now, just verify the module is available
            return ProviderStatus(
                provider_id="qwen",
                status=PS.AVAILABLE,
                available_models=list(self._models.keys())
            )

        except ImportError as e:
            return ProviderStatus(
                provider_id="qwen",
                status=PS.UNREACHABLE,
                error_message=f"dashscope package not installed: {str(e)}. Install with: pip install dashscope",
                available_models=[]
            )
        except Exception as e:
            return ProviderStatus(
                provider_id="qwen",
                status=PS.UNREACHABLE,
                error_message=f"Failed to initialize: {str(e)}",
                available_models=[]
            )

    def get_models(self) -> Dict[str, ModelInfo]:
        """Get all Qwen models"""
        return self._models.copy()

    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get info for a specific model"""
        return self._models.get(model_id)

    def create_model_instance(self, model_id: str, **kwargs):
        """Create a Qwen model instance"""
        if model_id not in self._models:
            return None

        try:
            # Import directly to avoid model_factory dependencies
            from ...models.qwen import QwenModel
            from ...configs.config import ModelConfig

            config = ModelConfig(
                name=model_id,
                provider="qwen",
                args=kwargs
            )

            return QwenModel(config)
        except Exception:
            return None

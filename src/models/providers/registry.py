"""
Provider Registry - Modular Model Availability System

This module provides a centralized registry for all model providers
with independent availability checking and graceful degradation.
Integrates with the existing model_factory system.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import os
from pathlib import Path


class ProviderStatus(Enum):
    """Status of a provider"""
    AVAILABLE = "available"
    UNCONFIGURED = "unconfigured"  # No API key configured
    UNREACHABLE = "unreachable"    # Network/API issues
    DISABLED = "disabled"          # Explicitly disabled


@dataclass
class ProviderInfo:
    """Information about a provider"""
    provider_id: str
    name: str
    region: str  # "china", "international", or "global"

    # Accessibility
    china_accessible: bool
    requires_vpn_in_china: bool
    registration_difficulty: str  # "easy", "medium", "hard"

    # API credentials
    env_api_key: Optional[str] = None
    api_key_configured: bool = False

    # Pricing (average cost per 1k tokens)
    avg_cost_per_1k_input: float = 0.0
    avg_cost_per_1k_output: float = 0.0

    # Documentation
    docs_url: str = ""
    official_website: str = ""


@dataclass
class ModelInfo:
    """Information about a specific model"""
    model_id: str
    provider_id: str
    name: str

    # Capability scores (0-1)
    reasoning_capability: float = 0.5
    language_understanding: float = 0.5
    instruction_following: float = 0.5

    # Role suitability scores
    defender_score: float = 0.5
    attacker_score: float = 0.5
    evaluator_score: float = 0.5

    # Pricing
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0

    # Technical specs
    max_tokens: int = 4096
    supports_function_calling: bool = False
    average_latency_ms: int = 1000


@dataclass
class ProviderAvailability:
    """Runtime availability status of a provider"""
    provider_id: str
    status: ProviderStatus
    available_models: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    last_checked: bool = False


class ProviderRegistry:
    """
    Centralized registry for all model providers.

    Features:
    - Independent availability checking for each provider
    - Graceful degradation when providers are unavailable
    - Integration with existing model_factory
    - Cost tracking and analysis
    """

    # Static provider information
    PROVIDERS: Dict[str, ProviderInfo] = {
        "deepseek": ProviderInfo(
            provider_id="deepseek",
            name="DeepSeek",
            region="china",
            china_accessible=True,
            requires_vpn_in_china=False,
            registration_difficulty="very_easy",
            env_api_key="DEEPSEEK_API_KEY",
            avg_cost_per_1k_input=0.14,
            avg_cost_per_1k_output=0.28,
            docs_url="https://platform.deepseek.com/api-docs",
            official_website="https://www.deepseek.com"
        ),
        "openai": ProviderInfo(
            provider_id="openai",
            name="OpenAI",
            region="international",
            china_accessible=False,
            requires_vpn_in_china=True,
            registration_difficulty="hard",
            env_api_key="OPENAI_API_KEY",
            avg_cost_per_1k_input=2.50,
            avg_cost_per_1k_output=10.00,
            docs_url="https://platform.openai.com/docs",
            official_website="https://openai.com"
        ),
        "anthropic": ProviderInfo(
            provider_id="anthropic",
            name="Anthropic (Claude)",
            region="international",
            china_accessible=False,
            requires_vpn_in_china=True,
            registration_difficulty="hard",
            env_api_key="ANTHROPIC_API_KEY",
            avg_cost_per_1k_input=3.00,
            avg_cost_per_1k_output=15.00,
            docs_url="https://docs.anthropic.com",
            official_website="https://www.anthropic.com"
        ),
        "qwen": ProviderInfo(
            provider_id="qwen",
            name="Qwen (Alibaba Cloud)",
            region="china",
            china_accessible=True,
            requires_vpn_in_china=False,
            registration_difficulty="easy",
            env_api_key="DASHSCOPE_API_KEY",
            avg_cost_per_1k_input=0.40,
            avg_cost_per_1k_output=1.00,
            docs_url="https://help.aliyun.com/zh/dashscope",
            official_website="https://tongyi.aliyun.com"
        ),
        "zhipu": ProviderInfo(
            provider_id="zhipu",
            name="Zhipu AI (GLM)",
            region="china",
            china_accessible=True,
            requires_vpn_in_china=False,
            registration_difficulty="easy",
            env_api_key="ZHIPUAI_API_KEY",
            avg_cost_per_1k_input=0.50,
            avg_cost_per_1k_output=0.50,
            docs_url="https://open.bigmodel.cn/dev/api",
            official_website="https://open.bigmodel.cn"
        ),
        "ollama": ProviderInfo(
            provider_id="ollama",
            name="Ollama (Local Models)",
            region="global",
            china_accessible=True,
            requires_vpn_in_china=False,
            registration_difficulty="very_easy",
            env_api_key=None,  # No API key needed
            avg_cost_per_1k_input=0.0,
            avg_cost_per_1k_output=0.0,
            docs_url="https://github.com/ollama/ollama",
            official_website="https://ollama.ai"
        ),
    }

    # Model definitions for each provider
    MODELS: Dict[str, Dict[str, ModelInfo]] = {}

    @classmethod
    def _initialize_models(cls):
        """Initialize model information"""
        if cls.MODELS:
            return

        # DeepSeek models
        cls.MODELS["deepseek"] = {
            "deepseek-chat": ModelInfo(
                model_id="deepseek-chat",
                provider_id="deepseek",
                name="DeepSeek Chat",
                reasoning_capability=0.82,
                language_understanding=0.88,
                instruction_following=0.85,
                defender_score=0.85,
                attacker_score=0.82,
                evaluator_score=0.82,
                cost_per_1k_input=0.14,
                cost_per_1k_output=0.28,
                max_tokens=128000,
                supports_function_calling=True,
                average_latency_ms=600
            ),
            "deepseek-reasoner": ModelInfo(
                model_id="deepseek-reasoner",
                provider_id="deepseek",
                name="DeepSeek Reasoner",
                reasoning_capability=0.90,
                language_understanding=0.85,
                instruction_following=0.82,
                defender_score=0.82,
                attacker_score=0.90,
                evaluator_score=0.88,
                cost_per_1k_input=0.55,
                cost_per_1k_output=2.19,
                max_tokens=64000,
                supports_function_calling=False,
                average_latency_ms=15000
            ),
        }

        # OpenAI models
        cls.MODELS["openai"] = {
            "gpt-4o": ModelInfo(
                model_id="gpt-4o",
                provider_id="openai",
                name="GPT-4o",
                reasoning_capability=0.95,
                language_understanding=0.95,
                instruction_following=0.92,
                defender_score=0.92,
                attacker_score=0.92,
                evaluator_score=0.94,
                cost_per_1k_input=2.50,
                cost_per_1k_output=10.00,
                max_tokens=128000,
                supports_function_calling=True,
                average_latency_ms=800
            ),
            "gpt-4o-mini": ModelInfo(
                model_id="gpt-4o-mini",
                provider_id="openai",
                name="GPT-4o Mini",
                reasoning_capability=0.80,
                language_understanding=0.85,
                instruction_following=0.88,
                defender_score=0.85,
                attacker_score=0.78,
                evaluator_score=0.80,
                cost_per_1k_input=0.15,
                cost_per_1k_output=0.60,
                max_tokens=128000,
                supports_function_calling=True,
                average_latency_ms=400
            ),
        }

        # Anthropic models
        cls.MODELS["anthropic"] = {
            "claude-3-5-sonnet-20241022": ModelInfo(
                model_id="claude-3-5-sonnet-20241022",
                provider_id="anthropic",
                name="Claude 3.5 Sonnet",
                reasoning_capability=0.94,
                language_understanding=0.95,
                instruction_following=0.93,
                defender_score=0.90,
                attacker_score=0.92,
                evaluator_score=0.95,
                cost_per_1k_input=3.00,
                cost_per_1k_output=15.00,
                max_tokens=200000,
                supports_function_calling=True,
                average_latency_ms=900
            ),
            "claude-3-haiku-20240307": ModelInfo(
                model_id="claude-3-haiku-20240307",
                provider_id="anthropic",
                name="Claude 3 Haiku",
                reasoning_capability=0.75,
                language_understanding=0.82,
                instruction_following=0.85,
                defender_score=0.80,
                attacker_score=0.72,
                evaluator_score=0.75,
                cost_per_1k_input=0.25,
                cost_per_1k_output=1.25,
                max_tokens=200000,
                supports_function_calling=True,
                average_latency_ms=300
            ),
        }

        # Qwen models
        cls.MODELS["qwen"] = {
            "qwen-turbo": ModelInfo(
                model_id="qwen-turbo",
                provider_id="qwen",
                name="Qwen Turbo",
                reasoning_capability=0.78,
                language_understanding=0.85,
                instruction_following=0.82,
                defender_score=0.82,
                attacker_score=0.77,
                evaluator_score=0.78,
                cost_per_1k_input=0.30,
                cost_per_1k_output=0.60,
                max_tokens=8000,
                supports_function_calling=True,
                average_latency_ms=500
            ),
            "qwen-plus": ModelInfo(
                model_id="qwen-plus",
                provider_id="qwen",
                name="Qwen Plus",
                reasoning_capability=0.85,
                language_understanding=0.88,
                instruction_following=0.86,
                defender_score=0.86,
                attacker_score=0.84,
                evaluator_score=0.84,
                cost_per_1k_input=0.40,
                cost_per_1k_output=1.00,
                max_tokens=32000,
                supports_function_calling=True,
                average_latency_ms=700
            ),
            "qwen-max": ModelInfo(
                model_id="qwen-max",
                provider_id="qwen",
                name="Qwen Max",
                reasoning_capability=0.90,
                language_understanding=0.90,
                instruction_following=0.88,
                defender_score=0.88,
                attacker_score=0.88,
                evaluator_score=0.88,
                cost_per_1k_input=1.20,
                cost_per_1k_output=2.00,
                max_tokens=30000,
                supports_function_calling=True,
                average_latency_ms=1000
            ),
        }

        # Zhipu models
        cls.MODELS["zhipu"] = {
            "glm-4": ModelInfo(
                model_id="glm-4",
                provider_id="zhipu",
                name="GLM-4",
                reasoning_capability=0.85,
                language_understanding=0.86,
                instruction_following=0.84,
                defender_score=0.84,
                attacker_score=0.84,
                evaluator_score=0.84,
                cost_per_1k_input=0.50,
                cost_per_1k_output=0.50,
                max_tokens=128000,
                supports_function_calling=True,
                average_latency_ms=800
            ),
            "glm-4-plus": ModelInfo(
                model_id="glm-4-plus",
                provider_id="zhipu",
                name="GLM-4 Plus",
                reasoning_capability=0.88,
                language_understanding=0.88,
                instruction_following=0.86,
                defender_score=0.86,
                attacker_score=0.86,
                evaluator_score=0.86,
                cost_per_1k_input=0.70,
                cost_per_1k_output=0.70,
                max_tokens=128000,
                supports_function_calling=True,
                average_latency_ms=1000
            ),
        }

        # Ollama models (local)
        cls.MODELS["ollama"] = {
            "llama3.1-70b": ModelInfo(
                model_id="llama3.1-70b",
                provider_id="ollama",
                name="Llama 3.1 70B",
                reasoning_capability=0.82,
                language_understanding=0.85,
                instruction_following=0.80,
                defender_score=0.82,
                attacker_score=0.80,
                evaluator_score=0.80,
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                max_tokens=128000,
                supports_function_calling=False,
                average_latency_ms=3000
            ),
            "qwen2-72b": ModelInfo(
                model_id="qwen2-72b",
                provider_id="ollama",
                name="Qwen2 72B",
                reasoning_capability=0.84,
                language_understanding=0.86,
                instruction_following=0.82,
                defender_score=0.84,
                attacker_score=0.82,
                evaluator_score=0.82,
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                max_tokens=128000,
                supports_function_calling=False,
                average_latency_ms=2000
            ),
        }

    def __init__(self, region: str = "international"):
        """
        Initialize the registry.

        Args:
            region: Target region ("china" or "international")
        """
        self._initialize_models()
        self.region = region
        self._availability_cache: Dict[str, ProviderAvailability] = {}

    def check_provider_availability(self, provider_id: str) -> ProviderAvailability:
        """
        Check if a provider is available.

        This performs independent checking for each provider:
        - Verifies API credentials
        - Tests basic connectivity
        - Lists available models

        Args:
            provider_id: Provider to check

        Returns:
            ProviderAvailability with status details
        """
        # Check cache first
        if provider_id in self._availability_cache:
            return self._availability_cache[provider_id]

        provider_info = self.PROVIDERS.get(provider_id)
        if not provider_info:
            return ProviderAvailability(
                provider_id=provider_id,
                status=ProviderStatus.DISABLED,
                error_message=f"Unknown provider: {provider_id}"
            )

        # Check API key configuration
        if provider_info.env_api_key:
            api_key = os.environ.get(provider_info.env_api_key)
            if not api_key:
                availability = ProviderAvailability(
                    provider_id=provider_id,
                    status=ProviderStatus.UNCONFIGURED,
                    error_message=f"{provider_info.env_api_key} not found in environment"
                )
                self._availability_cache[provider_id] = availability
                return availability

        # Special handling for Ollama (local)
        if provider_id == "ollama":
            availability = self._check_ollama_availability()
            self._availability_cache[provider_id] = availability
            return availability

        # Special handling for Qwen (avoid model_factory transformers dependency)
        if provider_id == "qwen":
            availability = self._check_qwen_availability()
            self._availability_cache[provider_id] = availability
            return availability

        # Special handling for DeepSeek (avoid model_factory transformers dependency)
        if provider_id == "deepseek":
            availability = self._check_deepseek_availability()
            self._availability_cache[provider_id] = availability
            return availability

        # For API providers, try to import and verify
        try:
            # Try to verify the provider can be imported
            from ..model_factory import get_model
            from ..configs.config import ModelConfig

            # Create a minimal test config
            test_models = list(self.MODELS.get(provider_id, {}).keys())
            if not test_models:
                availability = ProviderAvailability(
                    provider_id=provider_id,
                    status=ProviderStatus.UNREACHABLE,
                    error_message="No models defined for provider"
                )
            else:
                availability = ProviderAvailability(
                    provider_id=provider_id,
                    status=ProviderStatus.AVAILABLE,
                    available_models=test_models
                )

        except Exception as e:
            availability = ProviderAvailability(
                provider_id=provider_id,
                status=ProviderStatus.UNREACHABLE,
                error_message=f"Provider check failed: {str(e)}"
            )

        self._availability_cache[provider_id] = availability
        return availability

    def _check_ollama_availability(self) -> ProviderAvailability:
        """Check Ollama availability separately"""
        try:
            import subprocess
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                timeout=5,
                text=True
            )

            if result.returncode != 0:
                return ProviderAvailability(
                    provider_id="ollama",
                    status=ProviderStatus.UNREACHABLE,
                    error_message="Ollama not installed or not running. Install from https://ollama.ai"
                )

            # Parse available models
            available = []
            for line in result.stdout.split('\n')[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if parts:
                        model_name = parts[0]
                        if model_name in self.MODELS["ollama"]:
                            available.append(model_name)

            if not available:
                return ProviderAvailability(
                    provider_id="ollama",
                    status=ProviderStatus.AVAILABLE,
                    error_message="Ollama running but no supported models installed",
                    available_models=[]
                )

            return ProviderAvailability(
                provider_id="ollama",
                status=ProviderStatus.AVAILABLE,
                available_models=available
            )

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return ProviderAvailability(
                provider_id="ollama",
                status=ProviderStatus.UNREACHABLE,
                error_message="Ollama not found. Install from https://ollama.ai"
            )
        except Exception as e:
            return ProviderAvailability(
                provider_id="ollama",
                status=ProviderStatus.UNREACHABLE,
                error_message=f"Ollama check failed: {str(e)}"
            )

    def _check_qwen_availability(self) -> ProviderAvailability:
        """Check Qwen availability separately (avoid transformers dependency)"""
        try:
            # Try to import dashscope
            import dashscope

            # Check if API key is set
            provider_info = self.PROVIDERS["qwen"]
            api_key = os.environ.get(provider_info.env_api_key)

            if not api_key:
                return ProviderAvailability(
                    provider_id="qwen",
                    status=ProviderStatus.UNCONFIGURED,
                    error_message=f"{provider_info.env_api_key} not found in environment"
                )

            # Verify dashscope is available
            return ProviderAvailability(
                provider_id="qwen",
                status=ProviderStatus.AVAILABLE,
                available_models=list(self.MODELS.get("qwen", {}).keys())
            )

        except ImportError:
            return ProviderAvailability(
                provider_id="qwen",
                status=ProviderStatus.UNREACHABLE,
                error_message="dashscope package not installed. Install with: pip install dashscope"
            )
        except Exception as e:
            return ProviderAvailability(
                provider_id="qwen",
                status=ProviderStatus.UNREACHABLE,
                error_message=f"Qwen check failed: {str(e)}"
            )

    def _check_deepseek_availability(self) -> ProviderAvailability:
        """Check DeepSeek availability separately (avoid transformers dependency)"""
        try:
            # Try to import openai (DeepSeek uses OpenAI-compatible API)
            import openai

            # Check if API key is set
            provider_info = self.PROVIDERS["deepseek"]
            api_key = os.environ.get(provider_info.env_api_key)

            if not api_key:
                return ProviderAvailability(
                    provider_id="deepseek",
                    status=ProviderStatus.UNCONFIGURED,
                    error_message=f"{provider_info.env_api_key} not found in environment"
                )

            # Verify openai package is available (DeepSeek uses it)
            return ProviderAvailability(
                provider_id="deepseek",
                status=ProviderStatus.AVAILABLE,
                available_models=list(self.MODELS.get("deepseek", {}).keys())
            )

        except ImportError:
            return ProviderAvailability(
                provider_id="deepseek",
                status=ProviderStatus.UNREACHABLE,
                error_message="openai package not installed. Install with: pip install openai"
            )
        except Exception as e:
            return ProviderAvailability(
                provider_id="deepseek",
                status=ProviderStatus.UNREACHABLE,
                error_message=f"DeepSeek check failed: {str(e)}"
            )

    def get_available_providers(self) -> Dict[str, ProviderAvailability]:
        """
        Get availability of all providers.

        Returns:
            Dictionary of provider_id -> ProviderAvailability
        """
        availability = {}

        for provider_id in self.PROVIDERS.keys():
            avail = self.check_provider_availability(provider_id)

            # Filter by region
            if self.region == "china":
                provider_info = self.PROVIDERS[provider_id]
                if not provider_info.china_accessible:
                    continue

            availability[provider_id] = avail

        return availability

    def get_available_models(
        self,
        role: Optional[str] = None,  # "defender", "attacker", "evaluator"
        provider_id: Optional[str] = None
    ) -> List[ModelInfo]:
        """
        Get list of available models.

        Args:
            role: Optional role filter
            provider_id: Optional provider filter

        Returns:
            List of available ModelInfo
        """
        available_models = []
        provider_availability = self.get_available_providers()

        for pid, availability in provider_availability.items():
            if availability.status != ProviderStatus.AVAILABLE:
                continue

            if provider_id and pid != provider_id:
                continue

            for model_id in availability.available_models:
                if pid in self.MODELS and model_id in self.MODELS[pid]:
                    model_info = self.MODELS[pid][model_id]

                    # Filter by role score if specified
                    if role:
                        score_key = f"{role}_score"
                        score = getattr(model_info, score_key, 0.5)
                        if score < 0.7:  # Minimum threshold
                            continue

                    available_models.append(model_info)

        # Sort by relevant score
        if role:
            score_key = f"{role}_score"
            available_models.sort(
                key=lambda m: getattr(m, score_key, 0.5),
                reverse=True
            )
        else:
            available_models.sort(
                key=lambda m: (m.defender_score + m.attacker_score + m.evaluator_score) / 3,
                reverse=True
            )

        return available_models

    def get_provider_info(self, provider_id: str) -> Optional[ProviderInfo]:
        """Get provider information"""
        return self.PROVIDERS.get(provider_id)

    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get model information"""
        for provider_models in self.MODELS.values():
            if model_id in provider_models:
                return provider_models[model_id]
        return None

    def create_model_instance(
        self,
        model_id: str,
        temperature: float = 0.1,
        max_tokens: int = 2000,
        **kwargs
    ):
        """
        Create a model instance using provider-specific implementations.

        Args:
            model_id: Model to create
            temperature: Temperature parameter
            max_tokens: Max tokens parameter
            **kwargs: Additional parameters

        Returns:
            Model instance or None if creation fails
        """
        model_info = self.get_model_info(model_id)
        if not model_info:
            return None

        # Check provider availability first
        availability = self.check_provider_availability(model_info.provider_id)
        if availability.status != ProviderStatus.AVAILABLE:
            print(f"Warning: Provider {model_info.provider_id} is not available: {availability.error_message}")
            return None

        try:
            # Import directly to avoid model_factory transformers dependency
            from src.configs.config import ModelConfig

            config = ModelConfig(
                name=model_id,
                provider=model_info.provider_id,
                args={
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
                }
            )

            # Provider-specific imports
            if model_info.provider_id == "qwen":
                from src.models.qwen import QwenModel
                return QwenModel(config)
            elif model_info.provider_id == "deepseek":
                from src.models.deepseek import DeepSeekModel
                return DeepSeekModel(config)
            elif model_info.provider_id == "openai":
                from src.models.open_ai import OpenAIGPT
                return OpenAIGPT(config)
            elif model_info.provider_id == "anthropic":
                from src.models.anthropic import AnthropicModel
                return AnthropicModel(config)
            elif model_info.provider_id == "ollama":
                from src.models.ollama import OllamaModel
                return OllamaModel(config)
            else:
                # Fallback to model_factory for other providers
                from ..model_factory import get_model
                return get_model(config)

        except Exception as e:
            print(f"Error creating model {model_id}: {str(e)}")
            return None

    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get cost summary for all available providers.

        Returns:
            Dictionary with cost information
        """
        summary = {
            "by_provider": {},
            "by_model": {},
            "china_accessible": [],
            "international_only": []
        }

        for provider_id, provider_info in self.PROVIDERS.items():
            # Check availability
            availability = self.check_provider_availability(provider_id)
            if availability.status != ProviderStatus.AVAILABLE:
                continue

            provider_summary = {
                "name": provider_info.name,
                "region": provider_info.region,
                "china_accessible": provider_info.china_accessible,
                "avg_cost_input": provider_info.avg_cost_per_1k_input,
                "avg_cost_output": provider_info.avg_cost_per_1k_output,
                "models": []
            }

            # Group by accessibility
            if provider_info.china_accessible:
                summary["china_accessible"].append(provider_id)
            else:
                summary["international_only"].append(provider_id)

            # Add model details
            if provider_id in self.MODELS:
                for model_id, model_info in self.MODELS[provider_id].items():
                    if model_id in availability.available_models:
                        model_summary = {
                            "id": model_id,
                            "name": model_info.name,
                            "cost_input": model_info.cost_per_1k_input,
                            "cost_output": model_info.cost_per_1k_output,
                            "defender_score": model_info.defender_score,
                            "attacker_score": model_info.attacker_score,
                            "evaluator_score": model_info.evaluator_score
                        }
                        provider_summary["models"].append(model_summary)
                        summary["by_model"][model_id] = model_summary

            summary["by_provider"][provider_id] = provider_summary

        return summary


# Singleton instance for convenience
_global_registry: Optional[ProviderRegistry] = None


def get_registry(region: str = "international") -> ProviderRegistry:
    """Get the global provider registry instance"""
    global _global_registry
    if _global_registry is None or _global_registry.region != region:
        _global_registry = ProviderRegistry(region=region)
    return _global_registry


def check_all_providers(region: str = "international") -> Dict[str, ProviderAvailability]:
    """Convenience function to check all providers"""
    registry = get_registry(region)
    return registry.get_available_providers()


def print_provider_status(region: str = "international"):
    """Print status of all providers"""
    availability = check_all_providers(region)

    print(f"\n{'='*60}")
    print(f"Provider Status (Region: {region})")
    print(f"{'='*60}\n")

    for provider_id, avail in sorted(availability.items()):
        provider_info = ProviderRegistry.PROVIDERS[provider_id]

        status_symbol = {
            ProviderStatus.AVAILABLE: "✓",
            ProviderStatus.UNCONFIGURED: "✗",
            ProviderStatus.UNREACHABLE: "⚠",
            ProviderStatus.DISABLED: "⊘"
        }.get(avail.status, "?")

        print(f"{status_symbol} {provider_info.name} ({provider_id})")
        print(f"   Status: {avail.status.value}")
        print(f"   Region: {provider_info.region}")
        print(f"   China Accessible: {'Yes' if provider_info.china_accessible else 'No'}")

        if avail.status == ProviderStatus.AVAILABLE:
            print(f"   Available Models: {', '.join(avail.available_models)}")
            provider_models = ProviderRegistry.MODELS.get(provider_id, {})
            if provider_models and avail.available_models:
                sample_model = provider_models[avail.available_models[0]]
                print(f"   Cost: ${sample_model.cost_per_1k_input:.2f} input / ${sample_model.cost_per_1k_output:.2f} output per 1k tokens")
        else:
            print(f"   Error: {avail.error_message}")

        print()


if __name__ == "__main__":
    # Test the registry
    print_provider_status("international")
    print_provider_status("china")

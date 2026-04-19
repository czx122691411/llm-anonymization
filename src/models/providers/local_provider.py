"""
Local Model Provider Module (Ollama)

Independent module for local models via Ollama.
No API keys needed, runs locally.
"""

import subprocess
from typing import Dict, Optional

from .base import (
    BaseProviderModule,
    ProviderInfo,
    ModelInfo,
    ProviderStatus,
    ProviderState as PS
)


class LocalModelProvider(BaseProviderModule):
    """Local model provider via Ollama - No API keys, runs locally"""

    def __init__(self):
        super().__init__()
        self._load_models()
        self._ollama_available = None

    @property
    def provider_info(self) -> ProviderInfo:
        return ProviderInfo(
            provider_id="ollama",
            name="Ollama (Local Models)",
            region="global",
            china_accessible=True,
            requires_vpn_in_china=False,
            registration_difficulty="very_easy",
            docs_url="https://github.com/ollama/ollama",
            official_website="https://ollama.ai"
        )

    def _load_models(self):
        """Load model information for local models"""
        # Define commonly used local models
        local_models = {
            "llama3.1-70b": {
                "reasoning": 0.82, "language": 0.85, "instruction": 0.80,
                "attack": 0.78, "defense": 0.82, "evaluation": 0.80,
                "latency": 3000
            },
            "mistral-7b": {
                "reasoning": 0.72, "language": 0.78, "instruction": 0.75,
                "attack": 0.70, "defense": 0.75, "evaluation": 0.72,
                "latency": 500
            },
            "qwen2-72b": {
                "reasoning": 0.84, "language": 0.86, "instruction": 0.82,
                "attack": 0.80, "defense": 0.84, "evaluation": 0.82,
                "latency": 2000
            },
            "gemma2-27b": {
                "reasoning": 0.76, "language": 0.80, "instruction": 0.78,
                "attack": 0.74, "defense": 0.78, "evaluation": 0.76,
                "latency": 1000
            }
        }

        for model_id, caps in local_models.items():
            self._models[model_id] = ModelInfo(
                model_id=model_id,
                provider_id="ollama",
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
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                max_tokens=128000 if "70b" in model_id or "72b" in model_id else 32000,
                supports_function_calling=False,
                supports_vision=False,
                average_latency_ms=caps["latency"]
            )

    def _check_ollama_available(self) -> bool:
        """Check if Ollama is installed and running"""
        if self._ollama_available is not None:
            return self._ollama_available

        try:
            # Try to run ollama list
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                timeout=5,
                text=True
            )
            self._ollama_available = result.returncode == 0
            return self._ollama_available
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._ollama_available = False
            return False

    def _get_installed_models(self) -> list:
        """Get list of installed Ollama models"""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                timeout=10,
                text=True
            )

            if result.returncode != 0:
                return []

            # Parse output to get model names
            models = []
            for line in result.stdout.split('\n')[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if parts:
                        models.append(parts[0])

            return models
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return []

    def check_availability(self) -> ProviderStatus:
        """Check if Ollama and local models are available"""
        if not self._check_ollama_available():
            return ProviderStatus(
                provider_id="ollama",
                status=PS.UNREACHABLE,
                error_message="Ollama is not installed or not running. Install from https://ollama.ai",
                available_models=[]
            )

        # Get installed models
        installed = self._get_installed_models()
        available_in_pool = [m for m in installed if m in self._models]

        if not available_in_pool:
            return ProviderStatus(
                provider_id="ollama",
                status=PS.AVAILABLE,
                error_message="Ollama is running but no supported models are installed. "
                            "Install one with: ollama pull llama3.1-70b",
                available_models=[]
            )

        return ProviderStatus(
            provider_id="ollama",
            status=PS.AVAILABLE,
            available_models=available_in_pool
        )

    def get_models(self) -> Dict[str, ModelInfo]:
        """Get all local models"""
        return self._models.copy()

    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get info for a specific model"""
        return self._models.get(model_id)

    def create_model_instance(self, model_id: str, **kwargs):
        """Create a local model instance via Ollama"""
        from ...models.model_factory import ModelFactory
        from ...configs.config import ModelConfig

        if model_id not in self._models:
            return None

        # Check if model is installed
        installed = self._get_installed_models()
        if model_id not in installed:
            print(f"Warning: Model {model_id} is not installed in Ollama. "
                  f"Install with: ollama pull {model_id}")
            return None

        config = ModelConfig(
            name=model_id,
            provider="ollama",
            args=kwargs
        )

        try:
            return ModelFactory.create_model(config)
        except Exception:
            return None

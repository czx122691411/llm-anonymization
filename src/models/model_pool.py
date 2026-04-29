"""
Heterogeneous Model Pool for Multi-Model Adversarial Anonymization Platform

This module implements a dynamic model pool system that allows flexible composition
of different models as defenders, attackers, and evaluators in the adversarial framework.
"""

from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import random
from pathlib import Path
from datetime import datetime

from .model_factory import ModelFactory
from ..configs.config import ModelConfig
from ..api_cost_analyzer import APICostAnalyzer, Region, DifficultyLevel


class ModelRole(Enum):
    """Define possible roles in the adversarial framework"""
    DEFENDER = "defender"
    ATTACKER = "attacker"
    EVALUATOR = "evaluator"
    UTILITY = "utility"


class SelectionStrategy(Enum):
    """Model selection strategies"""
    BEST_PERFORMING = "best_performing"
    RANDOM = "random"
    COST_OPTIMIZED = "cost_optimized"
    BALANCED = "balanced"
    ROUND_ROBIN = "round_robin"
    HETEROGENEOUS = "heterogeneous"  # Prefer different providers


@dataclass
class ModelCapabilities:
    """Define capabilities and characteristics of a model"""
    provider: str
    model_name: str

    # Capability scores (0-1)
    reasoning_capability: float = 0.5
    language_understanding: float = 0.5
    instruction_following: float = 0.5
    attack_capability: float = 0.5
    defense_capability: float = 0.5
    evaluation_capability: float = 0.5

    # Cost information (from API analyzer)
    cost_per_1k_tokens_input: float = 0.0
    cost_per_1k_tokens_output: float = 0.0

    # Technical specifications
    max_tokens: int = 4096
    supports_function_calling: bool = False
    supports_vision: bool = False

    # Availability (for China/international access)
    china_accessible: bool = False
    international_accessible: bool = True
    requires_vpn: bool = False
    registration_difficulty: DifficultyLevel = DifficultyLevel.MEDIUM

    # Performance characteristics
    average_latency_ms: int = 1000
    rate_limit_rpm: int = 60

    # Suitability scores for different roles (auto-calculated)
    defender_score: float = field(init=False)
    attacker_score: float = field(init=False)
    evaluator_score: float = field(init=False)

    def __post_init__(self):
        """Calculate role suitability scores"""
        self.defender_score = (
            self.defense_capability * 0.4 +
            self.instruction_following * 0.3 +
            self.language_understanding * 0.3
        )
        self.attacker_score = (
            self.attack_capability * 0.4 +
            self.reasoning_capability * 0.3 +
            self.language_understanding * 0.3
        )
        self.evaluator_score = (
            self.evaluation_capability * 0.4 +
            self.reasoning_capability * 0.4 +
            self.instruction_following * 0.2
        )


class ModelPool:
    """
    Heterogeneous model pool for dynamic model composition in adversarial anonymization.

    This class manages a pool of models from different providers and allows dynamic
    selection and composition based on various strategies.
    """

    # Default model capabilities based on research and benchmarks
    DEFAULT_MODELS: Dict[str, ModelCapabilities] = {}

    @classmethod
    def _initialize_default_models(cls):
        """Initialize default models from API cost analyzer data"""
        if cls.DEFAULT_MODELS:
            return

        analyzer = APICostAnalyzer(region=Region.INTERNATIONAL)

        # Capability scores based on research benchmarks
        capability_scores = {
            # OpenAI
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
            },

            # Anthropic
            "claude-3-5-sonnet-20241022": {
                "reasoning": 0.94, "language": 0.95, "instruction": 0.93,
                "attack": 0.92, "defense": 0.90, "evaluation": 0.95
            },
            "claude-3-haiku-20240307": {
                "reasoning": 0.75, "language": 0.82, "instruction": 0.85,
                "attack": 0.70, "defense": 0.80, "evaluation": 0.75
            },

            # DeepSeek (China-friendly)
            "deepseek-chat": {
                "reasoning": 0.82, "language": 0.88, "instruction": 0.85,
                "attack": 0.80, "defense": 0.85, "evaluation": 0.82
            },
            "deepseek-reasoner": {
                "reasoning": 0.90, "language": 0.85, "instruction": 0.82,
                "attack": 0.92, "defense": 0.80, "evaluation": 0.88
            },

            # Qwen (China-friendly)
            "qwen-turbo": {
                "reasoning": 0.78, "language": 0.85, "instruction": 0.82,
                "attack": 0.75, "defense": 0.82, "evaluation": 0.78
            },
            "qwen-plus": {
                "reasoning": 0.85, "language": 0.88, "instruction": 0.86,
                "attack": 0.82, "defense": 0.86, "evaluation": 0.84
            },
            "qwen-max": {
                "reasoning": 0.90, "language": 0.90, "instruction": 0.88,
                "attack": 0.86, "defense": 0.88, "evaluation": 0.88
            },

            # Zhipu (China-friendly)
            "glm-4": {
                "reasoning": 0.85, "language": 0.86, "instruction": 0.84,
                "attack": 0.82, "defense": 0.84, "evaluation": 0.84
            },
            "glm-4-plus": {
                "reasoning": 0.88, "language": 0.88, "instruction": 0.86,
                "attack": 0.85, "defense": 0.86, "evaluation": 0.86
            },

            # Moonshot (China-friendly)
            "moonshot-v1-8k": {
                "reasoning": 0.78, "language": 0.82, "instruction": 0.80,
                "attack": 0.75, "defense": 0.80, "evaluation": 0.78
            },
            "moonshot-v1-32k": {
                "reasoning": 0.82, "language": 0.84, "instruction": 0.82,
                "attack": 0.78, "defense": 0.82, "evaluation": 0.80
            },

            # Google
            "gemini-1.5-pro": {
                "reasoning": 0.90, "language": 0.90, "instruction": 0.88,
                "attack": 0.85, "defense": 0.86, "evaluation": 0.88
            },
            "gemini-1.5-flash": {
                "reasoning": 0.75, "language": 0.80, "instruction": 0.82,
                "attack": 0.72, "defense": 0.78, "evaluation": 0.75
            },

            # Azure (special case - accessible in China)
            "gpt-4o-azure": {
                "reasoning": 0.95, "language": 0.95, "instruction": 0.92,
                "attack": 0.90, "defense": 0.92, "evaluation": 0.94
            },
        }

        # Build models from API analyzer data
        for provider_info in analyzer.PROVIDERS.values():
            provider_id = provider_info.provider_id

            for model_id, pricing in provider_info.pricing.items():
                # Skip Azure models that duplicate OpenAI
                if provider_id == "azure" and "turbo" in model_id:
                    continue

                # Get capability scores
                scores = capability_scores.get(model_id, {
                    "reasoning": 0.75, "language": 0.75, "instruction": 0.75,
                    "attack": 0.75, "defense": 0.75, "evaluation": 0.75
                })

                # Create model capabilities
                model_key = model_id if provider_id != "azure" else f"{model_id}-azure"

                cls.DEFAULT_MODELS[model_key] = ModelCapabilities(
                    provider=provider_id,
                    model_name=model_id,
                    reasoning_capability=scores["reasoning"],
                    language_understanding=scores["language"],
                    instruction_following=scores["instruction"],
                    attack_capability=scores["attack"],
                    defense_capability=scores["defense"],
                    evaluation_capability=scores["evaluation"],
                    cost_per_1k_tokens_input=pricing.input_cost_per_1k,
                    cost_per_1k_tokens_output=pricing.output_cost_per_1k,
                    max_tokens=128000 if "pro" in model_id or "max" in model_id else 32000,
                    supports_function_calling=provider_info.supports_function_calling,
                    supports_vision=provider_info.supports_vision,
                    china_accessible=provider_info.access_info.china_accessible,
                    international_accessible=provider_info.access_info.international_accessible,
                    requires_vpn=provider_info.access_info.requires_vpn_in_china,
                    registration_difficulty=provider_info.access_info.registration_difficulty,
                    average_latency_ms=provider_info.average_latency_ms,
                    rate_limit_rpm=60  # Default rate limit
                )

        # Add local models (Ollama)
        cls.DEFAULT_MODELS.update({
            "llama3.1-70b": ModelCapabilities(
                provider="ollama",
                model_name="llama3.1-70b",
                reasoning_capability=0.82,
                language_understanding=0.85,
                instruction_following=0.80,
                attack_capability=0.78,
                defense_capability=0.82,
                evaluation_capability=0.80,
                cost_per_1k_tokens_input=0.0,
                cost_per_1k_tokens_output=0.0,
                max_tokens=128000,
                supports_function_calling=False,
                supports_vision=False,
                china_accessible=True,
                international_accessible=True,
                requires_vpn=False,
                registration_difficulty=DifficultyLevel.VERY_EASY,
                average_latency_ms=3000,
                rate_limit_rpm=60
            ),
            "mistral-7b": ModelCapabilities(
                provider="ollama",
                model_name="mistral-7b",
                reasoning_capability=0.72,
                language_understanding=0.78,
                instruction_following=0.75,
                attack_capability=0.70,
                defense_capability=0.75,
                evaluation_capability=0.72,
                cost_per_1k_tokens_input=0.0,
                cost_per_1k_tokens_output=0.0,
                max_tokens=32000,
                supports_function_calling=False,
                supports_vision=False,
                china_accessible=True,
                international_accessible=True,
                requires_vpn=False,
                registration_difficulty=DifficultyLevel.VERY_EASY,
                average_latency_ms=500,
                rate_limit_rpm=120
            ),
            "qwen2-72b": ModelCapabilities(
                provider="ollama",
                model_name="qwen2-72b",
                reasoning_capability=0.84,
                language_understanding=0.86,
                instruction_following=0.82,
                attack_capability=0.80,
                defense_capability=0.84,
                evaluation_capability=0.82,
                cost_per_1k_tokens_input=0.0,
                cost_per_1k_tokens_output=0.0,
                max_tokens=128000,
                supports_function_calling=False,
                supports_vision=False,
                china_accessible=True,
                international_accessible=True,
                requires_vpn=False,
                registration_difficulty=DifficultyLevel.VERY_EASY,
                average_latency_ms=2000,
                rate_limit_rpm=60
            ),
        })

    def __init__(
        self,
        custom_models: Optional[Dict[str, ModelCapabilities]] = None,
        region: str = "international",
        budget_constrained: bool = False,
        max_cost_per_1k: Optional[float] = None
    ):
        """
        Initialize the model pool.

        Args:
            custom_models: Additional or override models
            region: Target region for model selection ("china" or "international")
            budget_constrained: Whether to prioritize cost-effective models
            max_cost_per_1k: Maximum cost per 1k tokens constraint
        """
        self._initialize_default_models()
        self.models = self.DEFAULT_MODELS.copy()
        if custom_models:
            self.models.update(custom_models)

        self.region = region
        self.budget_constrained = budget_constrained
        self.max_cost_per_1k = max_cost_per_1k
        self.usage_history: Dict[str, Dict[str, Any]] = {}
        self.performance_history: Dict[str, Dict[str, float]] = {}

        # Initialize usage tracking for each model
        for model_id in self.models.keys():
            self.usage_history[model_id] = {
                "total_calls": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "role_usage": {role.value: 0 for role in ModelRole}
            }
            self.performance_history[model_id] = {
                "privacy_scores": [],
                "utility_scores": [],
                "avg_latency": []
            }

    def get_available_models(
        self,
        role: Optional[ModelRole] = None,
        provider: Optional[str] = None,
        china_accessible: Optional[bool] = None,
        within_budget: bool = True
    ) -> List[str]:
        """
        Get list of available models based on filters.

        Args:
            role: Filter by role suitability
            provider: Filter by provider
            china_accessible: Filter by China accessibility
            within_budget: Filter by cost constraint

        Returns:
            List of model IDs
        """
        models = list(self.models.keys())

        # Filter by provider
        if provider:
            models = [
                m for m in models
                if self.models[m].provider == provider
            ]

        # Filter by region accessibility
        if self.region == "china":
            models = [
                m for m in models
                if self.models[m].china_accessible
            ]

        # Filter by explicit china accessibility
        if china_accessible is not None:
            models = [
                m for m in models
                if self.models[m].china_accessible == china_accessible
            ]

        # Filter by budget constraint
        if within_budget and self.max_cost_per_1k:
            models = [
                m for m in models
                if self.models[m].cost_per_1k_tokens_input <= self.max_cost_per_1k
            ]

        # Sort by role suitability if role specified
        if role:
            score_key = f"{role.value}_score"
            models.sort(
                key=lambda m: getattr(self.models[m], score_key),
                reverse=True
            )

        return models

    def get_model_for_role(
        self,
        role: ModelRole,
        strategy: SelectionStrategy = SelectionStrategy.BALANCED,
        exclude_models: Optional[List[str]] = None,
        exclude_providers: Optional[List[str]] = None,
        used_providers: Optional[set] = None
    ) -> Optional[str]:
        """
        Select the best model for a given role using the specified strategy.

        Args:
            role: The role to select a model for
            strategy: Selection strategy to use
            exclude_models: Models to exclude from selection
            exclude_providers: Providers to exclude from selection
            used_providers: Set of already used providers (for heterogeneous selection)

        Returns:
            Selected model ID or None
        """
        available = self.get_available_models(role=role)

        # Apply filters
        if exclude_models:
            available = [m for m in available if m not in exclude_models]

        if exclude_providers:
            available = [
                m for m in available
                if self.models[m].provider not in exclude_providers
            ]

        # For heterogeneous strategy, exclude already used providers
        if strategy == SelectionStrategy.HETEROGENEOUS and used_providers:
            available = [
                m for m in available
                if self.models[m].provider not in used_providers
            ]

        if not available:
            return None

        if strategy == SelectionStrategy.BEST_PERFORMING:
            score_key = f"{role.value}_score"
            return max(available, key=lambda m: getattr(self.models[m], score_key))

        elif strategy == SelectionStrategy.RANDOM:
            return random.choice(available)

        elif strategy == SelectionStrategy.COST_OPTIMIZED:
            return min(
                available,
                key=lambda m: self.models[m].cost_per_1k_tokens_input
            )

        elif strategy == SelectionStrategy.BALANCED:
            # Balance between performance and cost
            score_key = f"{role.value}_score"
            def balanced_score(m):
                capability = getattr(self.models[m], score_key)
                cost = self.models[m].cost_per_1k_tokens_input + self.models[m].cost_per_1k_tokens_output
                return capability / (cost + 0.01)  # Avoid division by zero
            return max(available, key=balanced_score)

        elif strategy == SelectionStrategy.ROUND_ROBIN:
            # Select least used model for this role
            role_usage = {
                m: self.usage_history[m]["role_usage"][role.value]
                for m in available
            }
            return min(role_usage, key=role_usage.get)

        elif strategy == SelectionStrategy.HETEROGENEOUS:
            # Prefer different providers while maintaining good performance
            score_key = f"{role.value}_score"
            # Bonus for using different provider
            def heterogeneous_score(m):
                base_score = getattr(self.models[m], score_key)
                provider_diversity_bonus = 1.5 if self.models[m].provider not in (used_providers or set()) else 1.0
                return base_score * provider_diversity_bonus
            return max(available, key=heterogeneous_score)

        return available[0]

    def get_model_config(
        self,
        model_id: str,
        role: ModelRole = ModelRole.DEFENDER
    ) -> ModelConfig:
        """
        Get ModelConfig for a given model ID.

        Args:
            model_id: Model identifier
            role: Role to use the model for

        Returns:
            ModelConfig object
        """
        if model_id not in self.models:
            raise ValueError(f"Unknown model: {model_id}")

        capabilities = self.models[model_id]

        # Determine temperature based on role
        temperature_map = {
            ModelRole.DEFENDER: 0.1,      # Low temp for consistent anonymization
            ModelRole.ATTACKER: 0.2,      # Slightly higher for exploration
            ModelRole.EVALUATOR: 0.0,     # Deterministic evaluation
            ModelRole.UTILITY: 0.0,       # Deterministic utility scoring
        }

        return ModelConfig(
            name=capabilities.model_name,
            provider=capabilities.provider,
            args={
                "temperature": temperature_map.get(role, 0.1),
                "max_tokens": min(capabilities.max_tokens, 4000)
            }
        )

    def create_model_instance(
        self,
        model_id: str,
        role: ModelRole = ModelRole.DEFENDER
    ):
        """
        Create a model instance using the factory.

        Args:
            model_id: Model identifier
            role: Role to use the model for

        Returns:
            Model instance
        """
        config = self.get_model_config(model_id, role)
        return ModelFactory.create_model(config)

    def get_model_info(self, model_id: str) -> ModelCapabilities:
        """Get capabilities info for a model"""
        if model_id not in self.models:
            raise ValueError(f"Unknown model: {model_id}")
        return self.models[model_id]

    def get_model_comparison(self) -> Dict[str, Any]:
        """
        Get comparison of all models for decision making.

        Returns:
            Dictionary with model comparisons
        """
        comparison = {
            "by_provider": {},
            "by_cost": {},
            "by_performance": {},
            "by_accessibility": {
                "china_accessible": [],
                "international_only": [],
                "requires_vpn": []
            },
            "recommendations": {
                "best_defender": None,
                "best_attacker": None,
                "best_evaluator": None,
                "most_cost_effective": None,
                "best_for_china": None
            }
        }

        # Group by provider
        for model_id, caps in self.models.items():
            provider = caps.provider
            if provider not in comparison["by_provider"]:
                comparison["by_provider"][provider] = []
            comparison["by_provider"][provider].append(model_id)

        # Sort by cost
        comparison["by_cost"] = sorted(
            self.models.keys(),
            key=lambda m: self.models[m].cost_per_1k_tokens_input
        )

        # Sort by performance (average of all scores)
        comparison["by_performance"] = sorted(
            self.models.keys(),
            key=lambda m: (
                self.models[m].defender_score +
                self.models[m].attacker_score +
                self.models[m].evaluator_score
            ) / 3,
            reverse=True
        )

        # Accessibility
        for model_id, caps in self.models.items():
            if caps.china_accessible:
                comparison["by_accessibility"]["china_accessible"].append(model_id)
            if not caps.international_accessible:
                if model_id not in comparison["by_accessibility"]["international_only"]:
                    comparison["by_accessibility"]["international_only"].append(model_id)
            if caps.requires_vpn:
                comparison["by_accessibility"]["requires_vpn"].append(model_id)

        # Recommendations
        comparison["recommendations"]["best_defender"] = max(
            self.models.keys(),
            key=lambda m: self.models[m].defender_score
        )
        comparison["recommendations"]["best_attacker"] = max(
            self.models.keys(),
            key=lambda m: self.models[m].attacker_score
        )
        comparison["recommendations"]["best_evaluator"] = max(
            self.models.keys(),
            key=lambda m: self.models[m].evaluator_score
        )
        comparison["recommendations"]["most_cost_effective"] = min(
            self.models.keys(),
            key=lambda m: self.models[m].cost_per_1k_tokens_input
        )

        # Best for China (balanced performance and accessibility)
        china_models = [
            m for m in self.models.keys()
            if self.models[m].china_accessible
        ]
        if china_models:
            comparison["recommendations"]["best_for_china"] = max(
                china_models,
                key=lambda m: (
                    self.models[m].defender_score +
                    self.models[m].attacker_score +
                    self.models[m].evaluator_score
                ) / 3
            )

        return comparison

    def track_usage(
        self,
        model_id: str,
        role: ModelRole,
        tokens_used: int,
        output_tokens: int = 0
    ):
        """
        Track API usage and costs for a model.

        Args:
            model_id: Model identifier
            role: Role the model was used for
            tokens_used: Number of input tokens
            output_tokens: Number of output tokens
        """
        if model_id not in self.usage_history:
            return

        caps = self.models[model_id]
        cost = (
            (tokens_used / 1000) * caps.cost_per_1k_tokens_input +
            (output_tokens / 1000) * caps.cost_per_1k_tokens_output
        )

        self.usage_history[model_id]["total_calls"] += 1
        self.usage_history[model_id]["total_tokens"] += tokens_used + output_tokens
        self.usage_history[model_id]["total_cost"] += cost
        self.usage_history[model_id]["role_usage"][role.value] += 1

    def get_usage_report(self) -> Dict[str, Any]:
        """Generate usage and cost report"""
        report = {
            "summary": {
                "total_cost": 0.0,
                "total_calls": 0,
                "total_tokens": 0
            },
            "by_model": {},
            "by_role": {role.value: {"cost": 0.0, "calls": 0} for role in ModelRole},
            "by_provider": {}
        }

        for model_id, usage in self.usage_history.items():
            if usage["total_calls"] == 0:
                continue

            caps = self.models[model_id]

            # Summary
            report["summary"]["total_cost"] += usage["total_cost"]
            report["summary"]["total_calls"] += usage["total_calls"]
            report["summary"]["total_tokens"] += usage["total_tokens"]

            # By model
            report["by_model"][model_id] = {
                "calls": usage["total_calls"],
                "tokens": usage["total_tokens"],
                "cost": usage["total_cost"],
                "avg_cost_per_call": usage["total_cost"] / usage["total_calls"],
                "provider": caps.provider,
                "china_accessible": caps.china_accessible
            }

            # By provider
            provider = caps.provider
            if provider not in report["by_provider"]:
                report["by_provider"][provider] = {
                    "cost": 0.0,
                    "calls": 0,
                    "tokens": 0,
                    "models": []
                }
            report["by_provider"][provider]["cost"] += usage["total_cost"]
            report["by_provider"][provider]["calls"] += usage["total_calls"]
            report["by_provider"][provider]["tokens"] += usage["total_tokens"]
            report["by_provider"][provider]["models"].append(model_id)

            # By role
            for role, count in usage["role_usage"].items():
                if count > 0:
                    # Estimate cost proportion by role
                    role_cost = usage["total_cost"] * (count / usage["total_calls"])
                    report["by_role"][role]["cost"] += role_cost
                    report["by_role"][role]["calls"] += count

        return report

    def save_usage_report(self, filepath: str):
        """Save usage report to JSON file"""
        report = self.get_usage_report()
        report["generated_at"] = datetime.now().isoformat()
        report["region"] = self.region
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)


class ModelOrchestrator:
    """
    Orchestrates model composition for adversarial anonymization.

    This class provides high-level methods for creating heterogeneous
    model compositions for the adversarial framework.
    """

    def __init__(
        self,
        pool: Optional[ModelPool] = None,
        region: str = "international",
        selection_strategy: SelectionStrategy = SelectionStrategy.HETEROGENEOUS
    ):
        """
        Initialize the orchestrator.

        Args:
            pool: Model pool to use (creates default if None)
            region: Target region
            selection_strategy: Default selection strategy
        """
        self.pool = pool or ModelPool(region=region)
        self.selection_strategy = selection_strategy
        self.active_composition: Dict[str, str] = {}

    def create_heterogeneous_composition(
        self,
        strategy: Optional[SelectionStrategy] = None,
        defender_model: Optional[str] = None,
        attacker_model: Optional[str] = None,
        evaluator_model: Optional[str] = None,
        exclude_same_provider: bool = True,
        max_cost_per_1k: Optional[float] = None
    ) -> Dict[ModelRole, str]:
        """
        Create a heterogeneous model composition for adversarial anonymization.

        Args:
            strategy: Selection strategy (uses default if None)
            defender_model: Specific model for defender (None for auto-select)
            attacker_model: Specific model for attacker (None for auto-select)
            evaluator_model: Specific model for evaluator (None for auto-select)
            exclude_same_provider: Whether to use different providers for each role
            max_cost_per_1k: Maximum cost constraint

        Returns:
            Dictionary mapping roles to model IDs
        """
        strategy = strategy or self.selection_strategy
        if exclude_same_provider and strategy != SelectionStrategy.HETEROGENEOUS:
            strategy = SelectionStrategy.HETEROGENEOUS

        composition = {}
        used_providers = set()
        used_models = set()

        # Select defender
        if defender_model:
            if defender_model not in self.pool.models:
                raise ValueError(f"Unknown defender model: {defender_model}")
            composition[ModelRole.DEFENDER] = defender_model
            used_providers.add(self.pool.models[defender_model].provider)
            used_models.add(defender_model)
        else:
            defender = self.pool.get_model_for_role(
                ModelRole.DEFENDER,
                strategy=strategy,
                used_providers=used_providers
            )
            if defender:
                composition[ModelRole.DEFENDER] = defender
                used_providers.add(self.pool.models[defender].provider)
                used_models.add(defender)

        # Select attacker
        if attacker_model:
            if attacker_model not in self.pool.models:
                raise ValueError(f"Unknown attacker model: {attacker_model}")
            composition[ModelRole.ATTACKER] = attacker_model
            used_providers.add(self.pool.models[attacker_model].provider)
            used_models.add(attacker_model)
        else:
            attacker = self.pool.get_model_for_role(
                ModelRole.ATTACKER,
                strategy=strategy,
                used_providers=used_providers
            )
            if attacker:
                composition[ModelRole.ATTACKER] = attacker
                used_providers.add(self.pool.models[attacker].provider)
                used_models.add(attacker)

        # Select evaluator
        if evaluator_model:
            if evaluator_model not in self.pool.models:
                raise ValueError(f"Unknown evaluator model: {evaluator_model}")
            composition[ModelRole.EVALUATOR] = evaluator_model
            used_models.add(evaluator_model)
        else:
            evaluator = self.pool.get_model_for_role(
                ModelRole.EVALUATOR,
                strategy=strategy,
                used_providers=used_providers
            )
            if evaluator:
                composition[ModelRole.EVALUATOR] = evaluator
                used_models.add(evaluator)

        self.active_composition = {role.value: model_id for role, model_id in composition.items()}
        return composition

    def create_model_instances(
        self,
        composition: Dict[ModelRole, str]
    ) -> Dict[ModelRole, Any]:
        """
        Create model instances for a composition.

        Args:
            composition: Role to model ID mapping

        Returns:
            Dictionary of instantiated models
        """
        instances = {}
        for role, model_id in composition.items():
            instances[role] = self.pool.create_model_instance(model_id, role)
        return instances

    def get_composition_info(self) -> Dict[str, Any]:
        """Get information about the active composition"""
        if not self.active_composition:
            return {"error": "No active composition"}

        info = {
            "composition": self.active_composition.copy(),
            "models": {},
            "total_cost_estimate": 0.0,
            "heterogeneous": False,
            "providers": set(),
            "china_accessible_composition": True
        }

        for role_value, model_id in self.active_composition.items():
            caps = self.pool.get_model_info(model_id)
            info["models"][model_id] = {
                "role": role_value,
                "provider": caps.provider,
                "china_accessible": caps.china_accessible,
                "cost_per_1k_input": caps.cost_per_1k_tokens_input,
                "cost_per_1k_output": caps.cost_per_1k_tokens_output,
                "defender_score": caps.defender_score,
                "attacker_score": caps.attacker_score,
                "evaluator_score": caps.evaluator_score
            }
            info["providers"].add(caps.provider)
            info["total_cost_estimate"] += (
                caps.cost_per_1k_tokens_input + caps.cost_per_1k_tokens_output
            )
            if not caps.china_accessible:
                info["china_accessible_composition"] = False

        info["heterogeneous"] = len(info["providers"]) > 1
        info["providers"] = list(info["providers"])
        info["num_providers"] = len(info["providers"])

        return info


def get_recommended_compositions(
    pool: Optional[ModelPool] = None,
    region: str = "international"
) -> Dict[str, Dict[ModelRole, str]]:
    """
    Get recommended model compositions for different scenarios.

    Args:
        pool: Model pool to use
        region: Target region

    Returns:
        Dictionary of scenario -> composition mappings
    """
    pool = pool or ModelPool(region=region)

    recommendations = {
        "best_performance": {
            ModelRole.DEFENDER: "gpt-4o",
            ModelRole.ATTACKER: "claude-3-5-sonnet-20241022",
            ModelRole.EVALUATOR: "gpt-4o"
        },
        "cost_optimized": {
            ModelRole.DEFENDER: "gpt-4o-mini",
            ModelRole.ATTACKER: "deepseek-chat",
            ModelRole.EVALUATOR: "gpt-4o-mini"
        },
        "china_friendly": {
            ModelRole.DEFENDER: "deepseek-chat",
            ModelRole.ATTACKER: "deepseek-reasoner",
            ModelRole.EVALUATOR: "qwen-max"
        },
        "local_only": {
            ModelRole.DEFENDER: "llama3.1-70b",
            ModelRole.ATTACKER: "qwen2-72b",
            ModelRole.EVALUATOR: "llama3.1-70b"
        },
        "multi_provider_heterogeneous": {
            ModelRole.DEFENDER: "deepseek-chat",      # Chinese
            ModelRole.ATTACKER: "claude-3-5-sonnet-20241022",  # US
            ModelRole.EVALUATOR: "gpt-4o"             # US
        },
        "balanced_multi_region": {
            ModelRole.DEFENDER: "deepseek-chat",      # Chinese, cost-effective
            ModelRole.ATTACKER: "gemini-1.5-flash",   # US, fast
            ModelRole.EVALUATOR: "gpt-4o-mini"        # US, balanced
        }
    }

    # Filter recommendations based on region
    if region == "china":
        recommendations["best_performance"] = {
            ModelRole.DEFENDER: "deepseek-chat",
            ModelRole.ATTACKER: "deepseek-reasoner",
            ModelRole.EVALUATOR: "qwen-max"
        }
        recommendations["multi_provider_heterogeneous"] = {
            ModelRole.DEFENDER: "deepseek-chat",
            ModelRole.ATTACKER: "qwen-max",
            ModelRole.EVALUATOR: "glm-4-plus"
        }

    return recommendations

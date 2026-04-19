"""
API Cost and Accessibility Analysis Module for LLM Providers

This module provides comprehensive analysis of API costs, accessibility,
and registration difficulty for major LLM providers across different regions.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime
from pathlib import Path


class Region(Enum):
    """Target regions for API access"""
    CHINA = "china"
    INTERNATIONAL = "international"
    GLOBAL = "global"


class DifficultyLevel(Enum):
    """Registration and access difficulty levels"""
    VERY_EASY = "very_easy"      # No verification, immediate access
    EASY = "easy"                 # Simple verification
    MEDIUM = "medium"             # Phone/SMS verification required
    HARD = "hard"                 # ID/business license required
    VERY_HARD = "very_hard"       # Complex requirements + VPN/proxy needed


@dataclass
class PricingTier:
    """Pricing information for a model"""
    model_id: str
    input_cost_per_1k: float      # USD
    output_cost_per_1k: float     # USD
    currency: str = "USD"
    effective_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))


@dataclass
class APIAccessInfo:
    """API access and registration information"""
    provider: str
    china_accessible: bool
    international_accessible: bool
    requires_vpn_in_china: bool
    registration_difficulty: DifficultyLevel
    documentation_language: List[str]  # Available documentation languages
    official_website: str
    api_docs_url: str

    # Registration requirements
    requires_phone: bool = False
    requires_credit_card: bool = False
    requires_id_verification: bool = False
    requires_business_license: bool = False

    # Service limitations in China
    blocked_in_china: bool = False
    degraded_in_china: bool = False
    local_alternative: Optional[str] = None

    # Rate limits (free tier)
    free_tier_available: bool = False
    free_tier_requests_per_day: Optional[int] = None
    free_tier_tokens_per_month: Optional[int] = None


@dataclass
class ProviderInfo:
    """Complete provider information"""
    provider_id: str
    name: str
    region: str  # "china", "international", or "global"
    access_info: APIAccessInfo
    pricing: Dict[str, PricingTier]
    models: List[str]

    # Additional metadata
    supports_function_calling: bool = False
    supports_vision: bool = False
    supports_streaming: bool = True
    average_latency_ms: int = 1000


class APICostAnalyzer:
    """
    Comprehensive API cost and accessibility analyzer for LLM providers.

    This class provides detailed pricing information, accessibility analysis,
    and cost comparison tools for different LLM providers across regions.
    """

    # Current pricing data (updated 2024-2025)
    PROVIDERS: Dict[str, ProviderInfo] = {}

    @classmethod
    def _initialize_providers(cls):
        """Initialize provider information"""
        if cls.PROVIDERS:
            return

        # === OpenAI ===
        cls.PROVIDERS["openai"] = ProviderInfo(
            provider_id="openai",
            name="OpenAI",
            region="international",
            access_info=APIAccessInfo(
                provider="openai",
                china_accessible=False,
                international_accessible=True,
                requires_vpn_in_china=True,
                registration_difficulty=DifficultyLevel.HARD,
                documentation_language=["en"],
                official_website="https://openai.com",
                api_docs_url="https://platform.openai.com/docs",
                requires_phone=True,
                requires_credit_card=True,
                requires_id_verification=False,
                requires_business_license=False,
                blocked_in_china=True,
                degraded_in_china=False,
                local_alternative=None,
                free_tier_available=False,
                free_tier_requests_per_day=None,
                free_tier_tokens_per_month=None
            ),
            pricing={
                "gpt-4o": PricingTier("gpt-4o", 2.50, 10.00),
                "gpt-4o-mini": PricingTier("gpt-4o-mini", 0.15, 0.60),
                "gpt-4-turbo": PricingTier("gpt-4-turbo", 10.00, 30.00),
                "gpt-4": PricingTier("gpt-4", 30.00, 60.00),
                "gpt-3.5-turbo": PricingTier("gpt-3.5-turbo", 0.50, 1.50),
            },
            models=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
            supports_function_calling=True,
            supports_vision=True,
            average_latency_ms=800
        )

        # === Anthropic ===
        cls.PROVIDERS["anthropic"] = ProviderInfo(
            provider_id="anthropic",
            name="Anthropic (Claude)",
            region="international",
            access_info=APIAccessInfo(
                provider="anthropic",
                china_accessible=False,
                international_accessible=True,
                requires_vpn_in_china=True,
                registration_difficulty=DifficultyLevel.HARD,
                documentation_language=["en"],
                official_website="https://www.anthropic.com",
                api_docs_url="https://docs.anthropic.com",
                requires_phone=True,
                requires_credit_card=True,
                requires_id_verification=False,
                requires_business_license=False,
                blocked_in_china=True,
                degraded_in_china=False,
                local_alternative=None,
                free_tier_available=False,
                free_tier_requests_per_day=None,
                free_tier_tokens_per_month=None
            ),
            pricing={
                "claude-3-5-sonnet-20241022": PricingTier("claude-3-5-sonnet-20241022", 3.00, 15.00),
                "claude-3-5-haiku-20241022": PricingTier("claude-3-5-haiku-20241022", 0.80, 4.00),
                "claude-3-haiku-20240307": PricingTier("claude-3-haiku-20240307", 0.25, 1.25),
                "claude-3-opus-20240229": PricingTier("claude-3-opus-20240229", 15.00, 75.00),
            },
            models=["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-haiku-20240307", "claude-3-opus-20240229"],
            supports_function_calling=True,
            supports_vision=True,
            average_latency_ms=900
        )

        # === DeepSeek ===
        cls.PROVIDERS["deepseek"] = ProviderInfo(
            provider_id="deepseek",
            name="DeepSeek (China)",
            region="china",
            access_info=APIAccessInfo(
                provider="deepseek",
                china_accessible=True,
                international_accessible=True,
                requires_vpn_in_china=False,
                registration_difficulty=DifficultyLevel.VERY_EASY,
                documentation_language=["zh", "en"],
                official_website="https://www.deepseek.com",
                api_docs_url="https://platform.deepseek.com/api-docs",
                requires_phone=False,
                requires_credit_card=False,  # Supports Alipay/WeChat Pay
                requires_id_verification=False,
                requires_business_license=False,
                blocked_in_china=False,
                degraded_in_china=False,
                local_alternative=None,
                free_tier_available=True,
                free_tier_requests_per_day=None,
                free_tier_tokens_per_month=None
            ),
            pricing={
                "deepseek-chat": PricingTier("deepseek-chat", 0.14, 0.28),
                "deepseek-reasoner": PricingTier("deepseek-reasoner", 0.55, 2.19),
            },
            models=["deepseek-chat", "deepseek-reasoner"],
            supports_function_calling=True,
            supports_vision=False,
            average_latency_ms=600
        )

        # === Qwen (Alibaba Cloud) ===
        cls.PROVIDERS["qwen"] = ProviderInfo(
            provider_id="qwen",
            name="Qwen (Alibaba Cloud)",
            region="china",
            access_info=APIAccessInfo(
                provider="qwen",
                china_accessible=True,
                international_accessible=False,
                requires_vpn_in_china=False,
                registration_difficulty=DifficultyLevel.EASY,
                documentation_language=["zh", "en"],
                official_website="https://tongyi.aliyun.com",
                api_docs_url="https://help.aliyun.com/zh/dashscope/developer-reference/quick-start",
                requires_phone=True,
                requires_credit_card=False,  # Alipay accepted
                requires_id_verification=False,
                requires_business_license=False,
                blocked_in_china=False,
                degraded_in_china=False,
                local_alternative=None,
                free_tier_available=True,
                free_tier_requests_per_day=100,
                free_tier_tokens_per_month=1000000
            ),
            pricing={
                "qwen-turbo": PricingTier("qwen-turbo", 0.30, 0.60),
                "qwen-plus": PricingTier("qwen-plus", 0.40, 1.00),
                "qwen-max": PricingTier("qwen-max", 1.20, 2.00),
            },
            models=["qwen-turbo", "qwen-plus", "qwen-max"],
            supports_function_calling=True,
            supports_vision=True,
            average_latency_ms=700
        )

        # === Zhipu AI (GLM) ===
        cls.PROVIDERS["zhipu"] = ProviderInfo(
            provider_id="zhipu",
            name="Zhipu AI (GLM)",
            region="china",
            access_info=APIAccessInfo(
                provider="zhipu",
                china_accessible=True,
                international_accessible=False,
                requires_vpn_in_china=False,
                registration_difficulty=DifficultyLevel.EASY,
                documentation_language=["zh", "en"],
                official_website="https://open.bigmodel.cn",
                api_docs_url="https://open.bigmodel.cn/dev/api",
                requires_phone=True,
                requires_credit_card=False,  # WeChat Pay accepted
                requires_id_verification=False,
                requires_business_license=False,
                blocked_in_china=False,
                degraded_in_china=False,
                local_alternative=None,
                free_tier_available=True,
                free_tier_requests_per_day=50,
                free_tier_tokens_per_month=500000
            ),
            pricing={
                "glm-4": PricingTier("glm-4", 0.50, 0.50),
                "glm-4-plus": PricingTier("glm-4-plus", 0.70, 0.70),
            },
            models=["glm-4", "glm-4-plus"],
            supports_function_calling=True,
            supports_vision=True,
            average_latency_ms=800
        )

        # === Moonshot (Kimi) ===
        cls.PROVIDERS["moonshot"] = ProviderInfo(
            provider_id="moonshot",
            name="Moonshot AI (Kimi)",
            region="china",
            access_info=APIAccessInfo(
                provider="moonshot",
                china_accessible=True,
                international_accessible=False,
                requires_vpn_in_china=False,
                registration_difficulty=DifficultyLevel.EASY,
                documentation_language=["zh"],
                official_website="https://www.moonshot.cn",
                api_docs_url="https://platform.moonshot.cn/docs",
                requires_phone=True,
                requires_credit_card=False,  # WeChat Pay accepted
                requires_id_verification=False,
                requires_business_license=False,
                blocked_in_china=False,
                degraded_in_china=False,
                local_alternative=None,
                free_tier_available=True,
                free_tier_requests_per_day=100,
                free_tier_tokens_per_month=1000000
            ),
            pricing={
                "moonshot-v1-8k": PricingTier("moonshot-v1-8k", 1.20, 1.20),
                "moonshot-v1-32k": PricingTier("moonshot-v1-32k", 2.40, 2.40),
            },
            models=["moonshot-v1-8k", "moonshot-v1-32k"],
            supports_function_calling=True,
            supports_vision=False,
            average_latency_ms=700
        )

        # === Google ===
        cls.PROVIDERS["google"] = ProviderInfo(
            provider_id="google",
            name="Google (Gemini)",
            region="international",
            access_info=APIAccessInfo(
                provider="google",
                china_accessible=False,
                international_accessible=True,
                requires_vpn_in_china=True,
                registration_difficulty=DifficultyLevel.MEDIUM,
                documentation_language=["en"],
                official_website="https://ai.google.dev",
                api_docs_url="https://ai.google.dev/docs",
                requires_phone=True,
                requires_credit_card=True,
                requires_id_verification=False,
                requires_business_license=False,
                blocked_in_china=True,
                degraded_in_china=False,
                local_alternative=None,
                free_tier_available=True,
                free_tier_requests_per_day=1500,
                free_tier_tokens_per_month=None
            ),
            pricing={
                "gemini-1.5-pro": PricingTier("gemini-1.5-pro", 1.25, 5.00),
                "gemini-1.5-flash": PricingTier("gemini-1.5-flash", 0.075, 0.30),
                "gemini-1.0-pro": PricingTier("gemini-1.0-pro", 0.50, 1.50),
            },
            models=["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"],
            supports_function_calling=True,
            supports_vision=True,
            average_latency_ms=1000
        )

        # === Azure OpenAI ===
        cls.PROVIDERS["azure"] = ProviderInfo(
            provider_id="azure",
            name="Azure OpenAI Service",
            region="international",
            access_info=APIAccessInfo(
                provider="azure",
                china_accessible=True,  # Azure operates in China via 21Vianet
                international_accessible=True,
                requires_vpn_in_china=False,  # Azure China is accessible
                registration_difficulty=DifficultyLevel.VERY_HARD,
                documentation_language=["en", "zh"],
                official_website="https://azure.microsoft.com",
                api_docs_url="https://learn.microsoft.com/azure/ai-services/openai",
                requires_phone=True,
                requires_credit_card=True,
                requires_id_verification=True,
                requires_business_license=True,  # Enterprise account typically required
                blocked_in_china=False,
                degraded_in_china=False,
                local_alternative="Azure China (21Vianet)",
                free_tier_available=True,
                free_tier_requests_per_day=None,
                free_tier_tokens_per_month=None
            ),
            pricing={
                "gpt-4o": PricingTier("gpt-4o", 5.00, 15.00),  # Azure premium pricing
                "gpt-4-turbo": PricingTier("gpt-4-turbo", 10.00, 30.00),
                "gpt-35-turbo": PricingTier("gpt-35-turbo", 0.50, 1.50),
            },
            models=["gpt-4o", "gpt-4-turbo", "gpt-35-turbo"],
            supports_function_calling=True,
            supports_vision=True,
            average_latency_ms=1200
        )

        # === Together AI ===
        cls.PROVIDERS["together"] = ProviderInfo(
            provider_id="together",
            name="Together AI",
            region="international",
            access_info=APIAccessInfo(
                provider="together",
                china_accessible=False,
                international_accessible=True,
                requires_vpn_in_china=True,
                registration_difficulty=DifficultyLevel.EASY,
                documentation_language=["en"],
                official_website="https://www.together.ai",
                api_docs_url="https://docs.together.ai",
                requires_phone=False,
                requires_credit_card=True,
                requires_id_verification=False,
                requires_business_license=False,
                blocked_in_china=True,
                degraded_in_china=False,
                local_alternative=None,
                free_tier_available=True,
                free_tier_requests_per_day=100,
                free_tier_tokens_per_month=500000
            ),
            pricing={
                "mistralai/Mixtral-8x7B-Instruct-v0.1": PricingTier("mistralai/Mixtral-8x7B-Instruct-v0.1", 0.60, 0.60),
                "meta-llama/Llama-3-70b-chat-hf": PricingTier("meta-llama/Llama-3-70b-chat-hf", 0.90, 0.90),
            },
            models=["mistralai/Mixtral-8x7B-Instruct-v0.1", "meta-llama/Llama-3-70b-chat-hf"],
            supports_function_calling=True,
            supports_vision=False,
            average_latency_ms=1500
        )

    def __init__(self, region: Region = Region.INTERNATIONAL):
        """
        Initialize the cost analyzer.

        Args:
            region: Target region for analysis
        """
        self._initialize_providers()
        self.region = region

    def get_provider_info(self, provider_id: str) -> Optional[ProviderInfo]:
        """Get provider information by ID"""
        return self.PROVIDERS.get(provider_id)

    def get_available_providers(
        self,
        china_accessible: Optional[bool] = None
    ) -> List[ProviderInfo]:
        """
        Get list of available providers based on region.

        Args:
            china_accessible: Filter by China accessibility

        Returns:
            List of available providers
        """
        providers = []

        for provider in self.PROVIDERS.values():
            if self.region == Region.CHINA:
                if not provider.access_info.china_accessible:
                    continue
            elif self.region == Region.INTERNATIONAL:
                if not provider.access_info.international_accessible:
                    continue

            if china_accessible is not None:
                if provider.access_info.china_accessible != china_accessible:
                    continue

            providers.append(provider)

        return providers

    def get_model_pricing(self, model_id: str) -> Optional[PricingTier]:
        """Get pricing information for a specific model"""
        for provider in self.PROVIDERS.values():
            if model_id in provider.pricing:
                return provider.pricing[model_id]
        return None

    def compare_costs(
        self,
        models: Optional[List[str]] = None,
        input_tokens: int = 1000,
        output_tokens: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Compare costs across models.

        Args:
            models: List of model IDs to compare (None for all available)
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Sorted list of cost comparisons
        """
        if models is None:
            models = []
            for provider in self.get_available_providers():
                models.extend(provider.models)

        comparisons = []

        for model_id in models:
            pricing = self.get_model_pricing(model_id)
            if not pricing:
                continue

            provider = None
            for p in self.PROVIDERS.values():
                if model_id in p.models:
                    provider = p
                    break

            if not provider:
                continue

            input_cost = (input_tokens / 1000) * pricing.input_cost_per_1k
            output_cost = (output_tokens / 1000) * pricing.output_cost_per_1k
            total_cost = input_cost + output_cost

            comparisons.append({
                "model_id": model_id,
                "provider": provider.provider_id,
                "china_accessible": provider.access_info.china_accessible,
                "input_cost": input_cost,
                "output_cost": output_cost,
                "total_cost": total_cost,
                "cost_per_1k_total": pricing.input_cost_per_1k + pricing.output_cost_per_1k,
            })

        comparisons.sort(key=lambda x: x["total_cost"])

        return comparisons

    def estimate_run_cost(
        self,
        defender_model: str,
        attacker_model: str,
        evaluator_model: str,
        num_profiles: int,
        num_rounds: int = 5,
        avg_input_tokens: int = 1000,
        avg_output_tokens: int = 500
    ) -> Dict[str, Any]:
        """
        Estimate total cost for an adversarial anonymization run.

        Args:
            defender_model: Model ID for defender
            attacker_model: Model ID for attacker
            evaluator_model: Model ID for evaluator
            num_profiles: Number of profiles to process
            num_rounds: Number of adversarial rounds
            avg_input_tokens: Average input tokens per API call
            avg_output_tokens: Average output tokens per API call

        Returns:
            Detailed cost breakdown
        """
        models = {
            "defender": defender_model,
            "attacker": attacker_model,
            "evaluator": evaluator_model
        }

        breakdown = {
            "by_role": {},
            "total_cost": 0.0,
            "cost_per_profile": 0.0,
            "assumptions": {
                "rounds": num_rounds,
                "profiles": num_profiles,
                "avg_input_tokens": avg_input_tokens,
                "avg_output_tokens": avg_output_tokens
            },
            "warnings": []
        }

        for role, model_id in models.items():
            pricing = self.get_model_pricing(model_id)
            provider = None

            for p in self.PROVIDERS.values():
                if model_id in p.models:
                    provider = p
                    break

            if not pricing:
                breakdown["warnings"].append(f"No pricing found for {role} model: {model_id}")
                continue

            # Check accessibility
            if self.region == Region.CHINA and not provider.access_info.china_accessible:
                breakdown["warnings"].append(
                    f"{role} model {model_id} may not be accessible in China"
                )

            # Calculate calls and costs
            calls_per_round = 1
            total_calls = num_rounds * num_profiles * calls_per_round
            total_input_tokens = total_calls * avg_input_tokens
            total_output_tokens = total_calls * avg_output_tokens

            input_cost = (total_input_tokens / 1000) * pricing.input_cost_per_1k
            output_cost = (total_output_tokens / 1000) * pricing.output_cost_per_1k
            total_role_cost = input_cost + output_cost

            breakdown["by_role"][role] = {
                "model_id": model_id,
                "provider": provider.provider_id if provider else "unknown",
                "china_accessible": provider.access_info.china_accessible if provider else False,
                "calls": total_calls,
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "input_cost": input_cost,
                "output_cost": output_cost,
                "total_cost": total_role_cost
            }

            breakdown["total_cost"] += total_role_cost

        breakdown["cost_per_profile"] = breakdown["total_cost"] / num_profiles if num_profiles > 0 else 0

        return breakdown

    def get_accessibility_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive accessibility report.

        Returns:
            Accessibility analysis by region
        """
        report = {
            "china_accessible": [],
            "international_accessible": [],
            "requires_vpn_in_china": [],
            "blocked_in_china": [],
            "registration_difficulty": {
                "very_easy": [],
                "easy": [],
                "medium": [],
                "hard": [],
                "very_hard": []
            },
            "free_tier_available": [],
            "payment_methods": {
                "credit_card_required": [],
                "chinese_payment_supported": []
            }
        }

        for provider in self.PROVIDERS.values():
            # China accessibility
            if provider.access_info.china_accessible:
                report["china_accessible"].append(provider.provider_id)

            if provider.access_info.international_accessible:
                report["international_accessible"].append(provider.provider_id)

            if provider.access_info.requires_vpn_in_china:
                report["requires_vpn_in_china"].append(provider.provider_id)

            if provider.access_info.blocked_in_china:
                report["blocked_in_china"].append(provider.provider_id)

            # Registration difficulty
            difficulty = provider.access_info.registration_difficulty.value
            report["registration_difficulty"][difficulty].append(provider.provider_id)

            # Free tier
            if provider.access_info.free_tier_available:
                report["free_tier_available"].append({
                    "provider": provider.provider_id,
                    "requests_per_day": provider.access_info.free_tier_requests_per_day,
                    "tokens_per_month": provider.access_info.free_tier_tokens_per_month
                })

            # Payment methods
            if provider.access_info.requires_credit_card:
                report["payment_methods"]["credit_card_required"].append(provider.provider_id)

            if not provider.access_info.requires_credit_card:
                report["payment_methods"]["chinese_payment_supported"].append(provider.provider_id)

        return report

    def get_recommended_models(
        self,
        budget_constraint: Optional[float] = None,
        china_accessible: bool = False,
        role: str = "general"
    ) -> List[Dict[str, Any]]:
        """
        Get recommended models based on constraints.

        Args:
            budget_constraint: Maximum cost per 1M tokens (USD)
            china_accessible: Whether model must be accessible in China
            role: Target role (general, defender, attacker, evaluator)

        Returns:
            List of recommended models with details
        """
        recommendations = []

        for provider in self.get_available_providers():
            for model_id, pricing in provider.pricing.items():
                # Check accessibility constraint
                if china_accessible and not provider.access_info.china_accessible:
                    continue

                # Check budget constraint
                cost_per_m = (
                    (pricing.input_cost_per_1k + pricing.output_cost_per_1k) * 500
                )  # Approximate per million tokens

                if budget_constraint and cost_per_m > budget_constraint:
                    continue

                recommendations.append({
                    "model_id": model_id,
                    "provider": provider.provider_id,
                    "cost_per_1k_input": pricing.input_cost_per_1k,
                    "cost_per_1k_output": pricing.output_cost_per_1k,
                    "estimated_cost_per_m_tokens": cost_per_m,
                    "china_accessible": provider.access_info.china_accessible,
                    "registration_difficulty": provider.access_info.registration_difficulty.value,
                    "free_tier": provider.access_info.free_tier_available,
                    "supports_function_calling": provider.supports_function_calling,
                })

        recommendations.sort(key=lambda x: x["estimated_cost_per_m_tokens"])

        return recommendations

    def generate_comparison_table(self) -> str:
        """
        Generate a formatted comparison table of all models.

        Returns:
            Markdown-formatted comparison table
        """
        lines = [
            "# LLM API Cost and Accessibility Comparison",
            "",
            "## Overview",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d')}",
            ""
        ]

        # Cost comparison table
        lines.extend([
            "## Cost Comparison (USD per 1K tokens)",
            "",
            "| Provider | Model | Input | Output | Total | China Accessible |",
            "|----------|-------|-------|--------|-------|------------------|"
        ])

        for provider in sorted(self.PROVIDERS.values(), key=lambda p: p.provider_id):
            for model_id, pricing in provider.pricing.items():
                total = pricing.input_cost_per_1k + pricing.output_cost_per_1k
                china_access = "✓" if provider.access_info.china_accessible else "✗"

                lines.append(
                    f"| {provider.provider_id} | {model_id} | "
                    f"${pricing.input_cost_per_1k:.2f} | "
                    f"${pricing.output_cost_per_1k:.2f} | "
                    f"${total:.2f} | {china_access} |"
                )

        # Accessibility summary
        lines.extend([
            "",
            "## Accessibility Summary",
            "",
            "### China Accessible Providers",
            ""
        ])

        china_providers = [
            p for p in self.PROVIDERS.values()
            if p.access_info.china_accessible
        ]

        if china_providers:
            for provider in china_providers:
                lines.append(f"**{provider.name}**")
                lines.append(f"- Registration Difficulty: {provider.access_info.registration_difficulty.value}")
                lines.append(f"- Free Tier: {'Yes' if provider.access_info.free_tier_available else 'No'}")
                lines.append(f"- Chinese Payment: {'Yes' if not provider.access_info.requires_credit_card else 'No'}")
                lines.append("")
        else:
            lines.append("None found")

        lines.extend([
            "",
            "### Blocked in China (Requires VPN)",
            ""
        ])

        blocked_providers = [
            p for p in self.PROVIDERS.values()
            if p.access_info.blocked_in_china
        ]

        if blocked_providers:
            for provider in blocked_providers:
                lines.append(f"**{provider.name}**")
                lines.append(f"- Registration Difficulty: {provider.access_info.registration_difficulty.value}")
                lines.append("")
        else:
            lines.append("None found")

        return "\n".join(lines)

    def save_analysis(self, output_path: str):
        """
        Save complete analysis to JSON file.

        Args:
            output_path: Path to save the analysis
        """
        output_data = {
            "generated_at": datetime.now().isoformat(),
            "region": self.region.value,
            "providers": {},
            "accessibility_report": self.get_accessibility_report(),
            "cost_comparison": self.compare_costs()
        }

        for provider_id, provider in self.PROVIDERS.items():
            output_data["providers"][provider_id] = {
                "name": provider.name,
                "region": provider.region,
                "china_accessible": provider.access_info.china_accessible,
                "international_accessible": provider.access_info.international_accessible,
                "requires_vpn_in_china": provider.access_info.requires_vpn_in_china,
                "registration_difficulty": provider.access_info.registration_difficulty.value,
                "blocked_in_china": provider.access_info.blocked_in_china,
                "free_tier_available": provider.access_info.free_tier_available,
                "requires_credit_card": provider.access_info.requires_credit_card,
                "supports_function_calling": provider.supports_function_calling,
                "models": {
                    model_id: {
                        "input_cost_per_1k": pricing.input_cost_per_1k,
                        "output_cost_per_1k": pricing.output_cost_per_1k,
                        "currency": pricing.currency
                    }
                    for model_id, pricing in provider.pricing.items()
                }
            }

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)


def analyze_for_project(
    region: str = "international",
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze API costs and accessibility for the project.

    Args:
        region: Target region ("china" or "international")
        output_path: Optional path to save analysis

    Returns:
        Analysis results
    """
    region_enum = Region.CHINA if region == "china" else Region.INTERNATIONAL
    analyzer = APICostAnalyzer(region=region_enum)

    # Generate comprehensive analysis
    analysis = {
        "region": region,
        "recommendations": {
            "china_friendly": analyzer.get_recommended_models(china_accessible=True),
            "international": analyzer.get_recommended_models(china_accessible=False),
            "budget_friendly": analyzer.get_recommended_models(budget_constraint=10),
        },
        "accessibility": analyzer.get_accessibility_report(),
        "cost_comparison": analyzer.compare_costs(),
        "sample_cost_estimate": analyzer.estimate_run_cost(
            defender_model="gpt-4o-mini" if region == "international" else "deepseek-chat",
            attacker_model="gpt-4o-mini" if region == "international" else "deepseek-reasoner",
            evaluator_model="gpt-4o-mini" if region == "international" else "qwen-plus",
            num_profiles=100,
            num_rounds=5
        )
    }

    if output_path:
        analyzer.save_analysis(output_path)

    return analysis


if __name__ == "__main__":
    # Generate and save analysis
    print("Generating API cost and accessibility analysis...")

    # International analysis
    int_analysis = analyze_for_project("international", "results/api_analysis_international.json")
    print(f"\nInternational Region Analysis:")
    print(f"- China-accessible providers: {len([p for p in int_analysis['accessibility']['china_accessible']])}")
    print(f"- Blocked providers: {len([p for p in int_analysis['accessibility']['blocked_in_china']])}")

    # China analysis
    china_analysis = analyze_for_project("china", "results/api_analysis_china.json")
    print(f"\nChina Region Analysis:")
    print(f"- China-accessible providers: {len([p for p in china_analysis['accessibility']['china_accessible']])}")

    # Generate markdown report
    analyzer = APICostAnalyzer(region=Region.INTERNATIONAL)
    markdown = analyzer.generate_comparison_table()

    report_path = Path("results/api_cost_comparison.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(markdown, encoding='utf-8')

    print(f"\nMarkdown report saved to: {report_path}")
    print("\nAnalysis complete!")

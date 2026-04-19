"""
Base Provider Module for LLM Heterogeneous Pool

This module defines the base interface for all model providers.
Each provider is implemented as an independent module that can be
loaded/used without affecting other providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ProviderState(Enum):
    """Status enum for provider availability"""
    AVAILABLE = "available"
    UNCONFIGURED = "unconfigured"  # No API key configured
    UNREACHABLE = "unreachable"    # Network/API issues
    DISABLED = "disabled"          # Explicitly disabled


@dataclass
class ProviderInfo:
    """Static information about a provider"""
    provider_id: str
    name: str
    region: str  # "china", "international", or "global"

    # Accessibility
    china_accessible: bool
    requires_vpn_in_china: bool
    registration_difficulty: str

    # Documentation
    docs_url: str
    official_website: str


@dataclass
class ModelInfo:
    """Information about a specific model"""
    model_id: str
    provider_id: str
    name: str

    # Capability scores
    reasoning_capability: float
    language_understanding: float
    instruction_following: float
    attack_capability: float
    defense_capability: float
    evaluation_capability: float

    # Role suitability (calculated)
    defender_score: float
    attacker_score: float
    evaluator_score: float

    # Pricing
    cost_per_1k_input: float
    cost_per_1k_output: float

    # Technical specs
    max_tokens: int
    supports_function_calling: bool
    supports_vision: bool
    average_latency_ms: int


@dataclass
class ProviderStatus:
    """Runtime status of a provider"""
    provider_id: str
    status: ProviderState
    error_message: Optional[str] = None
    last_checked: Optional[str] = None
    available_models: List[str] = None

    def __post_init__(self):
        if self.available_models is None:
            self.available_models = []


class BaseProviderModule(ABC):
    """
    Base class for all provider modules.

    Each provider module must:
    1. Be independently loadable
    2. Have its own availability check
    3. Handle its own errors gracefully
    4. Provide model information
    5. Support credential checking
    """

    def __init__(self):
        self._status: ProviderStatus = None
        self._models: Dict[str, ModelInfo] = {}

    @property
    @abstractmethod
    def provider_info(self) -> ProviderInfo:
        """Return static provider information"""
        pass

    @abstractmethod
    def check_availability(self) -> ProviderStatus:
        """
        Check if this provider is available.

        Should verify:
        - API credentials are configured
        - API is reachable
        - Which models are available

        Returns:
            ProviderStatus with details
        """
        pass

    @abstractmethod
    def get_models(self) -> Dict[str, ModelInfo]:
        """
        Get all models from this provider.

        Returns:
            Dictionary of model_id -> ModelInfo
        """
        pass

    @abstractmethod
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """
        Get information about a specific model.

        Args:
            model_id: Model identifier

        Returns:
            ModelInfo or None if model not found
        """
        pass

    @abstractmethod
    def create_model_instance(self, model_id: str, **kwargs):
        """
        Create a model instance for use.

        Args:
            model_id: Model to instantiate
            **kwargs: Additional parameters

        Returns:
            Model instance or None if creation fails
        """
        pass

    def is_available(self) -> bool:
        """Quick check if provider is available"""
        if self._status is None:
            self._status = self.check_availability()
        return self._status.status == ProviderStatus.AVAILABLE

    def get_status(self) -> ProviderStatus:
        """Get current provider status"""
        if self._status is None:
            self._status = self.check_availability()
        return self._status

    def refresh_status(self):
        """Force refresh the provider status"""
        self._status = self.check_availability()
        return self._status

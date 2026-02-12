try:
    from .azure_anonymizer import AzureAnonymizer
    AZURE_ANON_AVAILABLE = True
except ImportError:
    AZURE_ANON_AVAILABLE = False

from .llm_anonymizers import LLMFullAnonymizer, LLMBaselineAnonymizer
from .span_anonymizer import SpanAnonymizer
from .anonymizer import Anonymizer

from src.configs import AnonymizationConfig
from src.models.model_factory import get_model

def get_anonymizer(cfg: AnonymizationConfig) -> Anonymizer:

    if cfg.anonymizer.anon_type == "azure":
        if not AZURE_ANON_AVAILABLE:
            raise ImportError("Azure SDK is required for AzureAnonymizer. Install it with: pip install azure-ai-textanalytics")
        return AzureAnonymizer(cfg.anonymizer)
    elif cfg.anonymizer.anon_type == "llm":
        model = get_model(cfg.anon_model)
        return LLMFullAnonymizer(cfg.anonymizer, model)
    elif cfg.anonymizer.anon_type == "llm_base":
        model = get_model(cfg.anon_model)
        return LLMBaselineAnonymizer(cfg.anonymizer, model)
    elif cfg.anonymizer.anon_type == "span":
        return SpanAnonymizer(cfg.anonymizer)
    elif cfg.anonymizer.anon_type in ["adversarial_llm", "span_llm"]:
        # For adversarial mode, use adversarial framework
        # Return the span anonymizer as base for individual rounds
        return SpanAnonymizer(cfg.anonymizer)
    else:
        raise ValueError(f"Unknown anonymizer type {cfg.anonymizer.anon_type}")
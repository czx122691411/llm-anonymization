try:
    from .azure_anonymizer import AzureAnonymizer
    AZURE_ANON_AVAILABLE = True
except ImportError:
    AZURE_ANON_AVAILABLE = False

from .llm_anonymizers import LLMFullAnonymizer, LLMBaselineAnonymizer
from .llm_text_anonymizer import LLMTextAnonymizer
from .span_anonymizer import SpanAnonymizer
from .anonymizer import Anonymizer

try:
    from .trace_anonymizer import TRACEAnonymizerWrapper, TRACEAnonymizerWithInference
    TRACE_ANON_AVAILABLE = True
except ImportError:
    TRACE_ANON_AVAILABLE = False

try:
    from src.defense.trace_rps_unified import TRACERPSDefense
    TRACE_RPS_AVAILABLE = True
except ImportError:
    TRACE_RPS_AVAILABLE = False

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
    elif cfg.anonymizer.anon_type == "llm_text":
        model = get_model(cfg.anon_model)
        prompt_level = getattr(cfg.anonymizer, 'prompt_level', 2)
        return LLMTextAnonymizer(model, prompt_level)
    elif cfg.anonymizer.anon_type == "span":
        return SpanAnonymizer(cfg.anonymizer)
    elif cfg.anonymizer.anon_type == "trace":
        if not TRACE_ANON_AVAILABLE:
            raise ImportError("TRACE anonymizer not available. Check src/anonymized/anonymizers/trace_anonymizer.py")
        return TRACEAnonymizerWrapper(cfg.anonymizer)
    elif cfg.anonymizer.anon_type == "trace_inference":
        if not TRACE_ANON_AVAILABLE:
            raise ImportError("TRACE anonymizer not available. Check src/anonymized/anonymizers/trace_anonymizer.py")
        return TRACEAnonymizerWithInference(cfg.anonymizer)
    elif cfg.anonymizer.anon_type == "rps":
        if not TRACE_RPS_AVAILABLE:
            raise ImportError("TRACE-RPS not available. Check src/defense/trace_rps_unified.py")
        # RPS uses TRACE-RPS defense with TRACE disabled
        from src.defense.trace_rps_unified import TRACERPSDefense
        from src.configs.config import TRACEConfig, RPSConfig
        trace_cfg = TRACEConfig(enabled=False)
        rps_cfg = RPSConfig(enabled=True)
        # Create a wrapper that uses the defense system
        class RPSAnonymizerWrapper(Anonymizer):
            def __init__(self, defense_config, rps_config):
                self.defense = TRACERPSDefense(defense_config, rps_config)
            def anonymize(self, text: str) -> str:
                import asyncio
                result = asyncio.run(self.defense.defend(text, enable_trace=False, enable_rps=True))
                return result.final_text
            def anonymize_profiles(self, profiles):
                for profile in profiles:
                    latest = profile.get_latest_comments()
                    anon_comments = []
                    for comment in latest.comments:
                        anon_text = self.anonymize(comment.text)
                        anon_comments.append(comment.__class__(
                            text=anon_text,
                            subreddit=comment.subreddit,
                            user=comment.user,
                            timestamp=comment.timestamp,
                            pii={}
                        ))
                    from src.reddit.reddit_types import AnnotatedComments
                    new_annotations = AnnotatedComments(
                        comments=anon_comments,
                        review_pii=latest.review_pii,
                        predictions=latest.predictions,
                        evaluations=latest.evaluations,
                        utility=latest.utility
                    )
                    yield profile.__class__(
                        username=profile.username,
                        annotated_comments=profile.comments + [new_annotations],
                        review_pii=profile.review_pii,
                        predictions=profile.predictions,
                        evaluations=profile.evaluations
                    )
        return RPSAnonymizerWrapper(trace_cfg, rps_cfg)
    elif cfg.anonymizer.anon_type == "trace_rps":
        if not TRACE_RPS_AVAILABLE:
            raise ImportError("TRACE-RPS not available. Check src/defense/trace_rps_unified.py")
        # Full TRACE-RPS unified defense
        from src.defense.trace_rps_unified import TRACERPSDefense
        from src.configs.config import TRACEConfig, RPSConfig
        trace_cfg = TRACEConfig(
            enabled=getattr(cfg.task_config, 'trace', TRACEConfig()).enabled,
            analyzer_model=getattr(cfg.task_config, 'trace', TRACEConfig()).analyzer_model
        )
        rps_cfg = RPSConfig(
            enabled=getattr(cfg.task_config, 'rps', RPSConfig()).enabled,
            defender_model=getattr(cfg.task_config, 'rps', RPSConfig()).defender_model,
            attacker_model=getattr(cfg.task_config, 'rps', RPSConfig()).attacker_model
        )
        class TRACERPSAnonymizerWrapper(Anonymizer):
            def __init__(self, defense_config, rps_config):
                self.defense = TRACERPSDefense(defense_config, rps_config)
            def anonymize(self, text: str) -> str:
                import asyncio
                result = asyncio.run(self.defense.defend(text, enable_trace=True, enable_rps=True))
                return result.final_text
            def anonymize_profiles(self, profiles):
                for profile in profiles:
                    latest = profile.get_latest_comments()
                    anon_comments = []
                    for comment in latest.comments:
                        anon_text = self.anonymize(comment.text)
                        anon_comments.append(comment.__class__(
                            text=anon_text,
                            subreddit=comment.subreddit,
                            user=comment.user,
                            timestamp=comment.timestamp,
                            pii={}
                        ))
                    from src.reddit.reddit_types import AnnotatedComments
                    new_annotations = AnnotatedComments(
                        comments=anon_comments,
                        review_pii=latest.review_pii,
                        predictions=latest.predictions,
                        evaluations=latest.evaluations,
                        utility=latest.utility
                    )
                    yield profile.__class__(
                        username=profile.username,
                        annotated_comments=profile.comments + [new_annotations],
                        review_pii=profile.review_pii,
                        predictions=profile.predictions,
                        evaluations=profile.evaluations
                    )
        return TRACERPSAnonymizerWrapper(trace_cfg, rps_cfg)
    elif cfg.anonymizer.anon_type in ["adversarial_llm", "span_llm"]:
        # For adversarial mode, use adversarial framework
        # Return the span anonymizer as base for individual rounds
        return SpanAnonymizer(cfg.anonymizer)
    else:
        raise ValueError(f"Unknown anonymizer type {cfg.anonymizer.anon_type}")
from src.configs import ModelConfig

from .model import BaseModel
from .open_ai import OpenAIGPT
from .deepseek import DeepSeekModel
from .qwen import QwenModel


def get_model(config: ModelConfig) -> BaseModel:
    if config.provider == "openai" or config.provider == "azure":
        return OpenAIGPT(config)
    elif config.provider == "hf":
        from .hf_model import HFModel
        return HFModel(config)
    elif config.provider == "ner":
        from .ner_baseline import NERModel
        return NERModel(config)
    elif config.provider == "ollama":
        from .ollama import OllamaModel
        return OllamaModel(config)
    elif config.provider == "together":
        from .together import TogetherModel
        return TogetherModel(config)
    elif config.provider == "anthropic":
        from .anthropic import AnthropicModel
        return AnthropicModel(config)
    elif config.provider == "deepseek":
        return DeepSeekModel(config)
    elif config.provider == "qwen":
        return QwenModel(config)
    elif config.provider == "loc":
        raise NotImplementedError

    else:
        raise NotImplementedError

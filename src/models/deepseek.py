from typing import List, Dict, Tuple, Iterator

import openai
import time
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from openai.error import RateLimitError

from src.configs import ModelConfig
from src.prompts import Prompt, Conversation

from .model import BaseModel


class DeepSeekModel(BaseModel):
    """DeepSeek API model using OpenAI-compatible interface.

    Supports:
    - deepseek-chat (DeepSeek-V3.2)
    - deepseek-reasoner (DeepSeek-R1)
    """

    # Map for lookup name -> actual API model name
    MODEL_MAP = {
        "gpt-4-1106-preview": "deepseek-chat",
        "deepseek-chat": "deepseek-chat",
        "deepseek-reasoner": "deepseek-reasoner",
    }

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.config = config

        # Determine actual API model name
        self.api_model_name = self.MODEL_MAP.get(config.name, config.name)

        # Set DeepSeek API base URL
        openai.api_base = "https://api.deepseek.com"

        # Set default args
        if "temperature" not in self.config.args.keys():
            self.config.args["temperature"] = 0.0
        if "max_tokens" not in self.config.args.keys():
            self.config.args["max_tokens"] = 2000

    def _predict_call(self, input: List[Dict[str, str]]) -> str:
        response = openai.ChatCompletion.create(
            model=self.api_model_name, messages=input, **self.config.args
        )
        return response["choices"][0]["message"]["content"]

    def predict(self, input: Prompt, **kwargs) -> str:
        messages: List[Dict[str, str]] = []

        if input.system_prompt is not None:
            messages.append(
                {
                    "role": "system",
                    "content": input.system_prompt,
                }
            )
        else:
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert investigator and detective with years of experience in online profiling and text analysis.",
                }
            ]

        messages += [
            {"role": "user", "content": self.apply_model_template(input.get_prompt())}
        ]

        guess = self._predict_call(messages)

        return guess

    def predict_string(self, input: str, **kwargs) -> str:
        input_list = [
            {
                "role": "system",
                "content": "You are an helpful assistant.",
            },
            {"role": "user", "content": input},
        ]

        guess = self._predict_call(input_list)

        return guess

    def predict_multi(
        self, inputs: List[Prompt], **kwargs
    ) -> Iterator[Tuple[Prompt, str]]:
        max_workers = kwargs["max_workers"] if "max_workers" in kwargs else 4
        base_timeout = kwargs["timeout"] if "timeout" in kwargs else 120

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            ids_to_do = list(range(len(inputs)))
            retry_ctr = 0
            timeout = base_timeout

            while len(ids_to_do) > 0 and retry_ctr <= len(inputs):
                results = executor.map(
                    lambda id: (id, inputs[id], self.predict(inputs[id])),
                    ids_to_do,
                    timeout=timeout,
                )
                try:
                    for res in tqdm(
                        results,
                        total=len(ids_to_do),
                        desc="Profiles",
                        position=1,
                        leave=False,
                    ):
                        id, orig, answer = res
                        yield (orig, answer)
                        ids_to_do.remove(id)
                except TimeoutError:
                    print(f"Timeout: {len(ids_to_do)} prompts remaining")
                except RateLimitError as r:
                    print(f"Rate_limit {r}")
                    time.sleep(30)
                    continue
                except Exception as e:
                    print(f"Exception: {e}")
                    time.sleep(10)
                    continue

                if len(ids_to_do) == 0:
                    break

                time.sleep(2 * retry_ctr)
                timeout *= 2
                timeout = min(120, timeout)
                retry_ctr += 1

    def continue_conversation(self, input: Conversation, **kwargs) -> str:
        input_list: List[Dict[str, str]] = [
            {
                "role": "system",
                "content": input.system_prompt,
            }
        ]

        for message in input.prompts:
            assert message.role is not None
            input_list.append(
                {
                    "role": message.role,
                    "content": message.get_prompt(),
                }
            )

        guess = None
        while guess is None:
            try:
                guess = self._predict_call(input_list)
            except RateLimitError as r:
                time.sleep(30)
                continue

        return guess

from typing import List, Dict, Tuple, Iterator

import dashscope
from dashscope import Generation
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import time

from src.configs import ModelConfig
from src.prompts import Prompt, Conversation

from .model import BaseModel


class QwenModel(BaseModel):
    """Qwen API model using Alibaba DashScope interface.

    Supports:
    - qwen-turbo (Fast, cost-effective)
    - qwen-plus (Balanced performance)
    - qwen-max (Highest capability)
    """

    # Map for lookup name -> actual API model name
    MODEL_MAP = {
        "qwen-turbo": "qwen-turbo",
        "qwen-plus": "qwen-plus",
        "qwen-max": "qwen-max",
        "qwen-max-longcontext": "qwen-max-longcontext",
    }

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.config = config

        # Determine actual API model name
        self.api_model_name = self.MODEL_MAP.get(config.name, config.name)

        # Set default args
        if "temperature" not in self.config.args.keys():
            self.config.args["temperature"] = 0.0
        if "max_tokens" not in self.config.args.keys():
            self.config.args["max_tokens"] = 2000

        # Configure API key if provided in args
        if "api_key" in self.config.args.keys():
            dashscope.api_key = self.config.args["api_key"]

    def _predict_call(self, input: List[Dict[str, str]]) -> str:
        """Make a single API call to Qwen"""
        response = Generation.call(
            model=self.api_model_name,
            messages=input,
            result_format='message',
            **self.config.args
        )

        if response.status_code != 200:
            raise Exception(f"Qwen API error: {response.code} - {response.message}")

        return response.output.choices[0]['message']['content']

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
                except Exception as e:
                    # Handle rate limiting or other errors
                    if "rate limit" in str(e).lower() or "429" in str(e):
                        print(f"Rate limit error: {e}")
                        time.sleep(30)
                        continue
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
            except Exception as e:
                if "rate limit" in str(e).lower() or "429" in str(e):
                    time.sleep(30)
                    continue
                time.sleep(10)
                continue

        return guess

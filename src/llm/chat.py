import os
import time
from dataclasses import dataclass

from dotenv import load_dotenv
from openai import OpenAI


@dataclass
class ChatResult:
    data: object
    duration_ms: int
    prompt_tokens: int | None
    completion_tokens: int | None


class ChatClient:
    """Rozmowa z modelem czatu (LM Studio lub inne API zgodne z OpenAI) z wymuszonym schematem JSON."""

    def __init__(self, timeout=180):
        load_dotenv()
        self.client = OpenAI(base_url=os.environ["MODEL_URL"], api_key=os.environ["API_KEY"], timeout=timeout)
        self.model = os.environ["CHAT_MODEL"]

    def structured(self, system, user, schema, temperature=1.0, top_p=0.95, max_tokens=2000, reasoning_effort="none"):
        """Zwraca odpowiedź zwalidowaną przez model Pydantic `schema`.

        reasoning_effort="none" wyłącza tryb myślenia (Gemma 4, Qwen3) — przy ocenie z gotowymi faktami
        nie jest potrzebny, a potrafi zużyć cały limit tokenów, zanim model zacznie odpowiadać.
        """
        started = time.perf_counter()
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": schema.__name__, "schema": schema.model_json_schema(), "strict": True},
            },
        )
        usage = response.usage
        return ChatResult(
            data=schema.model_validate_json(response.choices[0].message.content),
            duration_ms=round((time.perf_counter() - started) * 1000),
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
        )

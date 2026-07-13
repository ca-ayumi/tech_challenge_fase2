from __future__ import annotations

import os

try:
    from google import genai as _google_genai
    from google.genai import types as _google_types
except ImportError:
    _google_genai = None
    _google_types = None

try:
    from openai import OpenAI as _OpenAI
except ImportError:
    _OpenAI = None


class LLMIndisponivel(RuntimeError):
    pass


def _autodetectar_provedor() -> str:
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        return "gemini"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    return ""


class ClienteLLM:
    def __init__(
        self,
        provedor: str | None = None,
        api_key: str | None = None,
        modelo: str | None = None,
        temperatura: float = 0.3,
    ) -> None:
        self.provedor = (provedor or os.getenv("LLM_PROVIDER") or _autodetectar_provedor()).lower()
        self.temperatura = temperatura
        self._client = None

        if self.provedor == "gemini":
            self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            self.modelo = modelo or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        elif self.provedor == "openai":
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            self.modelo = modelo or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        else:
            self.api_key = api_key
            self.modelo = modelo or "(nenhum)"

    @property
    def _sdk_ok(self) -> bool:
        if self.provedor == "gemini":
            return _google_genai is not None
        if self.provedor == "openai":
            return _OpenAI is not None
        return False

    @property
    def disponivel(self) -> bool:
        return bool(self._sdk_ok and self.api_key)

    def _obter_client(self):
        if self._client is not None:
            return self._client
        if not self.api_key:
            raise LLMIndisponivel(
                "Nenhuma chave de LLM configurada. Defina GEMINI_API_KEY "
                "(Gemini) ou OPENAI_API_KEY (OpenAI) no arquivo .env."
            )
        if self.provedor == "gemini":
            if _google_genai is None:
                raise LLMIndisponivel(
                    "Biblioteca 'google-genai' nao instalada. Rode 'pip install google-genai'."
                )
            self._client = _google_genai.Client(api_key=self.api_key)
        elif self.provedor == "openai":
            if _OpenAI is None:
                raise LLMIndisponivel(
                    "Biblioteca 'openai' nao instalada. Rode 'pip install openai'."
                )
            self._client = _OpenAI(api_key=self.api_key)
        else:
            raise LLMIndisponivel(f"Provedor de LLM desconhecido: '{self.provedor}'.")
        return self._client

    def chat(self, system: str, user: str, max_tokens: int = 900) -> str:
        client = self._obter_client()
        if self.provedor == "gemini":
            return self._chat_gemini(client, system, user, max_tokens)
        return self._chat_openai(client, system, user, max_tokens)

    def _chat_gemini(self, client, system: str, user: str, max_tokens: int) -> str:
        resposta = client.models.generate_content(
            model=self.modelo,
            contents=user,
            config=_google_types.GenerateContentConfig(
                system_instruction=system,
                temperature=self.temperatura,
                max_output_tokens=max_tokens,
            ),
        )
        return (resposta.text or "").strip()

    def _chat_openai(self, client, system: str, user: str, max_tokens: int) -> str:
        resposta = client.chat.completions.create(
            model=self.modelo,
            temperature=self.temperatura,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return (resposta.choices[0].message.content or "").strip()

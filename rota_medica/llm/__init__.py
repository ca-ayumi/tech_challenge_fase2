"""Integracao com LLM (OpenAI) para instrucoes, relatorios e perguntas."""

from .cliente import ClienteLLM, LLMIndisponivel
from .servico import ServicoLLM

__all__ = ["ClienteLLM", "LLMIndisponivel", "ServicoLLM"]

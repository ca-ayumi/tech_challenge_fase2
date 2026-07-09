"""Servico de alto nivel para gerar textos a partir de uma solucao de rotas.

Usa a LLM (OpenAI) quando ha chave configurada. Caso contrario, gera um texto
determinístico baseado em template (fallback offline), garantindo que a
demonstracao e os testes funcionem sem depender de rede/chave.
"""
from __future__ import annotations

from ..dominio import ProblemaRoteamento, Rota, Solucao
from . import prompts
from .cliente import ClienteLLM
from .contexto import solucao_para_texto


class ServicoLLM:
    def __init__(self, cliente: ClienteLLM | None = None) -> None:
        self.cliente = cliente or ClienteLLM()
        # Guarda a ultima falha de chamada a LLM (util para a interface exibir).
        self.ultimo_erro: str | None = None

    @property
    def usando_llm(self) -> bool:
        return self.cliente.disponivel

    def _chamar(self, system: str, user: str, fallback: str,
                max_tokens: int = 900) -> str:
        """Tenta a LLM; em caso de indisponibilidade ou erro, usa o fallback.

        Nunca levanta excecao: assim a interface continua funcional mesmo com
        problemas de cota, rede ou autenticacao na API da OpenAI.
        """
        self.ultimo_erro = None
        if not self.cliente.disponivel:
            return fallback
        try:
            return self.cliente.chat(system, user, max_tokens=max_tokens)
        except Exception as exc:  # noqa: BLE001 - degrada para o gerador local
            self.ultimo_erro = _mensagem_erro(exc)
            aviso = (
                f"> **Aviso:** nao foi possivel usar a LLM ({self.ultimo_erro}). "
                "Exibindo conteudo gerado localmente.\n\n"
            )
            return aviso + fallback

    def instrucoes_motorista(self, rota: Rota, problema: ProblemaRoteamento) -> str:
        texto = _rota_para_texto(rota, problema)
        return self._chamar(
            prompts.SYSTEM_LOGISTICA,
            prompts.prompt_instrucoes_motorista(texto),
            _instrucoes_fallback(rota, problema),
        )

    def relatorio(self, solucao: Solucao, problema: ProblemaRoteamento,
                  periodo: str = "diario") -> str:
        contexto = solucao_para_texto(solucao, problema)
        return self._chamar(
            prompts.SYSTEM_LOGISTICA,
            prompts.prompt_relatorio(contexto, periodo),
            _relatorio_fallback(solucao, problema, periodo),
            max_tokens=1100,
        )

    def sugestoes(self, solucao: Solucao, problema: ProblemaRoteamento) -> str:
        contexto = solucao_para_texto(solucao, problema)
        return self._chamar(
            prompts.SYSTEM_LOGISTICA,
            prompts.prompt_melhorias(contexto),
            _sugestoes_fallback(solucao),
        )

    def responder(self, pergunta: str, solucao: Solucao,
                  problema: ProblemaRoteamento) -> str:
        contexto = solucao_para_texto(solucao, problema)
        return self._chamar(
            prompts.SYSTEM_LOGISTICA,
            prompts.prompt_pergunta(contexto, pergunta),
            _resposta_fallback(pergunta, solucao),
        )


def _mensagem_erro(exc: Exception) -> str:
    """Converte excecoes da LLM (OpenAI/Gemini) em mensagens curtas e amigaveis."""
    nome = type(exc).__name__
    texto = str(exc)
    if ("RateLimit" in nome or "insufficient_quota" in texto
            or "RESOURCE_EXHAUSTED" in texto or "429" in texto):
        return "cota/creditos da API esgotados (erro 429)"
    if ("Authentication" in nome or "invalid_api_key" in texto
            or "API_KEY_INVALID" in texto or "401" in texto or "403" in texto):
        return "chave da API invalida ou sem permissao"
    if "APIConnection" in nome or "Timeout" in nome or "ConnectError" in nome:
        return "falha de conexao com a API"
    return f"{nome}"


# ---------------------------------------------------------------------- #
# Helpers
# ---------------------------------------------------------------------- #
def _rota_para_texto(rota: Rota, problema: ProblemaRoteamento) -> str:
    linhas = [
        f"Deposito: {problema.deposito.nome}",
        f"Veiculo: {rota.veiculo.nome} "
        f"(capacidade {rota.veiculo.capacidade_kg:.0f} kg, "
        f"autonomia {rota.veiculo.autonomia_km:.0f} km)",
        f"Carga: {rota.carga_kg:.1f} kg ({rota.ocupacao * 100:.0f}% de ocupacao)",
        f"Distancia: {rota.distancia_km:.1f} km | Tempo estimado: "
        f"{rota.tempo_total_min:.0f} min",
        "Paradas:",
    ]
    for ordem, e in enumerate(rota.entregas, start=1):
        linhas.append(
            f"  {ordem}. {e.nome} | {e.tipo} | prioridade {e.prioridade.rotulo} "
            f"| {e.demanda_kg:.1f} kg"
        )
    return "\n".join(linhas)


# --- Fallbacks offline (sem LLM) --------------------------------------- #
def _instrucoes_fallback(rota: Rota, problema: ProblemaRoteamento) -> str:
    linhas = [
        f"INSTRUCOES DE ENTREGA - {rota.veiculo.nome}",
        "(Texto gerado localmente - configure OPENAI_API_KEY para usar a LLM)",
        "",
        "Checklist de saida:",
        f"- Conferir carga total: {rota.carga_kg:.1f} kg / "
        f"{rota.veiculo.capacidade_kg:.0f} kg de capacidade",
        "- Conferir lote e validade dos itens; separar itens criticos e de cadeia de frio",
        f"- Combustivel/autonomia suficiente para {rota.distancia_km:.1f} km "
        f"(autonomia {rota.veiculo.autonomia_km:.0f} km)",
        "",
        "Sequencia de paradas (partindo do deposito):",
    ]
    for ordem, e in enumerate(rota.entregas, start=1):
        alerta = " [ATENCAO: item critico]" if e.prioridade.rotulo == "Critico" else ""
        linhas.append(f"  {ordem}. {e.nome} - entregar '{e.tipo}' ({e.demanda_kg:.1f} kg)"
                      f" - prioridade {e.prioridade.rotulo}{alerta}")
    linhas += [
        "  -> Retornar ao deposito.",
        "",
        "Seguranca e imprevistos:",
        "- Priorize itens criticos; em caso de atraso, comunique a central.",
        "- Recebedor ausente: registrar ocorrencia e reagendar itens nao criticos.",
        "- Problema com item de cadeia de frio: nao entregar e retornar imediatamente.",
    ]
    return "\n".join(linhas)


def _relatorio_fallback(solucao: Solucao, problema: ProblemaRoteamento,
                        periodo: str) -> str:
    r = solucao
    linhas = [
        f"RELATORIO {periodo.upper()} DE EFICIENCIA LOGISTICA",
        "(Texto gerado localmente - configure OPENAI_API_KEY para usar a LLM)",
        "",
        "Resumo executivo:",
        f"- {r.n_entregas_atendidas} entregas atendidas com {r.n_veiculos_usados} "
        f"veiculo(s), percorrendo {r.distancia_total_km:.1f} km.",
        "",
        "Indicadores principais:",
        f"- Distancia total: {r.distancia_total_km:.1f} km",
        f"- Custo estimado: R$ {r.custo_total_reais:.2f}",
        f"- Tempo total estimado: {r.tempo_total_min:.0f} min",
        f"- Veiculos utilizados: {r.n_veiculos_usados}",
        f"- Entregas nao atendidas: {len(r.nao_atendidas)}",
        "",
        "Analise por rota:",
    ]
    for i, rota in enumerate(r.rotas_utilizadas, start=1):
        linhas.append(
            f"- Rota {i} ({rota.veiculo.nome}): {len(rota.entregas)} paradas, "
            f"{rota.distancia_km:.1f} km, ocupacao {rota.ocupacao * 100:.0f}%."
        )
    if r.nao_atendidas:
        linhas.append("")
        linhas.append("Riscos e alertas:")
        for e in r.nao_atendidas:
            linhas.append(f"- Nao atendida: {e.nome} (prioridade {e.prioridade.rotulo}).")
    linhas.append("")
    linhas.append("Conclusao: operacao " + ("viavel." if r.viavel
                  else "com pendencias que exigem atencao."))
    return "\n".join(linhas)


def _sugestoes_fallback(solucao: Solucao) -> str:
    sugestoes = ["SUGESTOES DE MELHORIA (geradas localmente)"]
    ocupacoes = [r.ocupacao for r in solucao.rotas_utilizadas]
    if ocupacoes and (sum(ocupacoes) / len(ocupacoes)) < 0.6:
        sugestoes.append("- Consolidar rotas: ocupacao media baixa dos veiculos.")
    if solucao.nao_atendidas:
        sugestoes.append("- Adicionar veiculos ou capacidade: ha entregas nao atendidas.")
    sugestoes += [
        "- Agrupar entregas por regiao para reduzir deslocamentos.",
        "- Reservar um veiculo agil (moto) para itens criticos.",
        "- Revisar janelas de entrega para reduzir tempo ocioso.",
    ]
    return "\n".join(sugestoes)


def _resposta_fallback(pergunta: str, solucao: Solucao) -> str:
    return (
        "(Resposta local - configure OPENAI_API_KEY para respostas com LLM)\n"
        f"Pergunta: {pergunta}\n"
        f"Dados atuais: {solucao.n_entregas_atendidas} entregas atendidas, "
        f"{solucao.distancia_total_km:.1f} km, {solucao.n_veiculos_usados} veiculo(s), "
        f"custo R$ {solucao.custo_total_reais:.2f}, "
        f"{len(solucao.nao_atendidas)} nao atendidas."
    )

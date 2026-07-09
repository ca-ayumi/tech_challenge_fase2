"""Testes do servico de LLM no modo offline (sem chave), via fallback local."""
from rota_medica.dados import gerar_problema
from rota_medica.llm import ClienteLLM, ServicoLLM
from rota_medica.llm.contexto import solucao_para_dict, solucao_para_texto
from rota_medica.otimizacao import AlgoritmoGenetico, ConfigGenetico


def _solucao():
    p = gerar_problema(12, 3, seed=42)
    cfg = ConfigGenetico(tamanho_populacao=40, n_geracoes=60, seed=42)
    return AlgoritmoGenetico(p, cfg).executar().solucao, p


def _servico_offline():
    # Forca ausencia de chave para exercitar o fallback determinístico.
    return ServicoLLM(ClienteLLM(api_key=None))


def test_cliente_indisponivel_sem_chave():
    assert ClienteLLM(api_key=None).disponivel is False


def test_contexto_texto_e_dict():
    sol, p = _solucao()
    texto = solucao_para_texto(sol, p)
    assert "Resumo geral" in texto
    d = solucao_para_dict(sol, p)
    assert d["resumo"]["veiculos_usados"] == sol.n_veiculos_usados
    assert len(d["rotas"]) == sol.n_veiculos_usados


def test_instrucoes_fallback():
    sol, p = _solucao()
    servico = _servico_offline()
    rota = sol.rotas_utilizadas[0]
    texto = servico.instrucoes_motorista(rota, p)
    assert "INSTRUCOES DE ENTREGA" in texto
    assert "Checklist" in texto


def test_relatorio_fallback():
    sol, p = _solucao()
    texto = _servico_offline().relatorio(sol, p, "semanal")
    assert "RELATORIO" in texto
    assert "Indicadores" in texto


def test_responder_fallback():
    sol, p = _solucao()
    resp = _servico_offline().responder("Quantos veiculos?", sol, p)
    assert "entregas atendidas" in resp

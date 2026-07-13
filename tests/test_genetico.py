from rota_medica.dados import gerar_problema
from rota_medica.otimizacao import AlgoritmoGenetico, ConfigGenetico
from rota_medica.otimizacao.heuristicas import aleatoria, vizinho_mais_proximo


def test_ag_melhora_em_relacao_a_aleatoria():
    p = gerar_problema(15, 3, seed=42)
    cfg = ConfigGenetico(tamanho_populacao=60, n_geracoes=120, seed=42)
    resultado = AlgoritmoGenetico(p, cfg).executar()

    baseline = aleatoria(p, seed=42)
    assert resultado.melhor_custo <= baseline.custo_fitness
    assert resultado.solucao.n_entregas_atendidas == p.n_entregas


def test_ag_competitivo_com_vizinho_mais_proximo():
    p = gerar_problema(15, 3, seed=42)
    cfg = ConfigGenetico(tamanho_populacao=80, n_geracoes=200, seed=42)
    resultado = AlgoritmoGenetico(p, cfg).executar()
    vmp = vizinho_mais_proximo(p)
    assert resultado.melhor_custo <= vmp.custo_fitness + 1e-6


def test_ag_reprodutivel_com_mesma_seed():
    p = gerar_problema(12, 2, seed=1)
    cfg = ConfigGenetico(tamanho_populacao=40, n_geracoes=60, seed=7)
    r1 = AlgoritmoGenetico(p, cfg).executar()
    r2 = AlgoritmoGenetico(p, cfg).executar()
    assert r1.melhor_custo == r2.melhor_custo


def test_historico_registrado():
    p = gerar_problema(10, 2, seed=2)
    cfg = ConfigGenetico(tamanho_populacao=30, n_geracoes=50, seed=2, paciencia=1000)
    r = AlgoritmoGenetico(p, cfg).executar()
    assert len(r.historico_melhor) == r.geracoes_executadas
    assert all(
        r.historico_melhor[i] >= r.historico_melhor[i + 1]
        for i in range(len(r.historico_melhor) - 1)
    )

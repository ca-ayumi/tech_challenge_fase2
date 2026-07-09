import random

from rota_medica.otimizacao import operadores as ops


def _eh_permutacao(individuo, n):
    return sorted(individuo) == list(range(n))


def test_populacao_inicial_valida():
    rng = random.Random(0)
    pop = ops.populacao_inicial(10, 20, rng)
    assert len(pop) == 20
    assert all(_eh_permutacao(ind, 10) for ind in pop)


def test_crossover_ox_gera_filhos_validos():
    rng = random.Random(1)
    p1 = list(range(10))
    p2 = list(range(10))
    rng.shuffle(p2)
    f1, f2 = ops.crossover_ox(p1, p2, rng)
    assert _eh_permutacao(f1, 10)
    assert _eh_permutacao(f2, 10)


def test_mutacoes_preservam_permutacao():
    rng = random.Random(2)
    for mut in (ops.mutacao_troca, ops.mutacao_insercao, ops.mutacao_inversao):
        ind = list(range(12))
        mut(ind, rng)
        assert _eh_permutacao(ind, 12)


def test_selecao_torneio_retorna_melhor():
    rng = random.Random(3)
    pop = [[0], [1], [2], [3]]
    custos = [10.0, 1.0, 5.0, 8.0]
    # Torneio grande o suficiente para cobrir todos -> deve escolher custo minimo
    escolhido = ops.selecao_torneio(pop, custos, k=4, rng=rng)
    assert escolhido == [1]

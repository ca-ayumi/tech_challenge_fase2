"""Operadores geneticos especializados para representacao por permutacao (VRP).

- Selecao por torneio;
- Crossover de ordem (Order Crossover - OX), que preserva a validade da
  permutacao (nenhuma entrega duplicada ou faltante);
- Mutacoes de troca, insercao e inversao (esta ultima com efeito de 2-opt).
"""
from __future__ import annotations

import random


def populacao_inicial(n_entregas: int, tamanho: int,
                      rng: random.Random) -> list[list[int]]:
    """Gera uma populacao inicial de permutacoes aleatorias."""
    base = list(range(n_entregas))
    populacao = []
    for _ in range(tamanho):
        individuo = base[:]
        rng.shuffle(individuo)
        populacao.append(individuo)
    return populacao


def selecao_torneio(populacao: list[list[int]], custos: list[float],
                    k: int, rng: random.Random) -> list[int]:
    """Seleciona um individuo pelo torneio de tamanho `k` (menor custo vence)."""
    competidores = rng.sample(range(len(populacao)), k=min(k, len(populacao)))
    melhor = min(competidores, key=lambda idx: custos[idx])
    return populacao[melhor][:]


def crossover_ox(pai1: list[int], pai2: list[int],
                 rng: random.Random) -> tuple[list[int], list[int]]:
    """Order Crossover (OX). Retorna dois filhos validos."""
    n = len(pai1)
    if n < 2:
        return pai1[:], pai2[:]
    a, b = sorted(rng.sample(range(n), 2))

    def _gerar(p_a: list[int], p_b: list[int]) -> list[int]:
        filho = [None] * n
        filho[a:b + 1] = p_a[a:b + 1]
        presentes = set(filho[a:b + 1])
        pos = (b + 1) % n
        for gene in p_b[b + 1:] + p_b[:b + 1]:
            if gene not in presentes:
                filho[pos] = gene
                presentes.add(gene)
                pos = (pos + 1) % n
        return filho

    return _gerar(pai1, pai2), _gerar(pai2, pai1)


def mutacao_troca(individuo: list[int], rng: random.Random) -> None:
    """Troca duas posicoes de lugar (swap)."""
    if len(individuo) < 2:
        return
    i, j = rng.sample(range(len(individuo)), 2)
    individuo[i], individuo[j] = individuo[j], individuo[i]


def mutacao_insercao(individuo: list[int], rng: random.Random) -> None:
    """Remove um gene de uma posicao e o reinsere em outra."""
    if len(individuo) < 2:
        return
    i = rng.randrange(len(individuo))
    gene = individuo.pop(i)
    j = rng.randrange(len(individuo) + 1)
    individuo.insert(j, gene)


def mutacao_inversao(individuo: list[int], rng: random.Random) -> None:
    """Inverte um segmento (efeito de 2-opt, bom para desfazer cruzamentos)."""
    if len(individuo) < 2:
        return
    i, j = sorted(rng.sample(range(len(individuo)), 2))
    individuo[i:j + 1] = reversed(individuo[i:j + 1])


def mutar(individuo: list[int], rng: random.Random) -> None:
    """Aplica uma das mutacoes disponiveis, escolhida aleatoriamente."""
    operador = rng.choice((mutacao_troca, mutacao_insercao, mutacao_inversao))
    operador(individuo, rng)

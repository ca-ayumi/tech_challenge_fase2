from __future__ import annotations

import random
import time
from dataclasses import dataclass

from ..dominio import ProblemaRoteamento, Solucao
from .config import ConfigGenetico
from .fitness import decodificar


def permutacao_vizinho_mais_proximo(problema: ProblemaRoteamento) -> list[int]:
    matriz = problema.matriz
    nao_visitados = list(range(problema.n_entregas))
    permutacao: list[int] = []
    no_atual = 0

    while nao_visitados:
        def custo(gene: int) -> float:
            entrega = problema.entregas[gene]
            desconto = 1.0 / (1.0 + 0.15 * entrega.prioridade.peso)
            return matriz[no_atual][gene + 1] * desconto

        proximo = min(nao_visitados, key=custo)
        permutacao.append(proximo)
        nao_visitados.remove(proximo)
        no_atual = proximo + 1

    return permutacao


def vizinho_mais_proximo(problema: ProblemaRoteamento) -> Solucao:
    return decodificar(permutacao_vizinho_mais_proximo(problema), problema)


def aleatoria(problema: ProblemaRoteamento, seed: int | None = 0) -> Solucao:
    rng = random.Random(seed)
    permutacao = list(range(problema.n_entregas))
    rng.shuffle(permutacao)
    return decodificar(permutacao, problema)


@dataclass
class ResultadoComparativo:
    nome: str
    custo_fitness: float
    distancia_km: float
    custo_reais: float
    veiculos_usados: int
    entregas_atendidas: int
    nao_atendidas: int
    tempo_segundos: float


def _para_resultado(nome: str, solucao: Solucao, tempo: float) -> ResultadoComparativo:
    return ResultadoComparativo(
        nome=nome,
        custo_fitness=round(solucao.custo_fitness, 2),
        distancia_km=round(solucao.distancia_total_km, 2),
        custo_reais=round(solucao.custo_total_reais, 2),
        veiculos_usados=solucao.n_veiculos_usados,
        entregas_atendidas=solucao.n_entregas_atendidas,
        nao_atendidas=len(solucao.nao_atendidas),
        tempo_segundos=round(tempo, 4),
    )


def comparar(problema: ProblemaRoteamento,
             cfg: ConfigGenetico | None = None) -> list[ResultadoComparativo]:
    from .genetico import AlgoritmoGenetico

    cfg = cfg or ConfigGenetico()
    resultados: list[ResultadoComparativo] = []

    t0 = time.perf_counter()
    sol_rand = aleatoria(problema, seed=cfg.seed)
    resultados.append(_para_resultado("Aleatoria", sol_rand, time.perf_counter() - t0))

    t0 = time.perf_counter()
    sol_vmp = vizinho_mais_proximo(problema)
    resultados.append(
        _para_resultado("Vizinho mais proximo", sol_vmp, time.perf_counter() - t0)
    )

    t0 = time.perf_counter()
    ag = AlgoritmoGenetico(problema, cfg)
    res = ag.executar()
    resultados.append(
        _para_resultado("Algoritmo Genetico", res.solucao, time.perf_counter() - t0)
    )

    return resultados

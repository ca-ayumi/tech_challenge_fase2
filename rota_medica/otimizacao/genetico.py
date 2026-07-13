from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Callable

from ..dominio import ProblemaRoteamento, Solucao
from . import operadores as ops
from .config import ConfigGenetico
from .fitness import avaliar


@dataclass
class ResultadoOtimizacao:
    solucao: Solucao
    melhor_custo: float
    historico_melhor: list[float] = field(default_factory=list)
    historico_media: list[float] = field(default_factory=list)
    geracoes_executadas: int = 0
    tempo_segundos: float = 0.0
    problema: ProblemaRoteamento | None = None


class AlgoritmoGenetico:
    def __init__(self, problema: ProblemaRoteamento,
                 cfg: ConfigGenetico | None = None) -> None:
        self.problema = problema
        self.cfg = cfg or ConfigGenetico()
        self.rng = random.Random(self.cfg.seed)

    def executar(
        self,
        callback: Callable[[int, float, float], None] | None = None,
    ) -> ResultadoOtimizacao:
        cfg = self.cfg
        rng = self.rng
        n = self.problema.n_entregas
        inicio = time.perf_counter()

        if n == 0:
            vazio = avaliar([], self.problema, cfg)[1]
            return ResultadoOtimizacao(
                solucao=vazio, melhor_custo=vazio.custo_fitness, problema=self.problema
            )

        populacao = ops.populacao_inicial(n, cfg.tamanho_populacao, rng)
        from .heuristicas import permutacao_vizinho_mais_proximo

        populacao[0] = permutacao_vizinho_mais_proximo(self.problema)
        custos, solucoes = self._avaliar_populacao(populacao)

        melhor_idx = min(range(len(custos)), key=lambda i: custos[i])
        melhor_custo = custos[melhor_idx]
        melhor_solucao = solucoes[melhor_idx]
        melhor_individuo = populacao[melhor_idx][:]

        hist_melhor: list[float] = []
        hist_media: list[float] = []
        geracoes_sem_melhora = 0
        geracao = 0

        for geracao in range(1, cfg.n_geracoes + 1):
            nova_pop = self._elite(populacao, custos)

            while len(nova_pop) < cfg.tamanho_populacao:
                pai1 = ops.selecao_torneio(populacao, custos, cfg.tamanho_torneio, rng)
                pai2 = ops.selecao_torneio(populacao, custos, cfg.tamanho_torneio, rng)

                if rng.random() < cfg.taxa_crossover:
                    filho1, filho2 = ops.crossover_ox(pai1, pai2, rng)
                else:
                    filho1, filho2 = pai1[:], pai2[:]

                if rng.random() < cfg.taxa_mutacao:
                    ops.mutar(filho1, rng)
                if rng.random() < cfg.taxa_mutacao:
                    ops.mutar(filho2, rng)

                nova_pop.append(filho1)
                if len(nova_pop) < cfg.tamanho_populacao:
                    nova_pop.append(filho2)

            populacao = nova_pop
            custos, solucoes = self._avaliar_populacao(populacao)

            idx = min(range(len(custos)), key=lambda i: custos[i])
            custo_medio = sum(custos) / len(custos)
            hist_melhor.append(min(melhor_custo, custos[idx]))
            hist_media.append(custo_medio)

            if custos[idx] < melhor_custo - 1e-9:
                melhor_custo = custos[idx]
                melhor_solucao = solucoes[idx]
                melhor_individuo = populacao[idx][:]
                geracoes_sem_melhora = 0
            else:
                geracoes_sem_melhora += 1

            if callback is not None:
                callback(geracao, melhor_custo, custo_medio)

            if geracoes_sem_melhora >= cfg.paciencia:
                break

        _, melhor_solucao = avaliar(melhor_individuo, self.problema, cfg)

        return ResultadoOtimizacao(
            solucao=melhor_solucao,
            melhor_custo=melhor_custo,
            historico_melhor=hist_melhor,
            historico_media=hist_media,
            geracoes_executadas=geracao,
            tempo_segundos=time.perf_counter() - inicio,
            problema=self.problema,
        )

    def _avaliar_populacao(
        self, populacao: list[list[int]]
    ) -> tuple[list[float], list[Solucao]]:
        custos: list[float] = []
        solucoes: list[Solucao] = []
        for individuo in populacao:
            custo, solucao = avaliar(individuo, self.problema, self.cfg)
            custos.append(custo)
            solucoes.append(solucao)
        return custos, solucoes

    def _elite(self, populacao: list[list[int]], custos: list[float]) -> list[list[int]]:
        if self.cfg.elitismo <= 0:
            return []
        indices = sorted(range(len(custos)), key=lambda i: custos[i])
        return [populacao[i][:] for i in indices[: self.cfg.elitismo]]

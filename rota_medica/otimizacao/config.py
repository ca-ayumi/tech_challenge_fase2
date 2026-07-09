"""Parametros de configuracao do algoritmo genetico e da funcao de fitness."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConfigGenetico:
    """Hiperparametros do AG e pesos da funcao de fitness.

    Os pesos permitem equilibrar os multiplos objetivos do problema:
    minimizar distancia, priorizar entregas criticas, evitar entregas nao
    atendidas e reduzir o numero de veiculos utilizados.
    """

    # --- Parametros evolutivos ---
    tamanho_populacao: int = 120
    n_geracoes: int = 300
    taxa_crossover: float = 0.9
    taxa_mutacao: float = 0.2
    tamanho_torneio: int = 4
    elitismo: int = 2  # quantos melhores individuos passam intactos
    paciencia: int = 60  # geracoes sem melhora antes de parar (early stopping)
    seed: int | None = 42

    # --- Pesos da funcao de fitness (custo a minimizar) ---
    peso_distancia: float = 1.0
    peso_prioridade: float = 0.15  # penaliza atender entregas criticas tarde/longe
    peso_nao_atendida: float = 10000.0  # penalidade base por entrega nao atendida
    peso_veiculo: float = 25.0  # custo fixo por veiculo utilizado

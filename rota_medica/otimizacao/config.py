from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConfigGenetico:
    tamanho_populacao: int = 120
    n_geracoes: int = 300
    taxa_crossover: float = 0.9
    taxa_mutacao: float = 0.2
    tamanho_torneio: int = 4
    elitismo: int = 2
    paciencia: int = 60
    seed: int | None = 42

    peso_distancia: float = 1.0
    peso_prioridade: float = 0.15
    peso_nao_atendida: float = 10000.0
    peso_veiculo: float = 25.0

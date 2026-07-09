"""Modelos de dominio do problema de roteamento de veiculos (VRP) medico."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


class Prioridade(IntEnum):
    """Prioridade de uma entrega.

    O valor numerico e usado como peso na funcao de fitness: quanto menor o
    valor, mais critica a entrega e maior a penalidade por atende-la tarde.
    """

    CRITICO = 1  # Medicamentos criticos / emergencia
    ALTO = 2  # Insumos urgentes
    NORMAL = 3  # Reposicao regular
    BAIXO = 4  # Material administrativo / nao urgente

    @property
    def rotulo(self) -> str:
        return {
            Prioridade.CRITICO: "Critico",
            Prioridade.ALTO: "Alto",
            Prioridade.NORMAL: "Normal",
            Prioridade.BAIXO: "Baixo",
        }[self]

    @property
    def peso(self) -> float:
        """Peso de urgencia (maior = mais urgente) usado na funcao fitness."""
        return {
            Prioridade.CRITICO: 8.0,
            Prioridade.ALTO: 4.0,
            Prioridade.NORMAL: 2.0,
            Prioridade.BAIXO: 1.0,
        }[self]


@dataclass(frozen=True)
class Local:
    """Ponto geografico generico."""

    id: int
    nome: str
    lat: float
    lon: float

    @property
    def coordenada(self) -> tuple[float, float]:
        return (self.lat, self.lon)


@dataclass(frozen=True)
class Deposito(Local):
    """Hospital central / centro de distribuicao (ponto de partida e retorno)."""


@dataclass(frozen=True)
class Entrega(Local):
    """Uma entrega a ser realizada em uma unidade ou domicilio."""

    demanda_kg: float = 0.0
    prioridade: Prioridade = Prioridade.NORMAL
    tempo_servico_min: float = 10.0
    tipo: str = "Insumo"  # descricao livre (ex.: "Medicamento critico")


@dataclass(frozen=True)
class Veiculo:
    """Veiculo da frota, com restricoes de capacidade e autonomia."""

    id: int
    nome: str
    capacidade_kg: float
    autonomia_km: float
    velocidade_media_kmh: float = 40.0
    custo_por_km: float = 2.5  # R$/km (combustivel + desgaste)


@dataclass
class ProblemaRoteamento:
    """Instancia completa do problema de roteamento."""

    deposito: Deposito
    entregas: list[Entrega]
    veiculos: list[Veiculo]
    matriz: list[list[float]] = field(default_factory=list)

    @property
    def n_entregas(self) -> int:
        return len(self.entregas)

    @property
    def n_veiculos(self) -> int:
        return len(self.veiculos)

    def entrega_por_indice(self, idx: int) -> Entrega:
        """idx e a posicao na lista de entregas (0-based)."""
        return self.entregas[idx]


@dataclass
class Rota:
    """Rota atribuida a um veiculo: deposito -> entregas -> deposito."""

    veiculo: Veiculo
    entregas: list[Entrega] = field(default_factory=list)
    distancia_km: float = 0.0
    carga_kg: float = 0.0
    tempo_total_min: float = 0.0

    @property
    def utilizada(self) -> bool:
        return len(self.entregas) > 0

    @property
    def ocupacao(self) -> float:
        """Percentual de ocupacao da capacidade do veiculo."""
        if self.veiculo.capacidade_kg <= 0:
            return 0.0
        return self.carga_kg / self.veiculo.capacidade_kg

    @property
    def custo_reais(self) -> float:
        return self.distancia_km * self.veiculo.custo_por_km


@dataclass
class Solucao:
    """Solucao completa: conjunto de rotas + entregas nao atendidas + metricas."""

    rotas: list[Rota] = field(default_factory=list)
    nao_atendidas: list[Entrega] = field(default_factory=list)
    custo_fitness: float = float("inf")

    @property
    def rotas_utilizadas(self) -> list[Rota]:
        return [r for r in self.rotas if r.utilizada]

    @property
    def distancia_total_km(self) -> float:
        return sum(r.distancia_km for r in self.rotas)

    @property
    def custo_total_reais(self) -> float:
        return sum(r.custo_reais for r in self.rotas)

    @property
    def tempo_total_min(self) -> float:
        return sum(r.tempo_total_min for r in self.rotas)

    @property
    def n_veiculos_usados(self) -> int:
        return len(self.rotas_utilizadas)

    @property
    def n_entregas_atendidas(self) -> int:
        return sum(len(r.entregas) for r in self.rotas)

    @property
    def viavel(self) -> bool:
        return len(self.nao_atendidas) == 0

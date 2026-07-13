from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


class Prioridade(IntEnum):
    CRITICO = 1
    ALTO = 2
    NORMAL = 3
    BAIXO = 4

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
        return {
            Prioridade.CRITICO: 8.0,
            Prioridade.ALTO: 4.0,
            Prioridade.NORMAL: 2.0,
            Prioridade.BAIXO: 1.0,
        }[self]


@dataclass(frozen=True)
class Local:
    id: int
    nome: str
    lat: float
    lon: float

    @property
    def coordenada(self) -> tuple[float, float]:
        return (self.lat, self.lon)


@dataclass(frozen=True)
class Deposito(Local):
    pass


@dataclass(frozen=True)
class Entrega(Local):
    demanda_kg: float = 0.0
    prioridade: Prioridade = Prioridade.NORMAL
    tempo_servico_min: float = 10.0
    tipo: str = "Insumo"


@dataclass(frozen=True)
class Veiculo:
    id: int
    nome: str
    capacidade_kg: float
    autonomia_km: float
    velocidade_media_kmh: float = 40.0
    custo_por_km: float = 2.5


@dataclass
class ProblemaRoteamento:
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
        return self.entregas[idx]


@dataclass
class Rota:
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
        if self.veiculo.capacidade_kg <= 0:
            return 0.0
        return self.carga_kg / self.veiculo.capacidade_kg

    @property
    def custo_reais(self) -> float:
        return self.distancia_km * self.veiculo.custo_por_km


@dataclass
class Solucao:
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

from __future__ import annotations

import random

from .dominio import (
    Deposito,
    Entrega,
    Prioridade,
    ProblemaRoteamento,
    Veiculo,
)
from .utils import matriz_distancias

DEPOSITO_PADRAO = Deposito(
    id=0,
    nome="Hospital Central",
    lat=-23.5595,
    lon=-46.7313,
)

_REGIOES = [
    "Pinheiros", "Vila Madalena", "Butanta", "Lapa", "Perdizes", "Barra Funda",
    "Santa Cecilia", "Consolacao", "Bela Vista", "Liberdade", "Ipiranga",
    "Vila Mariana", "Saude", "Moema", "Campo Belo", "Santo Amaro", "Morumbi",
    "Jardim Paulista", "Itaim Bibi", "Tatuape", "Mooca", "Penha", "Santana",
    "Tucuruvi", "Freguesia do O", "Pirituba", "Osasco", "Guarulhos Centro",
    "Sao Caetano", "Diadema", "Taboao da Serra", "Cotia",
]

_TIPOS_ENTREGA = [
    ("Medicamento critico (insulina/oncologico)", Prioridade.CRITICO, (2, 15)),
    ("Hemoderivados / vacinas", Prioridade.CRITICO, (3, 20)),
    ("Antibioticos e soros urgentes", Prioridade.ALTO, (5, 30)),
    ("Kit cirurgico / OPME", Prioridade.ALTO, (10, 40)),
    ("Insumos de reposicao regular", Prioridade.NORMAL, (15, 60)),
    ("Material de enfermagem", Prioridade.NORMAL, (10, 50)),
    ("Material administrativo", Prioridade.BAIXO, (5, 25)),
]

_MODELOS_VEICULO = [
    ("Van Refrigerada", 300.0, 180.0, 45.0, 3.0),
    ("Furgao Utilitario", 500.0, 220.0, 40.0, 2.8),
    ("Moto Rapida (rota critica)", 40.0, 120.0, 50.0, 1.2),
    ("Carro Utilitario", 150.0, 200.0, 45.0, 2.0),
]


def gerar_entregas(
    n: int,
    *,
    seed: int | None = 42,
    centro: tuple[float, float] = (DEPOSITO_PADRAO.lat, DEPOSITO_PADRAO.lon),
    raio_graus: float = 0.11,
) -> list[Entrega]:
    rng = random.Random(seed)
    regioes = rng.sample(_REGIOES, k=min(n, len(_REGIOES)))
    while len(regioes) < n:
        base = rng.choice(_REGIOES)
        regioes.append(f"{base} {rng.randint(2, 9)}")

    entregas: list[Entrega] = []
    for i in range(n):
        descricao, prioridade, faixa_kg = rng.choices(
            _TIPOS_ENTREGA,
            weights=[1.5, 1.0, 2.0, 1.5, 3.0, 2.5, 1.5],
            k=1,
        )[0]
        lat = centro[0] + rng.gauss(0, raio_graus / 2)
        lon = centro[1] + rng.gauss(0, raio_graus / 2)
        demanda = round(rng.uniform(*faixa_kg), 1)
        entregas.append(
            Entrega(
                id=i + 1,
                nome=f"Unidade {regioes[i]}",
                lat=lat,
                lon=lon,
                demanda_kg=demanda,
                prioridade=prioridade,
                tempo_servico_min=round(rng.uniform(5, 20), 0),
                tipo=descricao,
            )
        )
    return entregas


def gerar_frota(n: int, *, seed: int | None = 42) -> list[Veiculo]:
    _ = seed
    frota: list[Veiculo] = []
    for i in range(n):
        nome_base, cap, aut, vel, custo = _MODELOS_VEICULO[i % len(_MODELOS_VEICULO)]
        frota.append(
            Veiculo(
                id=i + 1,
                nome=f"{nome_base} #{i + 1}",
                capacidade_kg=cap,
                autonomia_km=aut,
                velocidade_media_kmh=vel,
                custo_por_km=custo,
            )
        )
    return frota


def gerar_problema(
    n_entregas: int = 15,
    n_veiculos: int = 3,
    *,
    seed: int | None = 42,
    deposito: Deposito | None = None,
) -> ProblemaRoteamento:
    deposito = deposito or DEPOSITO_PADRAO
    entregas = gerar_entregas(n_entregas, seed=seed, centro=deposito.coordenada)
    veiculos = gerar_frota(n_veiculos, seed=seed)

    coordenadas = [deposito.coordenada] + [e.coordenada for e in entregas]
    matriz = matriz_distancias(coordenadas)

    return ProblemaRoteamento(
        deposito=deposito,
        entregas=entregas,
        veiculos=veiculos,
        matriz=matriz,
    )

"""Utilitarios geometricos e numericos compartilhados."""
from __future__ import annotations

import math
from typing import Iterable

RAIO_TERRA_KM = 6371.0088


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia em km entre dois pontos geograficos (formula de Haversine)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * RAIO_TERRA_KM * math.asin(math.sqrt(a))


def matriz_distancias(coordenadas: list[tuple[float, float]]) -> list[list[float]]:
    """Constroi a matriz de distancias (km) entre todos os pontos informados.

    O indice 0 e, por convencao, o deposito (hospital central).
    """
    n = len(coordenadas)
    matriz = [[0.0] * n for _ in range(n)]
    for i in range(n):
        lat_i, lon_i = coordenadas[i]
        for j in range(i + 1, n):
            lat_j, lon_j = coordenadas[j]
            d = haversine(lat_i, lon_i, lat_j, lon_j)
            matriz[i][j] = d
            matriz[j][i] = d
    return matriz


def media(valores: Iterable[float]) -> float:
    valores = list(valores)
    return sum(valores) / len(valores) if valores else 0.0

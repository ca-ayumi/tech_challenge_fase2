from rota_medica.utils import haversine, matriz_distancias


def test_haversine_zero():
    assert haversine(-23.5, -46.6, -23.5, -46.6) == 0.0


def test_haversine_conhecido():
    # Sao Paulo (Se) -> Rio de Janeiro (Centro): ~360 km
    d = haversine(-23.5505, -46.6333, -22.9068, -43.1729)
    assert 340 < d < 380


def test_matriz_simetrica_e_diagonal_zero():
    coords = [(-23.5, -46.6), (-23.6, -46.7), (-23.55, -46.65)]
    m = matriz_distancias(coords)
    n = len(coords)
    for i in range(n):
        assert m[i][i] == 0.0
        for j in range(n):
            assert abs(m[i][j] - m[j][i]) < 1e-9

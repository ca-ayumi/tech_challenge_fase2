from rota_medica.dados import gerar_entregas, gerar_frota, gerar_problema
from rota_medica.dominio import Prioridade


def test_gerar_entregas_quantidade_e_ids():
    entregas = gerar_entregas(12, seed=1)
    assert len(entregas) == 12
    assert [e.id for e in entregas] == list(range(1, 13))
    assert all(e.demanda_kg > 0 for e in entregas)
    assert all(isinstance(e.prioridade, Prioridade) for e in entregas)


def test_gerar_entregas_reprodutivel():
    a = gerar_entregas(10, seed=7)
    b = gerar_entregas(10, seed=7)
    assert [e.coordenada for e in a] == [e.coordenada for e in b]


def test_gerar_frota():
    frota = gerar_frota(4, seed=1)
    assert len(frota) == 4
    assert all(v.capacidade_kg > 0 and v.autonomia_km > 0 for v in frota)


def test_gerar_problema_matriz():
    p = gerar_problema(8, 2, seed=3)
    assert p.n_entregas == 8
    assert p.n_veiculos == 2
    assert len(p.matriz) == 9
    assert len(p.matriz[0]) == 9

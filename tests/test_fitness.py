from rota_medica.dados import gerar_problema
from rota_medica.dominio import Deposito, Entrega, Prioridade, ProblemaRoteamento, Veiculo
from rota_medica.otimizacao.config import ConfigGenetico
from rota_medica.otimizacao.fitness import avaliar, decodificar
from rota_medica.utils import matriz_distancias


def _problema_pequeno(capacidade=1000.0, autonomia=1000.0, n_veiculos=1):
    dep = Deposito(0, "Dep", -23.55, -46.63)
    entregas = [
        Entrega(1, "A", -23.56, -46.64, demanda_kg=10, prioridade=Prioridade.NORMAL),
        Entrega(2, "B", -23.57, -46.65, demanda_kg=10, prioridade=Prioridade.CRITICO),
        Entrega(3, "C", -23.58, -46.66, demanda_kg=10, prioridade=Prioridade.BAIXO),
    ]
    veiculos = [
        Veiculo(i + 1, f"V{i+1}", capacidade, autonomia) for i in range(n_veiculos)
    ]
    coords = [dep.coordenada] + [e.coordenada for e in entregas]
    return ProblemaRoteamento(dep, entregas, veiculos, matriz_distancias(coords))


def test_decodificar_atende_todas_quando_cabe():
    p = _problema_pequeno()
    sol = decodificar([0, 1, 2], p)
    assert sol.n_entregas_atendidas == 3
    assert len(sol.nao_atendidas) == 0
    assert sol.distancia_total_km > 0


def test_capacidade_limita_e_forca_mais_veiculos():
    p = _problema_pequeno(capacidade=15.0, n_veiculos=3)
    sol = decodificar([0, 1, 2], p)
    assert sol.n_veiculos_usados == 3
    assert sol.n_entregas_atendidas == 3


def test_falta_de_veiculos_gera_nao_atendidas():
    p = _problema_pequeno(capacidade=15.0, n_veiculos=1)
    sol = decodificar([0, 1, 2], p)
    assert len(sol.nao_atendidas) == 2


def test_autonomia_inviabiliza_entrega_muito_distante():
    dep = Deposito(0, "Dep", -23.55, -46.63)
    longe = Entrega(1, "Longe", -22.90, -43.17, demanda_kg=1)
    p = ProblemaRoteamento(
        dep, [longe], [Veiculo(1, "V1", 100, autonomia_km=50)],
        matriz_distancias([dep.coordenada, longe.coordenada]),
    )
    sol = decodificar([0], p)
    assert len(sol.nao_atendidas) == 1


def test_prioridade_reduz_custo_quando_critico_vem_antes():
    dep = Deposito(0, "Dep", -23.55, -46.63)
    critico = Entrega(1, "Crit", -23.55, -46.60, demanda_kg=5,
                      prioridade=Prioridade.CRITICO)
    normal = Entrega(2, "Norm", -23.55, -46.66, demanda_kg=5,
                     prioridade=Prioridade.BAIXO)
    coords = [dep.coordenada, critico.coordenada, normal.coordenada]
    p = ProblemaRoteamento(
        dep, [critico, normal], [Veiculo(1, "V1", 1000, 1000)],
        matriz_distancias(coords),
    )
    cfg = ConfigGenetico()
    custo_critico_antes, sol1 = avaliar([0, 1], p, cfg)
    custo_critico_depois, sol2 = avaliar([1, 0], p, cfg)
    assert abs(sol1.distancia_total_km - sol2.distancia_total_km) < 1e-6
    assert custo_critico_antes < custo_critico_depois


def test_avaliar_reprodutivel_em_instancia_gerada():
    p = gerar_problema(10, 2, seed=5)
    cfg = ConfigGenetico()
    c1, _ = avaliar(list(range(10)), p, cfg)
    c2, _ = avaliar(list(range(10)), p, cfg)
    assert c1 == c2

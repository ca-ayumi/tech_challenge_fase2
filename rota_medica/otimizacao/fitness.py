"""Decodificacao de cromossomos em rotas e funcao de fitness (custo) do VRP.

Representacao genetica
----------------------
Um individuo (cromossomo) e uma permutacao dos indices das entregas
(``0 .. n_entregas-1``), interpretada como um "giant tour". Um procedimento de
"split" percorre essa permutacao e distribui as entregas entre os veiculos
disponiveis, respeitando as restricoes de capacidade e autonomia. Assim, a
mesma representacao serve para TSP (1 veiculo) e VRP (varios veiculos).
"""
from __future__ import annotations

from ..dominio import ProblemaRoteamento, Rota, Solucao
from .config import ConfigGenetico


def _finalizar_rota(rota: Rota, no_atual: int, dist_parcial: float,
                    problema: ProblemaRoteamento) -> None:
    """Fecha a rota adicionando o trajeto de retorno ao deposito e o tempo."""
    dist_retorno = problema.matriz[no_atual][0]
    rota.distancia_km = dist_parcial + dist_retorno
    tempo_deslocamento = (rota.distancia_km / rota.veiculo.velocidade_media_kmh) * 60
    tempo_servico = sum(e.tempo_servico_min for e in rota.entregas)
    rota.tempo_total_min = tempo_deslocamento + tempo_servico


def decodificar(permutacao: list[int], problema: ProblemaRoteamento,
                cfg: ConfigGenetico | None = None) -> Solucao:
    """Transforma uma permutacao de entregas em uma solucao (conjunto de rotas).

    Estrategia de split sequencial: preenche o veiculo corrente enquanto couber
    (capacidade + autonomia, incluindo o retorno ao deposito). Quando nao couber,
    fecha a rota e abre a proxima com o proximo veiculo disponivel.
    """
    cfg = cfg or ConfigGenetico()
    veiculos = problema.veiculos
    matriz = problema.matriz
    solucao = Solucao()

    v_idx = 0
    rota = Rota(veiculo=veiculos[v_idx])
    no_atual = 0  # deposito
    dist_parcial = 0.0
    carga = 0.0

    i = 0
    n = len(permutacao)
    while i < n:
        gene = permutacao[i]
        entrega = problema.entregas[gene]
        no_entrega = gene + 1

        d_ate = matriz[no_atual][no_entrega]
        d_retorno = matriz[no_entrega][0]
        cabe_capacidade = (carga + entrega.demanda_kg) <= rota.veiculo.capacidade_kg
        cabe_autonomia = (dist_parcial + d_ate + d_retorno) <= rota.veiculo.autonomia_km

        if cabe_capacidade and cabe_autonomia:
            rota.entregas.append(entrega)
            carga += entrega.demanda_kg
            rota.carga_kg = carga
            dist_parcial += d_ate
            no_atual = no_entrega
            i += 1
            continue

        # Nao coube no veiculo atual.
        if rota.utilizada:
            # Fecha a rota corrente e tenta abrir a proxima.
            _finalizar_rota(rota, no_atual, dist_parcial, problema)
            solucao.rotas.append(rota)
            v_idx += 1
            if v_idx >= len(veiculos):
                # Sem mais veiculos: entregas restantes ficam sem atendimento.
                solucao.nao_atendidas.extend(
                    problema.entregas[g] for g in permutacao[i:]
                )
                break
            rota = Rota(veiculo=veiculos[v_idx])
            no_atual = 0
            dist_parcial = 0.0
            carga = 0.0
            # Nao incrementa i: tenta a mesma entrega no novo veiculo.
            continue

        # Veiculo vazio e a entrega ainda nao cabe: ela e inviavel neste veiculo.
        solucao.nao_atendidas.append(entrega)
        i += 1

    # Fecha a ultima rota aberta, se utilizada.
    if rota.utilizada:
        _finalizar_rota(rota, no_atual, dist_parcial, problema)
        solucao.rotas.append(rota)

    solucao.custo_fitness = _custo(solucao, problema, cfg)
    return solucao


def _custo(solucao: Solucao, problema: ProblemaRoteamento,
           cfg: ConfigGenetico) -> float:
    """Funcao de custo (menor = melhor) combinando os multiplos objetivos."""
    custo = solucao.distancia_total_km * cfg.peso_distancia

    # Penalidade de prioridade: entregas urgentes devem ser atendidas cedo/perto.
    # Usa a "latencia" (distancia acumulada ate a entrega) ponderada pela urgencia.
    for rota in solucao.rotas:
        no_atual = 0
        acumulado = 0.0
        for entrega in rota.entregas:
            no_entrega = entrega.id  # id == indice na matriz (deposito=0)
            acumulado += problema.matriz[no_atual][no_entrega]
            custo += cfg.peso_prioridade * entrega.prioridade.peso * acumulado
            no_atual = no_entrega

    # Penalidade por veiculos utilizados (incentiva consolidar rotas).
    custo += cfg.peso_veiculo * solucao.n_veiculos_usados

    # Penalidade forte por entregas nao atendidas, agravada pela prioridade.
    for entrega in solucao.nao_atendidas:
        custo += cfg.peso_nao_atendida * entrega.prioridade.peso

    return custo


def avaliar(permutacao: list[int], problema: ProblemaRoteamento,
            cfg: ConfigGenetico) -> tuple[float, Solucao]:
    """Decodifica e avalia um cromossomo, retornando (custo, solucao)."""
    solucao = decodificar(permutacao, problema, cfg)
    return solucao.custo_fitness, solucao

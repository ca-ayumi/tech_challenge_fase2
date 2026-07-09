"""Serializacao de uma solucao de roteamento em contexto textual para a LLM."""
from __future__ import annotations

from ..dominio import ProblemaRoteamento, Solucao


def solucao_para_dict(solucao: Solucao, problema: ProblemaRoteamento) -> dict:
    """Converte a solucao em um dicionario compacto e legivel para a LLM."""
    rotas = []
    for i, rota in enumerate(solucao.rotas_utilizadas, start=1):
        paradas = []
        for ordem, e in enumerate(rota.entregas, start=1):
            paradas.append(
                {
                    "ordem": ordem,
                    "unidade": e.nome,
                    "tipo_carga": e.tipo,
                    "prioridade": e.prioridade.rotulo,
                    "demanda_kg": e.demanda_kg,
                    "lat": round(e.lat, 5),
                    "lon": round(e.lon, 5),
                }
            )
        rotas.append(
            {
                "rota": i,
                "veiculo": rota.veiculo.nome,
                "capacidade_kg": rota.veiculo.capacidade_kg,
                "autonomia_km": rota.veiculo.autonomia_km,
                "carga_total_kg": round(rota.carga_kg, 1),
                "ocupacao_pct": round(rota.ocupacao * 100, 1),
                "distancia_km": round(rota.distancia_km, 1),
                "tempo_estimado_min": round(rota.tempo_total_min, 0),
                "custo_reais": round(rota.custo_reais, 2),
                "n_paradas": len(rota.entregas),
                "paradas": paradas,
            }
        )

    return {
        "deposito": problema.deposito.nome,
        "resumo": {
            "distancia_total_km": round(solucao.distancia_total_km, 1),
            "custo_total_reais": round(solucao.custo_total_reais, 2),
            "tempo_total_min": round(solucao.tempo_total_min, 0),
            "veiculos_usados": solucao.n_veiculos_usados,
            "entregas_atendidas": solucao.n_entregas_atendidas,
            "entregas_nao_atendidas": len(solucao.nao_atendidas),
        },
        "rotas": rotas,
        "nao_atendidas": [
            {"unidade": e.nome, "prioridade": e.prioridade.rotulo, "tipo": e.tipo}
            for e in solucao.nao_atendidas
        ],
    }


def solucao_para_texto(solucao: Solucao, problema: ProblemaRoteamento) -> str:
    """Versao textual enxuta usada em prompts (mais barata em tokens)."""
    linhas = [f"Deposito: {problema.deposito.nome}"]
    r = solucao
    linhas.append(
        f"Resumo geral: {r.distancia_total_km:.1f} km | "
        f"R$ {r.custo_total_reais:.2f} | {r.tempo_total_min:.0f} min | "
        f"{r.n_veiculos_usados} veiculo(s) | "
        f"{r.n_entregas_atendidas} entregas atendidas | "
        f"{len(r.nao_atendidas)} nao atendidas"
    )
    for i, rota in enumerate(r.rotas_utilizadas, start=1):
        linhas.append(
            f"\nRota {i} - {rota.veiculo.nome} "
            f"(carga {rota.carga_kg:.1f}/{rota.veiculo.capacidade_kg:.0f} kg, "
            f"{rota.ocupacao * 100:.0f}% | {rota.distancia_km:.1f} km | "
            f"~{rota.tempo_total_min:.0f} min):"
        )
        linhas.append("  Deposito (partida)")
        for ordem, e in enumerate(rota.entregas, start=1):
            linhas.append(
                f"  {ordem}. {e.nome} | {e.tipo} | prioridade {e.prioridade.rotulo} "
                f"| {e.demanda_kg:.1f} kg"
            )
        linhas.append("  Deposito (retorno)")
    if r.nao_atendidas:
        linhas.append("\nEntregas NAO atendidas:")
        for e in r.nao_atendidas:
            linhas.append(f"  - {e.nome} ({e.prioridade.rotulo}, {e.tipo})")
    return "\n".join(linhas)

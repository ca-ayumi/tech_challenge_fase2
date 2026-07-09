"""Visualizacao das rotas em mapa (folium) e graficos de apoio (plotly)."""
from __future__ import annotations

from .dominio import Prioridade, ProblemaRoteamento, Solucao

# Paleta de cores para diferenciar as rotas/veiculos no mapa.
CORES_ROTA = [
    "blue", "green", "purple", "orange", "darkred", "cadetblue",
    "darkgreen", "darkblue", "darkpurple", "black", "pink", "gray",
]

CORES_PRIORIDADE = {
    Prioridade.CRITICO: "#d62728",
    Prioridade.ALTO: "#ff7f0e",
    Prioridade.NORMAL: "#1f77b4",
    Prioridade.BAIXO: "#7f7f7f",
}


def criar_mapa(solucao: Solucao, problema: ProblemaRoteamento):
    """Cria um mapa folium com o deposito e as rotas coloridas por veiculo."""
    import folium

    dep = problema.deposito
    mapa = folium.Map(location=[dep.lat, dep.lon], zoom_start=12, control_scale=True)

    # Deposito
    folium.Marker(
        location=[dep.lat, dep.lon],
        tooltip=f"Deposito: {dep.nome}",
        icon=folium.Icon(color="red", icon="plus-sign", prefix="glyphicon"),
    ).add_to(mapa)

    for i, rota in enumerate(solucao.rotas_utilizadas):
        cor = CORES_ROTA[i % len(CORES_ROTA)]
        grupo = folium.FeatureGroup(name=f"Rota {i + 1} - {rota.veiculo.nome}")

        pontos = [(dep.lat, dep.lon)]
        for ordem, e in enumerate(rota.entregas, start=1):
            pontos.append((e.lat, e.lon))
            popup = folium.Popup(
                f"<b>{ordem}. {e.nome}</b><br>"
                f"Tipo: {e.tipo}<br>"
                f"Prioridade: {e.prioridade.rotulo}<br>"
                f"Demanda: {e.demanda_kg:.1f} kg<br>"
                f"Veiculo: {rota.veiculo.nome}",
                max_width=260,
            )
            folium.CircleMarker(
                location=[e.lat, e.lon],
                radius=7,
                color=cor,
                fill=True,
                fill_color=CORES_PRIORIDADE.get(e.prioridade, cor),
                fill_opacity=0.9,
                popup=popup,
                tooltip=f"{ordem}. {e.nome} ({e.prioridade.rotulo})",
            ).add_to(grupo)
        pontos.append((dep.lat, dep.lon))  # retorno ao deposito

        folium.PolyLine(pontos, color=cor, weight=3, opacity=0.8).add_to(grupo)
        grupo.add_to(mapa)

    # Entregas nao atendidas (marcadas em cinza com X)
    for e in solucao.nao_atendidas:
        folium.Marker(
            location=[e.lat, e.lon],
            tooltip=f"NAO ATENDIDA: {e.nome} ({e.prioridade.rotulo})",
            icon=folium.Icon(color="lightgray", icon="remove", prefix="glyphicon"),
        ).add_to(mapa)

    folium.LayerControl(collapsed=False).add_to(mapa)
    return mapa


def grafico_convergencia(historico_melhor: list[float], historico_media: list[float]):
    """Grafico de convergencia do AG (melhor custo x custo medio por geracao)."""
    import plotly.graph_objects as go

    geracoes = list(range(1, len(historico_melhor) + 1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=geracoes, y=historico_melhor, name="Melhor custo",
                             mode="lines", line=dict(color="#2ca02c")))
    fig.add_trace(go.Scatter(x=geracoes, y=historico_media, name="Custo medio",
                             mode="lines", line=dict(color="#1f77b4", dash="dot")))
    fig.update_layout(
        title="Convergencia do Algoritmo Genetico",
        xaxis_title="Geracao",
        yaxis_title="Custo (fitness)",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def grafico_comparativo(resultados) -> "object":
    """Grafico de barras comparando distancia e custo entre abordagens."""
    import plotly.graph_objects as go

    nomes = [r.nome for r in resultados]
    dist = [r.distancia_km for r in resultados]
    custo = [r.custo_reais for r in resultados]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=nomes, y=dist, name="Distancia (km)", marker_color="#1f77b4"))
    fig.add_trace(go.Bar(x=nomes, y=custo, name="Custo (R$)", marker_color="#ff7f0e"))
    fig.update_layout(
        title="Comparativo de abordagens de roteamento",
        barmode="group",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def grafico_ocupacao(solucao: Solucao):
    """Grafico de ocupacao (%) de cada veiculo utilizado."""
    import plotly.graph_objects as go

    rotas = solucao.rotas_utilizadas
    nomes = [f"Rota {i + 1}<br>{r.veiculo.nome}" for i, r in enumerate(rotas)]
    ocup = [round(r.ocupacao * 100, 1) for r in rotas]

    fig = go.Figure(go.Bar(x=nomes, y=ocup, marker_color="#2ca02c",
                           text=[f"{o}%" for o in ocup], textposition="auto"))
    fig.update_layout(
        title="Ocupacao dos veiculos",
        yaxis_title="Ocupacao (%)",
        yaxis_range=[0, 100],
        template="plotly_white",
    )
    return fig

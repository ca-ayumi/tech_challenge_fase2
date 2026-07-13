from __future__ import annotations

import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[2]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

from rota_medica.dados import gerar_problema  # noqa: E402
from rota_medica.llm import ServicoLLM  # noqa: E402
from rota_medica.otimizacao import AlgoritmoGenetico, ConfigGenetico  # noqa: E402
from rota_medica.otimizacao.heuristicas import comparar  # noqa: E402
from rota_medica import visualizacao as viz  # noqa: E402

load_dotenv(dotenv_path=_RAIZ / ".env", override=True)

st.set_page_config(
    page_title="Rotas Medicas | AG + LLM",
    page_icon="ambulance",
    layout="wide",
)


def _sidebar() -> tuple[ConfigGenetico, int, int]:
    st.sidebar.title("Configuracao")

    st.sidebar.subheader("Instancia do problema")
    n_entregas = st.sidebar.slider("Numero de entregas", 5, 30, 15)
    n_veiculos = st.sidebar.slider("Numero de veiculos (frota)", 1, 6, 3)
    seed = st.sidebar.number_input("Semente (seed)", value=42, step=1)

    st.sidebar.subheader("Algoritmo Genetico")
    populacao = st.sidebar.slider("Tamanho da populacao", 20, 300, 120, step=10)
    geracoes = st.sidebar.slider("Numero de geracoes", 20, 800, 300, step=20)
    taxa_cx = st.sidebar.slider("Taxa de crossover", 0.0, 1.0, 0.9, step=0.05)
    taxa_mut = st.sidebar.slider("Taxa de mutacao", 0.0, 1.0, 0.2, step=0.05)
    torneio = st.sidebar.slider("Tamanho do torneio", 2, 8, 4)
    elitismo = st.sidebar.slider("Elitismo", 0, 6, 2)

    with st.sidebar.expander("Pesos da funcao de fitness"):
        peso_dist = st.slider("Peso distancia", 0.0, 3.0, 1.0, step=0.1)
        peso_prio = st.slider("Peso prioridade", 0.0, 1.0, 0.15, step=0.05)
        peso_veic = st.slider("Custo por veiculo", 0.0, 100.0, 25.0, step=5.0)

    cfg = ConfigGenetico(
        tamanho_populacao=populacao,
        n_geracoes=geracoes,
        taxa_crossover=taxa_cx,
        taxa_mutacao=taxa_mut,
        tamanho_torneio=torneio,
        elitismo=elitismo,
        seed=int(seed),
        peso_distancia=peso_dist,
        peso_prioridade=peso_prio,
        peso_veiculo=peso_veic,
    )
    return cfg, n_entregas, n_veiculos


def _status_llm() -> None:
    servico = ServicoLLM()
    if servico.usando_llm:
        provedor = servico.cliente.provedor.capitalize()
        st.sidebar.success(f"LLM ativa: {provedor} ({servico.cliente.modelo})")
    else:
        st.sidebar.warning(
            "LLM offline (sem chave configurada). Defina GEMINI_API_KEY ou "
            "OPENAI_API_KEY no .env. Enquanto isso, os textos usam um gerador local."
        )


def _tab_mapa(resultado, problema) -> None:
    from streamlit_folium import st_folium

    sol = resultado.solucao
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Distancia total", f"{sol.distancia_total_km:.1f} km")
    c2.metric("Custo estimado", f"R$ {sol.custo_total_reais:.2f}")
    c3.metric("Veiculos usados", f"{sol.n_veiculos_usados}/{problema.n_veiculos}")
    c4.metric("Nao atendidas", f"{len(sol.nao_atendidas)}")

    st.markdown("#### Mapa das rotas otimizadas")
    mapa = viz.criar_mapa(sol, problema)
    st_folium(mapa, width=None, height=520, returned_objects=[])

    st.markdown("#### Detalhamento por rota")
    for i, rota in enumerate(sol.rotas_utilizadas, start=1):
        with st.expander(
            f"Rota {i} - {rota.veiculo.nome} | {len(rota.entregas)} paradas | "
            f"{rota.distancia_km:.1f} km | ocupacao {rota.ocupacao * 100:.0f}%"
        ):
            df = pd.DataFrame(
                [
                    {
                        "Ordem": ordem,
                        "Unidade": e.nome,
                        "Tipo": e.tipo,
                        "Prioridade": e.prioridade.rotulo,
                        "Demanda (kg)": e.demanda_kg,
                    }
                    for ordem, e in enumerate(rota.entregas, start=1)
                ]
            )
            st.dataframe(df, hide_index=True, width="stretch")


def _tab_analise(resultado, problema, cfg) -> None:
    st.markdown("#### Convergencia do Algoritmo Genetico")
    if resultado.historico_melhor:
        st.plotly_chart(
            viz.grafico_convergencia(
                resultado.historico_melhor, resultado.historico_media
            ),
            width="stretch",
        )
    st.caption(
        f"Geracoes executadas: {resultado.geracoes_executadas} | "
        f"Tempo: {resultado.tempo_segundos:.2f}s"
    )

    st.markdown("#### Ocupacao dos veiculos")
    st.plotly_chart(viz.grafico_ocupacao(resultado.solucao), width="stretch")

    st.markdown("#### Comparativo com outras abordagens")
    if st.button("Executar comparativo (AG x Vizinho x Aleatorio)"):
        with st.spinner("Comparando abordagens..."):
            resultados = comparar(problema, cfg)
        df = pd.DataFrame([r.__dict__ for r in resultados])
        df = df.rename(
            columns={
                "nome": "Abordagem",
                "custo_fitness": "Custo (fitness)",
                "distancia_km": "Distancia (km)",
                "custo_reais": "Custo (R$)",
                "veiculos_usados": "Veiculos",
                "entregas_atendidas": "Atendidas",
                "nao_atendidas": "Nao atendidas",
                "tempo_segundos": "Tempo (s)",
            }
        )
        st.dataframe(df, hide_index=True, width="stretch")
        st.plotly_chart(viz.grafico_comparativo(resultados), width="stretch")


def _tab_llm(resultado, problema) -> None:
    servico = ServicoLLM()
    sol = resultado.solucao

    st.markdown("#### Instrucoes para a equipe de entrega")
    rotas = sol.rotas_utilizadas
    if rotas:
        rotulos = [f"Rota {i + 1} - {r.veiculo.nome}" for i, r in enumerate(rotas)]
        escolha = st.selectbox("Selecione a rota", options=range(len(rotas)),
                               format_func=lambda i: rotulos[i])
        if st.button("Gerar instrucoes do motorista"):
            with st.spinner("Gerando instrucoes..."):
                texto = servico.instrucoes_motorista(rotas[escolha], problema)
            st.markdown(texto)

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Relatorio de eficiencia")
        periodo = st.radio("Periodo", ["diario", "semanal"], horizontal=True)
        if st.button("Gerar relatorio"):
            with st.spinner("Gerando relatorio..."):
                st.markdown(servico.relatorio(sol, problema, periodo))
    with col2:
        st.markdown("#### Sugestoes de melhoria")
        if st.button("Gerar sugestoes"):
            with st.spinner("Analisando..."):
                st.markdown(servico.sugestoes(sol, problema))


def _tab_chat(resultado, problema) -> None:
    st.markdown("#### Pergunte em linguagem natural sobre as rotas")
    st.caption(
        "Ex.: 'Qual rota tem mais entregas criticas?', "
        "'Quantos km percorre o veiculo 2?', 'Ha entregas nao atendidas?'"
    )
    servico = ServicoLLM()
    sol = resultado.solucao

    if "chat" not in st.session_state:
        st.session_state.chat = []

    for autor, msg in st.session_state.chat:
        with st.chat_message(autor):
            st.markdown(msg)

    pergunta = st.chat_input("Digite sua pergunta...")
    if pergunta:
        st.session_state.chat.append(("user", pergunta))
        with st.chat_message("user"):
            st.markdown(pergunta)
        with st.chat_message("assistant"):
            with st.spinner("Consultando..."):
                resposta = servico.responder(pergunta, sol, problema)
            st.markdown(resposta)
        st.session_state.chat.append(("assistant", resposta))


def main() -> None:
    st.title("Otimizacao de Rotas para Distribuicao de Medicamentos e Insumos")
    st.caption(
        "Algoritmos Geneticos (VRP) + LLM | Tech Challenge Fase 2 - FIAP IA para DEVS"
    )

    cfg, n_entregas, n_veiculos = _sidebar()
    _status_llm()

    if st.sidebar.button("Otimizar rotas", type="primary", width="stretch"):
        problema = gerar_problema(n_entregas, n_veiculos, seed=cfg.seed)
        progresso = st.progress(0.0, text="Evoluindo a populacao...")

        def _cb(g, melhor, media):
            progresso.progress(min(g / cfg.n_geracoes, 1.0),
                               text=f"Geracao {g}/{cfg.n_geracoes} | melhor custo {melhor:.1f}")

        ag = AlgoritmoGenetico(problema, cfg)
        resultado = ag.executar(callback=_cb)
        progresso.empty()

        st.session_state.resultado = resultado
        st.session_state.problema = problema
        st.session_state.cfg = cfg
        st.session_state.chat = []

    if "resultado" not in st.session_state:
        st.info(
            "Configure os parametros na barra lateral e clique em **Otimizar rotas** "
            "para comecar."
        )
        return

    resultado = st.session_state.resultado
    problema = st.session_state.problema
    cfg = st.session_state.cfg

    aba_mapa, aba_analise, aba_llm, aba_chat = st.tabs(
        ["Mapa & Rotas", "Analise & Comparativo", "Relatorios (LLM)", "Assistente"]
    )
    with aba_mapa:
        _tab_mapa(resultado, problema)
    with aba_analise:
        _tab_analise(resultado, problema, cfg)
    with aba_llm:
        _tab_llm(resultado, problema)
    with aba_chat:
        _tab_chat(resultado, problema)


main()

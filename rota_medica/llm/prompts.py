"""Prompts (system + templates) para os diferentes usos da LLM.

Os prompts sao escritos para serem objetivos e extrair informacao acionavel,
sempre com o cuidado adicional exigido pelo contexto de saude (medicamentos
criticos, cadeia de frio, conferencia de itens, etc.).
"""
from __future__ import annotations

SYSTEM_LOGISTICA = (
    "Voce e um especialista em logistica hospitalar e distribuicao de "
    "medicamentos e insumos. Escreve em portugues do Brasil, de forma clara, "
    "objetiva e profissional. Considere sempre a criticidade dos itens de saude "
    "(cadeia de frio, medicamentos criticos, conferencia de lote/validade) e a "
    "seguranca no transito. Baseie-se APENAS nos dados fornecidos; nao invente "
    "enderecos, horarios ou itens que nao estejam no contexto."
)


def prompt_instrucoes_motorista(rota_texto: str) -> str:
    return (
        "Gere instrucoes de entrega para o motorista/equipe responsavel pela "
        "rota abaixo. Inclua:\n"
        "1. Um checklist de conferencia antes da saida (carga, prioridade, "
        "cadeia de frio quando aplicavel);\n"
        "2. A sequencia de paradas numerada, com orientacoes praticas por parada "
        "(o que entregar, cuidados especiais por prioridade);\n"
        "3. Recomendacoes de seguranca e o que fazer em caso de imprevisto "
        "(atraso, ausencia do recebedor, problema com item critico).\n\n"
        "Use linguagem direta, em topicos. Dados da rota:\n\n"
        f"{rota_texto}"
    )


def prompt_relatorio(contexto_texto: str, periodo: str = "diario") -> str:
    return (
        f"Elabore um relatorio {periodo} de eficiencia logistica com base nos "
        "dados de roteirizacao abaixo. Estruture em secoes:\n"
        "- Resumo executivo (2 a 3 frases);\n"
        "- Indicadores principais (distancia total, custo estimado, tempo, "
        "ocupacao dos veiculos, entregas atendidas/nao atendidas);\n"
        "- Analise por rota (pontos de destaque e possiveis gargalos);\n"
        "- Riscos e alertas (especialmente entregas criticas e nao atendidas);\n"
        "- Conclusao.\n"
        "Seja quantitativo, cite os numeros do contexto. Dados:\n\n"
        f"{contexto_texto}"
    )


def prompt_melhorias(contexto_texto: str) -> str:
    return (
        "Analise a operacao de roteirizacao abaixo e sugira de 3 a 6 melhorias "
        "concretas e priorizadas para reduzir custo/tempo, aumentar a ocupacao "
        "dos veiculos e garantir o atendimento de entregas criticas. Para cada "
        "sugestao, indique o impacto esperado e a facilidade de implementacao "
        "(baixa/media/alta). Dados:\n\n"
        f"{contexto_texto}"
    )


def prompt_pergunta(contexto_texto: str, pergunta: str) -> str:
    return (
        "Responda a pergunta do usuario usando exclusivamente os dados de "
        "roteirizacao fornecidos. Se a resposta nao estiver nos dados, diga "
        "claramente que a informacao nao esta disponivel. Seja direto.\n\n"
        f"### Dados das rotas\n{contexto_texto}\n\n"
        f"### Pergunta\n{pergunta}"
    )

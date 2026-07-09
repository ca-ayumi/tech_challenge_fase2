"""Interface de linha de comando para demonstracao rapida sem interface grafica."""
from __future__ import annotations

import argparse

from .dados import gerar_problema
from .llm import ServicoLLM
from .otimizacao import AlgoritmoGenetico, ConfigGenetico
from .otimizacao.heuristicas import comparar
from .llm.contexto import solucao_para_texto


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Otimizacao de rotas medicas (VRP) com Algoritmo Genetico."
    )
    parser.add_argument("--entregas", type=int, default=15, help="Numero de entregas")
    parser.add_argument("--veiculos", type=int, default=3, help="Numero de veiculos")
    parser.add_argument("--geracoes", type=int, default=300, help="Geracoes do AG")
    parser.add_argument("--populacao", type=int, default=120, help="Tamanho da populacao")
    parser.add_argument("--seed", type=int, default=42, help="Semente aleatoria")
    parser.add_argument("--comparar", action="store_true",
                        help="Exibe comparativo com heuristicas")
    parser.add_argument("--relatorio", action="store_true",
                        help="Gera relatorio de eficiencia (usa LLM se configurada)")
    parser.add_argument("--mapa", type=str, default=None,
                        help="Caminho para salvar o mapa HTML (ex.: rotas.html)")
    args = parser.parse_args(argv)

    problema = gerar_problema(args.entregas, args.veiculos, seed=args.seed)
    cfg = ConfigGenetico(
        tamanho_populacao=args.populacao, n_geracoes=args.geracoes, seed=args.seed
    )

    print(f"Instancia: {problema.n_entregas} entregas, {problema.n_veiculos} veiculos\n")

    ag = AlgoritmoGenetico(problema, cfg)
    resultado = ag.executar()
    sol = resultado.solucao

    print("=== MELHOR SOLUCAO (Algoritmo Genetico) ===")
    print(solucao_para_texto(sol, problema))
    print(f"\nGeracoes executadas: {resultado.geracoes_executadas} | "
          f"Tempo: {resultado.tempo_segundos:.2f}s")

    if args.comparar:
        print("\n=== COMPARATIVO DE ABORDAGENS ===")
        print(f"{'Abordagem':22} {'Custo':>10} {'Dist(km)':>10} "
              f"{'R$':>10} {'Veic':>5} {'NaoAt':>6}")
        for r in comparar(problema, cfg):
            print(f"{r.nome:22} {r.custo_fitness:>10.1f} {r.distancia_km:>10.1f} "
                  f"{r.custo_reais:>10.1f} {r.veiculos_usados:>5} {r.nao_atendidas:>6}")

    if args.relatorio:
        servico = ServicoLLM()
        origem = "LLM (OpenAI)" if servico.usando_llm else "template local"
        print(f"\n=== RELATORIO DE EFICIENCIA ({origem}) ===")
        print(servico.relatorio(sol, problema))

    if args.mapa:
        import os

        from .visualizacao import criar_mapa

        pasta = os.path.dirname(args.mapa)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        criar_mapa(sol, problema).save(args.mapa)
        print(f"\nMapa salvo em: {args.mapa}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

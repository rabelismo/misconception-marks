"""Gera a planilha de inspeção manual: N submissões marcadas por regra, sorteio com semente fixa.

Uso: python3 -I gerar_planilha_inspecao.py <raiz_dos_dados> <saida.csv> [N] [semente]
"""
import ast
import csv
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analise_preliminar import ler_execucoes, regras  # noqa: E402

raiz, saida = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 20
semente = int(sys.argv[4]) if len(sys.argv) > 4 else 2026

por_regra = {"C8": [], "PD7": [], "PH2": [], "PD1": []}
for sem in sorted(os.listdir(raiz)):
    dsem = os.path.join(raiz, sem)
    if not os.path.isdir(dsem):
        continue
    for turma in sorted(os.listdir(dsem)):
        du = os.path.join(dsem, turma, "users")
        if not os.path.isdir(du):
            continue
        for u in sorted(os.listdir(du)):
            dex = os.path.join(du, u, "executions")
            if not os.path.isdir(dex):
                continue
            for arq in sorted(os.listdir(dex)):
                for (tipo, inst, cod, nota) in ler_execucoes(os.path.join(dex, arq)):
                    if tipo != "SUBMITION" or cod is None:
                        continue
                    try:
                        marcas, _ = regras(ast.parse(cod))
                    except (SyntaxError, ValueError, RecursionError):
                        continue
                    for r in marcas:
                        por_regra[r].append((f"{sem}/{turma}/users/{u}/executions/{arq}", inst, nota, cod))

with open(saida, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["regra", "arquivo", "instante", "nota", "codigo",
                "marca_presente (s/n)", "parece_crenca_ou_descuido", "observacao"])
    for r, lista in por_regra.items():
        rng = random.Random(f"{semente}-{r}")
        for item in rng.sample(lista, min(n, len(lista))):
            w.writerow([r, *item, "", "", ""])
print({r: len(v) for r, v in por_regra.items()})

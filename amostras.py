"""Sorteia submissões marcadas por regra para inspeção manual.

Uso: python3 -I amostras.py <dir_ferramentas> <raiz_dados> <regra> <n> <semente>
"""
import ast
import os
import random
import sys

sys.path.insert(0, sys.argv[1])
from analise_preliminar import ler_execucoes, regras  # noqa: E402

raiz, regra, n, semente = sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
achados = []
for sem in sorted(os.listdir(raiz)):
    for turma in sorted(os.listdir(os.path.join(raiz, sem))):
        du = os.path.join(raiz, sem, turma, "users")
        if not os.path.isdir(du):
            continue
        for u in os.listdir(du):
            dex = os.path.join(du, u, "executions")
            if not os.path.isdir(dex):
                continue
            for arq in os.listdir(dex):
                for (tipo, inst, cod, nota) in ler_execucoes(os.path.join(dex, arq)):
                    if tipo != "SUBMITION" or cod is None:
                        continue
                    try:
                        m, _ = regras(ast.parse(cod))
                    except Exception:
                        continue
                    if regra in m:
                        achados.append((f"{sem}/{turma}/{u}/{arq}", nota, cod))
random.Random(semente).shuffle(achados)
for chave, nota, cod in achados[:n]:
    print("=" * 70)
    print(chave, "nota:", nota)
    print(cod[:900])

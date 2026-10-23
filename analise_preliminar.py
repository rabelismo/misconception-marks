"""Análise preliminar no CodeBench: quatro regras do catálogo aplicadas às submissões.

Uso: python3 -I analise_preliminar.py <raiz_dos_dados> <saida_json>
A raiz contém as pastas de semestre (2022-1, 2022-2, 2023-1).
"""
import ast
import json
import os
import re
import sys
from collections import defaultdict

STR_METODOS_SEM_EFEITO = {
    "replace", "upper", "lower", "strip", "lstrip", "rstrip", "capitalize",
    "title", "swapcase", "zfill", "center", "ljust", "rjust", "casefold",
}

FUNCOES_PURAS = {
    "print", "len", "str", "int", "float", "abs", "range", "min", "max", "sum",
    "sorted", "round", "type", "isinstance", "bool", "list", "tuple", "set",
    "dict", "chr", "ord", "repr", "format", "pow", "divmod", "enumerate", "zip",
}

SEP = "*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*"
CAB = re.compile(r"^== (TEST|SUBMITION) \((\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\)")


def ler_execucoes(caminho):
    """Devolve a lista de eventos (tipo, instante, codigo, nota) de um log."""
    with open(caminho, encoding="utf-8", errors="replace") as f:
        texto = f.read()
    eventos = []
    for bloco in texto.split(SEP):
        bloco = bloco.strip("\n")
        m = CAB.match(bloco)
        if not m:
            continue
        tipo, instante = m.group(1), m.group(2)
        cod = re.search(r"-- CODE:\n(.*?)\n-- (?:OUTPUT|EXECUTION TIME|ERROR|TEST CASE)", bloco, re.S)
        codigo = cod.group(1) if cod else None
        nota = None
        g = re.search(r"-- GRADE:\n([\d.]+)%", bloco)
        if g:
            nota = float(g.group(1))
        eventos.append((tipo, instante, codigo, nota))
    return eventos


def _corpo_sem_defs(nos):
    """Percorre nós do corpo sem entrar em funções ou classes aninhadas."""
    pilha = list(nos)
    while pilha:
        n = pilha.pop()
        yield n
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        pilha.extend(ast.iter_child_nodes(n))


def _nomes_atribuidos(nos):
    nomes = set()
    for n in _corpo_sem_defs(nos):
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            nomes.add(n.id)
    return nomes


def regras(arvore):
    """Devolve (marcas, oportunidades) para C8, PD7, PH2 e PD1."""
    marcas, oport = set(), set()
    for n in ast.walk(arvore):
        if isinstance(n, ast.For) and isinstance(n.target, ast.Name):
            v = n.target.id
            sobre_range = (isinstance(n.iter, ast.Call) and isinstance(n.iter.func, ast.Name)
                           and n.iter.func.id == "range")
            if sobre_range:
                oport.add("C8")
            for m in (_corpo_sem_defs(n.body) if sobre_range else []):
                if isinstance(m, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                    alvos = m.targets if isinstance(m, ast.Assign) else [m.target]
                    if any(isinstance(a, ast.Name) and a.id == v for a in alvos):
                        marcas.add("C8")
            if isinstance(n.iter, ast.Name):
                lst = n.iter.id
                oport.add("PD7")
                for m in _corpo_sem_defs(n.body):
                    if (isinstance(m, ast.Subscript) and isinstance(m.value, ast.Name)
                            and m.value.id == lst and isinstance(m.slice, ast.Name)
                            and m.slice.id == v):
                        marcas.add("PD7")
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr in STR_METODOS_SEM_EFEITO:
            oport.add("PH2")
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) \
                and isinstance(n.value.func, ast.Attribute) \
                and n.value.func.attr in STR_METODOS_SEM_EFEITO \
                and isinstance(n.value.func.value, (ast.Name, ast.Subscript)):
            marcas.add("PH2")
        if isinstance(n, ast.While):
            chamados = {c.func.id for c in ast.walk(n.test)
                        if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
            nomes = {x.id for x in ast.walk(n.test)
                     if isinstance(x, ast.Name) and x.id not in chamados}
            if not nomes:
                continue
            oport.add("PD1")
            corpo = list(_corpo_sem_defs(n.body))
            if any(isinstance(m, (ast.Break, ast.Return, ast.Raise)) for m in corpo):
                continue
            if any(isinstance(m, ast.Call) and isinstance(m.func, ast.Name)
                   and m.func.id in {"exit", "quit"} for m in corpo):
                continue
            atualizados = _nomes_atribuidos(n.body)
            for m in corpo:
                if isinstance(m, ast.Call):
                    if isinstance(m.func, ast.Attribute) and isinstance(m.func.value, ast.Name):
                        atualizados.add(m.func.value.id)
                    puras = isinstance(m.func, ast.Name) and m.func.id in FUNCOES_PURAS
                    if not puras:
                        for a in m.args:
                            if isinstance(a, ast.Name):
                                atualizados.add(a.id)
                if isinstance(m, (ast.Global, ast.Nonlocal)):
                    atualizados.update(m.names)
            if not (nomes & atualizados):
                marcas.add("PD1")
    return marcas, oport


def main(raiz, saida):
    regras_ids = ["C8", "PD7", "PH2", "PD1"]
    tot = defaultdict(int)
    por_regra = {r: defaultdict(int) for r in regras_ids}
    # estudante -> regra -> exercícios com marca / com oportunidade
    est_marca = defaultdict(lambda: defaultdict(set))
    est_oport = defaultdict(lambda: defaultdict(set))
    est_exercicios = defaultdict(set)
    # persistência dentro do exercício com edição do código
    persist = {r: defaultdict(int) for r in regras_ids}
    estudantes_editor = set()
    estudantes = set()

    for sem in sorted(os.listdir(raiz)):
        dsem = os.path.join(raiz, sem)
        if not os.path.isdir(dsem):
            continue
        for turma in sorted(os.listdir(dsem)):
            dusers = os.path.join(dsem, turma, "users")
            if not os.path.isdir(dusers):
                continue
            for u in os.listdir(dusers):
                chave = f"{sem}/{turma}/{u}"
                dex = os.path.join(dusers, u, "executions")
                dcm = os.path.join(dusers, u, "codemirror")
                if os.path.isdir(dcm) and os.listdir(dcm):
                    estudantes_editor.add(chave)
                if not os.path.isdir(dex):
                    continue
                for arq in os.listdir(dex):
                    exercicio = arq.rsplit("_", 1)[-1].replace(".log", "")
                    evs = ler_execucoes(os.path.join(dex, arq))
                    subs = [e for e in evs if e[0] == "SUBMITION" and e[2] is not None]
                    tot["execucoes_teste"] += sum(1 for e in evs if e[0] == "TEST")
                    if not subs:
                        continue
                    estudantes.add(chave)
                    est_exercicios[chave].add(exercicio)
                    anterior = {}  # regra -> (codigo da última submissão marcada)
                    for (_, _, codigo, nota) in subs:
                        tot["submissoes"] += 1
                        correta = nota is not None and nota >= 100.0
                        tot["submissoes_corretas"] += correta
                        try:
                            arv = ast.parse(codigo)
                        except (SyntaxError, ValueError, RecursionError):
                            tot["sem_parse"] += 1
                            continue
                        tot["analisadas"] += 1
                        marcas, oport = regras(arv)
                        for r in regras_ids:
                            if r in oport:
                                por_regra[r]["com_oportunidade"] += 1
                                est_oport[chave][r].add(exercicio)
                            if r in marcas:
                                por_regra[r]["marcadas"] += 1
                                por_regra[r]["marcadas_corretas"] += correta
                                est_marca[chave][r].add(exercicio)
                                if r in anterior:
                                    if anterior[r] != codigo:
                                        persist[r]["reenvio_editado_com_marca"] += 1
                                    else:
                                        persist[r]["reenvio_identico"] += 1
                                anterior[r] = codigo
                            elif r in anterior:
                                persist[r]["marca_removida"] += 1
                                del anterior[r]

    res = {"totais": dict(tot), "estudantes_com_submissao": len(estudantes),
           "estudantes_com_eventos_editor": len(estudantes_editor & estudantes),
           "exercicios_por_estudante_mediana": None, "regras": {}}
    ns = sorted(len(v) for v in est_exercicios.values())
    if ns:
        res["exercicios_por_estudante_mediana"] = ns[len(ns) // 2]
    for r in regras_ids:
        com_marca = [k for k in estudantes if est_marca[k][r]]
        elegiveis = [k for k in com_marca if len(est_oport[k][r]) >= 2]
        repetem = [k for k in com_marca if len(est_marca[k][r]) >= 2]
        res["regras"][r] = {
            **por_regra[r],
            "estudantes_com_marca": len(com_marca),
            "estudantes_com_marca_e_oportunidade_de_repetir": len(elegiveis),
            "estudantes_com_marca_em_2_ou_mais_exercicios": len(repetem),
            "persistencia_no_exercicio": dict(persist[r]),
        }
    with open(saida, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

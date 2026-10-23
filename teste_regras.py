"""Testes das quatro regras em exemplos construídos à mão."""
import ast
import sys

sys.path.insert(0, sys.argv[1])
from analise_preliminar import regras  # noqa: E402

casos = {
    # C8
    "for i in range(5):\n    i = i + 2\n": ({"C8"}, set()),
    "for i in range(5):\n    j = i + 2\n": (set(), {"C8"}),
    "for i in range(5):\n    def f():\n        i = 1\n": (set(), {"C8"}),
    "for g in L:\n    g = g.strip()\n": (set(), {"C8"}),
    # PD7
    "L=[1,2]\nfor x in L:\n    print(L[x])\n": ({"PD7"}, set()),
    "L=[1,2]\nfor x in L:\n    print(x)\n": (set(), {"PD7"}),
    # PH2
    "s='a'\ns.replace('a','b')\n": ({"PH2"}, set()),
    "s='a'\ns = s.replace('a','b')\n": (set(), {"PH2"}),
    "s='a'\nprint(s.upper())\n": (set(), {"PH2"}),
    "s='a'\nprint(s).upper()\n": (set(), {"PH2"}),
    # PD1
    "i=0\nwhile i < 3:\n    print(i)\n": ({"PD1"}, set()),
    "i=0\nwhile i < 3:\n    i += 1\n": (set(), {"PD1"}),
    "i=0\nwhile i < 3:\n    break\n": (set(), {"PD1"}),
    "L=[1]\nwhile len(L) > 0:\n    L.pop()\n": (set(), {"PD1"}),
    "while True:\n    x = input()\n": (set(), set()),
}
falhas = 0
for codigo, (devem, nao_devem) in casos.items():
    marcas, _ = regras(ast.parse(codigo))
    ok = devem <= marcas and not (nao_devem & marcas)
    if not ok:
        falhas += 1
        print("FALHOU:", repr(codigo), "marcas:", marcas)
print(f"{len(casos) - falhas}/{len(casos)} casos corretos")
sys.exit(1 if falhas else 0)

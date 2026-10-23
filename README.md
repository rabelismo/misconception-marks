# Análise preliminar no CodeBench (Seção 7 do projeto FAPESP)

Pacote para reproduzir a Tabela 7 do projeto "Marcas de *misconceptions* no código e telemetria
do processo de programação como evidência para a construção de um inventário de conceitos de
programação introdutória".

## Dados

Conjunto de dados público do CodeBench (UFAM), versão 1.81, semestres 2022.1, 2022.2 e 2023.1.
Os arquivos usados foram:

| Arquivo | SHA-256 |
|---|---|
| cb_dataset_2022_1_v1_81_tar.gz | 592c5768bc21318e5ad05ee29de3a980d9c2e2766b988fc56cc3ee03b4fe9958 |
| cb_dataset_2022_2_v1_81_tar.gz | 3894fd6888147afed01951f397d54336d925b1f73a9ac8b3defecf3066358d9f |
| cb_dataset_2023_1_v1_81_tar.gz | 925168b9b0d540034e20eeebd0f41aec1e8aef6ddb0aac976d01b02dca71528e |

Para conferir se você tem os mesmos arquivos: `sha256sum -c SHA256SUMS_dados.txt` na pasta dos arquivos.
Os dados não estão neste pacote; devem ser obtidos com os mantenedores do CodeBench.

## Como reproduzir

Testado com Python 3.13 (ver `ambiente.txt`). Não há dependências externas.

```bash
mkdir dados && cd dados
tar -xzf cb_dataset_2022_1_v1_81_tar.gz
tar -xzf cb_dataset_2022_2_v1_81_tar.gz
tar -xzf cb_dataset_2023_1_v1_81_tar.gz
cd ..

python3 -I teste_regras.py .                          # 15/15 casos corretos
python3 -I analise_preliminar.py dados resultado.json # cerca de 40 segundos
```

O `resultado.json` deve ser idêntico a `resultado_esperado.json`. A análise é determinística: não há
sorteio nem parâmetro aleatório.

## O que cada arquivo faz

- `analise_preliminar.py`: lê os logs de execução de cada estudante, analisa cada submissão com o
  módulo `ast` e aplica quatro regras do catálogo (C8, PD.7, PH.2 e PD.1). Conta as submissões
  com oportunidade (que contêm a construção), as marcadas, as marcadas e aprovadas, os estudantes
  com marca e os que repetem a marca em dois ou mais exercícios.
- `teste_regras.py`: 15 exemplos construídos à mão, com o que cada regra deve e não deve marcar.
- `gerar_planilha_inspecao.py`: sorteia, com semente fixa (2026), 20 submissões marcadas por regra.
- `planilha_inspecao.csv`: a planilha gerada, com colunas em branco para a inspeção manual.
- `SHA256SUMS_codigo.txt`: hashes dos scripts, para mostrar que o código não mudou depois da análise.

## Limitações

Os números contam marcas, e não acertos do analisador. A precisão e a revocação serão estimadas na
QP1, com rotulagem independente por dois avaliadores. Durante o desenvolvimento, duas regras foram
refinadas após inspeção de amostras: a de C8 passou a considerar apenas laços `for` sobre `range`,
e a de PH.2 apenas chamadas sobre variáveis.

"""
ETAPA 2 — Limpeza e preparação da base.

Lê a base bruta exportada do sistema e resolve os problemas típicos de dados de
verdade antes de qualquer análise: espaços sobrando, texto com capitalização
inconsistente, linhas duplicadas e valores inválidos. A saída é uma base
"limpa", pronta para a análise de risco.

  Entrada:  data/despesas_corporativas.csv   (base bruta)
  Saída:    data/despesas_tratadas.csv       (base limpa)

Uso:
    python scripts/01_limpeza.py
"""

import pandas as pd

ENTRADA = "data/despesas_corporativas.csv"
SAIDA = "data/despesas_tratadas.csv"

# forma de pagamento: mapeia variações para o valor canônico
FORMAS_CANONICAS = {"Cartão Corporativo", "Reembolso", "Boleto"}


def limpar():
    df = pd.read_csv(ENTRADA)
    linhas_inicio = len(df)
    print(f"Base bruta: {linhas_inicio} linhas")

    # 1) Remover espaços sobrando (início/fim) nas colunas de texto
    colunas_texto = ["colaborador", "departamento", "categoria", "fornecedor",
                     "descricao", "forma_pagamento", "aprovador",
                     "status_aprovacao", "possui_comprovante"]
    for c in colunas_texto:
        df[c] = df[c].astype(str).str.strip()

    # 2) Padronizar capitalização da forma de pagamento
    #    "CARTÃO CORPORATIVO" / "cartão corporativo" -> "Cartão Corporativo"
    df["forma_pagamento"] = df["forma_pagamento"].str.title()
    # correção de acento perdido pelo .title() quando necessário (segurança)
    invalidas = set(df["forma_pagamento"].unique()) - FORMAS_CANONICAS
    if invalidas:
        print(f"  Aviso: formas de pagamento fora do padrão encontradas: {invalidas}")

    # 3) Converter tipos
    df["data_despesa"] = pd.to_datetime(df["data_despesa"], errors="coerce")
    df["data_submissao"] = pd.to_datetime(df["data_submissao"], errors="coerce")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df["limite_politica"] = pd.to_numeric(df["limite_politica"], errors="coerce")

    # 4) Remover linhas 100% duplicadas
    antes = len(df)
    df = df.drop_duplicates()
    print(f"  Duplicatas exatas removidas: {antes - len(df)}")

    # 5) Remover valores inválidos (nulos ou <= 0)
    antes = len(df)
    df = df[df["valor"] > 0]
    df = df.dropna(subset=["data_despesa", "valor"])
    print(f"  Linhas com valor inválido (<= 0 ou vazio) removidas: {antes - len(df)}")

    # 6) Ordenar por data e reindexar
    df = df.sort_values("data_despesa").reset_index(drop=True)

    # 7) Salvar base tratada (datas de volta como texto AAAA-MM-DD)
    df["data_despesa"] = df["data_despesa"].dt.strftime("%Y-%m-%d")
    df["data_submissao"] = df["data_submissao"].dt.strftime("%Y-%m-%d")
    df.to_csv(SAIDA, index=False, encoding="utf-8")

    print(f"Base tratada: {len(df)} linhas  ->  {SAIDA}")
    print(f"Total removido na limpeza: {linhas_inicio - len(df)} linhas")


if __name__ == "__main__":
    limpar()

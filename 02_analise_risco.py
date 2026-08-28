"""
Análise de Risco em Despesas Corporativas.

Lê o dataset bruto, aplica um conjunto de regras de risco (heurísticas usadas em
auditoria de despesas), calcula um score de risco por transação e exporta:

  1) data/despesas_com_risco.csv  -> base enriquecida (usada no Power BI)
  2) data/kpis_resumo.csv         -> KPIs agregados
  3) imagens/*.png                -> gráficos da análise exploratória

Cada regra vira uma coluna booleana `flag_*`. O score é a soma ponderada das
flags; a partir do score, a transação recebe uma classificação de risco.

Uso:
    python scripts/analise_risco.py
"""

import os
import pandas as pd

# feriados (mesmo subconjunto usado na geração)
FERIADOS = {
    "2024-01-01", "2024-02-12", "2024-02-13", "2024-03-29", "2024-04-21",
    "2024-05-01", "2024-09-07", "2024-10-12", "2024-11-02", "2024-11-15",
    "2024-12-25", "2025-01-01", "2025-03-03", "2025-03-04", "2025-04-18",
    "2025-04-21", "2025-05-01", "2025-06-19",
}
FORNECEDORES_ATIPICOS = {
    "Fornecedor Novo LTDA", "JM Serviços ME", "Comercial Alfa", "XPTO Solutions",
}
LIMITE_ALCADA = 500  # alçada de aprovação simples assumida (R$)

# peso de cada regra no score de risco
PESOS = {
    "flag_acima_limite":   3,
    "flag_sem_comprovante":3,
    "flag_fornecedor_atipico": 3,
    "flag_duplicidade":    3,
    "flag_fracionamento":  2,
    "flag_fim_semana_feriado": 1,
    "flag_valor_redondo":  1,
    "flag_horario_atipico":1,
}


def carregar(caminho="data/despesas_tratadas.csv"):
    df = pd.read_csv(caminho)
    df["data_despesa"] = pd.to_datetime(df["data_despesa"])
    df["data_submissao"] = pd.to_datetime(df["data_submissao"])
    df["valor"] = df["valor"].astype(float)
    df["limite_politica"] = df["limite_politica"].astype(float)
    df["mes"] = df["data_despesa"].dt.to_period("M").astype(str)
    df["dia_semana"] = df["data_despesa"].dt.weekday  # 0=seg ... 6=dom
    df["hora"] = df["hora_submissao"].str.slice(0, 2).astype(int)
    return df


def aplicar_regras(df):
    # 1) acima do limite da política
    df["flag_acima_limite"] = df["valor"] > df["limite_politica"]

    # 2) sem comprovante em valor relevante (> R$ 250)
    df["flag_sem_comprovante"] = (df["possui_comprovante"] == "Não") & (df["valor"] > 250)

    # 3) fornecedor não homologado
    df["flag_fornecedor_atipico"] = df["fornecedor"].isin(FORNECEDORES_ATIPICOS)

    # 4) duplicidade: mesmo colaborador + fornecedor + valor, com <= 3 dias de diferença
    df = df.sort_values(["colaborador", "fornecedor", "valor", "data_despesa"])
    chave = ["colaborador", "fornecedor", "valor"]
    df["prev_data"] = df.groupby(chave)["data_despesa"].shift(1)
    dif = (df["data_despesa"] - df["prev_data"]).dt.days
    df["flag_duplicidade"] = dif.notna() & (dif <= 3)
    # marca também a 1ª ocorrência do par como duplicada
    dup_keys = df.loc[df["flag_duplicidade"], chave].drop_duplicates()
    mask_par = df.set_index(chave).index.isin(dup_keys.set_index(chave).index)
    df["flag_duplicidade"] = df["flag_duplicidade"] | mask_par
    df = df.drop(columns=["prev_data"])

    # 5) fracionamento: >= 3 transações do mesmo colaborador+categoria no mesmo dia,
    #    todas logo abaixo da alçada de aprovação
    abaixo = df[(df["valor"] < LIMITE_ALCADA) & (df["valor"] >= LIMITE_ALCADA - 80)]
    cont = (abaixo.groupby(["colaborador", "categoria", "data_despesa"])
                  .size().rename("qtd").reset_index())
    frac = cont[cont["qtd"] >= 3][["colaborador", "categoria", "data_despesa"]]
    frac_idx = df.merge(frac, on=["colaborador", "categoria", "data_despesa"], how="left", indicator=True)
    df["flag_fracionamento"] = (frac_idx["_merge"] == "both").values & (df["valor"] < LIMITE_ALCADA).values

    # 6) fim de semana ou feriado
    is_feriado = df["data_despesa"].dt.strftime("%Y-%m-%d").isin(FERIADOS)
    df["flag_fim_semana_feriado"] = (df["dia_semana"] >= 5) | is_feriado

    # 7) valor redondo alto (múltiplo exato de 500, acima de R$ 900)
    df["flag_valor_redondo"] = (df["valor"] % 500 == 0) & (df["valor"] >= 900)

    # 8) submissão em horário atípico (00h–05h)
    df["flag_horario_atipico"] = df["hora"] <= 5

    return df


def pontuar(df):
    df["score_risco"] = 0
    for flag, peso in PESOS.items():
        df["score_risco"] += df[flag].astype(int) * peso

    def classificar(s):
        if s == 0:
            return "Sem risco"
        if s <= 2:
            return "Baixo"
        if s <= 4:
            return "Médio"
        return "Alto"

    df["classificacao_risco"] = df["score_risco"].apply(classificar)
    df["possui_risco"] = df["score_risco"] > 0
    # lista de motivos legível para tooltip do dashboard
    rotulos = {
        "flag_acima_limite": "Acima do limite",
        "flag_sem_comprovante": "Sem comprovante",
        "flag_fornecedor_atipico": "Fornecedor não homologado",
        "flag_duplicidade": "Possível duplicidade",
        "flag_fracionamento": "Fracionamento",
        "flag_fim_semana_feriado": "Dia não útil",
        "flag_valor_redondo": "Valor redondo",
        "flag_horario_atipico": "Horário atípico",
    }
    df["motivos_risco"] = df.apply(
        lambda r: "; ".join(lbl for f, lbl in rotulos.items() if r[f]) or "—", axis=1)
    return df


def gerar_kpis(df):
    total = len(df)
    em_risco = int(df["possui_risco"].sum())
    kpis = {
        "total_transacoes": total,
        "valor_total": round(df["valor"].sum(), 2),
        "transacoes_em_risco": em_risco,
        "pct_transacoes_em_risco": round(100 * em_risco / total, 1),
        "valor_em_risco": round(df.loc[df["possui_risco"], "valor"].sum(), 2),
        "pct_valor_em_risco": round(100 * df.loc[df["possui_risco"], "valor"].sum() / df["valor"].sum(), 1),
        "transacoes_risco_alto": int((df["classificacao_risco"] == "Alto").sum()),
    }
    return pd.DataFrame([kpis]).T.reset_index().rename(columns={"index": "kpi", 0: "valor"})


def graficos(df):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        print("matplotlib indisponível — pulando gráficos.")
        return
    os.makedirs("imagens", exist_ok=True)
    cor = "#1F4E79"

    # 1) valor em risco por departamento
    g = (df[df["possui_risco"]].groupby("departamento")["valor"].sum()
           .sort_values(ascending=True))
    plt.figure(figsize=(8, 4.5))
    g.plot(kind="barh", color=cor)
    plt.title("Valor em risco por departamento (R$)")
    plt.xlabel("R$"); plt.tight_layout()
    plt.savefig("imagens/valor_risco_departamento.png", dpi=120); plt.close()

    # 2) transações em risco por tipo de flag
    flags = list(PESOS.keys())
    contagem = df[flags].sum().sort_values(ascending=True)
    rotulos = {
        "flag_acima_limite": "Acima do limite",
        "flag_sem_comprovante": "Sem comprovante",
        "flag_fornecedor_atipico": "Fornecedor atípico",
        "flag_duplicidade": "Duplicidade",
        "flag_fracionamento": "Fracionamento",
        "flag_fim_semana_feriado": "Dia não útil",
        "flag_valor_redondo": "Valor redondo",
        "flag_horario_atipico": "Horário atípico",
    }
    contagem.index = [rotulos[i] for i in contagem.index]
    plt.figure(figsize=(8, 4.5))
    contagem.plot(kind="barh", color=cor)
    plt.title("Transações sinalizadas por tipo de risco")
    plt.xlabel("qtd de transações"); plt.tight_layout()
    plt.savefig("imagens/risco_por_tipo.png", dpi=120); plt.close()

    # 3) evolução mensal do valor em risco
    m = (df[df["possui_risco"]].groupby("mes")["valor"].sum())
    plt.figure(figsize=(9, 4))
    m.plot(marker="o", color=cor)
    plt.title("Evolução mensal do valor em risco (R$)")
    plt.xticks(rotation=45); plt.tight_layout()
    plt.savefig("imagens/evolucao_mensal_risco.png", dpi=120); plt.close()
    print("Gráficos salvos em imagens/")


def main():
    df = carregar()
    df = aplicar_regras(df)
    df = pontuar(df)
    df = df.sort_values("data_despesa").reset_index(drop=True)

    os.makedirs("data", exist_ok=True)
    df.to_csv("data/despesas_com_risco.csv", index=False, encoding="utf-8")

    kpis = gerar_kpis(df)
    kpis.to_csv("data/kpis_resumo.csv", index=False, encoding="utf-8")

    graficos(df)

    print("\n=== RESUMO ===")
    print(kpis.to_string(index=False))
    print("\nDistribuição por classificação de risco:")
    print(df["classificacao_risco"].value_counts().to_string())


if __name__ == "__main__":
    main()

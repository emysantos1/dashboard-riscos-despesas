# 🖥️ Guia — Montando o dashboard no Power BI (~2h30)

Passo a passo para reconstruir o dashboard a partir de `data/despesas_com_risco.csv`.
A ideia é ter **1 página executiva** limpa. Não precisa complicar — clareza vale mais que enfeite.

---

## 1. Importar os dados (10 min)

1. **Obter dados → Texto/CSV** → selecione `data/despesas_com_risco.csv`.
2. No **Transformar Dados (Power Query)**, confira os tipos:
   - `data_despesa`, `data_submissao` → **Data**
   - `valor`, `limite_politica`, `score_risco` → **Número decimal / inteiro**
   - `possui_risco` e as colunas `flag_*` → **Verdadeiro/Falso**
3. **Fechar e Aplicar.**

## 2. Medidas em DAX (20 min)

Crie uma tabela de medidas (`Inserir → Nova medida`):

```DAX
Total Transações = COUNTROWS('despesas_com_risco')

Valor Total = SUM('despesas_com_risco'[valor])

Transações em Risco =
CALCULATE([Total Transações], 'despesas_com_risco'[possui_risco] = TRUE())

% Transações em Risco =
DIVIDE([Transações em Risco], [Total Transações])

Valor em Risco =
CALCULATE([Valor Total], 'despesas_com_risco'[possui_risco] = TRUE())

% Valor em Risco = DIVIDE([Valor em Risco], [Valor Total])

Transações Risco Alto =
CALCULATE([Total Transações], 'despesas_com_risco'[classificacao_risco] = "Alto")
```

## 3. Layout da página (1h30)

Sugestão de organização, de cima para baixo:

**Linha 1 — Cartões de KPI** (visual "Cartão"):
- Valor Total · % Transações em Risco · Valor em Risco · Transações Risco Alto

**Linha 2 — Dois gráficos:**
- **Barras horizontais:** `departamento` × **Valor em Risco** (quem mais concentra risco)
- **Rosca/Pizza:** contagem por `classificacao_risco` (use cores: Alto = vermelho, Médio = laranja, Baixo = amarelo, Sem risco = cinza/verde)

**Linha 3 — Tendência + detalhe:**
- **Linha:** `mes` × **Valor em Risco** (evolução no tempo)
- **Tabela / Matriz:** top transações de risco Alto — colunas `id_transacao`, `colaborador`, `departamento`, `categoria`, `valor`, `score_risco`, `motivos_risco`. Ordene por `score_risco` decrescente.

**Segmentações (filtros) na lateral:**
- `departamento`, `categoria`, `classificacao_risco`, `mes`

## 4. Acabamento (20 min)

- Título da página: **"Riscos em Despesas Corporativas"**.
- Paleta sóbria (azul-escuro `#1F4E79` + cinzas); vermelho **apenas** para risco Alto.
- Formate os cartões de valor como moeda (R$) e os percentuais com 1 casa.
- Um pequeno texto/nota: *"Dados sintéticos — projeto de portfólio"*.

## 5. Exportar prints para o GitHub (10 min)

- Tire um print da página completa e salve como `imagens/dashboard_powerbi.png`.
- (Opcional) 1 print com um filtro aplicado, ex.: só departamento "Comercial".
- Referencie os prints no README (já há espaço reservado na seção de resultados).
- Salve o arquivo `.pbix` na raiz do repositório para quem quiser abrir.

---

### ⏱️ Dica de tempo
Se apertar o relógio, priorize nesta ordem: **KPIs → tabela de risco Alto → barras por departamento**. Esses três já contam a história toda. Rosca e linha do tempo são o "bônus".

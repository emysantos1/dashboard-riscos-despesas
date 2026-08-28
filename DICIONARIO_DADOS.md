# 📖 Dicionário de Dados

## `data/despesas_corporativas.csv` — base bruta

| Campo | Tipo | Descrição |
|---|---|---|
| `id_transacao` | texto | Identificador único da transação (ex.: `TX1313`) |
| `data_despesa` | data | Data em que a despesa ocorreu |
| `colaborador` | texto | Colaborador responsável pela despesa |
| `departamento` | texto | Departamento do colaborador |
| `categoria` | texto | Categoria da despesa (Viagem, Hospedagem, Alimentação, etc.) |
| `fornecedor` | texto | Fornecedor / estabelecimento |
| `descricao` | texto | Descrição livre da despesa |
| `valor` | decimal | Valor da despesa em R$ |
| `moeda` | texto | Moeda (BRL) |
| `forma_pagamento` | texto | Cartão Corporativo, Reembolso ou Boleto |
| `limite_politica` | decimal | Limite da política por transação para a categoria |
| `aprovador` | texto | Responsável pela aprovação |
| `status_aprovacao` | texto | Aprovado, Pendente ou Rejeitado |
| `possui_comprovante` | texto | Sim / Não |
| `data_submissao` | data | Data em que a despesa foi lançada no sistema |
| `hora_submissao` | texto | Hora do lançamento (HH:MM) |

## `data/despesas_com_risco.csv` — base enriquecida

Contém **todas as colunas acima** + as colunas de análise abaixo:

| Campo | Tipo | Descrição |
|---|---|---|
| `flag_acima_limite` | booleano | Valor acima do limite da política |
| `flag_sem_comprovante` | booleano | Despesa > R$ 250 sem comprovante |
| `flag_fornecedor_atipico` | booleano | Fornecedor não homologado |
| `flag_duplicidade` | booleano | Possível duplicidade (mesmo colaborador/fornecedor/valor em ≤ 3 dias) |
| `flag_fracionamento` | booleano | Compra fracionada abaixo da alçada de aprovação |
| `flag_fim_semana_feriado` | booleano | Despesa em fim de semana ou feriado |
| `flag_valor_redondo` | booleano | Valor redondo alto (múltiplo de R$ 500 ≥ R$ 900) |
| `flag_horario_atipico` | booleano | Submissão entre 00h e 05h |
| `score_risco` | inteiro | Soma ponderada das flags |
| `classificacao_risco` | texto | Sem risco · Baixo · Médio · Alto |
| `possui_risco` | booleano | Verdadeiro se `score_risco` > 0 |
| `motivos_risco` | texto | Lista legível dos motivos (para tooltip do dashboard) |
| `mes` | texto | Competência (AAAA-MM) da despesa |

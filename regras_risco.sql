-- =============================================================================
-- Regras de risco em despesas corporativas — versão SQL
-- Dialeto: padrão ANSI / compatível com PostgreSQL, SQLite e DuckDB.
-- Objetivo: reproduzir em SQL as mesmas heurísticas do script Python, mostrando
--           a lógica de consulta em banco de dados.
--
-- Tabela de entrada esperada: despesas
--   (id_transacao, data_despesa, colaborador, departamento, categoria,
--    fornecedor, valor, forma_pagamento, limite_politica, possui_comprovante,
--    data_submissao, hora_submissao)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1) Transações acima do limite da política
-- -----------------------------------------------------------------------------
SELECT id_transacao, colaborador, categoria, valor, limite_politica,
       (valor - limite_politica) AS excedente
FROM despesas
WHERE valor > limite_politica
ORDER BY excedente DESC;

-- -----------------------------------------------------------------------------
-- 2) Sem comprovante em valor relevante (> R$ 250)
-- -----------------------------------------------------------------------------
SELECT id_transacao, colaborador, categoria, valor
FROM despesas
WHERE possui_comprovante = 'Não' AND valor > 250;

-- -----------------------------------------------------------------------------
-- 3) Fornecedor não homologado (não consta na lista oficial)
-- -----------------------------------------------------------------------------
SELECT id_transacao, colaborador, fornecedor, valor
FROM despesas
WHERE fornecedor IN ('Fornecedor Novo LTDA', 'JM Serviços ME',
                     'Comercial Alfa', 'XPTO Solutions');

-- -----------------------------------------------------------------------------
-- 4) Possível duplicidade: mesmo colaborador + fornecedor + valor,
--    com diferença de até 3 dias entre as despesas
-- -----------------------------------------------------------------------------
SELECT a.id_transacao, a.colaborador, a.fornecedor, a.valor,
       a.data_despesa, b.data_despesa AS data_par
FROM despesas a
JOIN despesas b
  ON a.colaborador = b.colaborador
 AND a.fornecedor  = b.fornecedor
 AND a.valor       = b.valor
 AND a.id_transacao < b.id_transacao
 AND ABS(CAST(julianday(b.data_despesa) - julianday(a.data_despesa) AS INT)) <= 3;
-- (PostgreSQL: use ABS(b.data_despesa - a.data_despesa) <= 3 com colunas DATE)

-- -----------------------------------------------------------------------------
-- 5) Fracionamento: 3+ despesas do mesmo colaborador/categoria no mesmo dia,
--    todas logo abaixo da alçada de aprovação (R$ 500)
-- -----------------------------------------------------------------------------
SELECT colaborador, categoria, data_despesa,
       COUNT(*) AS qtd, SUM(valor) AS total_dia
FROM despesas
WHERE valor < 500 AND valor >= 420
GROUP BY colaborador, categoria, data_despesa
HAVING COUNT(*) >= 3
ORDER BY total_dia DESC;

-- -----------------------------------------------------------------------------
-- 6) Despesa em fim de semana (0=domingo em SQLite via strftime %w; 6=sábado)
-- -----------------------------------------------------------------------------
SELECT id_transacao, colaborador, categoria, valor, data_despesa
FROM despesas
WHERE CAST(strftime('%w', data_despesa) AS INT) IN (0, 6);
-- (PostgreSQL: WHERE EXTRACT(DOW FROM data_despesa) IN (0, 6))

-- -----------------------------------------------------------------------------
-- 7) Valor redondo alto (múltiplo exato de 500, a partir de R$ 900)
-- -----------------------------------------------------------------------------
SELECT id_transacao, colaborador, categoria, valor
FROM despesas
WHERE (valor - ROUND(valor / 500, 0) * 500) = 0 AND valor >= 900;

-- -----------------------------------------------------------------------------
-- 8) Submissão em horário atípico (madrugada, 00h–05h)
-- -----------------------------------------------------------------------------
SELECT id_transacao, colaborador, valor, hora_submissao
FROM despesas
WHERE CAST(substr(hora_submissao, 1, 2) AS INT) <= 5;

-- -----------------------------------------------------------------------------
-- KPIs agregados para o dashboard
-- -----------------------------------------------------------------------------
-- Valor total e nº de transações por departamento
SELECT departamento,
       COUNT(*)      AS qtd_transacoes,
       SUM(valor)    AS valor_total
FROM despesas
GROUP BY departamento
ORDER BY valor_total DESC;

-- Ticket médio por categoria
SELECT categoria,
       COUNT(*)          AS qtd,
       ROUND(AVG(valor), 2) AS ticket_medio,
       SUM(valor)        AS valor_total
FROM despesas
GROUP BY categoria
ORDER BY valor_total DESC;

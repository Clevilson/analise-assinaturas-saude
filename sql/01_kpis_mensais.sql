-- KPIs mensais da carteira de assinaturas
-- ativas no início, novas, cancelamentos, ativas no fim, churn % e receita recorrente (MRR)
--
-- Churn % = cancelamentos do mês / ativas no início do mês.
-- (Quem entra e cancela no mesmo mês conta como cancelamento, mas não entra na base inicial.)
--
-- BigQuery: troque o CTE recursivo por
--   UNNEST(GENERATE_DATE_ARRAY('2025-01-01', '2026-10-01', INTERVAL 1 MONTH)) AS mes
-- e date(mes, '+1 month') por DATE_ADD(mes, INTERVAL 1 MONTH).

WITH RECURSIVE meses(mes) AS (
    SELECT '2025-01-01'
    UNION ALL
    SELECT date(mes, '+1 month') FROM meses WHERE mes < '2026-10-01'
),
base AS (
    SELECT
        m.mes,
        SUM(a.data_inicio < m.mes
            AND (a.data_cancelamento IS NULL OR a.data_cancelamento >= m.mes))      AS ativas_inicio,
        SUM(a.data_inicio >= m.mes AND a.data_inicio < date(m.mes, '+1 month'))     AS novas,
        SUM(a.data_cancelamento >= m.mes
            AND a.data_cancelamento < date(m.mes, '+1 month'))                       AS cancelamentos,
        SUM(CASE WHEN a.data_inicio < date(m.mes, '+1 month')
                  AND (a.data_cancelamento IS NULL
                       OR a.data_cancelamento >= date(m.mes, '+1 month'))
                 THEN a.valor_mensal ELSE 0 END)                                    AS mrr_fim
    FROM meses m
    CROSS JOIN assinaturas a
    GROUP BY m.mes
)
SELECT
    mes,
    ativas_inicio,
    novas,
    cancelamentos,
    ativas_inicio + novas - cancelamentos                        AS ativas_fim,
    ROUND(100.0 * cancelamentos / NULLIF(ativas_inicio, 0), 2)   AS churn_pct,
    ROUND(mrr_fim, 2)                                            AS mrr_fim
FROM base
ORDER BY mes;

-- Onde está o churn? Taxa de cancelamento em 90 dias por canal de venda e plano.
-- Só considera assinaturas com pelo menos 90 dias de observação.

SELECT
    canal,
    plano,
    COUNT(*)                                                           AS assinaturas,
    SUM(data_cancelamento IS NOT NULL
        AND julianday(data_cancelamento) - julianday(data_inicio) <= 90) AS canceladas_90d,
    ROUND(100.0 * AVG(data_cancelamento IS NOT NULL
        AND julianday(data_cancelamento) - julianday(data_inicio) <= 90), 1) AS churn_90d_pct
FROM assinaturas
WHERE julianday('2026-10-31') - julianday(data_inicio) >= 90
GROUP BY canal, plano
ORDER BY churn_90d_pct DESC;

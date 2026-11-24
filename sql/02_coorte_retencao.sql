-- Retenção por coorte (mês de entrada) nos primeiros 12 meses
-- retencao = % das assinaturas da coorte ainda ativas ao fim do mês k
-- Só entram combinações coorte × k já completamente observadas até o corte da base.

WITH RECURSIVE deslocamentos(k) AS (
    SELECT 0
    UNION ALL
    SELECT k + 1 FROM deslocamentos WHERE k < 12
),
coortes AS (
    SELECT id, date(data_inicio, 'start of month') AS coorte, data_cancelamento
    FROM assinaturas
)
SELECT
    c.coorte,
    d.k                                                       AS meses_desde_entrada,
    COUNT(*)                                                  AS tamanho_coorte,
    ROUND(AVG(c.data_cancelamento IS NULL
              OR c.data_cancelamento >= date(c.coorte, '+' || (d.k + 1) || ' months')), 4) AS retencao
FROM coortes c
CROSS JOIN deslocamentos d
WHERE date(c.coorte, '+' || (d.k + 1) || ' months') <= '2026-11-01'
GROUP BY c.coorte, d.k
ORDER BY c.coorte, d.k;

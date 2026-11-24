-- Ranking mensal de vendedores: vendas × meta, atingimento e posição
-- Mostra funções de janela (ROW_NUMBER, SUM OVER) usadas em painéis de "Top 5".

WITH vendas AS (
    SELECT vendedor_id, date(data_inicio, 'start of month') AS mes, COUNT(*) AS vendas
    FROM assinaturas
    GROUP BY 1, 2
),
resultado AS (
    SELECT
        m.mes,
        v.nome            AS vendedor,
        u.nome            AS unidade,
        COALESCE(s.vendas, 0) AS vendas,
        m.meta,
        ROUND(100.0 * COALESCE(s.vendas, 0) / m.meta, 1) AS atingimento_pct
    FROM metas m
    JOIN vendedores v ON v.id = m.vendedor_id
    JOIN unidades u   ON u.id = v.unidade_id
    LEFT JOIN vendas s ON s.vendedor_id = m.vendedor_id AND s.mes = m.mes
)
SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY mes ORDER BY atingimento_pct DESC, vendas DESC) AS posicao,
    SUM(vendas) OVER (PARTITION BY mes, unidade)                                   AS vendas_unidade
FROM resultado
WHERE mes = (SELECT MAX(mes) FROM resultado)
ORDER BY posicao;

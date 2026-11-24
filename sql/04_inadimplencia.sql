-- Inadimplência por competência: valor faturado × valor não pago há mais de 30 dias do vencimento

SELECT
    competencia,
    COUNT(*)                                                            AS cobrancas,
    ROUND(SUM(valor), 2)                                                AS faturado,
    ROUND(SUM(CASE WHEN status = 'paga' THEN valor ELSE 0 END), 2)      AS recebido,
    ROUND(SUM(CASE WHEN status <> 'paga'
                    AND julianday('2026-10-31') - julianday(vencimento) > 30
                   THEN valor ELSE 0 END), 2)                           AS inadimplente_30d,
    ROUND(100.0 * SUM(CASE WHEN status <> 'paga'
                            AND julianday('2026-10-31') - julianday(vencimento) > 30
                           THEN valor ELSE 0 END) / SUM(valor), 2)      AS inadimplencia_pct
FROM cobrancas
GROUP BY competencia
ORDER BY competencia;

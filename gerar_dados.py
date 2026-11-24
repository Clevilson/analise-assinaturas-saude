"""Gera uma base FICTÍCIA de assinaturas de um plano de saúde/benefícios.

Nenhum dado real é usado: nomes, unidades, valores e comportamentos são
sintéticos, gerados com semente fixa para que o resultado seja reproduzível.

Saída: dados/assinaturas.db (SQLite) com as tabelas
    unidades, vendedores, assinaturas, cobrancas, metas
"""

from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

SEMENTE = 42
INICIO = date(2025, 1, 1)
FIM = date(2026, 10, 31)  # data de corte da base

UNIDADES = [
    (1, "Unidade Centro", "Cidade A"),
    (2, "Unidade Norte", "Cidade A"),
    (3, "Unidade Sul", "Cidade B"),
    (4, "Unidade Leste", "Cidade B"),
]
PLANOS = {"Individual": 39.90, "Familiar": 69.90}
CANAIS = {"Recepção": 0.55, "WhatsApp": 0.30, "Site": 0.15}
# risco mensal de cancelamento por canal (site converte "frio" e cancela mais)
RISCO_CANAL = {"Recepção": 0.030, "WhatsApp": 0.038, "Site": 0.055}

random.seed(SEMENTE)


def primeiro_dia(d: date) -> date:
    return d.replace(day=1)


def soma_meses(d: date, n: int) -> date:
    m = d.month - 1 + n
    return date(d.year + m // 12, m % 12 + 1, 1)


def meses(inicio: date, fim: date):
    m = primeiro_dia(inicio)
    while m <= fim:
        yield m
        m = soma_meses(m, 1)


def dia_aleatorio(mes: date) -> date:
    prox = soma_meses(mes, 1)
    return mes + timedelta(days=random.randrange((prox - mes).days))


def escolher(pesos: dict[str, float]) -> str:
    return random.choices(list(pesos), weights=list(pesos.values()))[0]


def main() -> None:
    destino = Path(__file__).parent / "dados"
    destino.mkdir(exist_ok=True)
    caminho = destino / "assinaturas.db"
    caminho.unlink(missing_ok=True)
    con = sqlite3.connect(caminho)
    cur = con.cursor()

    cur.executescript(
        """
        CREATE TABLE unidades (id INTEGER PRIMARY KEY, nome TEXT, cidade TEXT);
        CREATE TABLE vendedores (id INTEGER PRIMARY KEY, nome TEXT, unidade_id INTEGER);
        CREATE TABLE assinaturas (
            id INTEGER PRIMARY KEY, cliente_id INTEGER, unidade_id INTEGER,
            vendedor_id INTEGER, plano TEXT, canal TEXT, valor_mensal REAL,
            data_inicio TEXT, data_cancelamento TEXT
        );
        CREATE TABLE cobrancas (
            id INTEGER PRIMARY KEY, assinatura_id INTEGER, competencia TEXT,
            vencimento TEXT, valor REAL, status TEXT, data_pagamento TEXT
        );
        CREATE TABLE metas (vendedor_id INTEGER, mes TEXT, meta INTEGER);
        """
    )
    cur.executemany("INSERT INTO unidades VALUES (?,?,?)", UNIDADES)

    vendedores = []
    vid = 1
    for uid, *_ in UNIDADES:
        for _ in range(4):
            vendedores.append((vid, f"Vendedor {vid:02d}", uid))
            vid += 1
    cur.executemany("INSERT INTO vendedores VALUES (?,?,?)", vendedores)
    # cada vendedor tem uma "habilidade" que muda o volume de vendas
    habilidade = {v[0]: random.uniform(0.6, 1.5) for v in vendedores}

    assinaturas, cobrancas, metas = [], [], []
    aid = cid = cobid = 1
    for i, mes in enumerate(meses(INICIO, FIM)):
        # crescimento + sazonalidade simples (jan/jul mais fortes)
        base = 9 + i * 0.35 + (3 if mes.month in (1, 7) else 0)
        for v_id, _, u_id in vendedores:
            metas.append((v_id, mes.isoformat(), round(base * 1.1)))
            qtd = max(0, round(random.gauss(base * habilidade[v_id], 2.5)))
            for _ in range(qtd):
                plano = random.choices(list(PLANOS), weights=[0.7, 0.3])[0]
                canal = escolher(CANAIS)
                inicio = dia_aleatorio(mes)
                if inicio > FIM:
                    continue
                # sobrevivência mês a mês; risco maior nos 3 primeiros meses
                cancel = None
                m = soma_meses(primeiro_dia(inicio), 1)
                k = 1
                while m <= FIM:
                    risco = RISCO_CANAL[canal] * (1.8 if k <= 3 else 1.0)
                    risco *= 0.8 if plano == "Familiar" else 1.0
                    if random.random() < risco:
                        cancel = min(dia_aleatorio(m), FIM)
                        break
                    m = soma_meses(m, 1)
                    k += 1
                assinaturas.append(
                    (aid, cid, u_id, v_id, plano, canal, PLANOS[plano],
                     inicio.isoformat(), cancel.isoformat() if cancel else None)
                )
                # uma cobrança por mês de vigência
                for comp in meses(inicio, cancel or FIM):
                    venc = comp + timedelta(days=9)
                    if venc > FIM:
                        break
                    sorteio = random.random()
                    if sorteio < 0.94:
                        status, pago = "paga", venc + timedelta(days=random.randint(-5, 6))
                    elif (FIM - venc).days < 30:
                        status, pago = "em_aberto", None
                    else:
                        status, pago = "atrasada", None
                    cobrancas.append(
                        (cobid, aid, comp.isoformat(), venc.isoformat(), PLANOS[plano],
                         status, min(pago, FIM).isoformat() if pago else None)
                    )
                    cobid += 1
                aid += 1
                cid += 1

    cur.executemany("INSERT INTO assinaturas VALUES (?,?,?,?,?,?,?,?,?)", assinaturas)
    cur.executemany("INSERT INTO cobrancas VALUES (?,?,?,?,?,?,?)", cobrancas)
    cur.executemany("INSERT INTO metas VALUES (?,?,?)", metas)
    con.commit()
    con.close()
    print(f"{len(assinaturas):,} assinaturas e {len(cobrancas):,} cobranças em {caminho}")


if __name__ == "__main__":
    main()

"""Executa as consultas da pasta sql/ e gera tabelas (CSV) e gráficos (PNG).

Uso:
    python gerar_dados.py
    python analise.py
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

RAIZ = Path(__file__).parent
SQL = RAIZ / "sql"
SAIDA = RAIZ / "resultados"
IMG = RAIZ / "img"

AZUL, LARANJA, CINZA = "#2563eb", "#ea580c", "#6b7280"


def consultar(con: sqlite3.Connection, arquivo: str) -> pd.DataFrame:
    df = pd.read_sql_query((SQL / arquivo).read_text(encoding="utf-8"), con)
    df.to_csv(SAIDA / arquivo.replace(".sql", ".csv"), index=False)
    return df


def estilo(ax, titulo: str) -> None:
    ax.set_title(titulo, loc="left", fontsize=13, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25)


def grafico_mrr_churn(kpis: pd.DataFrame) -> None:
    kpis["mes"] = pd.to_datetime(kpis["mes"])
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(kpis["mes"], kpis["mrr_fim"] / 1000, color=AZUL, lw=2.5, label="MRR (R$ mil)")
    ax.set_ylabel("MRR (R$ mil)", color=AZUL)
    estilo(ax, "Receita recorrente cresce e o churn se estabiliza perto de 4% ao mês")
    ax2 = ax.twinx()
    ax2.plot(kpis["mes"].iloc[1:], kpis["churn_pct"].iloc[1:], color=LARANJA, lw=2, ls="--",
             label="Churn mensal (%)")
    ax2.set_ylabel("Churn mensal (%)", color=LARANJA)
    ax2.set_ylim(0, max(kpis["churn_pct"].iloc[1:]) * 1.4)
    ax2.spines[["top"]].set_visible(False)
    fig.legend(loc="upper left", bbox_to_anchor=(0.08, 0.86), frameon=False)
    fig.tight_layout()
    fig.savefig(IMG / "mrr_churn.png", dpi=150)
    plt.close(fig)


def grafico_coorte(coorte: pd.DataFrame) -> None:
    tabela = coorte.pivot(index="coorte", columns="meses_desde_entrada", values="retencao")
    nomes = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    tabela.index = [f"{nomes[d.month - 1]}/{d:%y}" for d in pd.to_datetime(tabela.index)]
    fig, ax = plt.subplots(figsize=(10, 6.5))
    im = ax.imshow(tabela.values * 100, cmap="Blues", vmin=40, vmax=100, aspect="auto")
    ax.set_xticks(range(tabela.shape[1]), tabela.columns)
    ax.set_yticks(range(tabela.shape[0]), tabela.index)
    ax.set_xlabel("Meses desde a entrada")
    for (i, j), v in pd.DataFrame(tabela.values).stack().dropna().items():
        ax.text(j, i, f"{v * 100:.0f}", ha="center", va="center", fontsize=7,
                color="white" if v > 0.75 else "black")
    ax.set_title("Retenção por coorte (%): a maior perda acontece nos 3 primeiros meses",
                 loc="left", fontsize=13, fontweight="bold")
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(IMG / "coorte_retencao.png", dpi=150)
    plt.close(fig)


def grafico_canal(canal: pd.DataFrame) -> None:
    canal = canal.sort_values("churn_90d_pct")
    rotulos = canal["canal"] + " · " + canal["plano"]
    fig, ax = plt.subplots(figsize=(9, 4))
    cores = [LARANJA if c == "Site" else CINZA for c in canal["canal"]]
    ax.barh(rotulos, canal["churn_90d_pct"], color=cores)
    for y, v in enumerate(canal["churn_90d_pct"]):
        ax.text(v + 0.3, y, f"{v:.1f}%", va="center", fontsize=9)
    estilo(ax, "Cancelamento em 90 dias por canal e plano")
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(IMG / "churn_canal.png", dpi=150)
    plt.close(fig)


def main() -> None:
    banco = RAIZ / "dados" / "assinaturas.db"
    if not banco.exists():
        raise SystemExit("Rode antes: python gerar_dados.py")
    SAIDA.mkdir(exist_ok=True)
    IMG.mkdir(exist_ok=True)

    with sqlite3.connect(banco) as con:
        kpis = consultar(con, "01_kpis_mensais.sql")
        coorte = consultar(con, "02_coorte_retencao.sql")
        canal = consultar(con, "03_churn_por_canal_plano.sql")
        inad = consultar(con, "04_inadimplencia.sql")
        ranking = consultar(con, "05_ranking_vendedores.sql")

    grafico_mrr_churn(kpis.copy())
    grafico_coorte(coorte)
    grafico_canal(canal)

    ult = kpis.iloc[-1]
    print("Último mês:", ult.to_dict())
    print("Churn médio (%):", round(kpis["churn_pct"].iloc[1:].mean(), 2))
    m1 = coorte[coorte.meses_desde_entrada == 3]["retencao"].mean()
    m12 = coorte[coorte.meses_desde_entrada == 12]["retencao"].mean()
    print(f"Retenção média M3: {m1:.1%} | M12: {m12:.1%}")
    print(canal.to_string(index=False))
    print("Inadimplência 30d média (%):",
          round(inad[inad.inadimplencia_pct > 0]["inadimplencia_pct"].mean(), 2))
    print(ranking.head(5).to_string(index=False))


if __name__ == "__main__":
    main()

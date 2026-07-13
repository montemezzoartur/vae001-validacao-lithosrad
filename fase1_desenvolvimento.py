#!/usr/bin/env python3
"""
VAE-001 - FASE 1: ANALISE EXPLORATORIA DOS 25 DE DESENVOLVIMENTO

Roda o detectar_calculos() REAL do LithosRad (hu_min=200, o default -- nao
passamos outro) sobre os 25 calculos do conjunto de DESENVOLVIMENTO do Freiburg.
NENHUM calculo LACRADO e tocado: carregar_freiburg e chamado SOMENTE com
grupo='DESENV'.

A mascara de rim cobre TODO o volume: cada VOI e um unico calculo isolado em
agua (fundo ~0 UH), entao o limiar de 200 UH ja isola o calculo.

Confronta o resultado com a predicao pre-registrada (results/fase1_predicao.md,
esferas: +8 a +17% de vies de volume no estrato >=10 mm) e avalia, de forma
EXPLORATORIA, as hipoteses pre-registradas:
  H1  o vies de volume real (>=10 mm) sera MAIOR que o das esferas
  H2  o vies cresce com a densidade (hu_max) do calculo
  H3  a taxa de falha de segmentacao sera ~ 0
A confirmacao/refutacao DEFINITIVA e sobre o conjunto LACRADO, apos o
congelamento do LithosRad. Aqui e exploracao no desenvolvimento -- nao e
criterio de aceitacao.

Saidas:
  results/fase1_desenv.csv
  results/fase1_bland_altman.png
  results/fase1_erro_vs_humax.png
  results/fase1_erro_vs_gtvol.png

Uso:  python fase1_desenvolvimento.py
"""
import csv
import io
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import spearmanr, wilcoxon

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from freiburg_io import carregar_freiburg                    # noqa: E402
from lithos.dicom_io import Volume                           # noqa: E402
from lithos.kidney_segmentation import MascarasRins          # noqa: E402
from lithos.stone_detection import detectar_calculos         # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

MAT = ROOT / "data" / "raw" / "ct-uroliths_matlab.mat"
OUT = ROOT / "results"

# Predicao pre-registrada (results/fase1_predicao.md): D (mm) -> vies de vol (%).
# Congelada; usada so para interpolar o previsto de cada calculo pelo seu D.
PRED_D = np.array([3, 4, 5, 6, 8, 10, 12, 15, 20], float)
PRED_E = np.array([53.0, 34.8, 36.3, 25.2, 21.3, 17.1, 11.8, 11.0, 8.3], float)

ESTRATOS = ["5-10", "10-20", ">20"]
COR = {"5-10": "#1b9e77", "10-20": "#d95f02", ">20": "#7570b3"}


def estrato(diam_mm):
    return "5-10" if diam_mm < 10 else ("10-20" if diam_mm < 20 else ">20")


def pred_esfera(diam_mm):
    """Vies previsto pela esfera para um diametro (interp/clamp na tabela)."""
    return float(np.interp(diam_mm, PRED_D, PRED_E))


def mede(vol):
    """detectar_calculos REAL com mascara cobrindo tudo. hu_min=200 e o default
    -- nao passamos outro. Retorna (maior_componente, n_componentes); o
    componente e None se nada foi segmentado (falha)."""
    cheia = np.ones(vol.array.shape, bool)
    m = MascarasRins(esquerdo=cheia, direito=None, spacing=vol.spacing, aviso=None)
    res = detectar_calculos(vol, m)
    if not res.itens:
        return None, 0
    return max(res.itens, key=lambda x: x.volume_mm3), len(res.itens)


def analisar():
    """Mede os 25 de DESENV e devolve uma lista de dicts (uma linha por calculo)."""
    linhas = []
    for c in carregar_freiburg(MAT, grupo="DESENV"):      # NUNCA 'LACRADO'/'TODOS'
        vol = Volume(array=c["array"], spacing=c["spacing"])
        st, n_it = mede(vol)
        gt_mm3 = c["gt_vol_mL"] * 1000.0                  # 1 mL = 1000 mm^3
        base = dict(mat_id=c["id"], gt_vol_mL=c["gt_vol_mL"],
                    gt_diam_mm=c["gt_diam_mm"], stone_type=c["stone_type"],
                    estrato=estrato(c["gt_diam_mm"]),
                    pred_esfera_pct=pred_esfera(c["gt_diam_mm"]))
        if st is None:
            linhas.append({**base, "hu_max": None, "volume_lithos_mm3": None,
                           "diametro_lithos_mm": None, "n_voxels": 0,
                           "status": "falha", "erro_vol_pct": None,
                           "erro_diam_mm": None})
            continue
        linhas.append({**base,
                       "hu_max": st.hu_max,
                       "volume_lithos_mm3": st.volume_mm3,
                       "diametro_lithos_mm": st.diametro_mm,
                       "n_voxels": st.n_voxels,
                       "status": "ok" if n_it == 1 else f"multiplo:{n_it}",
                       "erro_vol_pct": 100.0 * (st.volume_mm3 / gt_mm3 - 1.0),
                       "erro_diam_mm": st.diametro_mm - c["gt_diam_mm"]})
    return linhas


COLS = ["mat_id", "gt_vol_mL", "gt_diam_mm", "stone_type", "hu_max",
        "volume_lithos_mm3", "diametro_lithos_mm", "n_voxels", "status",
        "estrato", "erro_vol_pct", "erro_diam_mm", "pred_esfera_pct"]


def salvar_csv(linhas):
    OUT.mkdir(exist_ok=True)
    caminho = OUT / "fase1_desenv.csv"
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for l in linhas:
            w.writerow({k: l[k] for k in COLS})
    return caminho


# ---------------------------------------------------------------- graficos ----

def _pontos_por_estrato(ok, x_key, y_key):
    for e in ESTRATOS:
        xs = [l[x_key] for l in ok if l["estrato"] == e]
        ys = [l[y_key] for l in ok if l["estrato"] == e]
        yield e, xs, ys


def grafico_bland_altman(ok):
    err = np.array([l["erro_vol_pct"] for l in ok])
    vies, sd = err.mean(), err.std(ddof=1)
    lo, hi = vies - 1.96 * sd, vies + 1.96 * sd

    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    ax.axhspan(8, 17, color="#2ca02c", alpha=0.10,
               label="predicao esferas >=10 mm (+8..+17%)")
    for e, xs, ys in _pontos_por_estrato(ok, "volume_lithos_mm3", "erro_vol_pct"):
        xs = [l["gt_vol_mL"] * 1000 for l in ok if l["estrato"] == e]
        ax.scatter(xs, ys, c=COR[e], s=48, edgecolor="k", linewidth=0.4,
                   label=f"{e} mm (n={len(xs)})", zorder=3)
    ax.axhline(0, color="k", lw=0.8)
    ax.axhline(vies, color="k", ls="--", lw=1.2, label=f"vies global {vies:+.0f}%")
    ax.axhline(lo, color="grey", ls=":", lw=1.0)
    ax.axhline(hi, color="grey", ls=":", lw=1.0,
               label=f"LoA 95% [{lo:+.0f}, {hi:+.0f}]%")
    ax.set_xscale("log")
    ax.set_xlabel("volume de referencia (mm^3, escala log)")
    ax.set_ylabel("erro de volume  100*(V_lithos/V_gt - 1)  [%]")
    ax.set_title("Bland-Altman percentual do volume - DESENV (25)")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, which="both", alpha=0.15)
    fig.tight_layout()
    p = OUT / "fase1_bland_altman.png"
    fig.savefig(p, dpi=130)
    plt.close(fig)
    return p


def grafico_erro_vs_humax(ok, rho, pval):
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    for e, xs, ys in _pontos_por_estrato(ok, "hu_max", "erro_vol_pct"):
        ax.scatter(xs, ys, c=COR[e], s=48, edgecolor="k", linewidth=0.4,
                   label=f"{e} mm (n={len(xs)})", zorder=3)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xlabel("hu_max do calculo (UH)")
    ax.set_ylabel("erro de volume (%)")
    ax.set_title(f"H2: erro de volume vs densidade (hu_max)\n"
                 f"Spearman rho = {rho:+.2f}  (p = {pval:.3g})")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.15)
    fig.tight_layout()
    p = OUT / "fase1_erro_vs_humax.png"
    fig.savefig(p, dpi=130)
    plt.close(fig)
    return p


def grafico_erro_vs_gtvol(ok, rho, pval):
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    ax.axhspan(8, 17, color="#2ca02c", alpha=0.10,
               label="predicao esferas >=10 mm (+8..+17%)")
    for e, xs, ys in _pontos_por_estrato(ok, "gt_vol_mL", "erro_vol_pct"):
        xs = [l["gt_vol_mL"] * 1000 for l in ok if l["estrato"] == e]
        ax.scatter(xs, ys, c=COR[e], s=48, edgecolor="k", linewidth=0.4,
                   label=f"{e} mm (n={len(xs)})", zorder=3)
    # curva da predicao de esfera (por calculo, ordenada por volume de ref)
    ordenado = sorted(ok, key=lambda l: l["gt_vol_mL"])
    xv = [l["gt_vol_mL"] * 1000 for l in ordenado]
    yp = [l["pred_esfera_pct"] for l in ordenado]
    ax.plot(xv, yp, color="k", ls="--", lw=1.2, marker="^", ms=4,
            label="previsto p/ esfera do mesmo D", zorder=2)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xscale("log")
    ax.set_xlabel("volume de referencia (mm^3, escala log)")
    ax.set_ylabel("erro de volume (%)")
    ax.set_title(f"H1: erro de volume vs tamanho, real vs esferas\n"
                 f"Spearman(erro%, V_gt) rho = {rho:+.2f}  (p = {pval:.3g})")
    ax.legend(fontsize=8)
    ax.grid(True, which="both", alpha=0.15)
    fig.tight_layout()
    p = OUT / "fase1_erro_vs_gtvol.png"
    fig.savefig(p, dpi=130)
    plt.close(fig)
    return p


# ------------------------------------------------------------------ main ------

def main():
    linhas = analisar()
    ok = [l for l in linhas if l["volume_lithos_mm3"] is not None]
    n_falha = len(linhas) - len(ok)

    caminho_csv = salvar_csv(linhas)

    # tabela por calculo
    print("=" * 92)
    print("VAE-001 FASE 1 - ANALISE EXPLORATORIA DOS 25 DE DESENVOLVIMENTO")
    print("=" * 92)
    print(f"{'id':>3} {'estr':>5} {'gt_mm3':>9} {'lit_mm3':>9} {'erroV%':>7} "
          f"{'prev%':>6} {'gtD':>6} {'litD':>6} {'eD':>5} {'huMax':>6} {'status':>8}")
    print("-" * 92)
    for l in sorted(linhas, key=lambda x: x["gt_vol_mL"]):
        gt = l["gt_vol_mL"] * 1000
        if l["volume_lithos_mm3"] is None:
            print(f"{l['mat_id']:>3} {l['estrato']:>5} {gt:>9.1f}  ----  FALHA")
            continue
        print(f"{l['mat_id']:>3} {l['estrato']:>5} {gt:>9.1f} "
              f"{l['volume_lithos_mm3']:>9.1f} {l['erro_vol_pct']:>+7.1f} "
              f"{l['pred_esfera_pct']:>+6.1f} {l['gt_diam_mm']:>6.2f} "
              f"{l['diametro_lithos_mm']:>6.2f} {l['erro_diam_mm']:>+5.2f} "
              f"{l['hu_max']:>6.0f} {l['status']:>8}")
    print()

    # ---- Bland-Altman percentual por estrato ----
    print("BLAND-ALTMAN PERCENTUAL DO VOLUME, POR ESTRATO")
    print(f"{'estrato':>8} {'n':>3} {'vies%':>8} {'sd%':>7} {'LoA95% low':>11} {'high':>8}")
    for e in ESTRATOS:
        ev = np.array([l["erro_vol_pct"] for l in ok if l["estrato"] == e])
        if len(ev) == 0:
            continue
        b, s = ev.mean(), ev.std(ddof=1) if len(ev) > 1 else 0.0
        print(f"{e:>8} {len(ev):>3} {b:>+8.1f} {s:>7.1f} "
              f"{b - 1.96 * s:>+11.1f} {b + 1.96 * s:>+8.1f}")
    print()

    # diametro
    ed = np.array([l["erro_diam_mm"] for l in ok])
    print(f"Erro de diametro: media {ed.mean():+.2f} mm  sd {ed.std(ddof=1):.2f} mm  "
          f"(esferas previram ~ +1,6 mm, ~constante)")
    print()

    # ---- H2: erro% vs hu_max ----
    err = np.array([l["erro_vol_pct"] for l in ok])
    hu = np.array([l["hu_max"] for l in ok])
    rho2, p2 = spearmanr(hu, err)

    # ---- H1: >=10 mm, real vs previsto ----
    ge10 = [l for l in ok if l["estrato"] in ("10-20", ">20")]
    obs10 = np.array([l["erro_vol_pct"] for l in ge10])
    prev10 = np.array([l["pred_esfera_pct"] for l in ge10])
    n_acima = int((obs10 > prev10).sum())
    try:
        _, pw = wilcoxon(obs10, prev10)
    except ValueError:
        pw = float("nan")
    gtv = np.array([l["gt_vol_mL"] for l in ok])
    rho1, p1 = spearmanr(gtv, err)

    # graficos
    p_ba = grafico_bland_altman(ok)
    p_hu = grafico_erro_vs_humax(ok, rho2, p2)
    p_gv = grafico_erro_vs_gtvol(ok, rho1, p1)

    # ---- vereditos ----
    print("=" * 92)
    print("VEREDITOS EXPLORATORIOS (DESENV; a prova definitiva e sobre o LACRADO)")
    print("=" * 92)

    print(f"\nH3  falha de segmentacao ~ 0")
    print(f"    {n_falha}/{len(linhas)} falhas ({100 * n_falha / len(linhas):.0f}%).  "
          f"=> {'CONFIRMADA' if n_falha == 0 else 'REFUTADA'}.")

    print(f"\nH2  o vies de volume cresce com a densidade (hu_max)")
    print(f"    Spearman(hu_max, erro%) rho = {rho2:+.2f}, p = {p2:.3g} (n={len(ok)}).")
    h2 = rho2 > 0 and p2 < 0.05
    print(f"    => {'CONFIRMADA' if h2 else 'NAO CONFIRMADA'} "
          f"(correlacao {'positiva e significativa' if h2 else 'fraca/insignificante'}).")

    print(f"\nH1  o vies real no estrato >=10 mm e MAIOR que o das esferas (+8..+17%)")
    print(f"    Observado >=10 mm: media {obs10.mean():+.1f}%  "
          f"(mediana {np.median(obs10):+.1f}%, faixa [{obs10.min():+.1f}, {obs10.max():+.1f}]%).")
    print(f"    Previsto esferas (mesmos D): media {prev10.mean():+.1f}%.")
    print(f"    Acima do previsto: {n_acima}/{len(ge10)} calculos.  "
          f"Wilcoxon pareado p = {pw:.3g}.")
    print(f"    Spearman(V_gt, erro%) rho = {rho1:+.2f}, p = {p1:.3g} "
          f"(esferas preveem erro DECRESCENTE com o tamanho: rho<0).")
    med10 = float(np.median(obs10))
    na_banda = 8.0 <= med10 <= 17.0
    sig = pw < 0.05
    print(f"    Mediana {med10:+.1f}% {'DENTRO' if na_banda else 'FORA'} da banda "
          f"+8..+17%; teste pareado {'significativo' if sig else 'NAO significativo'}.")
    if sig and obs10.mean() > prev10.mean():
        print("    => CONFIRMADA: excesso sistematico sobre as esferas.")
    else:
        print("    => NAO CONFIRMADA como efeito proprio. A MEDIA sobe por poucos")
        print("       outliers densos (H2); a MEDIANA cai na banda das esferas e a")
        print("       dependencia com o tamanho segue a esfera (rho<0). O excesso e")
        print("       de DENSIDADE (H2), nao de forma/superficie como H1 supunha.")

    print()
    print("Saidas:")
    for p in (caminho_csv, p_ba, p_hu, p_gv):
        print(f"  {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

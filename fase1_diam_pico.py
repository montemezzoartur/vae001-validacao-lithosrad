#!/usr/bin/env python3
"""
VAE-001 - FASE 1: LIMIAR FRACIONARIO PARA O DIAMETRO -- ROBUSTEZ DO PICO

PERGUNTA
--------
A varredura anterior (fase1_diam_limiares.py) mostrou que um limiar fracionario
T = f x pico e claramente melhor que os 200 UH fixos:

    metodo      vies    sd    pior   LoA95   rho(pico)   recl
    fix200     +0,04  0,46    1,05   +-0,90     +0,84    1/25
    f = 0,20   +0,08  0,33    0,76   +-0,65     +0,02    1/25

Ela elimina a dependencia de densidade (rho 0,84 -> 0,02), reduz o sd em 28%,
e faz o diametro de um objeto sub-voxel deixar de depender da densidade:

    d(1 voxel) = 2 (1 - f) x spacing      <-- o pico CANCELA

MAS: aquele teste usou o MAX de um unico voxel para estimar o pico. O max e
enviesado para cima pelo ruido -- um unico voxel quente desloca o limiar do
calculo inteiro. Se o desempenho depender disso, o metodo e fragil.

Este script repete a varredura com TRES estimadores de pico:
    max   -- o que foi usado antes
    p95   -- percentil 95 dos voxels da mascara (robusto)
    p99   -- percentil 99 (intermediario)

O QUE OLHAR
-----------
O sd em torno de f = 0,20 sobrevive ao trocar max por p95?
  SOBREVIVE  -> o metodo e robusto; implemente com p95.
  DEGRADA    -> o max estava fazendo trabalho que nao deveria; volte ao fix200.

CUIDADO: o p95 e MENOR que o max, entao T = f x p95 e mais baixo para o mesmo f.
O f otimo deve SUBIR. Olhe o PLATO inteiro, nao so a linha do 0,20.

NENHUM calculo LACRADO e tocado.

Requer: pip install scikit-image
Uso:    python fase1_diam_pico.py
"""
import io, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import ndimage as ndi
from scipy.spatial import ConvexHull
from scipy.spatial.distance import pdist
from scipy.stats import spearmanr
from skimage.measure import marching_cubes

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from freiburg_io import carregar_freiburg

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

MAT = ROOT / "data" / "raw" / "ct-uroliths_matlab.mat"
CONN = np.ones((3, 3, 3), bool)

ESTIMADORES = ["max", "p99", "p95"]
FRACOES = [0.10, 0.125, 0.15, 0.175, 0.20, 0.225, 0.25, 0.275, 0.30, 0.35, 0.40]


def maior_comp(m):
    rot, n = ndi.label(m, structure=CONN)
    if n == 0:
        return None
    t = np.bincount(rot.ravel()); t[0] = 0
    return rot == t.argmax()


def d_mc(hu, T, sp):
    """Diametro pela isosuperficie (marching cubes), no maior componente.
    NOTA: usa np.pad para garantir borda de zeros -- sem isso, um componente
    encostado no limite do volume nao fecha a isosuperficie e mede 0."""
    m = maior_comp(hu >= T)
    if m is None or m.sum() < 1:
        return np.nan
    idx = np.argwhere(m)
    lo = np.maximum(idx.min(0) - 2, 0)
    hi = np.minimum(idx.max(0) + 3, np.array(hu.shape))
    sl = tuple(slice(a, b) for a, b in zip(lo, hi))
    sub = np.where(m[sl], hu[sl], 0.0).astype(np.float32)
    sub = np.pad(sub, 1, mode="constant", constant_values=0.0)   # ACHADO #1
    try:
        v, _, _, _ = marching_cubes(sub, level=T, spacing=sp)
    except Exception:
        return np.nan
    if len(v) < 2:
        return np.nan
    if len(v) < 4:
        return float(pdist(v).max())
    return float(pdist(v[ConvexHull(v).vertices]).max())


def pico(hu, modo, T0=200.0):
    m = maior_comp(hu >= T0)
    if m is None:
        return np.nan
    v = hu[m]
    if modo == "max":
        return float(v.max())
    if modo == "p99":
        return float(np.percentile(v, 99))
    if modo == "p95":
        return float(np.percentile(v, 95))
    raise ValueError(modo)


def categoria(d):
    if np.isnan(d):  return "?"
    if d < 10:       return "<10"
    if d < 15:       return "10-15"
    if d < 20:       return "15-20"
    return ">20"


def main():
    linhas = []
    for c in carregar_freiburg(MAT, grupo="DESENV"):    # NUNCA 'LACRADO'
        hu = np.asarray(c["array"], np.float64)
        sp = c["spacing"]
        row = dict(id=c["id"], tipo=c["stone_type"], d_gt=c["gt_diam_mm"],
                   t_eq=c["gt_vol_mL"] * 1000 /
                        (np.pi * (c["gt_diam_mm"] / 2) ** 2))
        for e in ESTIMADORES:
            row[f"pico_{e}"] = pico(hu, e)
        # limiar fixo, de referencia
        row["fix200"] = d_mc(hu, 200.0, sp)
        # limiares fracionarios, por estimador
        for e in ESTIMADORES:
            p = row[f"pico_{e}"]
            for f in FRACOES:
                row[f"{e}_{f:.3f}"] = d_mc(hu, f * p, sp)
                row[f"T_{e}_{f:.3f}"] = f * p
        linhas.append(row)

    df = pd.DataFrame(linhas)
    df["cg"] = df["d_gt"].map(categoria)

    def resumo(col):
        er = (df[col] - df["d_gt"]).to_numpy()
        ok = ~np.isnan(er)
        if ok.sum() < 5:
            return None
        v, s = er[ok].mean(), er[ok].std(ddof=1)
        r1, _ = spearmanr(df.loc[ok, "pico_max"], er[ok])
        r2, _ = spearmanr(df.loc[ok, "t_eq"], er[ok])
        rec = int((df[col].map(categoria) != df["cg"]).sum())
        return dict(vies=v, sd=s, ae=np.abs(er[ok]).mean(),
                    pior=np.abs(er[ok]).max(), loa=1.96 * s,
                    rho_pico=r1, rho_forma=r2, recl=rec)

    # ---------------------------------------------------------------- 0 ----
    print("=" * 104)
    print("0. OS ESTIMADORES DE PICO")
    print("=" * 104)
    print(f"{'estimador':>10} {'mediana':>9} {'min':>7} {'max':>7} "
          f"{'razao vs max':>14}")
    print("-" * 104)
    for e in ESTIMADORES:
        r = df[f"pico_{e}"] / df["pico_max"]
        print(f"{e:>10} {df[f'pico_{e}'].median():>9.0f} "
              f"{df[f'pico_{e}'].min():>7.0f} {df[f'pico_{e}'].max():>7.0f} "
              f"{r.median():>13.3f}x")
    print()
    print("   O p95 e MENOR que o max. Logo T = f x p95 e mais baixo para o mesmo f,")
    print("   e o f otimo deve SUBIR. Compare os PLATOS, nao as linhas do mesmo f.")
    print()

    # ---------------------------------------------------------------- 1 ----
    ref = resumo("fix200")
    print("=" * 104)
    print("1. REFERENCIA: marching cubes a 200 UH FIXO  (o que ja esta implementado)")
    print("=" * 104)
    print(f"   vies {ref['vies']:+.2f}   sd {ref['sd']:.2f}   |e| {ref['ae']:.2f}   "
          f"pior {ref['pior']:.2f}   LoA +-{ref['loa']:.2f}")
    print(f"   rho(pico) {ref['rho_pico']:+.2f}   rho(forma) {ref['rho_forma']:+.2f}   "
          f"reclassificacao {ref['recl']}/25")
    print()

    # ---------------------------------------------------------------- 2 ----
    for e in ESTIMADORES:
        print("=" * 104)
        print(f"2.{ESTIMADORES.index(e)+1}  LIMIAR FRACIONARIO com pico = {e.upper()}")
        print("=" * 104)
        print(f"{'f':>7} {'T (UH)':>14} {'vies':>7} {'sd':>6} {'|e|':>6} {'pior':>6} "
              f"{'LoA':>7} {'rho(pico)':>10} {'rho(forma)':>11} {'recl':>6}")
        print("-" * 104)
        for f in FRACOES:
            col = f"{e}_{f:.3f}"
            r = resumo(col)
            if r is None:
                continue
            tc = f"T_{e}_{f:.3f}"
            marca = ""
            if abs(r["vies"]) <= 0.20 and abs(r["rho_pico"]) < 0.30 \
               and r["sd"] < ref["sd"] and r["recl"] <= ref["recl"]:
                marca = "  <<<"
            print(f"{f:>7.3f} {df[tc].min():>6.0f}-{df[tc].max():>6.0f} "
                  f"{r['vies']:>+7.2f} {r['sd']:>6.2f} {r['ae']:>6.2f} "
                  f"{r['pior']:>6.2f} {r['loa']:>7.2f} {r['rho_pico']:>+10.2f} "
                  f"{r['rho_forma']:>+11.2f} {r['recl']:>4}/25{marca}")
        print()

    print("=" * 104)
    print("3. LEITURA")
    print("=" * 104)
    print("   '<<<' marca os f que batem o fix200 em TODOS os criterios:")
    print("     |vies| <= 0,20 mm   E   |rho(pico)| < 0,30   E   sd menor   E")
    print("     reclassificacao nao pior.")
    print()
    print("   A PERGUNTA CENTRAL: o PLATO do p95 e tao bom quanto o do max?")
    print("     SIM  -> o metodo e robusto ao estimador de pico. Implemente com p95")
    print("             (o max e enviesado pelo ruido de um unico voxel).")
    print("     NAO  -> o max estava fazendo trabalho que nao deveria. O metodo e")
    print("             fragil, e o fix200 (ja implementado, 736 testes verdes)")
    print("             volta a ser a escolha segura.")
    print()
    print("   E LEMBRE: o limiar de DETECCAO continua 200 UH fixo. A fracao so")
    print("   localiza a BORDA de um calculo JA DETECTADO. Sao duas funcoes.")
    print()

    df.to_csv(ROOT / "results" / "fase1_diam_pico.csv", index=False)
    print("Salvo: results/fase1_diam_pico.csv")


if __name__ == "__main__":
    main()

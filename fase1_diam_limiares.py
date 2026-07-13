#!/usr/bin/env python3
"""
VAE-001 - FASE 1: VARREDURA DE LIMIAR PARA O DIAMETRO (marching cubes)

PROBLEMA
--------
O D_mc_200 (marching cubes a 200 UH fixo) tem vies +0,12 mm -- praticamente
zero -- mas o erro DEPENDE DA DENSIDADE: rho(huMax) = +0,80.

Mecanismo: a 200 UH fixo, o corte relativo varia de 9% do pico (brushita,
2146 UH) a 31% do pico (acido urico, 642 UH). Corte mais raso -> borda mais
para fora -> diametro maior.

Consequencia: o erro varia de -0,99 mm (acido urico) a +0,84 mm (brushita).
Um swing de 1,8 mm DEPENDENTE DA COMPOSICAO -- e isso importa perto das linhas
de conduta de 10, 15 e 20 mm.

A IDEIA
-------
Limiar FRACIONARIO: T = f x pico. O corte fica a uma fracao CONSTANTE do pico,
independentemente da composicao -> mata a dependencia de densidade por
construcao.

E f baixo evita o truncamento de ponta que estragou a meia-altura (f = 0,5):
o diametro maximo de um calculo real esta numa PONTA AFIADA, que e sub-voxel;
limiar alto corta a ponta. Foi por isso que o D_mc_half deu vies -0,91 mm e
TRIPLICOU a reclassificacao clinica (1/25 -> 3/25).

O QUE ESPERAR
-------------
Deve existir um f (chute: 0,15-0,25) com vies ~ 0 E rho ~ 0. Ele vai PARECER
melhor que o D_mc_200.

MAS: este experimento e para CARACTERIZAR, nao necessariamente para adotar.
  - a reclassificacao clinica ja esta no piso (1/25, e esse esta a 0,13 mm
    da fronteira -- irredutivel)
  - f seria um parametro AJUSTADO em 25 calculos: passivo num dossie
  - o estimador de pico e nao confiavel exatamente nos calculos finos

Poder escrever "testamos limiares de X a Y; o vies variou de A a B; adotamos
200 UH por [razao externa de deteccao]" e mais forte que so "adotamos 200 UH".

NENHUM calculo LACRADO e tocado.

Requer: pip install scikit-image
Uso:    python fase1_diam_limiares.py
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


def maior_comp(m):
    rot, n = ndi.label(m, structure=CONN)
    if n == 0:
        return None
    t = np.bincount(rot.ravel()); t[0] = 0
    return rot == t.argmax()


def d_mc(hu, T, sp):
    """Diametro pela isosuperficie (marching cubes), so no maior componente."""
    m = maior_comp(hu >= T)
    if m is None or m.sum() < 2:
        return np.nan
    idx = np.argwhere(m)
    lo = np.maximum(idx.min(0) - 2, 0)
    hi = np.minimum(idx.max(0) + 3, np.array(hu.shape))
    sl = tuple(slice(a, b) for a, b in zip(lo, hi))
    sub = np.where(m[sl], hu[sl], 0.0).astype(np.float32)
    try:
        v, _, _, _ = marching_cubes(sub, level=T, spacing=sp)
    except Exception:
        return np.nan
    if len(v) < 4:
        return float(pdist(v).max()) if len(v) > 1 else np.nan
    return float(pdist(v[ConvexHull(v).vertices]).max())


def pico(hu, T0=200.0):
    m = maior_comp(hu >= T0)
    return float(hu[m].max()) if m is not None else np.nan


def categoria(d):
    if np.isnan(d): return "?"
    if d < 10:  return "<10"
    if d < 15:  return "10-15"
    if d < 20:  return "15-20"
    return ">20"


FRACOES = [0.10, 0.125, 0.15, 0.175, 0.20, 0.225, 0.25, 0.30, 0.35, 0.40, 0.50]
FIXOS = [130.0, 200.0, 272.0, 350.0]


def main():
    linhas = []
    for c in carregar_freiburg(MAT, grupo="DESENV"):    # NUNCA 'LACRADO'
        hu = np.asarray(c["array"], np.float64)
        sp = c["spacing"]
        p = pico(hu)
        row = dict(id=c["id"], tipo=c["stone_type"], d_gt=c["gt_diam_mm"],
                   pico=p,
                   t_eq=c["gt_vol_mL"] * 1000 / (np.pi * (c["gt_diam_mm"] / 2) ** 2))
        for T in FIXOS:
            row[f"fix{int(T)}"] = d_mc(hu, T, sp)
        for f in FRACOES:
            row[f"f{f:.3f}"] = d_mc(hu, f * p, sp)
            row[f"T_f{f:.3f}"] = f * p
        linhas.append(row)

    df = pd.DataFrame(linhas)
    METODOS = [f"fix{int(T)}" for T in FIXOS] + [f"f{f:.3f}" for f in FRACOES]

    print("=" * 106)
    print("1. VARREDURA - DIAMETRO POR MARCHING CUBES")
    print("=" * 106)
    print(f"{'metodo':>10} {'T (UH)':>14} {'vies':>7} {'sd':>6} {'|erro|':>7} "
          f"{'pior':>6} {'LoA95':>16} {'rho(pico)':>10} {'rho(t_eq)':>10} {'recl':>5}")
    print("-" * 106)

    df["cat_gt"] = df["d_gt"].map(categoria)
    res = []
    for m in METODOS:
        er = (df[m] - df["d_gt"]).to_numpy()
        ok = ~np.isnan(er)
        if ok.sum() < 5:
            continue
        v, s = er[ok].mean(), er[ok].std(ddof=1)
        r1, _ = spearmanr(df.loc[ok, "pico"], er[ok])
        r2, _ = spearmanr(df.loc[ok, "t_eq"], er[ok])
        rec = int((df[m].map(categoria) != df["cat_gt"]).sum())
        if m.startswith("fix"):
            tdesc = f"{m[3:]} fixo"
        else:
            f = float(m[1:])
            tdesc = f"{f:.3f}x pico"
            tdesc += f" ({df[f'T_{m}'].min():.0f}-{df[f'T_{m}'].max():.0f})"
        print(f"{m:>10} {tdesc:>14} {v:>+7.2f} {s:>6.2f} "
              f"{np.abs(er[ok]).mean():>7.2f} {np.abs(er[ok]).max():>6.2f} "
              f"[{v-1.96*s:>+6.2f},{v+1.96*s:>+6.2f}] {r1:>+10.2f} {r2:>+10.2f} "
              f"{rec:>3}/25")
        res.append(dict(metodo=m, vies=v, sd=s, pior=np.abs(er[ok]).max(),
                        rho_pico=r1, recl=rec))
    print()
    print("   rho(pico): dependencia de DENSIDADE. O limiar fracionario deve zera-la.")
    print("   recl: reclassificacao clinica (<10 / 10-15 / 15-20 / >20 mm). E o que decide.")
    print()

    r = pd.DataFrame(res)
    print("=" * 106)
    print("2. LEITURA")
    print("=" * 106)
    base = r[r.metodo == "fix200"].iloc[0]
    print(f"   Referencia (200 UH fixo): vies {base.vies:+.2f}  sd {base.sd:.2f}  "
          f"rho(pico) {base.rho_pico:+.2f}  recl {int(base.recl)}/25")
    print()
    # candidatos que batem o 200 fixo em TODOS os criterios
    bons = r[(r.vies.abs() <= abs(base.vies) + 0.10) &
             (r.rho_pico.abs() < 0.40) &
             (r.recl <= base.recl)]
    if len(bons):
        print("   Metodos com vies comparavel, SEM dependencia de densidade, e sem")
        print("   piorar a reclassificacao:")
        print(bons.to_string(index=False, float_format=lambda x: f"{x:7.2f}"))
        print()
        print("   >>> Se algum aparece aqui, ele e tecnicamente superior ao 200 fixo.")
        print("       Mas o f e um parametro AJUSTADO nestes 25. Pese isso.")
    else:
        print("   NENHUM limiar fracionario bate o 200 UH fixo em todos os criterios.")
        print("   >>> O 200 UH fixo se sustenta. E ele tem justificativa EXTERNA")
        print("       (deteccao), o que um f ajustado nao teria.")
    print()

    df.to_csv(ROOT / "results" / "fase1_diam_limiares.csv", index=False)
    print("Salvo: results/fase1_diam_limiares.csv")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
VAE-001 - FASE 1: EXPERIMENTO DE LIMIAR NOS 25 DE DESENVOLVIMENTO  (v2)

CORRECAO v2 (ACHADO 5): o LithosRad NAO faz preenchimento de cavidades.
O codigo real (stone_detection.py) rotula componentes conexos e conta os
voxels -- sem binary_fill_holes. A v1 deste script incluia fill_holes e por
isso divergia em 2 dos 25 (ids 95 e 92, os grandes e compactos, que tem
cavidades internas abaixo de 200 UH).

Consequencias:
  - O protocolo v2.0, Secao 3.2, esta ERRADO ao declarar "preenchimento de
    cavidades: ativo". Corrigir na v2.1.
  - Fisicamente, cavidades internas SAO parte do calculo (o deslocamento de
    agua as inclui). Descarta-las subestima. Por isso o fill entra aqui como
    estrategia a ser avaliada, nao como premissa.

Achado que motivou este experimento: o erro do LithosRad a 200 UH e dominado
pela FORMA (rho(compacidade, erro) = -0,74; isolando os densos, -0,95), nao
pela densidade. Calculos laminares (t_eq < 1 mm, sub-voxel) sao superestimados
em ate +563%.  Fisica: erro ~ dr x (S/V).

NENHUM calculo LACRADO e tocado.

Uso:  python fase1_limiares.py
"""
import io, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import ndimage as ndi
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from freiburg_io import carregar_freiburg
from lithos.dicom_io import Volume
from lithos.kidney_segmentation import MascarasRins
from lithos.stone_detection import detectar_calculos

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

MAT = ROOT / "data" / "raw" / "ct-uroliths_matlab.mat"
CONN = np.ones((3, 3, 3), bool)


def maior_componente(mask):
    rot, n = ndi.label(mask, structure=CONN)
    if n == 0:
        return None
    tam = np.bincount(rot.ravel()); tam[0] = 0
    return rot == tam.argmax()


def segmentar(hu, T, fill=False):
    """Limiar -> maior componente conexo. fill=False reproduz o LithosRad."""
    m = maior_componente(hu >= T)
    if m is None:
        return None
    return ndi.binary_fill_holes(m) if fill else m


def vol_de(m, vv):
    return float(m.sum()) * vv if m is not None else np.nan


def hu_do_calculo(hu, mask, modo):
    v = hu[mask]
    if v.size == 0:
        return None
    if modo == "max":
        return float(v.max())
    if modo == "p95":
        return float(np.percentile(v, 95))
    if modo == "erodido":
        e = ndi.binary_erosion(mask, CONN)
        return float(np.median(hu[e])) if e.sum() >= 3 else float(np.percentile(v, 90))
    raise ValueError(modo)


def meia_altura(hu, modo_hu="p95", fill=False, n_iter=4):
    """Limiar adaptativo em (HU_calculo + HU_fundo)/2. Fundo = 0 (dado mascarado)."""
    T = 200.0
    for _ in range(n_iter):
        m = segmentar(hu, T, fill)
        if m is None:
            return None, T
        hs = hu_do_calculo(hu, m, modo_hu)
        if hs is None or hs < 250:
            return m, T
        Tn = hs / 2.0
        if abs(Tn - T) < 5:
            T = Tn
            break
        T = Tn
    return segmentar(hu, T, fill), T


def fracionario(hu, vv, modo_hu="p95", banda=2):
    """Nucleo peso 1 (>= meia-altura); casca peso f = HU/HU_calculo."""
    nuc, T = meia_altura(hu, modo_hu, fill=True)
    if nuc is None:
        return np.nan
    hs = hu_do_calculo(hu, nuc, modo_hu)
    if not hs or hs <= 0:
        return np.nan
    casca = ndi.binary_dilation(nuc, CONN, iterations=banda) & ~nuc
    f = np.zeros(hu.shape)
    f[nuc] = 1.0
    f[casca] = np.clip(hu[casca] / hs, 0.0, 1.0)
    return float(f.sum()) * vv


def main():
    linhas = []
    for c in carregar_freiburg(MAT, grupo="DESENV"):     # NUNCA 'LACRADO'
        hu = np.asarray(c["array"], np.float64)
        sp = c["spacing"]; vv = float(np.prod(sp))
        gt = c["gt_vol_mL"] * 1000.0; d = c["gt_diam_mm"]

        m_lit = MascarasRins(esquerdo=np.ones(hu.shape, bool), direito=None,
                             spacing=sp, aviso=None)
        r = detectar_calculos(Volume(array=c["array"], spacing=sp), m_lit)
        v_lithos = max((x.volume_mm3 for x in r.itens), default=np.nan)

        row = dict(id=c["id"], gt=gt, d=d, tipo=c["stone_type"],
                   compac=gt / (4 / 3 * np.pi * (d / 2) ** 3),
                   t_eq=gt / (np.pi * (d / 2) ** 2),
                   hu_max=float(hu.max()), v_lithos=v_lithos)

        # limiares fixos, SEM fill (como o LithosRad)
        for T in (130, 200, 272, 400):
            row[f"fixo{T}"] = vol_de(segmentar(hu, float(T), False), vv)
        # 200 UH COM fill -- isola o efeito das cavidades internas
        row["fixo200_fill"] = vol_de(segmentar(hu, 200.0, True), vv)
        # meia-altura adaptativa (com fill: cavidades sao parte do calculo)
        for modo in ("max", "p95", "erodido"):
            m, T = meia_altura(hu, modo, fill=True)
            row[f"meia_{modo}"] = vol_de(m, vv)
            row[f"T_{modo}"] = T
        row["frac"] = fracionario(hu, vv, "p95")
        linhas.append(row)

    df = pd.DataFrame(linhas).sort_values("compac")

    dif = (df["fixo200"] - df["v_lithos"]).abs().max()
    print("=" * 100)
    print("1. VALIDACAO DA REIMPLEMENTACAO (sem fill_holes, como o LithosRad)")
    print("=" * 100)
    print(f"   max |fixo200 - LithosRad| = {dif:.6f} mm3")
    if dif > 0.01:
        print("   *** AINDA DIVERGENTE. Pare e investigue. ***")
        print(df.loc[(df.fixo200 - df.v_lithos).abs() > 0.01,
                     ["id", "v_lithos", "fixo200"]].to_string(index=False))
        return
    print("   IDENTICOS nos 25. A reimplementacao reproduz o LithosRad.")
    print()

    metodos = ["fixo130", "fixo200", "fixo200_fill", "fixo272", "fixo400",
               "meia_max", "meia_p95", "meia_erodido", "frac"]
    for m in metodos:
        df[f"e_{m}"] = 100.0 * (df[m] / df["gt"] - 1.0)

    print("=" * 100)
    print("2. ERRO (%) POR CALCULO, DO MAIS LAMINAR AO MAIS COMPACTO")
    print("=" * 100)
    rot = {"fixo130": "f130", "fixo200": "f200", "fixo200_fill": "f200+H",
           "fixo272": "f272", "fixo400": "f400", "meia_max": "mMAX",
           "meia_p95": "mP95", "meia_erodido": "mERO", "frac": "FRAC"}
    hdr = (f"{'id':>3} {'d':>5} {'gt':>7} {'comp':>5} {'t_eq':>5} {'huMx':>5} " +
           " ".join(f"{rot[m]:>7}" for m in metodos))
    print(hdr); print("-" * len(hdr))
    for _, r in df.iterrows():
        print(f"{int(r['id']):>3} {r['d']:>5.1f} {r['gt']:>7.1f} {r['compac']:>5.2f} "
              f"{r['t_eq']:>5.2f} {r['hu_max']:>5.0f} " +
              " ".join(f"{r[f'e_{m}']:>+7.0f}" for m in metodos))
    print()

    print("=" * 100)
    print("3. RESUMO POR METODO")
    print("=" * 100)
    lam = df["t_eq"] < 2.0
    ge10 = df["d"] >= 10.0
    print(f"{'metodo':>13} {'vies%':>7} {'mediana':>8} {'|erro|':>7} {'pior':>7} "
          f"{'RHO(comp)':>10} {'p':>7} {'>=10mm':>8} {'laminar':>8}")
    print("-" * 100)
    for m in metodos:
        e = df[f"e_{m}"].to_numpy()
        rho, p = spearmanr(df["compac"], e)
        print(f"{m:>13} {np.nanmean(e):>+7.0f} {np.nanmedian(e):>+8.0f} "
              f"{np.nanmean(np.abs(e)):>7.0f} {np.nanmax(np.abs(e)):>7.0f} "
              f"{rho:>+10.2f} {p:>7.4f} "
              f"{np.nanmean(df.loc[ge10, f'e_{m}']):>+8.0f} "
              f"{np.nanmean(df.loc[lam, f'e_{m}']):>+8.0f}")
    print()
    print("  RHO(comp) e a METRICA QUE DECIDE. Um metodo bom tem rho ~ 0:")
    print("  o erro NAO depende da forma do calculo. O fixo200 tem rho ~ -0,74.")
    print(f"  laminar: t_eq < 2 mm (n={int(lam.sum())})   >=10 mm: n={int(ge10.sum())}")
    print()

    print("=" * 100)
    print("4. LIMIAR ESCOLHIDO PELA MEIA-ALTURA")
    print("=" * 100)
    for k in ("T_max", "T_p95", "T_erodido"):
        print(f"   {k:>10}: min {df[k].min():>5.0f}   mediana {df[k].median():>5.0f}"
              f"   max {df[k].max():>5.0f} UH")
    print()
    print("   Nos LAMINARES (t_eq < 2 mm), o pico observado ja esta reduzido pelo")
    print("   volume parcial -- nao ha voxel interior puro. A meia-altura do pico")
    print("   OBSERVADO e mais baixa que a verdadeira, e o metodo continua")
    print("   superestimando. Veja a coluna 'laminar' no bloco 3.")
    print()
    print(df.loc[lam, ["id", "t_eq", "hu_max", "T_p95",
                       "e_fixo200", "e_meia_p95", "e_frac"]].to_string(index=False))
    print()

    df.to_csv(ROOT / "results" / "fase1_limiares.csv", index=False)
    print("Salvo: results/fase1_limiares.csv")


if __name__ == "__main__":
    main()

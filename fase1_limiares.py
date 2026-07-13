#!/usr/bin/env python3
"""
VAE-001 - FASE 1: EXPERIMENTO DE LIMIAR NOS 25 DE DESENVOLVIMENTO

Motivacao (achado da analise exploratoria):
  O erro de volume do LithosRad a 200 UH e dominado pela FORMA, nao pela
  densidade. Spearman(compacidade, erro) = -0,74 (p<0,0001); isolando os
  densos, rho = -0,95. Calculos laminares (espessura equivalente < 1 mm,
  sub-voxel) sao superestimados em ate +563%.

  Fisica: erro ~ dr x (S/V). A forma varia ~20x na amostra; o dr (que a
  densidade modula) varia ~3x. A forma domina por uma ordem de grandeza.

Objetivo: comparar estrategias de segmentacao nos 25 de DESENVOLVIMENTO,
para decidir o ponto de operacao ANTES do congelamento. Isto e permitido e
e a razao de existir o conjunto de desenvolvimento (protocolo, Secao 5).

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
CONN = np.ones((3, 3, 3), bool)   # 26-conectividade, como o LithosRad


# ------------------------------------------------------------------ nucleo ----
def maior_componente(mask):
    rot, n = ndi.label(mask, structure=CONN)
    if n == 0:
        return None
    tam = np.bincount(rot.ravel())
    tam[0] = 0
    return rot == tam.argmax()


def segmentar(hu, T):
    """Limiar -> maior componente conexo -> preenche cavidades. Como o LithosRad."""
    m = maior_componente(hu >= T)
    if m is None:
        return None
    return ndi.binary_fill_holes(m)


def vol_de(mask, voxvol):
    return float(mask.sum()) * voxvol


# ------------------------------------------------------------- estrategias ----
def hu_do_calculo(hu, mask, modo):
    """Estima a densidade interna do calculo. O calcanhar de Aquiles em
    objetos sub-voxel: nao ha voxel interior 'puro'."""
    v = hu[mask]
    if v.size == 0:
        return None
    if modo == "max":
        return float(v.max())
    if modo == "p95":
        return float(np.percentile(v, 95))
    if modo == "mediana":
        return float(np.median(v))
    if modo == "erodido":
        e = ndi.binary_erosion(mask, CONN)
        return float(np.median(hu[e])) if e.sum() >= 3 else float(np.percentile(v, 90))
    raise ValueError(modo)


def meia_altura(hu, voxvol, modo_hu="p95", n_iter=3):
    """Limiar adaptativo em (HU_calculo + HU_fundo)/2. Fundo ~ 0 (dado mascarado).
    Itera: segmenta grosseiro -> estima HU -> re-segmenta."""
    T = 200.0
    for _ in range(n_iter):
        m = segmentar(hu, T)
        if m is None:
            return None, T
        hs = hu_do_calculo(hu, m, modo_hu)
        if hs is None or hs < 250:
            return m, T
        T_novo = hs / 2.0
        if abs(T_novo - T) < 5:
            T = T_novo
            break
        T = T_novo
    m = segmentar(hu, T)
    return m, T


def fracionario_casca(hu, voxvol, modo_hu="p95", banda=2):
    """Nucleo com peso 1 (>= meia-altura); casca com peso fracionario
    f = HU / HU_calculo. Fundo = 0 (dado ja mascarado pelos autores)."""
    nucleo, T = meia_altura(hu, voxvol, modo_hu)
    if nucleo is None:
        return None
    hs = hu_do_calculo(hu, nucleo, modo_hu)
    if hs is None or hs <= 0:
        return None
    casca = ndi.binary_dilation(nucleo, CONN, iterations=banda) & ~nucleo
    f = np.zeros(hu.shape, np.float64)
    f[nucleo] = 1.0
    f[casca] = np.clip(hu[casca] / hs, 0.0, 1.0)
    return float(f.sum()) * voxvol


# ------------------------------------------------------------------- main -----
def main():
    linhas = []
    for c in carregar_freiburg(MAT, grupo="DESENV"):     # NUNCA 'LACRADO'
        hu = np.asarray(c["array"], np.float64)
        sp = c["spacing"]
        voxvol = float(np.prod(sp))
        gt = c["gt_vol_mL"] * 1000.0
        d = c["gt_diam_mm"]

        # --- referencia: o proprio LithosRad, para validar a reimplementacao ---
        m_lit = MascarasRins(esquerdo=np.ones(hu.shape, bool), direito=None,
                             spacing=sp, aviso=None)
        r = detectar_calculos(Volume(array=c["array"], spacing=sp), m_lit)
        v_lithos = max((x.volume_mm3 for x in r.itens), default=np.nan)

        row = dict(
            id=c["id"], gt=gt, d=d, tipo=c["stone_type"],
            compac=gt / (4 / 3 * np.pi * (d / 2) ** 3),
            t_eq=gt / (np.pi * (d / 2) ** 2),
            hu_max=float(hu.max()),
            v_lithos=v_lithos,
        )
        # --- limiares fixos ---
        for T in (130, 200, 272, 400):
            m = segmentar(hu, float(T))
            row[f"fixo{T}"] = vol_de(m, voxvol) if m is not None else np.nan
        # --- meia-altura adaptativa, 3 estimadores de HU ---
        for modo in ("max", "p95", "erodido"):
            m, T = meia_altura(hu, voxvol, modo)
            row[f"meia_{modo}"] = vol_de(m, voxvol) if m is not None else np.nan
            row[f"T_{modo}"] = T
        # --- fracionario na casca ---
        row["frac"] = fracionario_casca(hu, voxvol, "p95") or np.nan
        linhas.append(row)

    df = pd.DataFrame(linhas).sort_values("compac")

    # ---- 1. a reimplementacao e fiel? ----
    dif = (df["fixo200"] - df["v_lithos"]).abs().max()
    print("=" * 96)
    print("1. VALIDACAO DA REIMPLEMENTACAO")
    print("=" * 96)
    print(f"   max |fixo200(meu) - LithosRad| = {dif:.4f} mm3")
    if dif > 0.01:
        print("   *** DIVERGENTE. Nao confie no resto ate entender por que. ***")
        print(df[["id", "v_lithos", "fixo200"]].to_string(index=False))
        return
    print("   IDENTICOS. A reimplementacao reproduz o LithosRad a 200 UH.")
    print()

    metodos = ["fixo130", "fixo200", "fixo272", "fixo400",
               "meia_max", "meia_p95", "meia_erodido", "frac"]
    for m in metodos:
        df[f"e_{m}"] = 100.0 * (df[m] / df["gt"] - 1.0)

    # ---- 2. tabela por calculo, ordenada por compacidade ----
    print("=" * 96)
    print("2. ERRO (%) POR CALCULO, ORDENADO POR COMPACIDADE (mais laminar primeiro)")
    print("=" * 96)
    cols = ["id", "d", "gt", "compac", "t_eq", "hu_max"] + [f"e_{m}" for m in metodos]
    hdr = (f"{'id':>3} {'d':>5} {'gt':>7} {'comp':>5} {'t_eq':>5} {'huMx':>5} " +
           " ".join(f"{m.replace('e_','').replace('meia_','m.')[:6]:>7}" for m in
                    [f"e_{x}" for x in metodos]))
    print(hdr)
    print("-" * len(hdr))
    for _, r in df.iterrows():
        s = (f"{int(r['id']):>3} {r['d']:>5.1f} {r['gt']:>7.1f} {r['compac']:>5.2f} "
             f"{r['t_eq']:>5.2f} {r['hu_max']:>5.0f} ")
        s += " ".join(f"{r[f'e_{m}']:>+7.0f}" for m in metodos)
        print(s)
    print()

    # ---- 3. resumo ----
    print("=" * 96)
    print("3. RESUMO POR METODO")
    print("=" * 96)
    lam = df["t_eq"] < 2.0          # laminares (sub-voxel a ~3 voxels)
    ge10 = df["d"] >= 10.0          # estrato primario
    print(f"{'metodo':>14} {'vies%':>8} {'mediana%':>9} {'|erro| med':>11} "
          f"{'pior':>8} {'rho(comp)':>10} {'>=10mm vies':>12} {'laminares vies':>15}")
    print("-" * 96)
    for m in metodos:
        e = df[f"e_{m}"].to_numpy()
        rho, _ = spearmanr(df["compac"], e)
        print(f"{m:>14} {np.nanmean(e):>+8.0f} {np.nanmedian(e):>+9.0f} "
              f"{np.nanmean(np.abs(e)):>11.0f} {np.nanmax(np.abs(e)):>8.0f} "
              f"{rho:>+10.2f} {np.nanmean(df.loc[ge10, f'e_{m}']):>+12.0f} "
              f"{np.nanmean(df.loc[lam, f'e_{m}']):>+15.0f}")
    print()
    print("  rho(comp): correlacao do erro com a COMPACIDADE. Um metodo bom tem")
    print("             rho ~ 0 -- ou seja, o erro NAO depende da forma do calculo.")
    print(f"  laminares: t_eq < 2 mm  (n={int(lam.sum())})")
    print(f"  >=10 mm:   estrato primario  (n={int(ge10.sum())})")
    print()

    # ---- 4. limiares que a meia-altura escolheu ----
    print("=" * 96)
    print("4. LIMIAR ESCOLHIDO PELA MEIA-ALTURA (vs. os 200 UH fixos)")
    print("=" * 96)
    print(f"   T_p95:     min {df['T_p95'].min():.0f}   mediana {df['T_p95'].median():.0f}"
          f"   max {df['T_p95'].max():.0f} UH")
    print(f"   T_erodido: min {df['T_erodido'].min():.0f}   mediana {df['T_erodido'].median():.0f}"
          f"   max {df['T_erodido'].max():.0f} UH")
    print()
    print("   Se o limiar adaptativo escolher valores MUITO acima de 200 UH nos")
    print("   calculos densos, e exatamente isso que corrige o vies de forma:")
    print("   um dr menor multiplica um S/V grande e produz erro menor.")
    print()

    df.to_csv(ROOT / "results" / "fase1_limiares.csv", index=False)
    print("Salvo: results/fase1_limiares.csv")


if __name__ == "__main__":
    main()

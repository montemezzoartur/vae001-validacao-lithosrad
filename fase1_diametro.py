#!/usr/bin/env python3
"""
VAE-001 - FASE 1: PRECISAO DO DIAMETRO NOS 25 DE DESENVOLVIMENTO

POR QUE O DIAMETRO E UM ALVO MELHOR QUE O VOLUME
-------------------------------------------------
O erro de VOLUME e um efeito de CASCA: escala com S/V. Varia de -36% a +563%
nos 25, e nenhum limiar conserta a dependencia de forma (rho ~ -0,7 em todos).

O erro de DIAMETRO e um efeito de EXTENSAO MAXIMA: dominado pelo eixo longo do
calculo, que esta bem resolvido MESMO numa lasca. Nos 25, fica em +0,83 +- 0,45
mm, praticamente INDEPENDENTE da forma.

Mas depende da DENSIDADE, e por um motivo exato: com limiar fixo de 200 UH, um
calculo de 650 UH e cortado a 31% do pico (perto da meia-altura, borda quase
certa); um de 2100 UH e cortado a 9,5% do pico (na cauda da PSF, borda empurrada
para fora). Logo, um limiar ADAPTATIVO deveria zerar o vies.

O QUE DECIDE, CLINICAMENTE
--------------------------
As diretrizes decidem conduta em 10, 15 e 20 mm. O que importa nao e o vies em
milimetros -- e QUANTOS CALCULOS CRUZAM A LINHA ERRADA.

NENHUM calculo LACRADO e tocado.

Requer: pip install scikit-image
Uso:    python fase1_diametro.py
"""
import io, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import ndimage as ndi
from scipy.spatial import ConvexHull
from scipy.spatial.distance import pdist
from scipy.stats import spearmanr

try:
    from skimage.measure import marching_cubes
except ImportError:
    print("Falta scikit-image.  pip install scikit-image")
    sys.exit(1)

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
LIMIARES_CLINICOS = [10.0, 15.0, 20.0]


def maior_comp(m):
    rot, n = ndi.label(m, structure=CONN)
    if n == 0:
        return None
    t = np.bincount(rot.ravel()); t[0] = 0
    return rot == t.argmax()


def d_max_pontos(pts):
    """Maior distancia entre pares. ConvexHull primeiro (como o LithosRad)."""
    if len(pts) < 4:
        return float(pdist(pts).max()) if len(pts) > 1 else 0.0
    try:
        h = ConvexHull(pts)
        return float(pdist(pts[h.vertices]).max())
    except Exception:
        return float(pdist(pts).max())


def d_voxel(mask, sp):
    """Diametro por centros de voxel. E o que o LithosRad faz."""
    c = np.argwhere(mask).astype(float) * np.asarray(sp)
    return d_max_pontos(c)


def d_mc(hu, T, sp):
    """Diametro por isosuperficie (marching cubes) -- resolucao SUB-VOXEL."""
    try:
        v, _, _, _ = marching_cubes(hu, level=T, spacing=sp)
    except Exception:
        return np.nan
    if len(v) < 2:
        return np.nan
    # so o maior componente: filtra vertices longe do centroide do maior blob
    m = maior_comp(hu >= T)
    if m is None:
        return np.nan
    cen = np.array(ndi.center_of_mass(m)) * np.asarray(sp)
    r = np.linalg.norm(v - cen, axis=1)
    v = v[r <= np.percentile(r, 99.5) * 1.5]
    return d_max_pontos(v)


def pico(hu, mask, modo="p95"):
    v = hu[mask]
    return float(v.max()) if modo == "max" else float(np.percentile(v, 95))


def meia_altura_T(hu, modo="p95", n_iter=4):
    """Limiar adaptativo em HU_calculo/2 (fundo = 0, dado mascarado)."""
    T = 200.0
    for _ in range(n_iter):
        m = maior_comp(hu >= T)
        if m is None:
            return T
        hs = pico(hu, m, modo)
        if hs < 250:
            return T
        Tn = hs / 2.0
        if abs(Tn - T) < 5:
            return Tn
        T = Tn
    return T


def categoria(d):
    if d < 10:  return "<10"
    if d < 15:  return "10-15"
    if d < 20:  return "15-20"
    return ">20"


def main():
    linhas = []
    for c in carregar_freiburg(MAT, grupo="DESENV"):     # NUNCA 'LACRADO'
        hu = np.asarray(c["array"], np.float64)
        sp = c["spacing"]
        d_gt = c["gt_diam_mm"]
        gt = c["gt_vol_mL"] * 1000.0

        # o LithosRad, como esta
        r = detectar_calculos(Volume(array=c["array"], spacing=sp),
                              MascarasRins(esquerdo=np.ones(hu.shape, bool),
                                           direito=None, spacing=sp, aviso=None))
        it = max(r.itens, key=lambda x: x.volume_mm3)

        m200 = maior_comp(hu >= 200.0)
        T_half = meia_altura_T(hu, "p95")
        mhalf = maior_comp(hu >= T_half)

        linhas.append(dict(
            id=c["id"], d_gt=d_gt, gt=gt, tipo=c["stone_type"],
            hu_max=float(hu.max()), T_half=T_half,
            t_eq=gt / (np.pi * (d_gt / 2) ** 2),
            # --- estimadores ---
            D_lithos=it.diametro_mm,                       # o produto, hoje
            D_vox_200=d_voxel(m200, sp),                   # confere o LithosRad
            D_mc_200=d_mc(hu, 200.0, sp),                  # sub-voxel, limiar fixo
            D_vox_half=d_voxel(mhalf, sp) if mhalf is not None else np.nan,
            D_mc_half=d_mc(hu, T_half, sp),                # sub-voxel + adaptativo
        ))

    df = pd.DataFrame(linhas)
    EST = ["D_lithos", "D_vox_200", "D_mc_200", "D_vox_half", "D_mc_half"]
    for e in EST:
        df[f"e_{e}"] = df[e] - df["d_gt"]

    # calibrado: o LithosRad menos o vies medio (ajustado NESTES 25)
    b = df["e_D_lithos"].mean()
    df["D_calib"] = df["D_lithos"] - b
    df["e_D_calib"] = df["D_calib"] - df["d_gt"]
    EST_ALL = EST + ["D_calib"]

    # ---------------------------------------------------------------- 1 ----
    print("=" * 100)
    print("1. CONFERENCIA: o D_vox_200 reproduz o LithosRad?")
    print("=" * 100)
    dd = (df["D_vox_200"] - df["D_lithos"]).abs().max()
    print(f"   max |D_vox_200 - D_lithos| = {dd:.4f} mm  "
          f"({'OK' if dd < 0.01 else 'DIVERGENTE - investigar'})")
    print()

    # ---------------------------------------------------------------- 2 ----
    print("=" * 100)
    print("2. DESEMPENHO DE CADA ESTIMADOR (erro em mm)")
    print("=" * 100)
    print(f"{'estimador':>12} {'vies':>7} {'sd':>6} {'|erro|':>7} {'pior':>6} "
          f"{'LoA95 low':>10} {'high':>7} | {'rho vs huMax':>13} {'rho vs t_eq':>12}")
    print("-" * 100)
    for e in EST_ALL:
        er = df[f"e_{e}"].to_numpy()
        v, s = np.nanmean(er), np.nanstd(er, ddof=1)
        r1, _ = spearmanr(df["hu_max"], er)
        r2, _ = spearmanr(df["t_eq"], er)
        print(f"{e:>12} {v:>+7.2f} {s:>6.2f} {np.nanmean(np.abs(er)):>7.2f} "
              f"{np.nanmax(np.abs(er)):>6.2f} {v-1.96*s:>+10.2f} {v+1.96*s:>+7.2f} | "
              f"{r1:>+13.2f} {r2:>+12.2f}")
    print()
    print("   rho vs huMax: se o limiar adaptativo funcionar, ele deve CAIR para ~0.")
    print("   (O limiar fixo erra mais nos densos: corte a 9% do pico vs 31%.)")
    print("   rho vs t_eq: o erro de diametro NAO deveria depender da forma.")
    print()

    # ---------------------------------------------------------------- 3 ----
    print("=" * 100)
    print("3. O QUE DECIDE: RECLASSIFICACAO CLINICA  (<10 / 10-15 / 15-20 / >20 mm)")
    print("=" * 100)
    df["cat_gt"] = df["d_gt"].map(categoria)
    print(f"{'estimador':>12} {'n reclassificados':>18} {'%':>6} | {'ids (real -> reportado)'}")
    print("-" * 100)
    for e in EST_ALL:
        df[f"cat_{e}"] = df[e].map(lambda x: categoria(x) if pd.notna(x) else "?")
        erro = df[df[f"cat_{e}"] != df["cat_gt"]]
        det = ", ".join(f"{int(r.id)}:{r.d_gt:.1f}->{r[e]:.1f}" for _, r in erro.iterrows())
        print(f"{e:>12} {len(erro):>18} {100*len(erro)/len(df):>5.0f}% | {det}")
    print()
    print("   Um cálculo reclassificado é uma conduta potencialmente errada,")
    print("   induzida pelo laudo. É a métrica que importa.")
    print()

    # ---------------------------------------------------------------- 4 ----
    print("=" * 100)
    print("4. TABELA POR CALCULO")
    print("=" * 100)
    cols = ["id", "d_gt", "hu_max", "T_half", "t_eq"] + EST_ALL
    print(df[cols].sort_values("hu_max").to_string(
        index=False, float_format=lambda x: f"{x:7.2f}"))
    print()

    # ---------------------------------------------------------------- 5 ----
    print("=" * 100)
    print("5. LIMIAR ADAPTATIVO ESCOLHIDO")
    print("=" * 100)
    print(f"   T_half: min {df.T_half.min():.0f}   mediana {df.T_half.median():.0f}"
          f"   max {df.T_half.max():.0f} UH")
    print()
    print("   ATENCAO: um limiar de segmentacao adaptativo NAO altera o limiar de")
    print("   DETECCAO (200 UH), que continua fixo. Sao duas funcoes distintas.")
    print("   Este experimento so mexe em COMO a borda e localizada, depois que o")
    print("   calculo ja foi detectado.")
    print()
    print("   E o corte adaptativo aqui foi ajustado nos 25 de DESENVOLVIMENTO.")
    print("   Sua validacao e sobre os 76 LACRADOS, apos o congelamento.")
    print()

    df.to_csv(ROOT / "results" / "fase1_diametro.csv", index=False)
    print("Salvo: results/fase1_diametro.csv")


if __name__ == "__main__":
    main()

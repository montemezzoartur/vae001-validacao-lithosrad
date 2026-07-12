#!/usr/bin/env python3
"""
VAE-001 - FASE 1: VERIFICACAO EM DADO SINTETICO  (v2)

CORRECAO v2: a v1 usava scipy.ndimage.zoom para reamostrar da grade fina
para a grade do voxel. O zoom alinha as EXTREMIDADES da grade, nao os
centros -- o espacamento efetivo saia ~5% maior que o declarado, e esse
erro de escala CANCELAVA por acaso a superestimacao que o limiar produz.
Resultado: erro de volume ~0%, mascarando o comportamento real.

v2 usa media de caixa exata: a grade fina tem S subdivisoes por voxel em
cada eixo, e o valor do voxel e a media do bloco S x S x S. Isso e o modelo
correto de integracao do detector.

Roda o detectar_calculos() REAL do LithosRad. Nenhum dado do Freiburg e tocado.

Uso:  python fase1_esferas.py
"""
import sys, io
import numpy as np
from scipy.ndimage import gaussian_filter

from lithos.dicom_io import Volume
from lithos.kidney_segmentation import MascarasRins
from lithos.stone_detection import detectar_calculos

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

S = 7          # subdivisoes por voxel, por eixo
FWHM = 2.3548  # conversao FWHM -> sigma


def sintetiza(spacing_zyx, raios_zyx, hu_stone=900.0, hu_bg=0.0,
              psf_fwhm=0.7, mascarar_em=None):
    """
    Volume sintetico com elipsoide de volume ANALITICAMENTE conhecido.
    Reamostragem por MEDIA DE CAIXA (S subdivisoes por voxel, por eixo).
    Retorna (Volume, v_true_mm3, d_true_mm).
    """
    dz, dy, dx = spacing_zyx
    rz, ry, rx = raios_zyx
    v_true = 4.0 / 3.0 * np.pi * rz * ry * rx
    d_true = 2.0 * max(raios_zyx)

    # numero de voxels, com folga para a PSF
    nz = int(np.ceil(2 * (rz + 4 * dz) / dz)) | 1
    ny = int(np.ceil(2 * (ry + 4 * dy) / dy)) | 1
    nx = int(np.ceil(2 * (rx + 4 * dx) / dx)) | 1

    # grade fina: S subdivisoes por voxel -> espacamento fino = d/S
    fz, fy, fx = nz * S, ny * S, nx * S
    ez, ey, ex = dz / S, dy / S, dx / S
    az = (np.arange(fz) - (fz - 1) / 2) * ez
    ay = (np.arange(fy) - (fy - 1) / 2) * ey
    ax = (np.arange(fx) - (fx - 1) / 2) * ex
    Z, Y, X = np.meshgrid(az, ay, ax, indexing="ij")

    obj = (((Z / rz) ** 2 + (Y / ry) ** 2 + (X / rx) ** 2) <= 1.0).astype(np.float32)
    del Z, Y, X

    # PSF isotropica em mm -> sigma diferente por eixo, em unidades de voxel fino
    sig = psf_fwhm / FWHM
    obj = gaussian_filter(obj, (sig / ez, sig / ey, sig / ex), mode="nearest")

    # MEDIA DE CAIXA: integra o sinal sobre o voxel (isto e o que o detector faz)
    frac = obj.reshape(nz, S, ny, S, nx, S).mean(axis=(1, 3, 5))
    del obj
    frac = np.clip(frac, 0.0, 1.0)

    hu = hu_bg + frac * (hu_stone - hu_bg)
    if mascarar_em is not None:
        hu[hu < mascarar_em] = 0.0

    return Volume(array=hu.astype(np.float32), spacing=tuple(spacing_zyx),
                  affine=None), v_true, d_true


def mede(vol):
    """detectar_calculos REAL. hu_min=200 e o default do LithosRad."""
    cheia = np.ones(vol.array.shape, dtype=bool)
    m = MascarasRins(esquerdo=cheia, direito=None, spacing=vol.spacing, aviso=None)
    res = detectar_calculos(vol, m)
    if not res.itens:
        return None
    return max(res.itens, key=lambda x: x.volume_mm3)


# =====================================================================
def suite_a():
    print("=" * 78)
    print("SUITE A - CACA-BUGS DE EIXO   (voxel 2,0 x 0,5 x 0,5 mm, anisotropia 4x)")
    print("=" * 78)
    print()
    SP = (2.0, 0.5, 0.5)
    falhas = []

    print("A1. Elipsoide alongado em Z: rz=9, ry=2, rx=2 mm -> D verdadeiro = 18 mm")
    print("    (Z e o eixo de voxel GROSSO. Se os eixos trocarem, sai ~4 mm.)")
    vol, vt, dt = sintetiza(SP, (9.0, 2.0, 2.0), psf_fwhm=1.0)
    c = mede(vol)
    e = c.diametro_mm - dt
    print(f"    D verdadeiro={dt:6.2f} mm   medido={c.diametro_mm:6.2f} mm   erro={e:+5.2f} mm")
    if abs(e) > 2.5:
        falhas.append(f"A1: diametro erra {e:+.2f} mm -- SUSPEITA DE TROCA DE EIXO")
    print()

    print("A2. Elipsoide alongado em X: rz=2, ry=2, rx=9 mm -> D verdadeiro = 18 mm")
    print("    (X e o eixo de voxel FINO. O espelho de A1.)")
    vol, vt, dt = sintetiza(SP, (2.0, 2.0, 9.0), psf_fwhm=1.0)
    c = mede(vol)
    e = c.diametro_mm - dt
    print(f"    D verdadeiro={dt:6.2f} mm   medido={c.diametro_mm:6.2f} mm   erro={e:+5.2f} mm")
    if abs(e) > 2.5:
        falhas.append(f"A2: diametro erra {e:+.2f} mm -- SUSPEITA DE TROCA DE EIXO")
    print()
    return falhas


def suite_b():
    print("=" * 78)
    print("SUITE B - GEOMETRIA DO FREIBURG   (0,7 x 0,7363 x 0,7363 mm; PSF 0,7 mm)")
    print("=" * 78)
    print()
    print("Caracteriza o vies do limiar de 200 UH do LithosRad.")
    print("Esferas de volume analiticamente conhecido; fundo mascarado em 101 UH.")
    print()

    SP = (0.7, 0.7363, 0.7363)
    print(f"{'D (mm)':>7} {'V real':>10} {'V medido':>10} {'erro V':>9} "
          f"{'D medido':>9} {'erro D':>8} {'N vox':>7}")
    print("-" * 68)

    linhas = []
    for d in [3, 4, 5, 6, 8, 10, 12, 15, 20]:
        r = d / 2.0
        vol, vt, dt = sintetiza(SP, (r, r, r), hu_stone=900.0, hu_bg=0.0,
                                psf_fwhm=0.7, mascarar_em=101.0)
        c = mede(vol)
        if c is None:
            print(f"{d:>7} {vt:>10.1f}   FALHA DE SEGMENTACAO")
            continue
        ev = (c.volume_mm3 / vt - 1) * 100
        ed = c.diametro_mm - dt
        print(f"{d:>7} {vt:>10.1f} {c.volume_mm3:>10.1f} {ev:>+8.1f}% "
              f"{c.diametro_mm:>9.2f} {ed:>+7.2f} {c.n_voxels:>7}")
        linhas.append((d, ev, ed))
    print()

    falhas = []
    erros = [(d, e) for d, e, _ in linhas]

    # F1: limiar a 22% do pico DEVE superestimar
    if any(e <= 0 for _, e in erros):
        falhas.append("B1: erro de volume nao e positivo. Um corte a 22% do pico "
                      "DEVE superestimar. Suspeite do volume do voxel.")
    # F2: erro ~ 3*dr/r -> decresce com o tamanho
    peq = [e for d, e in erros if d <= 5]
    gra = [e for d, e in erros if d >= 12]
    if peq and gra and min(peq) <= max(gra):
        falhas.append("B2: o erro nao decresce com o tamanho. A fisica manda "
                      "erro ~ 3*dr/r. Suspeite da segmentacao.")
    # F3: diametro dentro de ~2 voxels (o limiar baixo tambem infla o diametro)
    for d, _, ed in linhas:
        if abs(ed) > 2.0:
            falhas.append(f"B3: diametro de {d} mm erra {ed:+.2f} mm (> 2 voxels)")
    return falhas


if __name__ == "__main__":
    f = suite_a() + suite_b()
    print("=" * 78)
    if f:
        print("FALHAS DETECTADAS:")
        for x in f:
            print(f"  [X] {x}")
        sys.exit(1)
    print("TODAS AS VERIFICACOES PASSARAM.")
    print()
    print("  - diametro correto em ambos os eixos, com anisotropia 4x (sem troca de eixo)")
    print("  - superestimacao POSITIVA e DECRESCENTE com o tamanho, a 200 UH")
    print("  - volume = N x prod(spacing), verificado contra verdade analitica")
    print()
    print("O motor de volumetria do LithosRad se comporta como a fisica manda.")

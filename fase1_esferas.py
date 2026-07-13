#!/usr/bin/env python3
"""
VAE-001 - FASE 1: VERIFICACAO EM DADO SINTETICO

Roda o detectar_calculos() REAL do LithosRad contra esferas de volume
analiticamente conhecido. Nenhum dado do Freiburg e tocado.

Isto NAO e ajuste de parametro. E verificacao de implementacao contra
verdade matematica - permitido e exigido pelo protocolo (Secao 12).

Duas suites:
  A. CACA-BUGS  - anisotropia exagerada (2,0 x 0,5 x 0,5 mm). Um erro de
                  ordem de eixos produz erro de 4x no diametro: grita.
  B. FREIBURG   - geometria real (0,7 x 0,7363 x 0,7363 mm, PSF 0,7 mm).
                  Caracteriza o vies do limiar de 200 UH.

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

FINE = 0.05   # grade fina (mm) para construir o objeto antes de amostrar


def sintetiza(diam_mm, spacing_zyx, hu_stone=900.0, hu_bg=0.0,
              psf_fwhm=0.7, mascarar_em=None, elipsoide=None):
    """
    Constroi um volume sintetico com um objeto de volume ANALITICAMENTE conhecido.

    spacing_zyx : (dz, dy, dx) em mm  -- mesma convencao do Volume do LithosRad
    elipsoide   : (rz, ry, rx) em mm; se dado, ignora diam_mm
    mascarar_em : se dado, zera tudo abaixo desse HU (imita o dataset de Freiburg)

    Retorna (Volume, volume_verdadeiro_mm3, diametro_verdadeiro_mm)
    """
    dz, dy, dx = spacing_zyx
    if elipsoide is None:
        r = diam_mm / 2.0
        rz = ry = rx = r
        v_true = 4.0 / 3.0 * np.pi * r ** 3
        d_true = diam_mm
    else:
        rz, ry, rx = elipsoide
        v_true = 4.0 / 3.0 * np.pi * rz * ry * rx
        d_true = 2.0 * max(rz, ry, rx)

    # extensao em mm com folga para a PSF
    ext = (rz + 4 * dz, ry + 4 * dy, rx + 4 * dx)
    nz = int(np.ceil(2 * ext[0] / dz)) | 1
    ny = int(np.ceil(2 * ext[1] / dy)) | 1
    nx = int(np.ceil(2 * ext[2] / dx)) | 1

    # grade fina, ISOTROPICA em mm
    fz = int(np.ceil(nz * dz / FINE))
    fy = int(np.ceil(ny * dy / FINE))
    fx = int(np.ceil(nx * dx / FINE))
    az = (np.arange(fz) - (fz - 1) / 2) * FINE
    ay = (np.arange(fy) - (fy - 1) / 2) * FINE
    ax = (np.arange(fx) - (fx - 1) / 2) * FINE
    Z, Y, X = np.meshgrid(az, ay, ax, indexing="ij")

    obj = (((Z / rz) ** 2 + (Y / ry) ** 2 + (X / rx) ** 2) <= 1.0).astype(np.float32)
    obj = gaussian_filter(obj, (psf_fwhm / 2.3548) / FINE, mode="nearest")

    # amostra na grade do voxel (media de caixa -> efeito de volume parcial)
    from scipy.ndimage import zoom
    frac = zoom(obj, (nz / fz, ny / fy, nx / fx), order=1)
    frac = np.clip(frac, 0.0, 1.0)

    hu = hu_bg + frac * (hu_stone - hu_bg)
    if mascarar_em is not None:
        hu[hu < mascarar_em] = 0.0

    vol = Volume(array=hu.astype(np.float32), spacing=tuple(spacing_zyx), affine=None)
    return vol, v_true, d_true


def mascara_total(shape, spacing):
    cheia = np.ones(shape, dtype=bool)
    return MascarasRins(esquerdo=cheia, direito=None, spacing=spacing, aviso=None)


def mede(vol):
    """Roda o detectar_calculos REAL. hu_min=200 e o default do LithosRad."""
    res = detectar_calculos(vol, mascara_total(vol.array.shape, vol.spacing))
    if not res.itens:
        return None
    c = max(res.itens, key=lambda x: x.volume_mm3)   # maior componente
    return c


# =====================================================================
# SUITE A - CACA-BUGS DE EIXO
# =====================================================================
def suite_a():
    print("=" * 78)
    print("SUITE A - CACA-BUGS DE EIXO (anisotropia exagerada: 2,0 x 0,5 x 0,5 mm)")
    print("=" * 78)
    print()
    print("Se a ordem dos eixos estiver trocada, o diametro erra por ~4x. Grita.")
    print()

    SP = (2.0, 0.5, 0.5)   # (dz, dy, dx)
    falhas = []

    # A1: esfera - volume deve bater independente de eixo (produto e comutativo)
    print("A1. Esfera de 8 mm  (testa o VOLUME)")
    vol, vt, dt = sintetiza(8.0, SP, psf_fwhm=0.9)
    c = mede(vol)
    err = (c.volume_mm3 / vt - 1) * 100
    print(f"    verdadeiro={vt:8.2f} mm3   medido={c.volume_mm3:8.2f} mm3   erro={err:+6.1f}%")
    print(f"    n_voxels={c.n_voxels}   voxel={np.prod(SP):.4f} mm3   "
          f"n*voxel={c.n_voxels*np.prod(SP):.2f} mm3")
    if not (0 < err < 120):
        falhas.append("A1: erro de volume fora do esperado para limiar de 200 UH")
    print()

    # A2: BASTAO ao longo de Z - o teste que mata erro de eixo
    print("A2. Elipsoide alongado em Z: rz=9, ry=2, rx=2 mm  (testa o DIAMETRO)")
    print("    Diametro verdadeiro = 18 mm (ao longo de Z, o eixo de voxel GROSSO).")
    print("    Se os eixos estiverem trocados, sai ~4 mm em vez de ~18 mm.")
    vol, vt, dt = sintetiza(None, SP, elipsoide=(9.0, 2.0, 2.0), psf_fwhm=0.9)
    c = mede(vol)
    err_d = c.diametro_mm - dt
    print(f"    verdadeiro={dt:6.2f} mm   medido={c.diametro_mm:6.2f} mm   erro={err_d:+5.2f} mm")
    if abs(err_d) > 2.5:
        falhas.append(f"A2: diametro errado por {err_d:+.2f} mm -- SUSPEITA DE ERRO DE EIXO")
    print()

    # A3: BASTAO ao longo de X - o espelho de A2
    print("A3. Elipsoide alongado em X: rz=2, ry=2, rx=9 mm")
    print("    Diametro verdadeiro = 18 mm (ao longo de X, o eixo de voxel FINO).")
    vol, vt, dt = sintetiza(None, SP, elipsoide=(2.0, 2.0, 9.0), psf_fwhm=0.9)
    c = mede(vol)
    err_d = c.diametro_mm - dt
    print(f"    verdadeiro={dt:6.2f} mm   medido={c.diametro_mm:6.2f} mm   erro={err_d:+5.2f} mm")
    if abs(err_d) > 2.5:
        falhas.append(f"A3: diametro errado por {err_d:+.2f} mm -- SUSPEITA DE ERRO DE EIXO")
    print()

    return falhas


# =====================================================================
# SUITE B - GEOMETRIA REAL DO FREIBURG
# =====================================================================
def suite_b():
    print("=" * 78)
    print("SUITE B - GEOMETRIA DO FREIBURG (0,7 x 0,7363 x 0,7363 mm; PSF 0,7 mm)")
    print("=" * 78)
    print()
    print("Caracteriza o vies do limiar de 200 UH do LithosRad em esferas de")
    print("volume conhecido. Fundo mascarado em 101 UH, como no dataset real.")
    print()

    SP = (0.7, 0.7363, 0.7363)
    print(f"{'D (mm)':>7} {'V real':>10} {'V medido':>10} {'erro V':>9} "
          f"{'D medido':>9} {'erro D':>8} {'HU pico':>8}")
    print("-" * 70)

    linhas = []
    for d in [3, 4, 5, 6, 8, 10, 12, 15, 20]:
        vol, vt, dt = sintetiza(d, SP, hu_stone=900.0, hu_bg=0.0,
                                psf_fwhm=0.7, mascarar_em=101.0)
        c = mede(vol)
        if c is None:
            print(f"{d:>7} {vt:>10.1f}        --  FALHA DE SEGMENTACAO")
            linhas.append((d, vt, None, None))
            continue
        ev = (c.volume_mm3 / vt - 1) * 100
        ed = c.diametro_mm - dt
        print(f"{d:>7} {vt:>10.1f} {c.volume_mm3:>10.1f} {ev:>+8.1f}% "
              f"{c.diametro_mm:>9.2f} {ed:>+7.2f} {c.hu_max:>8.0f}")
        linhas.append((d, vt, ev, ed))
    print()

    # ---- verificacoes de FISICA (nao de valores ajustados) ----
    falhas = []
    erros = [(d, e) for d, _, e, _ in linhas if e is not None]

    # 1. limiar de 200 UH num objeto de 900 UH corta a 22% do pico -> SUPERESTIMA
    if any(e <= 0 for _, e in erros):
        falhas.append("B1: erro de volume NAO e positivo. Um limiar a 22% do pico "
                      "DEVE superestimar. Suspeite do volume do voxel.")

    # 2. erro relativo ~ 3*dr/r  ->  decresce quando o calculo cresce
    grandes = [e for d, e in erros if d >= 10]
    pequenos = [e for d, e in erros if d <= 5]
    if grandes and pequenos and min(pequenos) <= max(grandes):
        falhas.append("B2: o erro NAO decresce com o tamanho. A fisica manda "
                      "erro ~ 3*dr/r. Suspeite da segmentacao.")

    # 3. diametro dentro de ~1,5 voxel
    for d, _, _, ed in linhas:
        if ed is not None and abs(ed) > 1.5:
            falhas.append(f"B3: diametro de {d} mm erra {ed:+.2f} mm (> 1,5 voxel)")

    return falhas


if __name__ == "__main__":
    f = suite_a() + suite_b()
    print("=" * 78)
    if f:
        print("FALHAS DETECTADAS:")
        for x in f:
            print(f"  [X] {x}")
        print()
        print("Conserte AGORA, na Fase 1. Bug encontrado aqui e conserto;")
        print("encontrado na Fase 2 e desvio a registrar.")
        sys.exit(1)
    print("TODAS AS VERIFICACOES PASSARAM.")
    print()
    print("O motor de volumetria se comporta como a fisica manda:")
    print("  - volume correto na geometria anisotropica")
    print("  - diametro correto em ambos os eixos (sem troca de eixo)")
    print("  - superestimacao positiva e decrescente com o tamanho, a 200 UH")

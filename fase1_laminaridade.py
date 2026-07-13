#!/usr/bin/env python3
"""
VAE-001 - FASE 1: INDICE DE LAMINARIDADE OBSERVAVEL

PROBLEMA
--------
O erro de volume do LithosRad e governado pela ESPESSURA do calculo:
    erro ~ dr x (S/V)  ~  2*dr / t_eq
onde t_eq = V / (pi*(d/2)^2) e a espessura equivalente.

Nenhum limiar conserta isso: os 9 metodos testados tem rho(compacidade, erro)
entre -0,58 e -0,79. Mudar o limiar muda dr; NAO muda S/V. E em objetos
sub-voxel (t_eq < 0,7 mm) o pico observado ja esta deprimido pelo volume
parcial, entao nem a meia-altura estima dr corretamente.

SAIDA POSSIVEL
--------------
Nao medir o que nao da para medir. Reportar o volume com confianca nos
calculos compactos, e SINALIZAR os laminares como estimativa nao confiavel.

Para isso e preciso um INDICE DE LAMINARIDADE computavel APENAS do que o
LithosRad enxerga (mascara + imagem). Na clinica nao existe gt_vol.

Este script testa 6 candidatos e mede, para cada um:
  - correlacao com a espessura VERDADEIRA (t_eq real)   -> ele mede o que quer?
  - poder de separar os calculos bons dos ruins          -> AUC
  - o CA-1 resultante no subconjunto retido              -> passa?

NENHUM calculo LACRADO e tocado.

Uso:  python fase1_laminaridade.py
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
HU_MIN = 200.0                    # ponto de operacao do LithosRad


def maior_componente(m):
    rot, n = ndi.label(m, structure=CONN)
    if n == 0:
        return None
    t = np.bincount(rot.ravel()); t[0] = 0
    return rot == t.argmax()


def area_superficie(mask, sp):
    """Area da superficie da mascara (mm2), contando faces expostas."""
    dz, dy, dx = sp
    a = 0.0
    for eixo, face in ((0, dy * dx), (1, dz * dx), (2, dz * dy)):
        d = np.diff(mask.astype(np.int8), axis=eixo)
        a += float(np.abs(d).sum()) * face
    # faces na borda do volume (o calculo nao deveria tocar a borda, mas garante)
    for eixo, face in ((0, dy * dx), (1, dz * dx), (2, dz * dy)):
        sl0 = [slice(None)] * 3; sl0[eixo] = 0
        sl1 = [slice(None)] * 3; sl1[eixo] = -1
        a += (float(mask[tuple(sl0)].sum()) + float(mask[tuple(sl1)].sum())) * face
    return a


def indices(hu, mask, sp):
    """Os 6 candidatos. TODOS computaveis so do que o LithosRad enxerga."""
    vv = float(np.prod(sp))
    V = float(mask.sum()) * vv
    S = area_superficie(mask, sp)

    # 1. raio hidraulico: 3V/S. Para uma esfera = r. Para um disco de espessura t = 3t/2.
    hidr = 3.0 * V / S if S > 0 else 0.0

    # 2. raio da maior esfera inscrita (transformada de distancia, em mm)
    edt = ndi.distance_transform_edt(mask, sampling=sp)
    r_insc = float(edt.max())

    # 3. media da transformada de distancia dentro da mascara
    edt_med = float(edt[mask].mean()) if mask.any() else 0.0

    # 4. sobrevivencia a erosao de 1 voxel
    ero = ndi.binary_erosion(mask, CONN)
    f_ero = float(ero.sum()) / float(mask.sum()) if mask.sum() else 0.0

    # 5. fracao de voxels no "plato" (>= 90% do pico). Uma lasca nao tem interior:
    #    todos os seus voxels sao de casca, entao o plato e minusculo.
    v = hu[mask]
    pico = float(v.max())
    f_plato = float((v >= 0.9 * pico).sum()) / v.size if v.size else 0.0

    # 6. razao mediana/pico. Calculo compacto tem massa de voxels perto do pico.
    r_med_pico = float(np.median(v)) / pico if pico > 0 else 0.0

    # e a espessura equivalente OBSERVADA, para comparacao (usa o diametro da mascara)
    return dict(hidr=hidr, r_insc=r_insc, edt_med=edt_med, f_ero=f_ero,
                f_plato=f_plato, r_med_pico=r_med_pico, V_mask=V, S_mask=S)


def auc(score, bom):
    """AUC de Mann-Whitney: P(score de um BOM > score de um RUIM)."""
    a = np.asarray(score)[np.asarray(bom, bool)]
    b = np.asarray(score)[~np.asarray(bom, bool)]
    if a.size == 0 or b.size == 0:
        return np.nan
    return float((a[:, None] > b[None, :]).mean() + 0.5 * (a[:, None] == b[None, :]).mean())


def main():
    linhas = []
    for c in carregar_freiburg(MAT, grupo="DESENV"):    # NUNCA 'LACRADO'
        hu = np.asarray(c["array"], np.float64)
        sp = c["spacing"]
        gt = c["gt_vol_mL"] * 1000.0
        d = c["gt_diam_mm"]

        m = maior_componente(hu >= HU_MIN)
        if m is None:
            continue

        r = detectar_calculos(Volume(array=c["array"], spacing=sp),
                              MascarasRins(esquerdo=np.ones(hu.shape, bool),
                                           direito=None, spacing=sp, aviso=None))
        it = max(r.itens, key=lambda x: x.volume_mm3)

        idx = indices(hu, m, sp)
        # espessura equivalente OBSERVADA (do que o LithosRad reporta)
        t_obs = it.volume_mm3 / (np.pi * (it.diametro_mm / 2) ** 2)

        linhas.append(dict(
            id=c["id"], d_gt=d, gt=gt, tipo=c["stone_type"],
            t_real=gt / (np.pi * (d / 2) ** 2),          # VERDADE (so p/ avaliar)
            v_lithos=it.volume_mm3, d_lithos=it.diametro_mm,
            erro=100.0 * (it.volume_mm3 / gt - 1.0),
            t_obs=t_obs, **idx))

    df = pd.DataFrame(linhas).sort_values("t_real")
    CAND = ["t_obs", "hidr", "r_insc", "edt_med", "f_ero", "f_plato", "r_med_pico"]

    # ---------------------------------------------------------------- 1 ----
    print("=" * 104)
    print("1. OS CANDIDATOS PREDIZEM A ESPESSURA VERDADEIRA?")
    print("=" * 104)
    print(f"{'indice':>12} {'rho vs t_real':>14} {'p':>9} | {'rho vs erro':>12} {'p':>9}")
    print("-" * 104)
    for k in CAND:
        r1, p1 = spearmanr(df[k], df["t_real"])
        r2, p2 = spearmanr(df[k], df["erro"])
        print(f"{k:>12} {r1:>+14.3f} {p1:>9.4f} | {r2:>+12.3f} {p2:>9.4f}")
    print()
    print("  Queremos rho ALTO e POSITIVO vs t_real (o indice mede a espessura)")
    print("  e rho ALTO e NEGATIVO vs erro (indice alto -> erro baixo).")
    print()

    # ---------------------------------------------------------------- 2 ----
    # "bom" = o calculo cujo erro o LithosRad acerta dentro de +-25% (o CA-1)
    df["bom"] = df["erro"].abs() <= 25.0
    print("=" * 104)
    print(f"2. PODER DE SEPARAR BONS DE RUINS   (bom = |erro| <= 25%; "
          f"{int(df['bom'].sum())} bons, {int((~df['bom']).sum())} ruins)")
    print("=" * 104)
    print(f"{'indice':>12} {'AUC':>7}")
    print("-" * 104)
    aucs = {}
    for k in CAND:
        a = auc(df[k], df["bom"])
        aucs[k] = a
        print(f"{k:>12} {a:>7.3f}")
    melhor = max(aucs, key=lambda k: aucs[k] if not np.isnan(aucs[k]) else -1)
    print()
    print(f"  MELHOR: {melhor}  (AUC = {aucs[melhor]:.3f})")
    print("  AUC 1,0 = separacao perfeita. 0,5 = inutil.")
    print()

    # ---------------------------------------------------------------- 3 ----
    print("=" * 104)
    print("3. TABELA POR CALCULO (do mais laminar ao mais compacto)")
    print("=" * 104)
    cols = ["id", "d_gt", "gt", "t_real", "t_obs", "hidr", "r_insc", "edt_med",
            "f_ero", "f_plato", "r_med_pico", "erro"]
    print(df[cols].to_string(index=False,
                             float_format=lambda x: f"{x:8.2f}"))
    print()

    # ---------------------------------------------------------------- 4 ----
    print("=" * 104)
    print("4. VARREDURA DE CORTE NO MELHOR INDICE - CA-1 no subconjunto RETIDO")
    print("=" * 104)
    ge10 = df["d_gt"] >= 10.0
    print(f"   Estrato primario (>=10 mm): n = {int(ge10.sum())}")
    print()
    print(f"{'corte':>8} {'n retido':>9} {'% retido':>9} {'vies%':>8} {'sd':>7} "
          f"{'semi-LoA':>9} {'CA-1':>6} | {'ids excluidos'}")
    print("-" * 104)
    sub = df[ge10]
    for q in np.percentile(sub[melhor], [0, 10, 20, 30, 40, 50, 60]):
        ret = sub[sub[melhor] >= q]
        if len(ret) < 3:
            continue
        e = ret["erro"].to_numpy()
        b, s = e.mean(), e.std(ddof=1)
        semi = 1.96 * s
        ok = "PASSA" if semi <= 25 else "reprova"
        exc = sorted(sub.loc[sub[melhor] < q, "id"].astype(int).tolist())
        print(f"{q:>8.2f} {len(ret):>9} {100*len(ret)/len(sub):>8.0f}% {b:>+8.1f} "
              f"{s:>7.1f} {semi:>9.1f} {ok:>6} | {exc}")
    print()
    print("   CA-1: semi-amplitude dos LoA 95% <= 25 pontos percentuais.")
    print("   Um corte que PASSA, retendo a maioria dos calculos, resolve o problema:")
    print("   o LithosRad reporta volume onde acerta, e sinaliza onde nao acerta.")
    print()
    print("   ATENCAO: o corte escolhido aqui e ajustado nos 25 de DESENVOLVIMENTO.")
    print("   Sua validacao e sobre os 76 LACRADOS, depois do congelamento.")
    print()

    df.to_csv(ROOT / "results" / "fase1_laminaridade.csv", index=False)
    print("Salvo: results/fase1_laminaridade.csv")


if __name__ == "__main__":
    main()

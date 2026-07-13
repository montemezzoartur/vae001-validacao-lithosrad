#!/usr/bin/env python3
"""
VAE-001 - FASE 1: SHI E VCSD  --  CONFUNDIMENTO DE FORMA E NAO-TRANSFERIBILIDADE

=============================================================================
DUAS PERGUNTAS
=============================================================================

(A) O SHI do LithosRad e confundido pela FORMA do calculo?

    O SHI e o desvio-padrao das UH DENTRO da mascara. A mascara a 200 UH inclui
    toda a casca de voxels de volume parcial -- voxels cujo valor e baixo nao
    porque o calculo seja heterogeneo, mas porque estao MEIO VAZIOS.

    Quanto mais casca, maior o espalhamento das UH. E a fracao de casca e
    exatamente a razao S/V que ja governa o erro de volume (rho = -0,74).

    PREDICAO: SHI/VCSD na mascara CHEIA correlacionam com a forma (t_eq,
    compacidade); a correlacao SOME na mascara ERODIDA (so o nucleo).

    SE CONFIRMADO: o SHI como calculado hoje mede FORMA, nao heterogeneidade.

(B) Quao diferente e o SHI do LithosRad do SHI da LITERATURA?

    O SHI da literatura (Lee 2016 Sci Rep; Yamashita 2019; Iqbal 2021) e:
      - 2D:       um unico corte axial, no ponto de maior diametro
      - ELIPTICO: uma ROI eliptica, nao o contorno real do calculo
      - INTERIOR: "sem incluir o tecido mole adjacente" -- a borda e EVITADA

    O do LithosRad e 3D, sobre a segmentacao real, e INCLUI a borda.

    Sao TRES diferencas, nao uma. Este script mede as tres.

    CONSEQUENCIA: os cortes publicados (SHI 213; VCSD 51,3%) NAO sao
    transferiveis. Este script quantifica o quanto.

=============================================================================
LIMITACOES DECLARADAS
=============================================================================
1. Os calculos do Freiburg estao em AGUA, nao em tecido renal. A ROI da
   literatura evita TECIDO MOLE; aqui nao ha tecido a evitar. O simulacro
   captura as diferencas 2D-vs-3D e ELIPSE-vs-CONTORNO, mas NAO a diferenca
   de fundo. E parcial, e isso deve ser declarado.
2. Os calculos sao de composicao PURA. A heterogeneidade verdadeira deles e
   ESTRUTURAL (laminacao, porosidade), nao composicional. Um SHI que separa
   os TIPOS pode estar separando DENSIDADE.
3. Nada aqui calibra corte algum. n=25 nao permite.

NENHUM calculo LACRADO e tocado.

Requer: pip install scikit-image
Uso:    python fase1_shi.py
=============================================================================
"""
import io, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import ndimage as ndi
from scipy.stats import spearmanr, kruskal
from skimage.measure import regionprops, label as sk_label

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
HU_MIN = 200.0
N_MIN = 5            # abaixo disso, um desvio-padrao nao significa nada
CONTIDO = 0.98       # a elipse inscrita deve estar 98% dentro do calculo


def maior_comp(m):
    rot, n = ndi.label(m, structure=CONN)
    if n == 0:
        return None
    t = np.bincount(rot.ravel()); t[0] = 0
    return rot == t.argmax()


def shi_vcsd(hu, mask):
    """SHI = desvio-padrao das UH na mascara. VCSD = 100 * SHI / media."""
    v = hu[mask]
    if v.size < N_MIN:
        return np.nan, np.nan, np.nan, int(v.size)
    m, s = float(v.mean()), float(v.std(ddof=1))
    return s, (100.0 * s / m if m > 0 else np.nan), m, int(v.size)


def elipse(shape, c, a, b, th):
    """Mascara eliptica 2D. Convencao do skimage: eixo maior = (cos th, sin th)
    em coordenadas (linha, coluna)."""
    Y, X = np.ogrid[:shape[0], :shape[1]]
    dy, dx = Y - c[0], X - c[1]
    ct, st = np.cos(th), np.sin(th)
    pm = dy * ct + dx * st
    pn = -dy * st + dx * ct
    return (pm / a) ** 2 + (pn / b) ** 2 <= 1.0


def roi_literatura(hu, mask3d):
    """Simula a ROI da literatura: elipse 2D no corte axial de MAIOR AREA,
    INSCRITA no calculo (o operador evita o tecido mole -> nao transborda).

    Lee 2016: "imagem axial ampliada, no ponto de maior diametro, ROI eliptica
    incorporando a maior area de seccao transversal, SEM incluir tecido mole".

    Retorna (mascara_no_volume, k_do_corte, cobertura) -- ou (None, k, 0.0) se
    nao houver elipse inscrita util. Isso, por si so, e um RESULTADO: o metodo
    da literatura NAO SE APLICA a esse calculo.
    """
    areas = mask3d.sum(axis=(1, 2))
    k = int(np.argmax(areas))
    corte = mask3d[k]
    if corte.sum() < N_MIN:
        return None, k, 0.0

    lab = sk_label(corte, connectivity=2)
    props = regionprops(lab)
    if not props:
        return None, k, 0.0
    p = max(props, key=lambda x: x.area)
    reg = lab == p.label

    cy, cx = p.centroid
    a0 = p.axis_major_length / 2.0
    b0 = p.axis_minor_length / 2.0
    th = p.orientation
    if a0 < 0.5 or b0 < 0.5:
        return None, k, 0.0

    for s in np.linspace(1.20, 0.20, 41):
        e = elipse(corte.shape, (cy, cx), max(a0 * s, 0.5), max(b0 * s, 0.5), th)
        n = int(e.sum())
        if n < N_MIN:
            continue
        if int((e & reg).sum()) / n >= CONTIDO:
            m3 = np.zeros_like(mask3d)
            m3[k] = e
            return m3, k, float(n) / float(reg.sum())
    return None, k, 0.0


def main():
    linhas = []
    for c in carregar_freiburg(MAT, grupo="DESENV"):     # NUNCA 'LACRADO'
        hu = np.asarray(c["array"], np.float64)
        sp = c["spacing"]
        gt = c["gt_vol_mL"] * 1000.0
        d = c["gt_diam_mm"]

        m = maior_comp(hu >= HU_MIN)
        if m is None:
            continue

        r = detectar_calculos(Volume(array=c["array"], spacing=sp),
                              MascarasRins(esquerdo=np.ones(hu.shape, bool),
                                           direito=None, spacing=sp, aviso=None))
        it = max(r.itens, key=lambda x: x.volume_mm3)

        row = dict(id=c["id"], tipo=c["stone_type"], d_gt=d, gt=gt,
                   t_eq=gt / (np.pi * (d / 2) ** 2),
                   compac=gt / (4 / 3 * np.pi * (d / 2) ** 3),
                   pico=float(hu[m].max()), shi_lithos=it.shi_hu)

        s, vc, mu, n = shi_vcsd(hu, m)
        row.update(shi_3d_cheia=s, vcsd_3d_cheia=vc, hu_med=mu, n_cheia=n)

        for k in (1, 2):
            e = ndi.binary_erosion(m, CONN, iterations=k)
            s, vc, mu, n = shi_vcsd(hu, e)
            row.update(**{f"shi_3d_ero{k}": s, f"vcsd_3d_ero{k}": vc,
                          f"n_ero{k}": n,
                          f"f_ero{k}": n / max(row["n_cheia"], 1)})

        # --- DEFINICAO CORRETA: preenche cavidades, depois erode a casca ---
        # O LithosRad hoje esta INVERTIDO nas duas pontas: EXCLUI as cavidades
        # internas (heterogeneidade REAL) e INCLUI os voxels de borda (ARTEFATO
        # de volume parcial). O correto e o oposto.
        ext = ndi.binary_fill_holes(m)
        row["n_cav"] = int(ext.sum() - m.sum())     # voxels de cavidade recuperados

        # extensao preenchida, SEM erosao (isola o efeito das cavidades)
        s, vc, mu, n = shi_vcsd(hu, ext)
        row.update(shi_3d_pre=s, vcsd_3d_pre=vc, n_pre=n)

        # NUCLEO CORRETO: preenchido E erodido
        for k in (1, 2):
            nuc = ndi.binary_erosion(ext, CONN, iterations=k)
            s, vc, mu, n = shi_vcsd(hu, nuc)
            row.update(**{f"shi_nuc{k}": s, f"vcsd_nuc{k}": vc, f"n_nuc{k}": n})

        roi, kc, cob = roi_literatura(hu, m)
        if roi is not None:
            s, vc, mu, n = shi_vcsd(hu, roi)
            row.update(shi_2d_roi=s, vcsd_2d_roi=vc, n_2d_roi=n,
                       k_corte=kc, cob_2d=cob, roi_ok=True)
        else:
            row.update(shi_2d_roi=np.nan, vcsd_2d_roi=np.nan, n_2d_roi=0,
                       k_corte=kc, cob_2d=0.0, roi_ok=False)

        linhas.append(row)

    df = pd.DataFrame(linhas).sort_values("t_eq")
    ge10 = df["d_gt"] >= 10.0

    # ---------------------------------------------------------------- 0 ----
    print("=" * 108)
    print("0. CONFERENCIA: meu SHI reproduz o do LithosRad?")
    print("=" * 108)
    dd = (df["shi_3d_cheia"] - df["shi_lithos"]).abs()
    print(f"   max |shi_3d_cheia - shi_lithos| = {dd.max():.4f} UH")
    print("   OK." if dd.max() <= 0.5 else
          "   DIVERGENTE. Se for pequeno e sistematico, e ddof (numpy usa 0).")
    print()

    # ---------------------------------------------------------------- 1 ----
    print("=" * 108)
    print("1. (A) O SHI/VCSD DEPENDE DA FORMA?")
    print("=" * 108)
    print(f"{'metrica':>15} {'n':>4} {'rho vs t_eq':>12} {'p':>8} "
          f"{'rho vs compac':>14} {'p':>8}")
    print("-" * 108)
    for k in ["shi_3d_cheia", "vcsd_3d_cheia", "shi_3d_pre", "vcsd_3d_pre",
              "shi_3d_ero1", "vcsd_3d_ero1",
              "shi_nuc1", "vcsd_nuc1", "shi_nuc2", "vcsd_nuc2",
              "shi_2d_roi", "vcsd_2d_roi"]:
        ok = df[k].notna()
        if ok.sum() < 6:
            print(f"{k:>15} {int(ok.sum()):>4}   (poucos validos)")
            continue
        r1, p1 = spearmanr(df.loc[ok, "t_eq"], df.loc[ok, k])
        r2, p2 = spearmanr(df.loc[ok, "compac"], df.loc[ok, k])
        print(f"{k:>15} {int(ok.sum()):>4} {r1:>+12.3f} {p1:>8.4f} "
              f"{r2:>+14.3f} {p2:>8.4f}")
    print()
    print("   PREDICAO: rho NEGATIVO e forte na mascara CHEIA (calculo fino ->")
    print("   mais casca -> mais espalhamento de UH -> SHI alto); rho ~ 0 no NUCLEO.")
    print("   Se confirmado: o SHI da mascara cheia mede FORMA, nao heterogeneidade.")
    print()
    print("   shi_nuc1/2 = DEFINICAO CORRETA: fill_holes (recupera as cavidades")
    print("   internas, que sao heterogeneidade REAL) + erosao (remove a casca de")
    print("   volume parcial, que e ARTEFATO). O LithosRad hoje faz o INVERSO nas")
    print("   duas pontas.")
    print()

    # -------------------------------------------------------------- 1b ----
    print("=" * 108)
    print("1b. QUANTO AS CAVIDADES INTERNAS MUDAM O SHI?")
    print("=" * 108)
    com_cav = df[df["n_cav"] > 0]
    print(f"   Calculos com cavidade interna (< 200 UH): {len(com_cav)}/{len(df)}")
    if len(com_cav):
        print(f"{'id':>3} {'d_gt':>6} {'n_cheia':>8} {'n_cav':>6} {'%':>5} "
              f"{'SHI cheia':>10} {'SHI preench':>12} {'delta':>8}")
        print("-" * 108)
        for _, r in com_cav.iterrows():
            dlt = r["shi_3d_pre"] - r["shi_3d_cheia"]
            print(f"{int(r['id']):>3} {r['d_gt']:>6.2f} {int(r['n_cheia']):>8} "
                  f"{int(r['n_cav']):>6} {100*r['n_cav']/r['n_cheia']:>4.1f}% "
                  f"{r['shi_3d_cheia']:>10.1f} {r['shi_3d_pre']:>12.1f} "
                  f"{dlt:>+8.1f}")
    print()
    print("   ATENCAO (ACHADO 2): os autores do Freiburg ZERARAM tudo abaixo de")
    print("   ~101 UH. Uma cavidade de 60 UH aparece como 0, nao como 60. O")
    print("   fill_holes recupera a POSICAO, mas o VALOR esta destruido. Isso")
    print("   INFLA o SHI do nucleo. Nao e corrigivel aqui -- e limitacao declarada.")
    print("   Em TC clinica (sem mascaramento) o problema nao existe.")
    print()

    # ---------------------------------------------------------------- 2 ----
    print("=" * 108)
    print("2. (B) QUANTO O METODO MUDA O NUMERO?")
    print("=" * 108)
    print(f"{'metodo':>16} {'n valido':>9} {'SHI mediano':>12} {'VCSD mediano':>13} "
          f"{'faixa VCSD':>22}")
    print("-" * 108)
    for nome, ks, kv in [("3D cheia (hoje)", "shi_3d_cheia", "vcsd_3d_cheia"),
                         ("3D preenchida", "shi_3d_pre", "vcsd_3d_pre"),
                         ("3D ero1 (s/fill)", "shi_3d_ero1", "vcsd_3d_ero1"),
                         ("NUCLEO(1) correto", "shi_nuc1", "vcsd_nuc1"),
                         ("NUCLEO(2) correto", "shi_nuc2", "vcsd_nuc2"),
                         ("2D ROI literatura", "shi_2d_roi", "vcsd_2d_roi")]:
        ok = df[kv].notna()
        if ok.sum() == 0:
            print(f"{nome:>16} {0:>9}")
            continue
        print(f"{nome:>16} {int(ok.sum()):>9} {df.loc[ok, ks].median():>12.1f} "
              f"{df.loc[ok, kv].median():>13.1f} "
              f"[{df.loc[ok, kv].min():>8.1f}, {df.loc[ok, kv].max():>8.1f}]")
    print()
    print("   O unico corte publicado de VCSD e 51,3% (Yamashita 2019).")
    print("   Se a mediana muda com o METODO, o corte NAO e transferivel.")
    print()
    ok = df["vcsd_2d_roi"].notna() & df["vcsd_3d_cheia"].notna()
    if ok.sum() >= 6:
        raz = df.loc[ok, "vcsd_3d_cheia"] / df.loc[ok, "vcsd_2d_roi"]
        print(f"   VCSD(3D cheia) / VCSD(2D ROI):  mediana {raz.median():.2f}x   "
              f"faixa [{raz.min():.2f}x, {raz.max():.2f}x]   (n={int(ok.sum())})")
        r, p = spearmanr(df.loc[ok, "t_eq"], raz)
        print(f"   rho(t_eq, razao) = {r:+.2f}  (p = {p:.4f})")
        print("   -> Se rho for forte, a DISCREPANCIA entre os metodos e ela propria")
        print("      um efeito de forma. Nem um fator de conversao unico salva.")
    print()

    # ---------------------------------------------------------------- 3 ----
    print("=" * 108)
    print("3. A ARMADILHA: quantos calculos sobrevivem a cada metodo?")
    print("=" * 108)
    print(f"{'id':>3} {'d_gt':>6} {'t_eq':>6} {'n_cheia':>8} {'n_cav':>6} "
          f"{'n_nuc1':>7} {'n_nuc2':>7} {'n_2dROI':>8} {'>=10':>5}")
    print("-" * 108)
    for _, r in df.iterrows():
        print(f"{int(r['id']):>3} {r['d_gt']:>6.2f} {r['t_eq']:>6.2f} "
              f"{int(r['n_cheia']):>8} {int(r['n_cav']):>6} "
              f"{int(r['n_nuc1']):>7} {int(r['n_nuc2']):>7} "
              f"{int(r['n_2d_roi']):>8} "
              f"{'sim' if r['d_gt'] >= 10 else '-':>5}")
    print()
    sub = df[ge10]
    print(f"   Entre os {len(sub)} calculos >= 10 mm (onde o LithosRad exibe SHI):")
    print(f"     sem nucleo apos erosao de 1 voxel:  "
          f"{int((sub['n_nuc1'] < N_MIN).sum())}/{len(sub)}")
    print(f"     sem nucleo apos erosao de 2 voxels: "
          f"{int((sub['n_nuc2'] < N_MIN).sum())}/{len(sub)}")
    print(f"     ROI 2D da literatura INAPLICAVEL:   "
          f"{int((~sub['roi_ok']).sum())}/{len(sub)}")
    print()
    print("   ARGUMENTO CENTRAL: os calculos que o LithosRad vai RECUSAR sao os")
    print("   mesmos que a literatura NUNCA CONSEGUIU MEDIR -- so que ela nunca")
    print("   disse isso. Uma recusa explicita e mais honesta que um numero ruim")
    print("   apresentado sem ressalva.")
    print()

    # ---------------------------------------------------------------- 4 ----
    print("=" * 108)
    print("4. O SHI DISCRIMINA COMPOSICAO?")
    print("=" * 108)
    for kv in ["vcsd_3d_cheia", "vcsd_nuc1", "vcsd_2d_roi"]:
        s = df[df["tipo"].notna() & df[kv].notna()]
        if s["tipo"].nunique() < 2:
            continue
        print(f"\n   {kv}:")
        for t, g in s.groupby("tipo"):
            print(f"     {str(t):>26}  n={len(g):>2}  mediana {g[kv].median():>7.1f}"
                  f"  [{g[kv].min():>6.1f}, {g[kv].max():>6.1f}]"
                  f"   pico mediano {g['pico'].median():>6.0f} UH")
        gr = [g[kv].values for _, g in s.groupby("tipo") if len(g) >= 2]
        if len(gr) >= 2:
            try:
                _, p = kruskal(*gr)
                print(f"     Kruskal-Wallis: p = {p:.4f} "
                      f"({'discrimina' if p < 0.05 else 'NAO discrimina'})")
            except Exception:
                pass
    print()
    print("   CUIDADO: os calculos do Freiburg sao de composicao PURA. Um SHI que")
    print("   separa os TIPOS pode estar separando DENSIDADE (veja a coluna 'pico'),")
    print("   nao heterogeneidade. Nao conclua sem cruzar.")
    print()

    # ---------------------------------------------------------------- 5 ----
    print("=" * 108)
    print("5. TABELA COMPLETA")
    print("=" * 108)
    print(df[["id", "tipo", "d_gt", "t_eq", "pico", "n_cav",
              "shi_3d_cheia", "vcsd_3d_cheia", "shi_nuc1", "vcsd_nuc1",
              "shi_2d_roi", "vcsd_2d_roi"]]
          .to_string(index=False, float_format=lambda x: f"{x:8.1f}"))
    print()

    df.to_csv(ROOT / "results" / "fase1_shi.csv", index=False)
    print("Salvo: results/fase1_shi.csv")


if __name__ == "__main__":
    main()

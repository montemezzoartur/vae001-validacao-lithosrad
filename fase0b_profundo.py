#!/usr/bin/env python3
"""
VAE-001 - FASE 0b: INVENTARIO PROFUNDO (v3)

Varre os 101 calculos e responde o que ficou em aberto:
  - voxsiz e constante? imgdata tem sempre 83^3?
  - qual foi o corte de mascaramento do fundo? (menor valor nao-zero)
  - gt_vol/gt_diam do .mat batem com Volume/Diameter do CSV?
  - qual a faixa de UH dos calculos?

REGRA DA FASE 0: caracteriza a ENTRADA. NAO computa volume segmentado,
NAO compara nenhuma saida com a referencia. Nenhum desfecho e revelado.

Uso:  python fase0b_profundo.py data\\raw
"""
import sys, os, io
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.io import loadmat

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT = []
def w(s=""):
    print(s); OUT.append(s)


def main(raw):
    raw = Path(raw)
    mat = next(p for p in raw.iterdir() if p.suffix.lower() == ".mat")
    csv = next(p for p in raw.iterdir() if p.suffix.lower() == ".csv")

    m = loadmat(mat, squeeze_me=False, struct_as_record=True)
    st = m["stones"].ravel()
    df = pd.read_csv(csv, sep=";")

    w("# VAE-001 - Fase 0b: Inventario profundo")
    w()
    w(f"n calculos no .mat: **{len(st)}**   n linhas no CSV: **{len(df)}**")
    w()

    rows = []
    for i, s in enumerate(st):
        img = np.asarray(s["imgdata"])
        vs = np.asarray(s["voxsiz"]).ravel()
        vv = float(np.asarray(s["voxvol_mL"]).ravel()[0])
        nz = img[img != 0]
        rows.append(dict(
            idx=i + 1,
            gt_vol=float(np.asarray(s["gt_vol"]).ravel()[0]),
            gt_diam=float(np.asarray(s["gt_diam"]).ravel()[0]),
            shape=tuple(img.shape),
            vx=vs[0], vy=vs[1], vz=vs[2],
            voxvol_mL=vv,
            voxvol_calc=float(np.prod(vs) / 1000.0),
            img_min=float(img.min()),
            img_max=float(img.max()),
            nz_min=float(nz.min()) if nz.size else np.nan,
            nz_p01=float(np.percentile(nz, 1)) if nz.size else np.nan,
            n_zero=int((img == 0).sum()),
            n_total=int(img.size),
            n_neg=int((img < 0).sum()),
        ))
    r = pd.DataFrame(rows)

    # ---------- 1. geometria ----------
    w("## 1. Geometria do voxel")
    w()
    w("| Campo | Valores unicos | Detalhe |")
    w("|---|---|---|")
    for c in ["vx", "vy", "vz"]:
        u = np.unique(np.round(r[c].values, 6))
        w(f"| `{c}` | {len(u)} | {u[:8].tolist()}{' ...' if len(u) > 8 else ''} |")
    su = r["shape"].astype(str).unique()
    w(f"| `shape` | {len(su)} | {su[:5].tolist()}{' ...' if len(su) > 5 else ''} |")
    w()
    if len(np.unique(np.round(r[["vx", "vy", "vz"]].values, 6), axis=0)) == 1:
        vx, vy, vz = r.loc[0, ["vx", "vy", "vz"]]
        w(f"**voxsiz e CONSTANTE nos {len(r)} calculos: {vx} x {vy} x {vz} mm**")
        w()
        w(f"- Volume do voxel = {vx*vy*vz:.6f} mm3 = {vx*vy*vz/1000:.9f} mL")
        w(f"- ATENCAO: o artigo declara 0,7 x 0,7 mm no plano. O DADO diz {vx}.")
        w(f"- Usar 0,7 isotropico daria {0.7**3:.6f} mm3 -> erro de "
          f"{(0.7**3/(vx*vy*vz)-1)*100:+.1f}% em TODOS os volumes.")
    else:
        w("**ATENCAO: voxsiz VARIA entre calculos.** Cada um precisa do seu proprio "
          "volume de voxel. Distribuicao:")
        w()
        w("```")
        w(r[["vx", "vy", "vz"]].describe().to_string())
        w("```")
    w()
    dv = (r["voxvol_mL"] - r["voxvol_calc"]).abs().max()
    w(f"- Consistencia `voxvol_mL` vs prod(voxsiz)/1000: erro maximo = {dv:.3e} mL "
      f"({'OK' if dv < 1e-9 else 'DIVERGENTE - investigar'})")
    w()

    # ---------- 2. mascaramento ----------
    w("## 2. Os dados sao TC crua ou pre-processada?")
    w()
    w("| Metrica | min | mediana | max |")
    w("|---|---|---|---|")
    for c, lab in [("img_min", "menor valor do volume"),
                   ("nz_min", "menor valor NAO-ZERO"),
                   ("nz_p01", "percentil 1 dos nao-zero"),
                   ("img_max", "maior valor (pico do calculo)")]:
        w(f"| {lab} | {r[c].min():.2f} | {r[c].median():.2f} | {r[c].max():.2f} |")
    w()
    frac_zero = (r["n_zero"] / r["n_total"])
    w(f"- Fracao de voxels EXATAMENTE zero: mediana **{frac_zero.median()*100:.2f}%** "
      f"(min {frac_zero.min()*100:.2f}%, max {frac_zero.max()*100:.2f}%)")
    w(f"- Calculos com QUALQUER voxel negativo: **{(r['n_neg']>0).sum()} de {len(r)}**")
    w()
    w("**INTERPRETACAO:**")
    w()
    if (r["n_neg"] == 0).all():
        nzmin = r["nz_min"].min()
        w(f"- Nenhum voxel negativo em nenhum calculo. TC real de agua teria ruido")
        w(f"  negativo. Portanto: **o fundo FOI zerado / mascarado**.")
        w(f"- Menor valor nao-zero observado no dataset inteiro: **{nzmin:.2f}**")
        if nzmin < 5:
            w("- Isso sugere CLIPPING em zero (negativos -> 0), preservando 0-130 UH.")
            w("  Bom: a rampa de volume parcial acima de 0 esta INTACTA.")
        else:
            w(f"- Isso sugere MASCARAMENTO com corte em ~{nzmin:.0f} UH.")
            w(f"  A rampa de volume parcial ABAIXO de {nzmin:.0f} UH foi DESTRUIDA.")
            w("  Consequencia: metodos que dependem da rampa completa (voxel fracionario)")
            w("  NAO podem ser validados neste dataset. Contagem de voxels a 130 UH: OK.")
    else:
        w("- Ha voxels negativos. Os dados parecem ser UH crua (com ruido).")
        w("- O `min=0` do calculo #1 era coincidencia ou caso particular.")
    w()

    # ---------- 3. calculo vs referencia ----------
    w("## 3. Consistencia .mat vs CSV")
    w()
    merged = r.merge(df, left_on="idx", right_on="ID", how="outer", indicator=True)
    w(f"- Linhas casadas por ID: **{(merged['_merge']=='both').sum()} de {len(df)}**")
    dvol = (merged["gt_vol"] - merged["Volume"]).abs()
    ddia = (merged["gt_diam"] - merged["Diameter"]).abs()
    w(f"- `gt_vol` vs `Volume` (CSV): diferenca maxima = **{dvol.max():.6f}** "
      f"({'IDENTICOS' if dvol.max() < 1e-6 else 'DIVERGENTES - investigar'})")
    w(f"- `gt_diam` vs `Diameter` (CSV): diferenca maxima = **{ddia.max():.6f}** "
      f"({'IDENTICOS' if ddia.max() < 1e-6 else 'DIVERGENTES - investigar'})")
    w()
    w("- Unidades confirmadas: `gt_vol` em **mL**, `gt_diam` em **mm**, "
      "`voxsiz` em **mm**, `voxvol_mL` em **mL**.")
    w()

    # ---------- 4. faixa de HU dos calculos ----------
    w("## 4. Faixa de atenuacao dos calculos (pico por calculo)")
    w()
    w("```")
    w(r["img_max"].describe().to_string())
    w("```")
    w()
    w("- Se o pico maximo do dataset for < 1500 UH, nao ha saturacao aparente.")
    w("- Picos muito baixos (<300 UH) em calculos pequenos indicam volume parcial")
    w("  severo: nao ha voxel interior 'puro'.")
    w()

    # ---------- 5. tabela por calculo ----------
    w("## 5. Tabela por calculo (para a divisao pre-registrada)")
    w()
    out = merged[["ID", "Diameter", "Volume", "StoneType", "img_max", "n_zero"]].copy()
    out["estrato"] = pd.cut(out["Diameter"], [0, 5, 10, 20, np.inf],
                            labels=["<5", "5-10", "10-20", ">20"], right=False)
    w("```")
    w(out.to_string(index=False))
    w("```")
    w()
    out.to_csv("results/fase0b_por_calculo.csv", index=False)
    w("Salvo tambem em `results/fase0b_por_calculo.csv`.")
    w()


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    main(sys.argv[1] if len(sys.argv) > 1 else "data/raw")
    with open("results/fase0b_profundo.md", "w", encoding="utf-8") as f:
        f.write("\n".join(OUT) + "\n")
    print("\n>>> Salvo em results/fase0b_profundo.md")

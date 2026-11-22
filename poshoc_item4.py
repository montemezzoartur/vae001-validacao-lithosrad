#!/usr/bin/env python3
"""
VAE-001 -- ADENDO P, ITEM 4: INSPECAO DESCRITIVA DOS OITO CALCULOS NOMEADOS
===========================================================================

O Adendo P (P-3.2, item 4) nomeia oito calculos do conjunto lacrado para
inspecao DESCRITIVA: numero e tamanho das componentes, posicao do diametro
maximo e figura. Nenhuma estatistica e derivada deles.

A execucao unica (poshoc_lacrado.py, 22/11/2026) copiou a imagem publica desses
oito para results/poshoc_casos.npz. ESTE SCRIPT LE SO ESSE ARQUIVO, o CSV da
execucao e o registro. NAO LE O .mat: nao ha novo acesso ao conjunto lacrado.

POR CALCULO
-----------
1. Componentes 26-conexas dos voxels >= 200 UH e dos voxels >= T
   (T = 0,225 x p95): quantas sao e, de cada uma, voxels, volume e extensao.
2. Diametro maximo do dispositivo: a MESMA conta de d_mc_dispositivo
   (poshoc_lacrado.py), devolvendo tambem os dois extremos. O valor tem de ser
   o gravado no CSV da execucao; se nao for, o script aborta.
3. Figura: tres projecoes de intensidade maxima e as fatias axiais, com o
   contorno de 200 UH, o contorno de T, os vertices da isossuperficie medida
   e o diametro maximo.

NAO FAZ: estatistica, teste ou medida nova. O diametro no plano axial ficou
fora do adendo e continua fora.

Uso:
    python poshoc_item4.py --desenv    # teste: os dois calculos do DESENVOLVIMENTO (56 e 23)
    python poshoc_item4.py             # os oito do lacrado (exige a execucao registrada)
"""
import argparse
import hashlib
import io
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                       # sem janela: so grava arquivo
import matplotlib.pyplot as plt             # noqa: E402
import numpy as np                          # noqa: E402
import pandas as pd                         # noqa: E402
from scipy import ndimage as ndi            # noqa: E402
from scipy.spatial import ConvexHull        # noqa: E402
from scipy.spatial.distance import pdist    # noqa: E402
from skimage.measure import marching_cubes  # noqa: E402

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
import fase1_diam_pico as F                 # noqa: E402  (maior_comp, pico, CONN: as da execucao)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RESULTS = ROOT / "results"
TRAVA = RESULTS / "POSHOC_EXECUTADA.json"
F_ADOTADO = 0.225          # fracao do p95 (a do dispositivo congelado)
T_DETECCAO = 200.0         # limiar de deteccao, UH
TOL = 1e-6                 # mm; a mesma tolerancia da execucao
MENOS = chr(8722)          # sinal de menos tipografico

# Os oito do Adendo P, na ordem em que o adendo os nomeia, e por que foram nomeados.
MOTIVO = {
    29: "erro acima de 1 mm",
    83: "erro acima de 1 mm; componentes multiplas",
    91: "erro acima de 1 mm",
    41: "estruvita",
    88: "estruvita",
    100: "componentes multiplas",
    28: "troca de categoria a 10 mm",
    3: "troca de categoria a 5 mm; menor atenuacao",
}
ORDEM_ADENDO = list(MOTIVO)

CIANO, MAGENTA, VERMELHO, AMARELO = "#00c8ff", "#ff4dff", "#ff3b30", "#ffe000"


# ------------------------------------------------------------ UTILITARIOS ----
def sha256(p: Path, texto: bool = False) -> str:
    b = Path(p).read_bytes()
    if texto:                                   # CSV e script: fins de linha normalizados
        b = b.replace(b"\r\n", b"\n")
    return hashlib.sha256(b).hexdigest()


def br(x, casas=2, sinal=False) -> str:
    """Numero com virgula decimal; o zero sai sem sinal."""
    s = f"{x:+.{casas}f}" if sinal else f"{x:.{casas}f}"
    if float(s) == 0:
        s = f"{0:.{casas}f}"
    return s.replace(".", ",").replace("-", MENOS)


# ----------------------------------------------------------- DESCRICAO ----
def componentes(mask: np.ndarray, sp) -> list:
    """Componentes 26-conexas, da maior para a menor. No empate vem primeiro a
    de menor rotulo, que e a que o argmax da execucao escolhe."""
    rot, n = ndi.label(mask, structure=F.CONN)
    if n == 0:
        return []
    tam = np.bincount(rot.ravel())[1:]
    caixas = ndi.find_objects(rot)
    vox_mm3 = float(np.prod(sp))
    out = []
    for l in np.argsort(-tam, kind="stable"):
        cx = caixas[l]
        out.append(dict(voxels=int(tam[l]), volume_mm3=float(tam[l] * vox_mm3),
                        ext_mm=[float((s.stop - s.start) * d) for s, d in zip(cx, sp)],
                        fatias=[int(cx[0].start), int(cx[0].stop - 1)]))
    return out


def diametro_com_extremos(hu, m, T, sp):
    """A conta de d_mc_dispositivo (poshoc_lacrado.py), linha a linha, com a
    mascara m vinda de fora. Devolve o diametro, os dois extremos e os vertices
    da isossuperficie, em mm, no referencial do recorte publico (o centro do
    voxel [0, 0, 0] e a origem)."""
    idx = np.argwhere(m)
    lo = np.maximum(idx.min(0) - 2, 0)
    hi = np.minimum(idx.max(0) + 3, np.array(hu.shape))
    sl = tuple(slice(a, b) for a, b in zip(lo, hi))
    sub = np.where(m[sl], hu[sl], 0.0).astype(np.float32)
    sub = np.pad(sub, 1, mode="constant", constant_values=0.0)
    v, _, _, _ = marching_cubes(sub, level=T, spacing=sp)
    casco = v[ConvexHull(v).vertices] if len(v) >= 4 else v
    dd = pdist(casco)
    k = int(dd.argmax())
    i, j = (int(a[k]) for a in np.triu_indices(len(casco), 1))
    origem = (lo - 1) * np.asarray(sp, float)   # o recorte comeca em lo; o pad acrescenta 1 voxel
    a, b = casco[i] + origem, casco[j] + origem
    if a[0] > b[0]:
        a, b = b, a                             # extremo 1 = o de menor z
    return float(dd[k]), a, b, v + origem


def descreve(cid: int, hu, sp, linha) -> tuple:
    """Descricao de UM calculo. Aborta se nao reproduzir o CSV da execucao."""
    hu = np.asarray(hu, np.float64)
    sp = tuple(float(x) for x in sp)
    m200 = F.maior_comp(hu >= T_DETECCAO)
    p95 = F.pico(hu, "p95")
    pmax = F.pico(hu, "max")
    T = F_ADOTADO * p95
    c200 = componentes(hu >= T_DETECCAO, sp)
    cT = componentes(hu >= T, sp)
    d, a, b, verts = diametro_com_extremos(hu, m200, T, sp)

    conf = {
        "diametro (emulacao)": abs(d - float(linha["d_emul"])) < TOL,
        "diametro (dispositivo)": abs(d - float(linha["d_disp"])) < TOL,
        "p95": abs(p95 - float(linha["p95"])) < TOL,
        "maximo": abs(pmax - float(linha["pico_max"])) < TOL,
        "T": abs(T - float(linha["T"])) < TOL,
        "numero de componentes >= 200 UH": len(c200) == int(linha["n_comp200"]),
        "maior componente >= 200 UH": c200[0]["voxels"] == int(linha["vox_comp200"]),
        "segunda componente >= 200 UH": (c200[1]["voxels"] if len(c200) > 1 else 0) == int(linha["vox_comp200_2"]),
        "maior componente >= T": cT[0]["voxels"] == int(linha["vox_compT"]),
    }
    falhou = [k for k, ok in conf.items() if not ok]
    if falhou:
        raise SystemExit(f"ABORTADO: o calculo {cid} nao reproduz o CSV da execucao em: {', '.join(falhou)}.\n"
                         "  Nada foi gravado para ele. Corrija o AMBIENTE, nunca o codigo.")

    spv = np.asarray(sp, float)
    delta = b - a
    desc = dict(
        id=int(cid), motivo=MOTIVO.get(int(cid), ""), tipo=str(linha["tipo"]),
        forma=[int(n) for n in hu.shape], espacamento_mm=[float(x) for x in sp],
        d_gt=float(linha["d_gt"]),
        d_disp=float(linha["d_disp"]), e_disp=float(linha["e_disp"]),
        d_reimpl=float(linha["d_reimpl"]), e_reimpl=float(linha["e_reimpl"]),
        d_fix200=float(linha["d_fix200"]), e_fix200=float(linha["e_fix200"]),
        pico_max=float(pmax), p95=float(p95), T=float(T),
        regime="T < 200 UH" if T < T_DETECCAO else "T >= 200 UH",
        piso=float(linha["piso"]), T_abaixo_piso=bool(linha["T_abaixo_piso"]),
        comp200=c200, compT=cT,
        vox200_fora_da_maior=int(sum(c["voxels"] for c in c200[1:])),
        d_recalculado=float(d),
        extremo1_vox=[float(x) for x in a / spv], extremo2_vox=[float(x) for x in b / spv],
        fatia_extremo1=int(round(a[0] / spv[0])), fatia_extremo2=int(round(b[0] / spv[0])),
        delta_mm=[float(x) for x in delta],
        confere_com_csv=True,
    )
    return desc, verts, a, b


# -------------------------------------------------------------- FIGURA ----
def contorno(ax, X, Y, img, nivel, **kw):
    if img.min() < nivel <= img.max():
        ax.contour(X, Y, img, levels=[nivel], **kw)


def figura(desc: dict, hu, sp, verts, a, b, conjunto: str, caminho: Path):
    hu = np.asarray(hu, np.float64)
    dz, dy, dx = (float(v) for v in sp)
    idx = np.argwhere(hu > 0)
    margem = np.array([1, 3, 3])                 # voxels em z, y, x
    lo = np.maximum(idx.min(0) - margem, 0)
    hi = np.minimum(idx.max(0) + margem + 1, np.array(hu.shape))
    sub = hu[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
    z = np.arange(lo[0], hi[0]) * dz
    y = np.arange(lo[1], hi[1]) * dy
    x = np.arange(lo[2], hi[2]) * dx
    vmax = float(hu.max())
    T = desc["T"]
    centro = {id(e): (e[0] + e[-1]) / 2 for e in (z, y, x)}
    meia = max(e[-1] - e[0] for e in (z, y, x)) / 2 + 3 * max(dz, dy, dx)   # mesma escala nas tres projecoes

    nz = sub.shape[0]
    ncol = 8 if nz > 24 else 6
    nlin = int(np.ceil(nz / ncol))
    larg = 11.0
    alt_topo = 4.3
    alt_fatia = (larg / ncol) * (len(y) * dy) / (len(x) * dx) + 0.24
    alt_baixo = nlin * alt_fatia + 0.45
    fig = plt.figure(figsize=(larg, 0.85 + alt_topo + alt_baixo), dpi=150, layout="constrained")
    topo, baixo = fig.subfigures(2, 1, height_ratios=[alt_topo, alt_baixo])

    tam = " e ".join(str(c["voxels"]) for c in desc["comp200"][:4])
    motivo = f" \u2014 {desc['motivo']}" if desc["motivo"] else ""
    fig.suptitle(
        f"C\u00e1lculo {desc['id']} ({desc['tipo']}), {conjunto}{motivo}\n"
        f"refer\u00eancia {br(desc['d_gt'])} mm; dispositivo {br(desc['d_disp'])} mm; "
        f"erro {br(desc['e_disp'], sinal=True)} mm; p95 {desc['p95']:.0f} UH; "
        f"T = 0,225 \u00d7 p95 = {T:.0f} UH; componentes \u2265 200 UH: {len(desc['comp200'])} ({tam} voxels)",
        fontsize=9.5)

    eixos = topo.subplots(1, 3)
    # (imagem, coordenadas horizontais, verticais, colunas dos vertices [h, v], rotulos)
    vistas = [
        (sub.max(0), x, y, (2, 1), "x (mm)", "y (mm)", "Proje\u00e7\u00e3o ao longo de z"),
        (sub.max(1), x, z, (2, 0), "x (mm)", "z (mm)", "Proje\u00e7\u00e3o ao longo de y"),
        (sub.max(2), y, z, (1, 0), "y (mm)", "z (mm)", "Proje\u00e7\u00e3o ao longo de x"),
    ]
    for ax, (img, H, V, (ch, cv), rh, rv, tit) in zip(eixos, vistas):
        dh, dv = H[1] - H[0], V[1] - V[0]
        ax.imshow(img, cmap="gray", vmin=0, vmax=vmax, interpolation="nearest",
                  extent=[H[0] - dh / 2, H[-1] + dh / 2, V[-1] + dv / 2, V[0] - dv / 2])
        contorno(ax, H, V, img, T_DETECCAO, colors=CIANO, linewidths=0.9)
        contorno(ax, H, V, img, T, colors=MAGENTA, linewidths=0.9, linestyles="--")
        ax.scatter(verts[:, ch], verts[:, cv], s=1.6, c=VERMELHO, alpha=0.45, linewidths=0)
        ax.plot([a[ch], b[ch]], [a[cv], b[cv]], color=AMARELO, lw=1.3, marker="o", ms=4,
                mfc="none", mec=AMARELO, mew=1.1)
        ax.set_facecolor("black")
        ax.set_xlim(centro[id(H)] - meia, centro[id(H)] + meia)
        ax.set_ylim(centro[id(V)] + meia, centro[id(V)] - meia)
        ax.set_aspect("equal")
        ax.set_xlabel(rh, fontsize=8)
        ax.set_ylabel(rv, fontsize=8)
        ax.set_title(tit, fontsize=9)
        ax.tick_params(labelsize=7)
    topo.supxlabel(
        "ciano: contorno de 200 UH; magenta tracejado: contorno de T; pontos vermelhos: v\u00e9rtices da "
        "isossuperf\u00edcie medida; amarelo: di\u00e2metro m\u00e1ximo do dispositivo. "
        f"Janela de cinza: 0 a {vmax:.0f} UH.", fontsize=8)

    grade = np.atleast_2d(baixo.subplots(nlin, ncol))
    baixo.suptitle("Fatias axiais (o n\u00famero \u00e9 o \u00edndice da fatia no recorte p\u00fablico, a partir de 0); "
                   "c\u00edrculo amarelo: extremo do di\u00e2metro", fontsize=9)
    for k, ax in enumerate(grade.ravel()):
        if k >= nz:
            ax.axis("off")
            continue
        img = sub[k]
        ax.imshow(img, cmap="gray", vmin=0, vmax=vmax, interpolation="nearest",
                  extent=[x[0] - dx / 2, x[-1] + dx / 2, y[-1] + dy / 2, y[0] - dy / 2])
        contorno(ax, x, y, img, T_DETECCAO, colors=CIANO, linewidths=0.6)
        contorno(ax, x, y, img, T, colors=MAGENTA, linewidths=0.6, linestyles="--")
        fatia = int(lo[0] + k)
        for p, f in ((a, desc["fatia_extremo1"]), (b, desc["fatia_extremo2"])):
            if f == fatia:
                ax.plot(p[2], p[1], marker="o", ms=5, mfc="none", mec=AMARELO, mew=1.0)
        ax.set_title(str(fatia), fontsize=6, pad=1.5)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect("equal")
    fig.savefig(caminho, dpi=150)
    plt.close(fig)


# ------------------------------------------------------------ RELATORIO ----
def texto_comp(c: dict) -> str:
    e = c["ext_mm"]
    return (f"{c['voxels']} voxels ({br(c['volume_mm3'], 1)} mm3; {br(e[0], 1)} x {br(e[1], 1)} x {br(e[2], 1)} mm "
            f"em z, y, x; fatias {c['fatias'][0]} a {c['fatias'][1]})")


def relatorio_md(descs, conjunto, cab, sufixo) -> str:
    L = [f"# VAE-001, Adendo P, item 4: inspecao descritiva -- {conjunto} ({len(descs)} calculos)", ""]
    L += cab + [""]
    L.append("Descricao apenas: numero e tamanho das componentes, posicao do diametro maximo e figura. "
             "Nenhuma estatistica e derivada destes calculos (Adendo P, item 4).")
    L.append("")
    L.append("| Calculo | Motivo | Tipo | Referencia (mm) | Dispositivo (mm) | Erro (mm) | Fracao pura (mm) | 200 UH fixos (mm) "
             "| Maximo (UH) | p95 (UH) | T (UH) | Comp. >= 200 UH | Comp. >= T |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for d in descs:
        L.append(f"| {d['id']} | {d['motivo'] or '-'} | {d['tipo']} | {br(d['d_gt'])} | {br(d['d_disp'])} | "
                 f"{br(d['e_disp'], sinal=True)} | {br(d['d_reimpl'])} | {br(d['d_fix200'])} | {d['pico_max']:.0f} | "
                 f"{d['p95']:.0f} | {d['T']:.0f} | {len(d['comp200'])} | {len(d['compT'])} |")
    L.append("")
    for d in descs:
        f, s = d["forma"], d["espacamento_mm"]
        e1, e2, dl = d["extremo1_vox"], d["extremo2_vox"], d["delta_mm"]
        L.append(f"## Calculo {d['id']}" + (f" -- {d['motivo']}" if d["motivo"] else ""))
        L.append("")
        L.append(f"- Tipo: {d['tipo']}. Recorte publico de {f[0]} x {f[1]} x {f[2]} voxels (z, y, x); "
                 f"voxel de {br(s[0], 3)} x {br(s[1], 3)} x {br(s[2], 3)} mm.")
        L.append(f"- Diametro: referencia {br(d['d_gt'])} mm; dispositivo {br(d['d_disp'])} mm (erro {br(d['e_disp'], sinal=True)}); "
                 f"reimplementacao a 0,225 x p95 {br(d['d_reimpl'])} mm ({br(d['e_reimpl'], sinal=True)}); "
                 f"reimplementacao a 200 UH fixos {br(d['d_fix200'])} mm ({br(d['e_fix200'], sinal=True)}).")
        L.append(f"- Atenuacao: maximo {d['pico_max']:.0f} UH; p95 {br(d['p95'], 1)} UH; T = {br(d['T'], 1)} UH ({d['regime']}); "
                 f"piso da mascara {d['piso']:.0f} UH" + ("; T ABAIXO DO PISO." if d["T_abaixo_piso"] else "."))
        L.append(f"- Componentes >= 200 UH: {len(d['comp200'])}. " + "; ".join(texto_comp(c) for c in d["comp200"][:6])
                 + (f"; e mais {len(d['comp200']) - 6}" if len(d["comp200"]) > 6 else "")
                 + f". Voxels >= 200 UH fora da maior: {d['vox200_fora_da_maior']}.")
        L.append(f"- Componentes >= T: {len(d['compT'])}. " + "; ".join(texto_comp(c) for c in d["compT"][:6])
                 + (f"; e mais {len(d['compT']) - 6}" if len(d["compT"]) > 6 else "") + ".")
        L.append(f"- Diametro maximo do dispositivo ({br(d['d_recalculado'])} mm): de (z {br(e1[0], 1)}; y {br(e1[1], 1)}; x {br(e1[2], 1)}) "
                 f"a (z {br(e2[0], 1)}; y {br(e2[1], 1)}; x {br(e2[2], 1)}), em voxels do recorte; fatias {d['fatia_extremo1']} e "
                 f"{d['fatia_extremo2']}; componentes do vetor: {br(dl[0], 2, True)} mm em z, {br(dl[1], 2, True)} mm em y, "
                 f"{br(dl[2], 2, True)} mm em x.")
        L.append("- Conferencia com o CSV da execucao: diametro, maximo, p95, T e componentes iguais.")
        L.append(f"- Figura: `poshoc_item4{sufixo}_calc_{d['id']:03d}.png`.")
        L.append("")
    return "\n".join(L) + "\n"


def tabela_csv(descs) -> pd.DataFrame:
    linhas = []
    for d in descs:
        r = {k: d[k] for k in ("id", "motivo", "tipo", "d_gt", "d_disp", "e_disp", "d_reimpl", "e_reimpl", "d_fix200",
                               "e_fix200", "pico_max", "p95", "T", "regime", "piso", "T_abaixo_piso")}
        r["n_comp200"] = len(d["comp200"])
        r["n_compT"] = len(d["compT"])
        for nome, cs in (("comp200", d["comp200"]), ("compT", d["compT"])):
            for i in range(3):
                c = cs[i] if i < len(cs) else None
                r[f"{nome}_{i + 1}_voxels"] = c["voxels"] if c else 0
                r[f"{nome}_{i + 1}_mm3"] = c["volume_mm3"] if c else 0.0
            r[f"{nome}_1_ext_z_mm"], r[f"{nome}_1_ext_y_mm"], r[f"{nome}_1_ext_x_mm"] = cs[0]["ext_mm"]
        r["vox200_fora_da_maior"] = d["vox200_fora_da_maior"]
        r["d_recalculado"] = d["d_recalculado"]
        for nome, e in (("extremo1", d["extremo1_vox"]), ("extremo2", d["extremo2_vox"])):
            r[f"{nome}_z_vox"], r[f"{nome}_y_vox"], r[f"{nome}_x_vox"] = e
        r["fatia_extremo1"], r["fatia_extremo2"] = d["fatia_extremo1"], d["fatia_extremo2"]
        r["delta_z_mm"], r["delta_y_mm"], r["delta_x_mm"] = d["delta_mm"]
        r["confere_com_csv"] = d["confere_com_csv"]
        linhas.append(r)
    return pd.DataFrame(linhas)


# ---------------------------------------------------------------- MAIN ----
def main():
    ap = argparse.ArgumentParser(description="VAE-001, Adendo P, item 4: inspecao descritiva dos calculos nomeados.")
    ap.add_argument("--desenv", action="store_true", help="teste nos dois calculos do DESENVOLVIMENTO (56 e 23)")
    ap.add_argument("--saida", default=None, help="pasta de saida (padrao: results/)")
    arg = ap.parse_args()
    saida = Path(arg.saida) if arg.saida else RESULTS
    saida.mkdir(parents=True, exist_ok=True)

    if arg.desenv:
        npz, csv, sufixo, conjunto, reg = (RESULTS / "poshoc_casos_desenv.npz", RESULTS / "poshoc_prevoo_desenv.csv",
                                           "_desenv", "DESENVOLVIMENTO", None)
    else:
        npz, csv, sufixo, conjunto = RESULTS / "poshoc_casos.npz", RESULTS / "poshoc_lacrado.csv", "", "LACRADO"
        if not TRAVA.exists():
            raise SystemExit("ABORTADO: results/POSHOC_EXECUTADA.json nao existe. Este script so descreve o que a "
                             "execucao registrada gravou.")
        reg = json.loads(TRAVA.read_text(encoding="utf-8"))
    for p in (npz, csv):
        if not p.exists():
            raise SystemExit(f"ABORTADO: {p.relative_to(ROOT)} nao existe.")
    h_npz, h_csv = sha256(npz), sha256(csv, texto=True)
    h_script = sha256(Path(__file__), texto=True)

    print("=" * 100)
    print(f"ADENDO P, ITEM 4 -- inspecao descritiva -- {conjunto}. O .mat NAO e lido.")
    print("=" * 100)
    print(f"  {npz.name:<28} {h_npz}")
    print(f"  {csv.name:<28} {h_csv}")
    print(f"  {Path(__file__).name:<28} {h_script}")
    if reg is not None:
        if reg.get("casos_sha256") != h_npz or reg.get("csv_sha256") != h_csv:
            raise SystemExit("ABORTADO: o NPZ ou o CSV nao conferem com results/POSHOC_EXECUTADA.json.")
        print("  conferem com o registro da execucao de", reg.get("quando"))
    print()

    z = np.load(npz)
    no_npz = sorted(int(k[3:]) for k in z.files if k.startswith("hu_"))
    if reg is not None and sorted(int(i) for i in reg["casos_ids"]) != no_npz:
        raise SystemExit("ABORTADO: os calculos do NPZ nao sao os do registro da execucao.")
    ids = ORDEM_ADENDO if set(no_npz) == set(ORDEM_ADENDO) else no_npz
    df = pd.read_csv(csv)
    df = df.set_index(df["id"].astype(int))

    descs, figuras = [], []
    for cid in ids:
        hu, sp = z[f"hu_{cid}"], z[f"sp_{cid}"]
        desc, verts, a, b = descreve(cid, hu, sp, df.loc[cid])
        descs.append(desc)
        figuras.append((desc, hu, sp, verts, a, b))
        print(f"  calculo {cid:>3}  {desc['tipo']:<10}  ref {desc['d_gt']:6.2f}  disp {desc['d_disp']:6.2f}  "
              f"erro {desc['e_disp']:+5.2f}  p95 {desc['p95']:6.0f}  T {desc['T']:5.0f}  "
              f"comp>=200: {len(desc['comp200'])}  comp>=T: {len(desc['compT'])}  confere com o CSV: sim")
    print()

    # So grava depois de TODOS os calculos conferirem com o CSV da execucao.
    cab = [f"Entradas: `results/{npz.name}` (SHA-256 `{h_npz}`) e `results/{csv.name}` (SHA-256 `{h_csv}`)"
           + (f", as da execucao registrada em {reg.get('quando')}." if reg is not None else ", do pre-voo.")
           + " O .mat nao e lido.",
           f"Script: `poshoc_item4.py` (SHA-256, fins de linha normalizados, `{h_script}`)."]
    for desc, hu, sp, verts, a, b in figuras:
        figura(desc, hu, sp, verts, a, b, conjunto, saida / f"poshoc_item4{sufixo}_calc_{desc['id']:03d}.png")
    (saida / f"poshoc_item4{sufixo}.md").write_bytes(relatorio_md(descs, conjunto, cab, sufixo).encode("utf-8"))
    (saida / f"poshoc_item4{sufixo}.csv").write_bytes(
        tabela_csv(descs).to_csv(index=False).replace("\r\n", "\n").encode("utf-8"))
    (saida / f"poshoc_item4{sufixo}.json").write_bytes((json.dumps(
        dict(conjunto=conjunto, npz=f"results/{npz.name}", npz_sha256=h_npz, csv=f"results/{csv.name}",
             csv_sha256=h_csv, script_sha256_lf=h_script, execucao=(reg or {}).get("quando"), calculos=descs),
        indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    print(f"  Salvo em {saida}: poshoc_item4{sufixo}.md, .csv, .json e {len(descs)} figuras "
          f"(poshoc_item4{sufixo}_calc_NNN.png).")
    print("  Nenhuma estatistica foi calculada.")


if __name__ == "__main__":
    main()

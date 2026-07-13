#!/usr/bin/env python3
"""
VAE-001 — FASE 2: CONJUNTO LACRADO (n=76)
=========================================

    ####################################################################
    #  ESTE SCRIPT RODA UMA VEZ. NAO EXISTE SEGUNDA CHANCE.            #
    #                                                                  #
    #  Depois de rodar, os 76 calculos deixam de ser um conjunto       #
    #  cego. Qualquer reanalise sai do CSV que ele grava -- NUNCA      #
    #  do .mat de novo.                                                #
    #                                                                  #
    #  Se este script tiver um bug, o estudo esta comprometido e nao   #
    #  ha como refazer. Por isso ele e revisado e commitado ANTES de   #
    #  ser executado, e trava-se contra execucao dupla.                #
    ####################################################################

O QUE ELE FAZ
-------------
1. RECUSA rodar sem VAE001_LACRE_ABERTO=1
2. RECUSA rodar duas vezes (arquivo de trava em results/)
3. PRE-VOO: remede os 25 de DESENVOLVIMENTO com o codigo CONGELADO e verifica
   que reproduz o desempenho declarado. Se nao reproduzir, ABORTA -- porque
   entao o codigo congelado NAO e o codigo que validamos.
4. So entao abre o lacre e mede os 76
5. CONTA os fallbacks (metodo_diametro == "centros_voxel"). Esperado: ZERO.
6. ESTRATIFICA por t_eq (espessura equivalente). O vies depende da morfologia --
   um numero global unico esconderia isso.
7. Avalia os criterios de aceite CA-1/CA-2/CA-3
8. Grava o CSV bruto + um registro de execucao com SHA-256 de tudo

POR QUE ESTRATIFICAR POR t_eq
-----------------------------
Fase 1 (n=25) mostrou:
    VOLUME   -- o erro e governado pela razao superficie/volume, nao pela
                densidade. rho(compacidade, erro) = -0,95 isolando os densos.
    DIAMETRO -- o vies depende da morfologia:
                    espiculados (t_eq < 2 mm):  -0,10 mm
                    compactos   (t_eq >= 4 mm): +0,36 mm
                    esfera lisa (fantoma PSF):  +0,73 mm  <- teto
                O vies global de +0,04 mm no conjunto de desenvolvimento e
                propriedade da MISTURA DE FORMAS daquela amostra, nao do metodo.

Reportar um vies global unico nos 76 seria enganoso.

Uso:
    # 1. leia o codigo inteiro
    # 2. commite
    # 3. rode o pre-voo sozinho primeiro:
    python fase2_lacrado.py --pre-voo
    # 4. so entao:
    VAE001_LACRE_ABERTO=1 python fase2_lacrado.py
"""
import argparse
import hashlib
import io
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from freiburg_io import carregar_freiburg          # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

MAT      = ROOT / "data" / "raw" / "ct-uroliths_matlab.mat"
RESULTS  = ROOT / "results"
TRAVA    = RESULTS / "FASE2_EXECUTADA.json"
CSV_OUT  = RESULTS / "fase2_lacrado.csv"
CSV_DEV  = RESULTS / "fase2_prevoo_desenv.csv"

# ===========================================================================
# CRITERIOS DE ACEITE — COPIADOS DO PROTOCOLO v2.0, SECAO 10
# ===========================================================================
#  Aplicaveis ao DESFECHO PRIMARIO: braco 1 (LithosRad @ 200 UH), conjunto
#  LACRADO, estrato de diametro de referencia >= 10 mm.
#
#  CA-1  PRECISAO           semi-amplitude dos LoA 95% <= 25 pontos percentuais
#                           em torno do vies medio.
#  CA-2  AUSENCIA DE        |inclinacao| da regressao de delta% sobre
#        TENDENCIA          log2(gt_vol) <= 5 pp por duplicacao de volume,
#                           OU IC 95% da inclinacao CONTENDO ZERO.
#  CA-3  ROBUSTEZ           taxa de falha de segmentacao <= 5% no estrato
#                           primario.
#  CA-4  VIES               CARACTERIZADO E REPORTADO. SEM CRITERIO DE
#                           REPROVACAO -- deliberadamente. Se |vies| > 10%, e
#                           DECLARADO nas Instrucoes de Uso como vies
#                           sistematico conhecido e quantificado.
# ===========================================================================
CA = {
    "estrato_primario_mm": 10.0,
    "CA1_semiamplitude_loa_max_pp": 25.0,
    "CA2_inclinacao_max_pp_por_dobra": 5.0,
    "CA3_taxa_falha_max_pct": 5.0,
    "CA4_limiar_declaracao_ifu_pct": 10.0,   # nao e reprovacao; e gatilho de IFU
}

# Desempenho DECLARADO na Fase 1 (n=25) e na emenda v2.1, Quadro E-3.
# O pre-voo confere contra isto. Se o codigo congelado nao reproduzir, ele NAO
# e o codigo caracterizado na emenda -- e abrir o lacre seria validar outro
# software.
PREVOO_ESPERADO = {
    "diam_vies_mm":  (+0.04, 0.06),   # (valor esperado, tolerancia)
    "diam_sd_mm":    (0.35,  0.06),
    "diam_pior_mm":  (0.76,  0.10),
    "vol_vies_pct":  (+76.0, 15.0),   # o motor de volume NAO foi alterado
}

# Estratos de MORFOLOGIA (emenda v2.1, E-7, Quadro E-6).
# t_eq = V_ref / (pi * (d_ref/2)^2), calculada SO a partir da REFERENCIA.
ESTRATOS_MORF = [
    ("espiculado",     0.0,  2.0),
    ("intermediario",  2.0,  4.0),
    ("compacto",       4.0,  np.inf),
]

# Estratos de TAMANHO (protocolo v2.0, Secao 5).
ESTRATOS_TAM = [
    ("5-10 mm",   0.0, 10.0),
    ("10-20 mm", 10.0, 20.0),
    (">20 mm",   20.0, np.inf),
]


# --------------------------------------------------------------- UTIL ----
def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 16), b""):
            h.update(bloco)
    return h.hexdigest()


def commit_lithosrad() -> str:
    """Le o commit CONGELADO do LithosRad, registrado na Fase 0."""
    p = ROOT / "protocol" / "lithosrad_commit.txt"
    if not p.exists():
        raise SystemExit(
            "ABORTADO: protocol/lithosrad_commit.txt nao existe.\n"
            "O commit congelado do LithosRad e obrigatorio para rastreabilidade."
        )
    return p.read_text(encoding="utf-8").strip().split()[0]


def commit_validacao() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "DESCONHECIDO"


def git_limpo() -> bool:
    try:
        s = subprocess.check_output(["git", "status", "--porcelain"],
                                    cwd=ROOT, text=True)
        return s.strip() == ""
    except Exception:
        return False


# --------------------------------------------------- MEDIDA (o adaptador) --
# >>> ESTA E A UNICA FUNCAO QUE FALA COM O LITHOSRAD. <<<
# Ela replica EXATAMENTE a chamada de fase1_desenvolvimento.py (funcao mede()):
#
#     cheia = np.ones(vol.array.shape, bool)
#     m = MascarasRins(esquerdo=cheia, direito=None, spacing=vol.spacing, aviso=None)
#     res = detectar_calculos(vol, m)            # <-- SEM kwargs. So os defaults.
#     return max(res.itens, key=lambda x: x.volume_mm3), len(res.itens)
#
# NAO passe hu_min/diametro_min_*/dilatacao_mm explicitamente: a Fase 1 usou os
# DEFAULTS. Se passassemos os valores "na mao" e algum default mudasse, os dois
# scripts divergiriam em silencio. O pre-voo existe para provar que nao divergem.
def medir(hu: np.ndarray, spacing: tuple) -> dict:
    """Mede UM calculo isolado (VOI em agua) com o LithosRad congelado."""
    from lithos.dicom_io import Volume
    from lithos.kidney_segmentation import MascarasRins
    from lithos.stone_detection import detectar_calculos

    vol = Volume(array=hu, spacing=spacing)
    # VOI isolado em agua: nao ha rim. A mascara cobre TODO o volume -- o limiar
    # de 200 UH ja isola o calculo (fundo ~0 UH).
    cheia = np.ones(vol.array.shape, bool)
    m = MascarasRins(esquerdo=cheia, direito=None, spacing=vol.spacing, aviso=None)

    res = detectar_calculos(vol, m)              # defaults, como na Fase 1

    if not res.itens:
        return dict(diametro_mm=np.nan, volume_mm3=0.0, hu_media=np.nan,
                    hu_max=np.nan, shi_hu=np.nan, n_voxels=0,
                    metodo_diametro="NENHUM", n_componentes=0)

    # O VOI contem UM calculo. Criterio do maior componente: VOLUME (como na
    # Fase 1), nao n_voxels. Se aparecer mais de um componente, e REGISTRADO --
    # pode indicar fragmentacao da segmentacao.
    it = max(res.itens, key=lambda x: x.volume_mm3)
    return dict(
        diametro_mm=float(it.diametro_mm),
        volume_mm3=float(it.volume_mm3),
        hu_media=None if it.hu_media is None else float(it.hu_media),
        hu_max=None if it.hu_max is None else float(it.hu_max),
        shi_hu=None if it.shi_hu is None else float(it.shi_hu),
        n_voxels=int(it.n_voxels),
        metodo_diametro=getattr(it, "metodo_diametro", "DESCONHECIDO"),
        n_componentes=len(res.itens),
    )


def linha(c: dict) -> dict:
    """Monta a linha de resultado para UM calculo, com as covariaveis de forma
    calculadas SO a partir da REFERENCIA (nunca da saida do LithosRad --
    isso seria circular)."""
    d_gt = float(c["gt_diam_mm"])
    v_gt = float(c["gt_vol_mL"]) * 1000.0            # mL -> mm3

    # espessura equivalente: V / (area do disco de diametro d)
    t_eq = v_gt / (np.pi * (d_gt / 2.0) ** 2)
    # compacidade: V / V_esfera(d)
    v_esf = (np.pi / 6.0) * d_gt ** 3
    compac = v_gt / v_esf

    m = medir(np.asarray(c["array"], np.float64), c["spacing"])

    return dict(
        id=c["id"], tipo=c["stone_type"],
        d_gt=d_gt, v_gt=v_gt, t_eq=t_eq, compac=compac,
        **m,
        e_diam_mm=m["diametro_mm"] - d_gt,
        e_vol_pct=100.0 * (m["volume_mm3"] - v_gt) / v_gt if v_gt > 0 else np.nan,
    )


def estrato_morf(t):
    for nome, lo, hi in ESTRATOS_MORF:
        if lo <= t < hi:
            return nome
    return "?"


def estrato_tam(d):
    for nome, lo, hi in ESTRATOS_TAM:
        if lo <= d < hi:
            return nome
    return "?"


def regressao_tendencia(delta_pct, gt_vol_mm3):
    """CA-2: regressao de delta% sobre log2(gt_vol), com IC 95% da inclinacao.
    Protocolo v2.0, Secoes 9.2 e 10."""
    y = np.asarray(delta_pct, float)
    v = np.asarray(gt_vol_mm3, float)
    ok = ~np.isnan(y) & ~np.isnan(v) & (v > 0)
    y, v = y[ok], v[ok]
    if len(y) < 4:
        return None
    x = np.log2(v)
    n = len(y)
    xm, ym = x.mean(), y.mean()
    sxx = float(np.sum((x - xm) ** 2))
    if sxx == 0:
        return None
    b1 = float(np.sum((x - xm) * (y - ym)) / sxx)
    b0 = float(ym - b1 * xm)
    resid = y - (b0 + b1 * x)
    s2 = float(np.sum(resid ** 2) / (n - 2))
    se = float(np.sqrt(s2 / sxx))
    tc = float(stats.t.ppf(0.975, n - 2))
    return dict(n=n, inclinacao=b1, intercepto=b0, se=se,
                ic_inf=b1 - tc * se, ic_sup=b1 + tc * se)


# ------------------------------------------------------------- PRE-VOO ----
def pre_voo() -> pd.DataFrame:
    """Remede os 25 de DESENVOLVIMENTO com o codigo congelado e confere que
    reproduz o desempenho declarado.

    Se nao reproduzir, o codigo congelado NAO e o codigo que validamos, e
    abrir o lacre seria fraude -- estariamos validando um software diferente
    daquele cuja Fase 1 foi analisada.
    """
    print("=" * 100)
    print("PRE-VOO — remedindo os 25 de DESENVOLVIMENTO com o codigo CONGELADO")
    print("=" * 100)
    print("  (o lacre NAO foi tocado)")
    print()

    linhas = [linha(c) for c in carregar_freiburg(MAT, grupo="DESENV")]
    df = pd.DataFrame(linhas)
    df["estrato"] = df["t_eq"].map(estrato_morf)
    df["tam"] = df["d_gt"].map(estrato_tam)
    df.to_csv(CSV_DEV, index=False)

    e = df["e_diam_mm"].to_numpy()
    obs = {
        "diam_vies_mm": float(np.nanmean(e)),
        "diam_sd_mm":   float(np.nanstd(e, ddof=1)),
        "diam_pior_mm": float(np.nanmax(np.abs(e))),
        "vol_vies_pct": float(np.nanmean(df["e_vol_pct"])),
    }

    print(f"{'metrica':>16} {'esperado':>12} {'tol':>7} {'obtido':>10}   ")
    print("-" * 100)
    ok = True
    for k, (esp, tol) in PREVOO_ESPERADO.items():
        v = obs[k]
        passou = abs(v - esp) <= tol
        ok &= passou
        print(f"{k:>16} {esp:>+12.2f} {tol:>7.2f} {v:>+10.2f}   "
              f"{'OK' if passou else '>>> DIVERGE <<<'}")
    print()

    # fallbacks no conjunto de desenvolvimento
    fb = df[df["metodo_diametro"] == "centros_voxel"]
    print(f"  fallbacks (centros_voxel): {len(fb)}/25", end="")
    if len(fb):
        print(f"   >>> ids {sorted(fb['id'].astype(int).tolist())}")
        print("      ATENCAO: o fallback usa OUTRO estimador (vies -0,26 mm contra")
        print("      +0,12 mm do marching cubes). Estes calculos foram medidos por")
        print("      um metodo diferente.")
    else:
        print("   (esperado)")

    multi = df[df["n_componentes"] > 1]
    print(f"  VOIs com mais de 1 componente: {len(multi)}/25", end="")
    print(f"   ids {sorted(multi['id'].astype(int).tolist())}" if len(multi) else "")
    print()

    if not ok:
        raise SystemExit(
            "\n"
            "############################################################\n"
            "#  PRE-VOO REPROVADO — ABORTADO. O LACRE NAO FOI TOCADO.   #\n"
            "#                                                          #\n"
            "#  O codigo congelado NAO reproduz o desempenho declarado  #\n"
            "#  na Fase 1. Isso significa que ele NAO e o codigo que    #\n"
            "#  analisamos.                                             #\n"
            "#                                                          #\n"
            "#  Causas possiveis:                                       #\n"
            "#    - o commit congelado esta errado                      #\n"
            "#    - a funcao medir() nao replica a chamada da Fase 1    #\n"
            "#    - algo mudou no LithosRad depois do congelamento      #\n"
            "#                                                          #\n"
            "#  RESOLVA ISSO ANTES DE ABRIR O LACRE.                    #\n"
            "############################################################\n"
        )

    print("  >>> PRE-VOO APROVADO. O codigo congelado reproduz a Fase 1.")
    print()
    return df


# --------------------------------------------------------------- FASE 2 ----
def bland_altman(x, rotulo, unidade):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) < 3:
        return None
    v, s = x.mean(), x.std(ddof=1)
    return dict(rotulo=rotulo, n=len(x), vies=v, sd=s,
                loa_inf=v - 1.96 * s, loa_sup=v + 1.96 * s,
                pior=np.abs(x).max(), unidade=unidade)


def imprime_ba(r):
    if r is None:
        print(f"  {'(n insuficiente)'}")
        return
    u = r["unidade"]
    print(f"  n={r['n']:>3}   vies {r['vies']:>+7.2f} {u}   sd {r['sd']:>6.2f}   "
          f"LoA95 [{r['loa_inf']:>+7.2f}, {r['loa_sup']:>+7.2f}] {u}   "
          f"pior {r['pior']:>6.2f} {u}")


def avalia_ca(nome, valor, limite, unidade):
    if limite is None:
        print(f"  {nome}: {valor:+.2f} {unidade}   >>> LIMITE NAO PREENCHIDO "
              f"(copie do protocolo)")
        return None
    passou = abs(valor) <= limite
    print(f"  {nome}: {valor:+.2f} {unidade}   limite {limite:.2f}   "
          f"{'APROVADO' if passou else 'REPROVADO'}")
    return passou


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pre-voo", action="store_true",
                    help="roda SO o pre-voo (nao abre o lacre) e sai")
    args = ap.parse_args()

    # ---- guarda 1: trava de execucao unica ------------------------------
    if TRAVA.exists() and not args.pre_voo:
        reg = json.loads(TRAVA.read_text(encoding="utf-8"))
        raise SystemExit(
            "\n"
            "############################################################\n"
            "#  A FASE 2 JA FOI EXECUTADA. ABORTADO.                    #\n"
            "############################################################\n"
            f"\n  quando : {reg.get('quando')}\n"
            f"  csv    : {reg.get('csv')}\n"
            f"  sha256 : {reg.get('csv_sha256')}\n"
            "\n"
            "  Os 76 nao sao mais um conjunto cego. Rodar de novo nao os\n"
            "  torna cegos de novo -- so produziria a ILUSAO de uma segunda\n"
            "  medida independente.\n"
            "\n"
            "  Qualquer reanalise deve ler o CSV acima. NUNCA o .mat.\n"
            f"\n  Se precisa MESMO refazer (bug no script), apague {TRAVA.name}\n"
            "  DE PROPOSITO, e registre por escrito o motivo no protocolo.\n"
        )

    # ---- pre-voo (sempre, e nao toca no lacre) ---------------------------
    df_dev = pre_voo()

    if args.pre_voo:
        print("=" * 100)
        print("MODO --pre-voo: parando aqui. O LACRE NAO FOI TOCADO.")
        print("=" * 100)
        print(f"\n  Salvo: {CSV_DEV.relative_to(ROOT)}")
        print("\n  Para abrir o lacre:")
        print("      VAE001_LACRE_ABERTO=1 python fase2_lacrado.py")
        return

    # ---- guarda 2: o lacre ----------------------------------------------
    if os.environ.get("VAE001_LACRE_ABERTO") != "1":
        raise SystemExit(
            "\n  O lacre esta FECHADO.\n"
            "\n  Para abrir (e isto e IRREVERSIVEL):\n"
            "      PowerShell:  $env:VAE001_LACRE_ABERTO=1; python fase2_lacrado.py\n"
            "      bash:        VAE001_LACRE_ABERTO=1 python fase2_lacrado.py\n"
        )

    # ---- guarda 3: arvore limpa -----------------------------------------
    if not git_limpo():
        print()
        print("  ################################################################")
        print("  #  AVISO: a arvore do git NAO esta limpa.                      #")
        print("  #                                                              #")
        print("  #  O resultado da Fase 2 deve ser rastreavel a um commit       #")
        print("  #  exato. Commite tudo ANTES de rodar.                         #")
        print("  ################################################################")
        print()
        if input("  Rodar assim mesmo? (digite ABRIR O LACRE) > ") != "ABRIR O LACRE":
            raise SystemExit("  Abortado. Commite e rode de novo.")

    c_lithos = commit_lithosrad()
    c_valid  = commit_validacao()

    print()
    print("#" * 100)
    print("#  ABRINDO O LACRE — 76 CALCULOS. EXECUCAO UNICA.")
    print("#" * 100)
    print(f"  LithosRad congelado : {c_lithos}")
    print(f"  Validacao (HEAD)    : {c_valid}")
    print(f"  Quando              : {datetime.now(timezone.utc).isoformat()}")
    print()

    linhas = [linha(c) for c in carregar_freiburg(MAT, grupo="LACRADO")]
    df = pd.DataFrame(linhas)
    df["estrato"] = df["t_eq"].map(estrato_morf)
    df["tam"] = df["d_gt"].map(estrato_tam)
    df.to_csv(CSV_OUT, index=False)

    # ================================================================== 1 ==
    print("=" * 100)
    print("1. INTEGRIDADE DA EXECUCAO")
    print("=" * 100)
    print(f"  calculos medidos: {len(df)}   (esperado 76)")

    fb = df[df["metodo_diametro"] == "centros_voxel"]
    print(f"\n  FALLBACKS do diametro (centros_voxel): {len(fb)}/{len(df)}")
    if len(fb):
        print(f"    ids: {sorted(fb['id'].astype(int).tolist())}")
        print("    >>> ATENCAO: estes calculos foram medidos por OUTRO estimador.")
        print("    >>> marching cubes: vies +0,12 mm | centros de voxel: vies -0,26 mm")
        print("    >>> Isto DEVE ser declarado no relatorio. Considere reporta-los")
        print("    >>> separadamente ou exclui-los, com justificativa.")
    else:
        print("    (nenhum — como esperado)")

    falhas = df[(df["n_voxels"] == 0) | df["diametro_mm"].isna()]
    print(f"\n  FALHAS de segmentacao: {len(falhas)}/{len(df)}")
    if len(falhas):
        print(f"    ids: {sorted(falhas['id'].astype(int).tolist())}")

    multi = df[df["n_componentes"] > 1]
    print(f"\n  VOIs com mais de 1 componente: {len(multi)}/{len(df)}")
    if len(multi):
        print(f"    ids: {sorted(multi['id'].astype(int).tolist())}")
        print("    (fragmentacao da segmentacao — o maior componente foi usado)")
    print()

    # ================================================================== 2 ==
    print("=" * 100)
    print("2. DIAMETRO — GLOBAL e ESTRATIFICADO POR MORFOLOGIA")
    print("=" * 100)
    print("  Global:")
    imprime_ba(bland_altman(df["e_diam_mm"], "diametro", "mm"))
    print()
    print("  >>> O vies GLOBAL depende da mistura de formas desta amostra.")
    print("  >>> A leitura correta e a ESTRATIFICADA:")
    print()
    for nome, lo, hi in ESTRATOS_MORF:
        sub = df[df["estrato"] == nome]
        rot = f"{nome} ({lo:.0f} <= t_eq < {hi:.0f} mm)" if np.isfinite(hi) \
              else f"{nome} (t_eq >= {lo:.0f} mm)"
        print(f"  {rot}")
        imprime_ba(bland_altman(sub["e_diam_mm"], nome, "mm"))
        print()

    ok = df["e_diam_mm"].notna()
    if ok.sum() >= 5:
        r, p = spearmanr(df.loc[ok, "t_eq"], df.loc[ok, "e_diam_mm"])
        print(f"  rho(t_eq, erro do diametro) = {r:+.3f}   p = {p:.4f}")
        print(f"    Fase 1 (n=25) deu +0,59 (p=0,0018). Replica?")
        print()

    # ================================================================== 3 ==
    print("=" * 100)
    print("3. VOLUME — GLOBAL e ESTRATIFICADO")
    print("=" * 100)
    print("  Global:")
    imprime_ba(bland_altman(df["e_vol_pct"], "volume", "%"))
    print()
    for nome, lo, hi in ESTRATOS_MORF:
        sub = df[df["estrato"] == nome]
        print(f"  {nome}  (n={len(sub)})")
        imprime_ba(bland_altman(sub["e_vol_pct"], nome, "%"))
        print()

    if ok.sum() >= 5:
        okv = df["e_vol_pct"].notna()
        r, p = spearmanr(df.loc[okv, "compac"], df.loc[okv, "e_vol_pct"])
        print(f"  rho(compacidade, erro do volume) = {r:+.3f}   p = {p:.4f}")
        print("    Fase 1 (n=25) deu -0,74 (p<0,0001). Replica?")
        print()
        dens = df[okv & (df["hu_max"] > 1600)]
        if len(dens) >= 5:
            r2, p2 = spearmanr(dens["compac"], dens["e_vol_pct"])
            print(f"  rho(compacidade, erro) SO nos densos (huMax>1600, n={len(dens)}) "
                  f"= {r2:+.3f}   p = {p2:.4f}")
            print("    Fase 1 deu -0,95 (p=0,0003). Este e o CONTROLE que separa")
            print("    forma de densidade. Se replicar, o achado esta confirmado.")
            print()

    # ================================================================== 4 ==
    print("=" * 100)
    print("4. SHI — a redundancia com o pico replica?")
    print("=" * 100)
    s = df[df["shi_hu"].notna() & df["hu_max"].notna()]
    if len(s) >= 6:
        x = (s["hu_max"] - 200.0).to_numpy()
        y = s["shi_hu"].to_numpy()
        k = float(np.sum(x * y) / np.sum(x * x))
        r2 = 1.0 - np.sum((y - k * x) ** 2) / np.sum((y - y.mean()) ** 2)
        print(f"  SHI ~ k x (pico - 200)     n = {len(s)}")
        print(f"    k  = {k:.3f}     (Fase 1: 0,283;  1/sqrt(12) = 0,2887)")
        print(f"    r2 = {r2:.4f}    (Fase 1: 0,968)")
        print()
        print("  Se k continuar em ~0,28 e o r2 em ~0,97, o SHI e a rampa de volume")
        print("  parcial -- e a conclusao da Fase 1 esta confirmada em n=101.")
    print()

    # ================================================================== 5 ==
    print("=" * 100)
    print("5. CRITERIOS DE ACEITE  (protocolo v2.0, Secao 10)")
    print("=" * 100)
    prim = df[df["d_gt"] >= CA["estrato_primario_mm"]]
    fal_p = prim[(prim["n_voxels"] == 0) | prim["diametro_mm"].isna()]
    val_p = prim[~prim.index.isin(fal_p.index)]
    print(f"  Desfecho primario: braco 1 (LithosRad @ 200 UH), conjunto LACRADO,")
    print(f"  estrato de diametro de referencia >= {CA['estrato_primario_mm']:.0f} mm.")
    print(f"    n no estrato : {len(prim)}   (protocolo previa 43)")
    print(f"    falhas       : {len(fal_p)}   (excluidas do Bland-Altman)")
    print(f"    n analisavel : {len(val_p)}")
    print()

    ba = bland_altman(val_p["e_vol_pct"], "vol", "%")

    # ---- CA-1 : PRECISAO -------------------------------------------------
    print("  " + "-" * 96)
    print("  CA-1  PRECISAO")
    print("        semi-amplitude dos LoA 95% <= "
          f"{CA['CA1_semiamplitude_loa_max_pp']:.0f} pontos percentuais")
    print("  " + "-" * 96)
    ca1 = None
    if ba:
        imprime_ba(ba)
        semi = 1.96 * ba["sd"]
        ca1 = semi <= CA["CA1_semiamplitude_loa_max_pp"]
        print(f"    semi-amplitude = 1,96 x {ba['sd']:.2f} = {semi:.2f} pp")
        print(f"    limite         = {CA['CA1_semiamplitude_loa_max_pp']:.2f} pp")
        print(f"    >>> {'APROVADO' if ca1 else 'REPROVADO'}")
    print()

    # ---- CA-2 : AUSENCIA DE TENDENCIA ------------------------------------
    print("  " + "-" * 96)
    print("  CA-2  AUSENCIA DE TENDENCIA PROPORCIONAL")
    print("        |inclinacao| da regressao de delta% sobre log2(gt_vol) <= "
          f"{CA['CA2_inclinacao_max_pp_por_dobra']:.0f} pp/dobra")
    print("        OU  IC 95% da inclinacao CONTENDO ZERO")
    print("  " + "-" * 96)
    ca2 = None
    reg = regressao_tendencia(val_p["e_vol_pct"], val_p["v_gt"])
    if reg:
        contem_zero = reg["ic_inf"] <= 0.0 <= reg["ic_sup"]
        abaixo = abs(reg["inclinacao"]) <= CA["CA2_inclinacao_max_pp_por_dobra"]
        ca2 = abaixo or contem_zero
        print(f"    inclinacao = {reg['inclinacao']:+.2f} pp por duplicacao de volume")
        print(f"    IC 95%     = [{reg['ic_inf']:+.2f}, {reg['ic_sup']:+.2f}]")
        print(f"    |b1| <= {CA['CA2_inclinacao_max_pp_por_dobra']:.0f} ? "
              f"{'sim' if abaixo else 'NAO'}      IC contem zero ? "
              f"{'sim' if contem_zero else 'NAO'}")
        print(f"    >>> {'APROVADO' if ca2 else 'REPROVADO'}")
    else:
        print("    (n insuficiente)")
    print()

    # ---- CA-3 : ROBUSTEZ -------------------------------------------------
    print("  " + "-" * 96)
    print("  CA-3  ROBUSTEZ")
    print(f"        taxa de falha de segmentacao <= "
          f"{CA['CA3_taxa_falha_max_pct']:.0f}% no estrato primario")
    print("  " + "-" * 96)
    taxa = 100.0 * len(fal_p) / max(len(prim), 1)
    ca3 = taxa <= CA["CA3_taxa_falha_max_pct"]
    print(f"    falhas = {len(fal_p)}/{len(prim)} = {taxa:.1f}%")
    print(f"    limite = {CA['CA3_taxa_falha_max_pct']:.1f}%")
    print(f"    >>> {'APROVADO' if ca3 else 'REPROVADO'}")
    print()

    # ---- CA-4 : VIES (sem reprovacao) ------------------------------------
    print("  " + "-" * 96)
    print("  CA-4  VIES")
    print("        CARACTERIZADO E REPORTADO. Sem criterio de reprovacao.")
    print("  " + "-" * 96)
    if ba:
        print(f"    vies = {ba['vies']:+.2f}%")
        lim = CA["CA4_limiar_declaracao_ifu_pct"]
        if abs(ba["vies"]) > lim:
            print(f"    |vies| > {lim:.0f}%  -->  DEVE SER DECLARADO nas Instrucoes")
            print(f"    de Uso como vies sistematico conhecido e quantificado do")
            print(f"    metodo de contagem de voxels a 200 UH. (v2.0, Secao 10, CA-4)")
        else:
            print(f"    |vies| <= {lim:.0f}%  -->  declaracao em IFU nao exigida")
    print()

    # ---- resumo ----------------------------------------------------------
    print("  " + "=" * 96)
    print(f"  CA-1 {'APROVADO' if ca1 else 'REPROVADO' if ca1 is not None else '?'}"
          f"   |   CA-2 {'APROVADO' if ca2 else 'REPROVADO' if ca2 is not None else '?'}"
          f"   |   CA-3 {'APROVADO' if ca3 else 'REPROVADO'}"
          f"   |   CA-4 caracterizado")
    print("  " + "=" * 96)
    print()
    print("  LEMBRE (emenda v2.1, E-5.5): a REPROVACAO do CA-1 foi ANTECIPADA e")
    print("  registrada ANTES da abertura do lacre. Ela e um RESULTADO VALIDO do")
    print("  estudo -- a caracterizacao do vies por S/V --, e nao uma falha de")
    print("  execucao. NAO ajuste nada. O ajuste pos-desfecho DESCARTA o estudo")
    print("  como validacao (v2.0, Secao 12).")
    print()

    # ---- desfecho secundario: DIAMETRO -----------------------------------
    print("=" * 100)
    print("5b. DESFECHO SECUNDARIO — DIAMETRO (v2.0, Secao 8.2)")
    print("=" * 100)
    print("  Estrato primario, global:")
    imprime_ba(bland_altman(val_p["e_diam_mm"], "diam", "mm"))
    print()
    print("  Referencia da Fase 1 (emenda v2.1, Quadro E-3):")
    print("    vies +0,04 mm | sd 0,35 | pior 0,76 | LoA +-0,68 | rho(pico) +0,04")
    print()

    # ================================================================== 6 ==
    print("=" * 100)
    print("6. TABELA COMPLETA (76)")
    print("=" * 100)
    cols = ["id", "tipo", "tam", "estrato", "d_gt", "diametro_mm", "e_diam_mm",
            "t_eq", "v_gt", "volume_mm3", "e_vol_pct", "hu_max", "shi_hu",
            "metodo_diametro"]
    print(df[cols].to_string(index=False, float_format=lambda x: f"{x:9.2f}"))
    print()

    # ---- registro de execucao -------------------------------------------
    reg = {
        "quando":             datetime.now(timezone.utc).isoformat(),
        "commit_lithosrad":   c_lithos,
        "commit_validacao":   c_valid,
        "git_limpo":          git_limpo(),
        "n_calculos":         int(len(df)),
        "n_fallbacks":        int(len(fb)),
        "ids_fallback":       sorted(fb["id"].astype(int).tolist()),
        "n_falhas":           int(len(falhas)),
        "ids_falha":          sorted(falhas["id"].astype(int).tolist()),
        "csv":                str(CSV_OUT.relative_to(ROOT)),
        "csv_sha256":         sha256(CSV_OUT),
        "csv_prevoo":         str(CSV_DEV.relative_to(ROOT)),
        "csv_prevoo_sha256":  sha256(CSV_DEV),
        "mat_sha256":         sha256(MAT),
        "criterios_aceite":   CA,
        "prevoo_esperado":    {k: list(v) for k, v in PREVOO_ESPERADO.items()},
    }
    TRAVA.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=" * 100)
    print("EXECUCAO REGISTRADA")
    print("=" * 100)
    print(f"  {CSV_OUT.relative_to(ROOT)}")
    print(f"    sha256  {reg['csv_sha256']}")
    print(f"  {TRAVA.relative_to(ROOT)}")
    print()
    print("  >>> O LACRE ESTA ABERTO. Nao ha volta.")
    print("  >>> Toda reanalise sai do CSV. NUNCA do .mat.")
    print("  >>> COMMITE o CSV e a trava agora.")
    print()


if __name__ == "__main__":
    main()

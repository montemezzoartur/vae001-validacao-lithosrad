#!/usr/bin/env python3
"""
VAE-001 -- ADENDO P: ANALISES POS-HOC SOBRE AS IMAGENS DO CONJUNTO LACRADO (n=76)
=================================================================================

    ####################################################################
    #  ESTE SCRIPT LE AS IMAGENS DOS 76 CALCULOS LACRADOS PELA SEGUNDA #
    #  VEZ. O Protocolo v2.0 (Secao 5) dizia que o acesso seria unico. #
    #  Este segundo acesso e um DESVIO DECLARADO, autorizado pelo      #
    #  Adendo P, assinado ANTES desta execucao, e restrito a lista     #
    #  fechada que o Adendo P enumera.                                 #
    #                                                                  #
    #  Ele NAO contem nem chama o LithosRad. O dispositivo congelado   #
    #  NAO e reexecutado. Nenhum parametro do dispositivo muda. O      #
    #  desfecho pre-especificado (results/fase2_lacrado.csv) nao e     #
    #  alterado -- so e LIDO, para comparacao.                         #
    #                                                                  #
    #  Roda UMA vez. Trava-se contra execucao dupla.                   #
    ####################################################################

O QUE ELE FAZ
-------------
1. RECUSA rodar duas vezes (trava em results/POSHOC_EXECUTADA.json).
2. Confere o SHA-256 das entradas: o .mat publico (contra o protocolo v2.0) e
   os dois CSV da execucao unica do dispositivo (contra FASE2_EXECUTADA.json).
3. PRE-VOO nos 25 de DESENVOLVIMENTO: a reimplementacao depositada, inalterada,
   tem de reproduzir results/fase1_diam_pico.csv, e a emulacao do dispositivo
   tem de reproduzir results/fase2_prevoo_desenv.csv (diametro, maximo e numero
   de voxels), em 25 de 25. Se nao reproduzir, ABORTA sem tocar no lacrado:
   corrige-se o AMBIENTE, nunca o codigo.
4. So abre o lacrado com VAE001_LACRE_ABERTO=1, com o Adendo P ASSINADO em
   protocol/, com os SHA-256 dos scripts iguais aos que o Adendo P registra, e
   com tudo isso commitado e enviado ao repositorio remoto.
5. Mede os 76 (itens 1 a 3 do Adendo P): emulacao do dispositivo; p95, maximo e
   limiar por calculo; reimplementacao a 0,225 x p95 e a 200 UH fixos.
6. Copia as imagens dos 8 calculos nomeados no item 4 do Adendo P.
7. Grava o CSV, o arquivo de casos e o registro de execucao, com SHA-256.

NAO calcula estatistica: isso e do poshoc_analise.py, que le so o CSV gravado aqui.

AS TRES MEDIDAS (todas com marching cubes e diametro maximo sobre o fecho convexo)
----------------------------------------------------------------------------------
  d_emul    EMULACAO DO DISPOSITIVO: zera fora da maior componente >= 200 UH e
            extrai a isossuperficie em T = 0,225 x p95. E a funcao do Adendo R-17
            (emula_r17.py), que reproduziu o dispositivo em 25 de 25 no
            desenvolvimento.
  d_reimpl  REIMPLEMENTACAO DE REFERENCIA, 0,225 x p95: zera fora da maior
            componente >= T. E fase1_diam_pico.d_mc, importada sem alteracao.
  d_fix200  REIMPLEMENTACAO DE REFERENCIA, 200 UH fixos: a mesma d_mc com T = 200.

Uso:
    python poshoc_lacrado.py --pre-voo            # so o pre-voo; NAO abre o lacrado
    PowerShell:  $env:VAE001_LACRE_ABERTO=1; python poshoc_lacrado.py
    bash:        VAE001_LACRE_ABERTO=1 python poshoc_lacrado.py

Requer: numpy, pandas, scipy, scikit-image.
"""
import argparse
import difflib
import hashlib
import inspect
import io
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import skimage
from scipy import ndimage as ndi
from scipy.spatial import ConvexHull
from scipy.spatial.distance import pdist
from skimage.measure import marching_cubes

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
import fase1_diam_pico as F                 # noqa: E402  reimplementacao depositada (main() protegido)
from freiburg_io import carregar_freiburg   # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

MAT          = ROOT / "data" / "raw" / "ct-uroliths_matlab.mat"
RESULTS      = ROOT / "results"
PROTOCOL     = ROOT / "protocol"
TRAVA        = RESULTS / "POSHOC_EXECUTADA.json"
REG_FASE2    = RESULTS / "FASE2_EXECUTADA.json"
CSV_DISP     = RESULTS / "fase2_lacrado.csv"          # dispositivo congelado, lacrado (so leitura)
CSV_DISP_DEV = RESULTS / "fase2_prevoo_desenv.csv"    # dispositivo congelado, desenvolvimento (so leitura)
CSV_PICO     = RESULTS / "fase1_diam_pico.csv"        # reimplementacao, desenvolvimento (so leitura)
ADENDO_P     = PROTOCOL / "ADENDO_VAE-001_P_POSHOC_v1.0_assinado.pdf"
ADENDO_P_SHA = PROTOCOL / "adendo_p_sha256.txt"       # opcional: SHA-256 do PDF assinado
HASHES_P     = PROTOCOL / "adendo_p_scripts_sha256.txt"

NOME_CSV, NOME_CSV_DEV = "poshoc_lacrado.csv", "poshoc_prevoo_desenv.csv"
NOME_NPZ, NOME_NPZ_DEV = "poshoc_casos.npz", "poshoc_casos_desenv.npz"

# SHA-256 do arquivo publico, registrado no Protocolo v2.0 e em FASE2_EXECUTADA.json
SHA_MAT_PROTOCOLO = "d8184b37eb6a8fa4aa4affd249787068d5e77f19388323b8e99736c99313ec87"

F_ADOTADO  = 0.225      # fracao do p95: a regra congelada (Emenda v2.1, Quadro E-2)
T_DETECCAO = 200.0      # UH: limiar de deteccao e limiar fixo de comparacao
TOL        = 1e-6       # mm: tolerancia para "identico" (a mesma do emula_r17.py)

# Item 4 do Adendo P: calculos nomeados ANTES da execucao.
#   29, 83, 91  |erro| > 1 mm          41, 88  estruvita
#   100         componentes multiplos (como o 83)
#   28, 3       trocas de categoria a 10 mm e a 5 mm
CASOS_LACRADO = [3, 28, 29, 41, 83, 88, 91, 100]
# Desenvolvimento: menor e maior p95 dos 25 (so para ilustrar a regra; irrestrito).
CASOS_DESENV = [56, 23]

# Arquivos cujo SHA-256 (fins de linha normalizados) o Adendo P registra.
ARQUIVOS_COM_HASH = ["poshoc_lacrado.py", "poshoc_analise.py",
                     "fase1_diam_pico.py", "src/freiburg_io.py"]


# --------------------------------------------------------------- UTIL ----
def sha256_bruto(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 16), b""):
            h.update(bloco)
    return h.hexdigest()


def sha256_lf(p: Path) -> str:
    """SHA-256 do conteudo com fins de linha normalizados para LF: o mesmo
    arquivo de texto da o mesmo valor no Windows (CRLF) e no Linux (LF)."""
    return hashlib.sha256(Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def sha256_crlf(p: Path) -> str:
    """SHA-256 do conteudo com fins de linha CRLF (como o Windows gravou os CSV
    da Fase 2, cujos valores registrados se referem a essa forma)."""
    b = Path(p).read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return hashlib.sha256(b).hexdigest()


def grava_csv(df: pd.DataFrame, caminho: Path) -> None:
    """Grava com LF em qualquer sistema, para o SHA-256 nao depender dele."""
    txt = df.to_csv(index=False).replace("\r\n", "\n")
    Path(caminho).write_bytes(txt.encode("utf-8"))


def git(*args):
    """Saida de um comando git, ou None se falhar (inclui codigo de saida != 0)."""
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True,
                                       stderr=subprocess.STDOUT).strip()
    except Exception:
        return None


# ---------------------------------------------- EMULACAO DO DISPOSITIVO ----
# Copia de emula_r17.d_mc_dispositivo (Adendo R-17). Difere de F.d_mc em UMA
# linha: a mascara e a maior componente >= 200 UH (limiar de deteccao, como o
# dispositivo), e nao >= T. O diff abaixo e conferido a cada execucao.
def d_mc_dispositivo(hu, T, sp):
    """Diametro pela isosuperficie (marching cubes), no maior componente.
    NOTA: usa np.pad para garantir borda de zeros -- sem isso, um componente
    encostado no limite do volume nao fecha a isosuperficie e mede 0."""
    m = F.maior_comp(hu >= 200.0)
    if m is None or m.sum() < 1:
        return np.nan
    idx = np.argwhere(m)
    lo = np.maximum(idx.min(0) - 2, 0)
    hi = np.minimum(idx.max(0) + 3, np.array(hu.shape))
    sl = tuple(slice(a, b) for a, b in zip(lo, hi))
    sub = np.where(m[sl], hu[sl], 0.0).astype(np.float32)
    sub = np.pad(sub, 1, mode="constant", constant_values=0.0)   # ACHADO #1
    try:
        v, _, _, _ = marching_cubes(sub, level=T, spacing=sp)
    except Exception:
        return np.nan
    if len(v) < 2:
        return np.nan
    if len(v) < 4:
        return float(pdist(v).max())
    return float(pdist(v[ConvexHull(v).vertices]).max())


def diff_emulacao():
    """Linhas que diferem entre F.d_mc (depositada) e d_mc_dispositivo."""
    a = inspect.getsource(F.d_mc).replace("def d_mc(", "def FUNC(").replace("maior_comp(", "F.maior_comp(")
    b = inspect.getsource(d_mc_dispositivo).replace("def d_mc_dispositivo(", "def FUNC(")
    return [l.rstrip() for l in difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=0)
            if l[:1] in "+-" and l[:3] not in ("+++", "---")]


DIFF_ESPERADO = ["-    m = F.maior_comp(hu >= T)", "+    m = F.maior_comp(hu >= 200.0)"]


# -------------------------------------------------------------- MEDIDA ----
def mede(c: dict) -> dict:
    """As tres medidas e as grandezas de imagem de UM calculo. E a MESMA funcao
    para o desenvolvimento (pre-voo) e para o lacrado."""
    hu = np.asarray(c["array"], np.float64)
    sp = c["spacing"]
    d_gt = c["gt_diam_mm"]

    rot, n = ndi.label(hu >= T_DETECCAO, structure=F.CONN)
    tam = np.sort(np.bincount(rot.ravel())[1:])[::-1] if n else np.array([], int)

    p95 = F.pico(hu, "p95")       # percentil 95 da maior componente >= 200 UH
    pmax = F.pico(hu, "max")      # maximo da mesma componente
    T = F_ADOTADO * p95

    pos = hu[hu > 0]
    piso = float(pos.min()) if pos.size else np.nan     # menor valor nao nulo: piso da mascara publica
    mT = F.maior_comp(hu >= T)

    d_emul = d_mc_dispositivo(hu, T, sp)
    d_reimpl = F.d_mc(hu, T, sp)
    d_fix200 = F.d_mc(hu, T_DETECCAO, sp)

    return dict(
        id=int(c["id"]), tipo=c["stone_type"], d_gt=d_gt,
        n_comp200=int(n),
        vox_comp200=int(tam[0]) if n >= 1 else 0,
        vox_comp200_2=int(tam[1]) if n >= 2 else 0,
        pico_max=pmax, p95=p95, T=T,
        piso=piso, T_abaixo_piso=bool(T < piso),
        vox_compT=int(mT.sum()) if mT is not None else 0,
        d_emul=d_emul, d_reimpl=d_reimpl, d_fix200=d_fix200,
        e_emul=d_emul - d_gt, e_reimpl=d_reimpl - d_gt, e_fix200=d_fix200 - d_gt,
    )


def junta_dispositivo(df: pd.DataFrame, csv_disp: Path) -> pd.DataFrame:
    """Acrescenta as saidas do DISPOSITIVO CONGELADO (lidas do CSV da execucao
    unica) e as tres conferencias da emulacao contra ele."""
    disp = pd.read_csv(csv_disp)
    assert sorted(disp["id"].astype(int)) == sorted(df["id"]), "ids diferem do CSV do dispositivo"
    disp = disp.set_index(disp["id"].astype(int))
    out = df.copy()
    ids = out["id"]
    assert np.allclose(disp.loc[ids, "d_gt"].to_numpy(), out["d_gt"].to_numpy(), atol=1e-9, rtol=0), \
        "d_gt difere do CSV do dispositivo"
    out["d_disp"] = disp.loc[ids, "diametro_mm"].to_numpy()
    out["e_disp"] = disp.loc[ids, "e_diam_mm"].to_numpy()
    out["hu_max_disp"] = disp.loc[ids, "hu_max"].to_numpy()
    out["n_voxels_disp"] = disp.loc[ids, "n_voxels"].to_numpy().astype(int)
    out["n_componentes_disp"] = disp.loc[ids, "n_componentes"].to_numpy().astype(int)
    out["dif_emul_disp"] = out["d_emul"] - out["d_disp"]
    out["confere_diam"] = out["dif_emul_disp"].abs() < TOL
    out["confere_hu_max"] = (out["pico_max"] - out["hu_max_disp"]).abs() < TOL
    out["confere_n_voxels"] = out["vox_comp200"] == out["n_voxels_disp"]
    return out


def guarda_casos(calculos: list, ids: list, caminho: Path) -> list:
    """Copia a imagem INTEIRA dos calculos nomeados (o recorte publico, como
    esta no .mat) para um .npz, para inspecao descritiva e figura. Depois disto
    nada mais precisa ser lido do .mat para esses calculos."""
    por_id = {int(c["id"]): c for c in calculos}
    faltam = [i for i in ids if i not in por_id]
    assert not faltam, f"calculos nomeados ausentes do grupo: {faltam}"
    blocos = {}
    for i in ids:
        a = np.asarray(por_id[i]["array"])
        inteiro = bool(np.all(a == np.round(a))) and a.min() >= -32768 and a.max() <= 32767
        blocos[f"hu_{i}"] = a.astype(np.int16) if inteiro else a.astype(np.float64)
        blocos[f"sp_{i}"] = np.asarray(por_id[i]["spacing"], np.float64)
    np.savez_compressed(caminho, **blocos)
    return ids


# -------------------------------------------------------------- GUARDAS ----
def confere_entradas() -> dict:
    """SHA-256 do .mat e dos dois CSV da execucao unica do dispositivo."""
    reg2 = json.loads(REG_FASE2.read_text(encoding="utf-8"))
    h_mat = sha256_bruto(MAT)
    ok_mat = h_mat == SHA_MAT_PROTOCOLO == reg2.get("mat_sha256")

    def ok_csv(p, esperado):   # o valor registrado refere-se ao arquivo com CRLF
        return esperado in (sha256_bruto(p), sha256_crlf(p))

    ok_lac = ok_csv(CSV_DISP, reg2.get("csv_sha256"))
    ok_dev = ok_csv(CSV_DISP_DEV, reg2.get("csv_prevoo_sha256"))

    print("=" * 100)
    print("ENTRADAS -- SHA-256")
    print("=" * 100)
    print(f"  {MAT.name:<28} {h_mat}   {'OK (protocolo v2.0)' if ok_mat else '>>> NAO CONFERE <<<'}")
    print(f"  {CSV_DISP.name:<28} {reg2.get('csv_sha256')}   {'OK' if ok_lac else '>>> NAO CONFERE <<<'}")
    print(f"  {CSV_DISP_DEV.name:<28} {reg2.get('csv_prevoo_sha256')}   {'OK' if ok_dev else '>>> NAO CONFERE <<<'}")
    print()
    if not (ok_mat and ok_lac and ok_dev):
        raise SystemExit("ABORTADO: uma entrada nao confere com o SHA-256 registrado. O lacrado NAO foi tocado.")
    return dict(mat_sha256=h_mat, fase2_lacrado_csv_sha256=reg2.get("csv_sha256"),
                fase2_prevoo_csv_sha256=reg2.get("csv_prevoo_sha256"),
                fase2_quando=reg2.get("quando"), commit_lithosrad=reg2.get("commit_lithosrad"))


def pre_voo(saida: Path, gravar: bool):
    """Mede os 25 de DESENVOLVIMENTO com as MESMAS funcoes e confere que este
    ambiente reproduz o que esta depositado. NAO toca no lacrado.

    gravar=True  (modo --pre-voo): grava o CSV e os casos do desenvolvimento.
    gravar=False (execucao): NAO regrava -- os arquivos ja estao commitados;
                 so informa se o CSV recalculado e igual ao commitado."""
    print("=" * 100)
    print("PRE-VOO -- 25 calculos de DESENVOLVIMENTO (o lacrado NAO e tocado)")
    print("=" * 100)

    dif = diff_emulacao()
    print("  diferenca entre d_mc (depositada) e d_mc_dispositivo:")
    for l in dif:
        print("     ", l)
    ok_diff = dif == DIFF_ESPERADO
    print(f"  so a mascara muda: {'OK' if ok_diff else '>>> NAO -- o codigo divergiu <<<'}")
    print()

    calculos = carregar_freiburg(MAT, grupo="DESENV")     # NUNCA 'LACRADO' aqui
    df = junta_dispositivo(pd.DataFrame([mede(c) for c in calculos]), CSV_DISP_DEV)

    ref = pd.read_csv(CSV_PICO)
    ref = ref.set_index(ref["id"].astype(int))
    d = df.set_index("id")
    assert set(d.index) == set(ref.index) and len(d) == 25, "ids do desenvolvimento nao conferem"
    confs = {
        "p95                          x fase1_diam_pico.csv":   (d["p95"] - ref.loc[d.index, "pico_p95"]).abs() < TOL,
        "maximo                       x fase1_diam_pico.csv":   (d["pico_max"] - ref.loc[d.index, "pico_max"]).abs() < TOL,
        "reimplementacao 0,225 x p95  x fase1_diam_pico.csv":   (d["d_reimpl"] - ref.loc[d.index, "p95_0.225"]).abs() < TOL,
        "reimplementacao 200 UH fixos x fase1_diam_pico.csv":   (d["d_fix200"] - ref.loc[d.index, "fix200"]).abs() < TOL,
        "emulacao: diametro           x dispositivo congelado": d["confere_diam"],
        "emulacao: maximo             x dispositivo congelado": d["confere_hu_max"],
        "emulacao: numero de voxels   x dispositivo congelado": d["confere_n_voxels"],
    }
    ok = ok_diff
    resumo = {}
    for nome, serie in confs.items():
        k = int(serie.sum())
        ok &= (k == 25)
        resumo[" ".join(nome.split())] = f"{k}/25"
        print(f"  {nome:<56} {k:>2}/25   {'OK' if k == 25 else '>>> DIVERGE <<<'}")
    maior = float(d["dif_emul_disp"].abs().max())
    resumo["maior_dif_emulacao_dispositivo_mm"] = maior
    print(f"  maior |diferenca| emulacao - dispositivo: {maior:.2e} mm   (tolerancia {TOL:.0e})")
    print()

    if gravar:
        grava_csv(df, saida / NOME_CSV_DEV)
        guarda_casos(calculos, CASOS_DESENV, saida / NOME_NPZ_DEV)
        print(f"  Salvo: {NOME_CSV_DEV} e {NOME_NPZ_DEV} em {saida}")
    else:
        novo = df.to_csv(index=False).replace("\r\n", "\n").encode("utf-8")
        arq = saida / NOME_CSV_DEV
        if arq.exists():
            igual = arq.read_bytes().replace(b"\r\n", b"\n") == novo
            resumo["csv_prevoo_igual_ao_gravado_antes"] = bool(igual)
            print(f"  {NOME_CSV_DEV} recalculado e {'IGUAL ao' if igual else 'DIFERENTE do'} gravado no modo --pre-voo")
        else:
            arq.write_bytes(novo)
            resumo["csv_prevoo_igual_ao_gravado_antes"] = None
            print(f"  {NOME_CSV_DEV} nao existia (o modo --pre-voo nao foi rodado antes); gravado agora")
    print()
    if not ok:
        raise SystemExit(
            "ABORTADO: o pre-voo NAO reproduziu o que esta depositado.\n"
            "  Este ambiente nao e equivalente ao que gerou os arquivos de referencia.\n"
            "  Corrija o AMBIENTE (versoes de numpy, scipy, scikit-image), nunca o codigo.\n"
            "  O lacrado NAO foi tocado.")
    print("  PRE-VOO APROVADO.")
    print()
    return df, resumo


def confere_hashes_scripts() -> dict:
    """Os scripts em disco tem de ser os que o Adendo P assinado registra."""
    if not HASHES_P.exists():
        raise SystemExit(f"ABORTADO: {HASHES_P.relative_to(ROOT)} nao existe. O lacrado NAO foi tocado.")
    registrado = {}
    for linha in HASHES_P.read_text(encoding="utf-8").splitlines():
        partes = linha.split()
        if len(partes) == 2:
            registrado[partes[1].replace("\\", "/")] = partes[0].lower()
    obtido, ok = {}, True
    print("=" * 100)
    print("SCRIPTS -- SHA-256 (fins de linha normalizados) contra o Adendo P")
    print("=" * 100)
    for rel in ARQUIVOS_COM_HASH:
        h = sha256_lf(ROOT / rel)
        obtido[rel] = h
        igual = registrado.get(rel) == h
        ok &= igual
        print(f"  {rel:<22} {h}   {'OK' if igual else '>>> DIFERE DO REGISTRADO <<<'}")
    print()
    if not ok:
        raise SystemExit("ABORTADO: um script difere do que o Adendo P registra. O lacrado NAO foi tocado.")
    return obtido


def confere_adendo() -> str:
    if not ADENDO_P.exists():
        raise SystemExit(
            f"ABORTADO: o Adendo P ASSINADO nao esta em {ADENDO_P.relative_to(ROOT)}.\n"
            "  Assine o plano ANTES de rodar. O lacrado NAO foi tocado.")
    h = sha256_bruto(ADENDO_P)
    if ADENDO_P_SHA.exists():
        esperado = ADENDO_P_SHA.read_text(encoding="utf-8").split()[0].lower()
        if esperado != h:
            raise SystemExit(f"ABORTADO: {ADENDO_P.name} nao confere com {ADENDO_P_SHA.name}. "
                             "O lacrado NAO foi tocado.")
    print(f"  Adendo P assinado: {ADENDO_P.name}")
    print(f"    sha256  {h}")
    print()
    return h


def confere_git(motivo_sem_git):
    """O codigo e o plano tem de estar commitados e enviados ANTES da execucao."""
    head = git("rev-parse", "HEAD")
    rastreaveis = [*ARQUIVOS_COM_HASH, str(HASHES_P.relative_to(ROOT)).replace("\\", "/"),
                   str(ADENDO_P.relative_to(ROOT)).replace("\\", "/")]
    nao_rastreados = [r for r in rastreaveis if git("ls-files", "--error-unmatch", r) is None]
    alterados = git("status", "--porcelain", "--untracked-files=no")
    upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    enviado = upstream is not None and git("merge-base", "--is-ancestor", "HEAD", upstream) is not None
    ok = (head is not None and not nao_rastreados and alterados == "" and enviado)
    print("=" * 100)
    print("GIT -- codigo e plano commitados e enviados antes da execucao")
    print("=" * 100)
    print(f"  HEAD                         : {head}")
    print(f"  ramo remoto                  : {upstream}")
    print(f"  arquivos do plano rastreados : {'sim' if not nao_rastreados else 'NAO: ' + ', '.join(nao_rastreados)}")
    print(f"  rastreados sem alteracao     : {'sim' if alterados == '' else 'NAO'}")
    print(f"  HEAD ja esta no remoto       : {'sim' if enviado else 'NAO'}")
    print()
    if not ok and not motivo_sem_git:
        raise SystemExit(
            "ABORTADO: commite os scripts, o arquivo de hashes e o Adendo P assinado, e faca o push,\n"
            "  ANTES de rodar. (Para rodar sem essa conferencia, use --sem-git \"motivo\"; o motivo\n"
            "  fica no registro de execucao.) O lacrado NAO foi tocado.")
    return dict(commit_validacao=head, ramo_remoto=upstream, head_no_remoto=bool(enviado),
                arquivos_nao_rastreados=nao_rastreados, rastreados_sem_alteracao=(alterados == ""),
                sem_git_motivo=motivo_sem_git or None)


# ---------------------------------------------------------------- MAIN ----
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pre-voo", action="store_true",
                    help="roda SO o pre-voo nos 25 de desenvolvimento (nao abre o lacrado) e sai")
    ap.add_argument("--saida", default=None,
                    help="pasta de saida; SO vale com --pre-voo (teste). A execucao grava em results/")
    ap.add_argument("--sem-git", default="", metavar="MOTIVO",
                    help="roda sem a conferencia de commit e push; o motivo fica no registro")
    args = ap.parse_args()

    if args.saida and not args.pre_voo:
        raise SystemExit("--saida so vale com --pre-voo. A execucao no lacrado grava em results/.")
    saida = Path(args.saida).resolve() if args.saida else RESULTS
    saida.mkdir(parents=True, exist_ok=True)

    # ---- guarda 1: trava de execucao unica ------------------------------
    if TRAVA.exists() and not args.pre_voo:
        reg = json.loads(TRAVA.read_text(encoding="utf-8"))
        raise SystemExit(
            "\n"
            "############################################################\n"
            "#  A ANALISE POS-HOC JA FOI EXECUTADA. ABORTADO.           #\n"
            "############################################################\n"
            f"\n  quando : {reg.get('quando')}\n"
            f"  csv    : {reg.get('csv')}\n"
            f"  sha256 : {reg.get('csv_sha256')}\n"
            "\n  Toda reanalise sai do CSV acima (poshoc_analise.py). NUNCA do .mat.\n"
            f"\n  Reexecucao so por falha tecnica documentada, com codigo identico: apague\n"
            f"  {TRAVA.name} DE PROPOSITO e registre o incidente por escrito.\n")

    # ---- guarda 2: entradas ----------------------------------------------
    entradas = confere_entradas()

    # ---- guarda 3: pre-voo (sempre; nao toca no lacrado) ------------------
    _, resumo_prevoo = pre_voo(saida, gravar=args.pre_voo)

    if args.pre_voo:
        print("=" * 100)
        print("MODO --pre-voo: parando aqui. O LACRADO NAO FOI TOCADO.")
        print("=" * 100)
        return

    # ---- guarda 4: o lacre -------------------------------------------------
    if os.environ.get("VAE001_LACRE_ABERTO") != "1":
        raise SystemExit(
            "\n  O acesso as imagens do lacrado esta FECHADO.\n"
            "\n  Para abrir (segundo acesso, autorizado pelo Adendo P):\n"
            "      PowerShell:  $env:VAE001_LACRE_ABERTO=1; python poshoc_lacrado.py\n"
            "      bash:        VAE001_LACRE_ABERTO=1 python poshoc_lacrado.py\n")

    # ---- guardas 5 a 7: plano assinado, scripts registrados, commit e push --
    print("=" * 100)
    print("PLANO -- Adendo P assinado antes da execucao")
    print("=" * 100)
    h_adendo = confere_adendo()
    h_scripts = confere_hashes_scripts()
    reg_git = confere_git(args.sem_git.strip())

    print("#" * 100)
    print("#  SEGUNDO ACESSO AS IMAGENS DO LACRADO -- 76 CALCULOS. EXECUCAO UNICA.")
    print("#  O dispositivo congelado NAO e reexecutado.")
    print("#" * 100)
    quando = datetime.now(timezone.utc).isoformat()
    print(f"  Quando : {quando}")
    print()

    calculos = carregar_freiburg(MAT, grupo="LACRADO")
    presentes = {int(c["id"]) for c in calculos}
    faltam = [i for i in CASOS_LACRADO if i not in presentes]
    if faltam:
        raise SystemExit(f"ABORTADO antes de medir: calculos nomeados no item 4 ausentes do lacrado: {faltam}")
    df = junta_dispositivo(pd.DataFrame([mede(c) for c in calculos]), CSV_DISP)

    # ---- grava tudo, e a trava por ultimo ---------------------------------
    grava_csv(df, RESULTS / NOME_CSV)
    casos = guarda_casos(calculos, CASOS_LACRADO, RESULTS / NOME_NPZ)

    nan = {c: int(df[c].isna().sum()) for c in ("d_emul", "d_reimpl", "d_fix200")}
    item1 = dict(
        diametro=int(df["confere_diam"].sum()),
        maximo=int(df["confere_hu_max"].sum()),
        n_voxels=int(df["confere_n_voxels"].sum()),
        maior_dif_mm=float(df["dif_emul_disp"].abs().max()),
        ids_diametro_difere=sorted(df.loc[~df["confere_diam"], "id"].astype(int).tolist()),
    )

    print("=" * 100)
    print("EXECUCAO -- integridade (a estatistica e do poshoc_analise.py)")
    print("=" * 100)
    n = len(df)
    print(f"  calculos medidos : {n}   (esperado 76)")
    print(f"  medidas sem valor: emulacao {nan['d_emul']}, reimplementacao {nan['d_reimpl']}, 200 UH fixos {nan['d_fix200']}")
    print(f"  emulacao x dispositivo congelado, identicos (|dif| < {TOL:.0e} mm):")
    print(f"      diametro {item1['diametro']}/{n}   maximo {item1['maximo']}/{n}   numero de voxels {item1['n_voxels']}/{n}")
    print(f"      maior |diferenca| de diametro: {item1['maior_dif_mm']:.2e} mm")
    if item1["ids_diametro_difere"]:
        print(f"      ids em que o diametro difere: {item1['ids_diametro_difere']}")
    print()

    reg = {
        "quando":                    quando,
        "o_que":                     "Adendo P -- analises pos-hoc sobre as imagens do lacrado; dispositivo NAO reexecutado",
        "adendo_p_pdf":              str(ADENDO_P.relative_to(ROOT)).replace("\\", "/"),
        "adendo_p_pdf_sha256":       h_adendo,
        "scripts_sha256_lf":         h_scripts,
        **reg_git,
        **entradas,
        "ambiente": {
            "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
            "pandas": pd.__version__, "scikit-image": skimage.__version__, "plataforma": platform.platform(),
        },
        "parametros":                {"fracao_do_p95": F_ADOTADO, "limiar_fixo_UH": T_DETECCAO, "tolerancia_mm": TOL},
        "diff_emulacao":             diff_emulacao(),
        "prevoo":                    resumo_prevoo,
        "n_calculos":                int(len(df)),
        "n_sem_valor":               nan,
        "item1_emulacao_x_dispositivo": item1,
        "casos_ids":                 casos,
        "csv":                       f"results/{NOME_CSV}",
        "csv_sha256":                sha256_bruto(RESULTS / NOME_CSV),
        "csv_prevoo":                f"results/{NOME_CSV_DEV}",
        "csv_prevoo_sha256":         sha256_bruto(RESULTS / NOME_CSV_DEV),
        "casos":                     f"results/{NOME_NPZ}",
        "casos_sha256":              sha256_bruto(RESULTS / NOME_NPZ),
    }
    TRAVA.write_bytes((json.dumps(reg, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))

    print("=" * 100)
    print("EXECUCAO REGISTRADA")
    print("=" * 100)
    print(f"  results/{NOME_CSV}")
    print(f"    sha256  {reg['csv_sha256']}")
    print(f"  results/{TRAVA.name}")
    print()
    print("  >>> Rode agora:  python poshoc_analise.py")
    print("  >>> Depois COMMITE e envie os arquivos poshoc_* e POSHOC_EXECUTADA.json de results/.")


if __name__ == "__main__":
    main()

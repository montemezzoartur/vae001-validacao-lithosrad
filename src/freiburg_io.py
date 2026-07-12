#!/usr/bin/env python3
"""
freiburg_io — converte o dataset ct-uroliths-freiburg para o objeto Volume do
LithosRad: array (z, y, x) em UH + spacing (z, y, x) em mm.

Fonte: Kellner E & Neubauer J. 2023, DOI 10.6084/m9.figshare.21992264 (CC BY 4.0).

Premissas VERIFICADAS (Fase 0/0d) — não assumidas:

  * ACHADO 4 (results/fase0d_correcao.md): o `ct-uroliths_table.csv` está
    DESALINHADO em relação ao .mat em 53 dos 101 cálculos. Ambos estão ordenados
    por volume crescente, mas dentro de blocos de volume idêntico a ordem difere;
    o volume bate 101/101 (por isso não denuncia), mas o diâmetro diverge em até
    5,69 mm. Por isso o CSV original NÃO é lido aqui — NUNCA. A referência vem de
    `results/referencia_autoritativa.csv` (gerada por fase0d_correcao.py), keyed
    por `mat_id` (1-based) = posição no .mat: gt_vol, gt_diam, voxvol_mL,
    stone_type (já normalizado; vazio = n.d.), estrato, grupo.

  * `voxsiz` do .mat é 0.7363 x 0.7363 x 0.7 mm CONSTANTE e está ERRADO para 21
    cálculos; é IGNORADO. O espaçamento no plano vem de `voxvol_mL` (autoritativo),
    com a espessura de corte fixa dz = 0.7:
        dxy = sqrt(voxvol_mL * 1000 / dz)      # mm  (voxvol_mL * 1000 = mm^3)
    voxvol_mL é idêntico nas duas fontes (.mat e referência); isso é conferido
    por assert a cada cálculo.
"""
import csv
import os
from pathlib import Path

import numpy as np
from scipy.io import loadmat

DZ_MM = 0.7  # espessura de corte fixa (eixo z), do artigo

# Referência CORRETA (nunca o ct-uroliths_table.csv). Localizada pela estrutura
# do repositório, não pelo caminho do .mat, pois é um artefato do projeto.
REF_CSV = Path(__file__).resolve().parents[1] / "results" / "referencia_autoritativa.csv"

# Composições esperadas (referência já normalizada; None = n.d.). Se alguém
# regenerar a referência com um bug de normalização, o assert em _load_referencia
# quebra na carga — não na análise.
VALIDOS = {"cystine", "brushite", "uric acid", "calciumoxalate-dihydrate",
           "calciumoxalate-monohydrate", "struvite", None}


def _scalar(field):
    """Extrai um float de um campo escalar do struct MATLAB (shape (1, 1))."""
    return float(np.asarray(field).ravel()[0])


def _load_referencia():
    """Mapa mat_id (1-based) -> dados de referência autoritativos."""
    ref = {}
    with open(REF_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            stone_type = row["stone_type"].strip() or None   # vazio (n.d.) -> None
            assert stone_type in VALIDOS, f"stone_type inesperado: {stone_type!r}"
            ref[int(row["mat_id"])] = dict(
                gt_vol=float(row["gt_vol"]),
                gt_diam=float(row["gt_diam"]),
                voxvol_mL=float(row["voxvol_mL"]),
                stone_type=stone_type,
                grupo=row["grupo"],
            )
    return ref


def carregar_freiburg(path, *, grupo):
    """
    Carrega o dataset ct-uroliths-freiburg como uma lista de dicts.

    `path` aponta para o .mat (data/raw/ct-uroliths_matlab.mat), do qual vêm as
    imagens. A referência (gt_vol, gt_diam, stone_type, grupo) vem de
    `results/referencia_autoritativa.csv`, casada por posição: cálculo i do .mat
    <-> mat_id i+1.

    `grupo` é OBRIGATÓRIO e keyword-only (trava contra acesso acidental):
      'DESENV'   — os 25 cálculos de desenvolvimento.
      'LACRADO'  — os 76 lacrados; EXIGE VAE001_LACRE_ABERTO=1 no ambiente. O
                   lacre só cai após o congelamento do LithosRad (protocolo
                   VAE-001, Seções 3.2 e 12) e abri-lo é um evento único e
                   irreversível.
      'TODOS'    — proibido: revelaria os desfechos do conjunto lacrado.

    Cada dict contém:
      id          : int          — 1-based; igual ao mat_id da referência
      array       : ndarray      — (z, y, x) em UH
      spacing     : tuple        — (dz, dy, dx) em mm = (0.7, dxy, dxy)
      gt_vol_mL   : float        — volume de referência (mL)
      gt_diam_mm  : float        — diâmetro de referência (mm)
      stone_type  : str | None   — composição (None = n.d.)
    """
    if grupo == "DESENV":
        pass
    elif grupo == "LACRADO":
        if not os.environ.get("VAE001_LACRE_ABERTO"):
            raise RuntimeError(
                "CONJUNTO LACRADO. O acesso exige congelamento previo do "
                "LithosRad (protocolo VAE-001, Secao 3.2 e 12). Para abrir, "
                "defina VAE001_LACRE_ABERTO=1 -- e saiba que isso e um evento "
                "unico e irreversivel."
            )
    elif grupo == "TODOS":
        raise RuntimeError(
            "Carregar os 101 juntos e proibido: revelaria desfechos do "
            "conjunto lacrado. Use grupo='DESENV'."
        )
    else:
        raise ValueError(f"grupo invalido: {grupo!r}")

    ref = _load_referencia()

    m = loadmat(path, squeeze_me=False, struct_as_record=True)
    stones = m["stones"].ravel()
    assert len(stones) == len(ref), (
        f".mat tem {len(stones)} cálculos, referência tem {len(ref)}"
    )

    calculos = []
    for i, s in enumerate(stones):
        mat_id = i + 1
        r = ref[mat_id]
        if r["grupo"] != grupo:
            continue

        img = np.asarray(s["imgdata"])
        # imgdata vem em ordem MATLAB (x, y, z): o plano é (x, y) e seus dois
        # eixos são SEMPRE iguais; o terceiro (z) são os cortes. Se o plano não
        # for quadrado, uma premissa geométrica quebrou — pare e investigue.
        assert img.shape[0] == img.shape[1], (
            f"cálculo {mat_id}: eixos no plano diferem (shape={img.shape}); a "
            f"premissa de plano quadrado (x==y) falhou"
        )
        # (x, y, z) -> (z, y, x) para o LithosRad
        array = np.transpose(img, (2, 1, 0))

        # GUARD DE ALINHAMENTO. gt_diam é o campo DISCRIMINANTE — foi ele que
        # expôs o ACHADO 4. gt_vol NÃO serve aqui: há muitos empates (0,10 mL
        # ocorre 13x), então uma troca entre duas linhas do .mat passaria por
        # um assert sobre gt_vol. A referência foi gerada do próprio .mat, logo
        # os dois devem ser bit-idênticos; se divergirem, quebre alto.
        gt_diam_mat = _scalar(s["gt_diam"])
        assert abs(gt_diam_mat - r["gt_diam"]) < 1e-9, (
            f"DESALINHAMENTO em mat_id={mat_id}: .mat={gt_diam_mat}, "
            f"referencia={r['gt_diam']}"
        )

        # Checagem secundária: voxvol_mL das duas fontes também deve bater.
        voxvol_mL = _scalar(s["voxvol_mL"])
        assert abs(voxvol_mL - r["voxvol_mL"]) <= 1e-12, (
            f"cálculo {mat_id}: voxvol_mL do .mat ({voxvol_mL}) diverge da "
            f"referência ({r['voxvol_mL']})"
        )
        dxy = np.sqrt(voxvol_mL * 1000.0 / DZ_MM)

        calculos.append(dict(
            id=mat_id,
            array=array,
            spacing=(DZ_MM, dxy, dxy),
            gt_vol_mL=r["gt_vol"],
            gt_diam_mm=r["gt_diam"],
            stone_type=r["stone_type"],
        ))
    return calculos

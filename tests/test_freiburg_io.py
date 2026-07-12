"""
Testes de src/freiburg_io.py — invariantes de geometria do dataset
ct-uroliths-freiburg e a correção do desalinhamento do CSV (ACHADO 4).
Requerem data/raw/ct-uroliths_matlab.mat presente.

    pytest tests/test_freiburg_io.py
"""
import builtins
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pytest
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from freiburg_io import carregar_freiburg  # noqa: E402

MAT = ROOT / "data" / "raw" / "ct-uroliths_matlab.mat"
DIVISAO_V2 = ROOT / "results" / "divisao_v2.json"


@pytest.fixture(scope="module")
def calculos():
    """Os 101 = DESENV + LACRADO. O acesso ao LACRADO e explicito e efemero:
    a variavel de lacre so fica setada durante a carga (MonkeyPatch.context a
    desfaz na saida do `with`), entao nao vaza para test_lacrado_sem_variavel."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("VAE001_LACRE_ABERTO", "1")
        desenv = carregar_freiburg(MAT, grupo="DESENV")
        lacrado = carregar_freiburg(MAT, grupo="LACRADO")
    return sorted(desenv + lacrado, key=lambda c: c["id"])


@pytest.fixture(scope="module")
def voxvol_mL_ref():
    """voxvol_mL cru, na ordem do .mat — fonte independente do loader."""
    m = loadmat(MAT, squeeze_me=False, struct_as_record=True)
    return [float(np.asarray(s["voxvol_mL"]).ravel()[0]) for s in m["stones"].ravel()]


# ---- os 5 testes anteriores ----

def test_carrega_101_calculos(calculos):
    assert len(calculos) == 101


def test_dz_fixo_em_todos(calculos):
    assert all(c["spacing"][0] == 0.7 for c in calculos)


def test_plano_isotropico(calculos):
    assert all(c["spacing"][1] == c["spacing"][2] for c in calculos)


def test_prod_spacing_bate_voxvol(calculos, voxvol_mL_ref):
    assert len(calculos) == len(voxvol_mL_ref)
    for c, vv in zip(calculos, voxvol_mL_ref):
        assert np.prod(c["spacing"]) == pytest.approx(vv * 1000.0, abs=1e-6)


def test_quatro_resolucoes_no_plano(calculos):
    contagem = Counter(round(c["spacing"][1], 4) for c in calculos)
    assert len(contagem) == 4
    assert sorted(contagem.values()) == [5, 8, 8, 80]


# ---- correção do ACHADO 4 ----

def test_nao_abre_csv_original(monkeypatch):
    """O adaptador NÃO pode tocar no ct-uroliths_table.csv desalinhado."""
    real_open = builtins.open
    abertos = []

    def _spy_open(file, *args, **kwargs):
        abertos.append(str(file))
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", _spy_open)
    carregar_freiburg(MAT, grupo="DESENV")
    assert not any(p.endswith("ct-uroliths_table.csv") for p in abertos), \
        f"abriu o CSV proibido: {[p for p in abertos if p.endswith('ct-uroliths_table.csv')]}"


def test_filtro_por_grupo(monkeypatch):
    assert len(carregar_freiburg(MAT, grupo="DESENV")) == 25
    monkeypatch.setenv("VAE001_LACRE_ABERTO", "1")
    assert len(carregar_freiburg(MAT, grupo="LACRADO")) == 76


def test_ids_desenv_batem_divisao_v2():
    div = json.loads(DIVISAO_V2.read_text(encoding="utf-8"))
    ids = sorted(c["id"] for c in carregar_freiburg(MAT, grupo="DESENV"))
    assert ids == sorted(div["desenvolvimento"])


# ---- a trava do conjunto lacrado (VAE-001, Secao 3.2 e 12) ----

def test_grupo_none_levanta_erro():
    """grupo e obrigatorio: None nao e valido e cai no ramo de erro."""
    with pytest.raises(ValueError):
        carregar_freiburg(MAT, grupo=None)


def test_lacrado_sem_variavel_bloqueia(monkeypatch):
    """LACRADO sem VAE001_LACRE_ABERTO no ambiente e bloqueado."""
    monkeypatch.delenv("VAE001_LACRE_ABERTO", raising=False)
    with pytest.raises(RuntimeError):
        carregar_freiburg(MAT, grupo="LACRADO")

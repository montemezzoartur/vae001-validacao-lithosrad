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
    return carregar_freiburg(MAT)


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
    carregar_freiburg(MAT)
    assert not any(p.endswith("ct-uroliths_table.csv") for p in abertos), \
        f"abriu o CSV proibido: {[p for p in abertos if p.endswith('ct-uroliths_table.csv')]}"


def test_filtro_por_grupo():
    assert len(carregar_freiburg(MAT, grupo="DESENV")) == 25
    assert len(carregar_freiburg(MAT, grupo="LACRADO")) == 76


def test_ids_desenv_batem_divisao_v2():
    div = json.loads(DIVISAO_V2.read_text(encoding="utf-8"))
    ids = sorted(c["id"] for c in carregar_freiburg(MAT, grupo="DESENV"))
    assert ids == sorted(div["desenvolvimento"])

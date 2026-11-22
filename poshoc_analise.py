#!/usr/bin/env python3
"""
VAE-001 -- ADENDO P: ESTATISTICA DAS ANALISES POS-HOC (lista fechada)
=====================================================================

Le SO o CSV gravado pelo poshoc_lacrado.py. NAO le imagem. E deterministico
(semente fixa): pode ser rodado quantas vezes for preciso e da o mesmo resultado.

A LISTA FECHADA (Adendo P)
--------------------------
  Item 1  Emulacao do dispositivo nos 76, contra as saidas da execucao unica:
          quantos conferem em diametro (|dif| < 1e-6 mm), maximo e numero de voxels.
  Item 2  Com o p95 de cada calculo: rho de Spearman entre p95 e o erro do
          DISPOSITIVO (o estimador pre-especificado), com IC; contagem de
          T = 0,225 x p95 abaixo de 200 UH; vies e DP do dispositivo por regime;
          DP por tercil de p95.
  Item 3  Reimplementacao de referencia com 200 UH fixos e com 0,225 x p95:
          vies, DP, pior erro e rho(p95, erro) com IC de cada regra; diferenca
          pareada dos rho (bootstrap) e dos DP (Pitman-Morgan).
  Item 5  Sensibilidade: itens 2 e 3 sem os calculos em que T fica abaixo do
          piso da mascara do arquivo publico.
  (O item 4, inspecao descritiva dos 8 calculos nomeados, nao e estatistica.)

REGRA DE LEITURA (fixada ANTES da execucao)
-------------------------------------------
  Ordenacao pela atenuacao   sustentada se o IC de 95% (bootstrap BCa) da
                             diferenca rho(fixo) - rho(fracao) excluir zero,
                             com a diferenca positiva.
  "Sem evidencia de          vale se o IC de 95% (z de Fisher) do rho da fracao
   associacao" na fracao     incluir zero; se excluir, reporta-se dependencia
                             residual, com o sinal.
  Dispersao menor na fracao  sustentada so se o teste de Pitman-Morgan der
                             p < 0,05 com DP(fracao) < DP(fixo).
  Todo resultado e reportado, em qualquer direcao.

Uso:
    python poshoc_analise.py             # lacrado (exige results/POSHOC_EXECUTADA.json)
    python poshoc_analise.py --desenv    # desenvolvimento: teste do codigo; reproduz a Tabela 1

Requer: numpy, pandas, scipy.
"""
import argparse
import hashlib
import io
import json
import math
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from scipy import stats

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT     = Path(__file__).resolve().parent
RESULTS  = ROOT / "results"
TRAVA    = RESULTS / "POSHOC_EXECUTADA.json"
HASHES_P = ROOT / "protocol" / "adendo_p_scripts_sha256.txt"

SEMENTE  = 20260712      # a mesma do bootstrap do artigo
B        = 10000         # reamostras
ALFA     = 0.05
T_FIXO   = 200.0         # UH
TOL      = 1e-6          # mm
Z975     = float(stats.norm.ppf(1 - ALFA / 2))


# ---------------------------------------------------------- ESTATISTICA ----
def rho_s(x, y) -> float:
    """rho de Spearman (postos medios nos empates)."""
    rx, ry = stats.rankdata(x), stats.rankdata(y)
    if np.ptp(rx) == 0 or np.ptp(ry) == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def ic_fisher(r: float, n: int, bonett_wright: bool = False):
    """IC de 95% por z de Fisher. Com bonett_wright, o erro-padrao proprio do
    rho de Spearman: sqrt((1 + r^2/2) / (n - 3))."""
    if not np.isfinite(r) or n < 4 or abs(r) >= 1:
        return [float("nan"), float("nan")]
    ep = math.sqrt((1 + r * r / 2) / (n - 3)) if bonett_wright else 1 / math.sqrt(n - 3)
    z = math.atanh(r)
    return [math.tanh(z - Z975 * ep), math.tanh(z + Z975 * ep)]


def rho_completo(x, y) -> dict:
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    r = rho_s(x, y)
    p = float(stats.spearmanr(x, y).pvalue) if len(x) > 2 else float("nan")
    return dict(n=int(len(x)), rho=r, p=p, ic95_fisher=ic_fisher(r, len(x)),
                ic95_bonett_wright=ic_fisher(r, len(x), True))


def resumo_erro(e) -> dict:
    e = np.asarray(e, float)
    e = e[np.isfinite(e)]
    dp = float(e.std(ddof=1)) if len(e) > 1 else float("nan")
    return dict(n=int(len(e)), vies=float(e.mean()), dp=dp, semi_loa=1.96 * dp,
                pior=float(np.abs(e).max()), minimo=float(e.min()), maximo=float(e.max()))


def pitman_morgan(x, y) -> dict:
    """Teste de igualdade de variancias em amostras PAREADAS: correlacao de
    Pearson entre (x + y) e (x - y); t com n - 2 graus de liberdade."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    n = len(x)
    r = float(np.corrcoef(x + y, x - y)[0, 1])
    t = r * math.sqrt((n - 2) / (1 - r * r))
    p = float(2 * stats.t.sf(abs(t), n - 2))
    return dict(n=int(n), r=r, t=t, p=p, dp_x=float(x.std(ddof=1)), dp_y=float(y.std(ddof=1)))


def bootstrap_pareado(colunas, estat) -> dict:
    """Reamostra CALCULOS (linhas), mantendo o pareamento entre as colunas.
    Devolve a estimativa, o IC percentil e o IC BCa (vies corrigido e acelerado)."""
    colunas = [np.asarray(c, float) for c in colunas]
    n = len(colunas[0])
    obs = float(estat(*colunas))
    rng = np.random.default_rng(SEMENTE)
    boot = np.empty(B)
    for b in range(B):
        i = rng.integers(0, n, n)
        boot[b] = estat(*[c[i] for c in colunas])
    boot = boot[np.isfinite(boot)]
    jack = np.array([estat(*[np.delete(c, k) for c in colunas]) for k in range(n)])
    jack = jack[np.isfinite(jack)]

    perc = [float(np.quantile(boot, ALFA / 2)), float(np.quantile(boot, 1 - ALFA / 2))]

    prop = (np.sum(boot < obs) + 0.5 * np.sum(boot == obs)) / len(boot)
    prop = min(max(prop, 1 / (len(boot) + 1)), 1 - 1 / (len(boot) + 1))
    z0 = float(stats.norm.ppf(prop))
    jm = jack.mean()
    den = 6 * np.sum((jm - jack) ** 2) ** 1.5
    a = float(np.sum((jm - jack) ** 3) / den) if den > 0 else 0.0
    q = []
    for z in (-Z975, Z975):
        q.append(float(stats.norm.cdf(z0 + (z0 + z) / (1 - a * (z0 + z)))))
    bca = [float(np.quantile(boot, q[0])), float(np.quantile(boot, q[1]))]
    return dict(estimativa=obs, ic95_bca=bca, ic95_percentil=perc, z0=z0, aceleracao=a,
                reamostras_validas=int(len(boot)), semente=SEMENTE)


# ------------------------------------------------------------- BLOCOS ----
def item1(df: pd.DataFrame) -> dict:
    n = len(df)
    return dict(
        n=int(n),
        diametro_identico=int(df["confere_diam"].sum()),
        maximo_identico=int(df["confere_hu_max"].sum()),
        n_voxels_identico=int(df["confere_n_voxels"].sum()),
        maior_dif_mm=float(df["dif_emul_disp"].abs().max()),
        ids_diametro_difere=sorted(df.loc[~df["confere_diam"], "id"].astype(int).tolist()),
        componentes_200UH_mais_de_uma=sorted(df.loc[df["n_comp200"] > 1, "id"].astype(int).tolist()),
    )


def item2(df: pd.DataFrame) -> dict:
    e = df["e_disp"].to_numpy(float)
    baixo = df["T"].to_numpy(float) < T_FIXO
    out = dict(
        rho_p95_erro=rho_completo(df["p95"], e),              # estimador PRE-ESPECIFICADO
        rho_maximo_erro=rho_completo(df["pico_max"], e),      # o que o relatorio da Fase 2 tinha
        rho_p95_erro_abs=rho_completo(df["p95"], np.abs(e)),
        n_T_abaixo_de_200=int(baixo.sum()),
        regime={
            "T < 200 UH": resumo_erro(e[baixo]) if baixo.sum() > 1 else None,
            "T >= 200 UH": resumo_erro(e[~baixo]) if (~baixo).sum() > 1 else None,
        },
        razao_p95_maximo_media=float((df["p95"] / df["pico_max"]).mean()),
    )
    if baixo.sum() > 1 and (~baixo).sum() > 1:
        out["regime_levene_mediana_p"] = float(stats.levene(e[baixo], e[~baixo], center="median").pvalue)
    terc = pd.qcut(df["p95"], 3, labels=["inferior", "medio", "superior"])
    out["tercis_p95"] = [
        dict(tercil=str(k), p95_min=float(df.loc[terc == k, "p95"].min()),
             p95_max=float(df.loc[terc == k, "p95"].max()), **resumo_erro(e[(terc == k).to_numpy()]))
        for k in ["inferior", "medio", "superior"]]
    grupos = [e[(terc == k).to_numpy()] for k in ["inferior", "medio", "superior"]]
    out["tercis_levene_mediana_p"] = float(stats.levene(*grupos, center="median").pvalue)
    if not df["confere_diam"].all():      # sensibilidade: so onde a emulacao reproduz o dispositivo
        s = df[df["confere_diam"]]
        out["rho_p95_erro_so_onde_emulacao_confere"] = rho_completo(s["p95"], s["e_disp"])
    return out


def item3(df: pd.DataFrame) -> dict:
    s = df.dropna(subset=["e_fix200", "e_reimpl", "p95"])
    p95 = s["p95"].to_numpy(float)
    ef, er = s["e_fix200"].to_numpy(float), s["e_reimpl"].to_numpy(float)
    out = dict(
        n=int(len(s)), n_excluidos_sem_valor=int(len(df) - len(s)),
        fixo_200UH=dict(**resumo_erro(ef), rho_p95=rho_completo(p95, ef), rho_maximo=rho_completo(s["pico_max"], ef)),
        fracao_0225_p95=dict(**resumo_erro(er), rho_p95=rho_completo(p95, er), rho_maximo=rho_completo(s["pico_max"], er)),
        dispositivo=dict(**resumo_erro(s["e_disp"]), rho_p95=rho_completo(p95, s["e_disp"])),
        delta_rho_fixo_menos_fracao=bootstrap_pareado(
            [p95, ef, er], lambda p, a, b: rho_s(p, a) - rho_s(p, b)),
        pitman_morgan_fixo_x_fracao=pitman_morgan(ef, er),
        razao_dp_fracao_sobre_fixo=bootstrap_pareado(
            [ef, er], lambda a, b: b.std(ddof=1) / a.std(ddof=1)),
    )
    d = (s["d_emul"] - s["d_reimpl"]).to_numpy(float)
    baixo = s["T"].to_numpy(float) < T_FIXO
    out["dispositivo_menos_reimplementacao"] = dict(
        identicos=int((np.abs(d) < TOL).sum()),
        T_abaixo_de_200=dict(n=int(baixo.sum()), menores_no_dispositivo=int((d[baixo] < -TOL).sum()),
                             minimo=float(d[baixo].min()) if baixo.any() else None,
                             maximo=float(d[baixo].max()) if baixo.any() else None),
        T_de_200_ou_mais=dict(n=int((~baixo).sum()), maiores_no_dispositivo=int((d[~baixo] > TOL).sum()),
                              minimo=float(d[~baixo].min()) if (~baixo).any() else None,
                              maximo=float(d[~baixo].max()) if (~baixo).any() else None),
    )
    return out


def regra_de_leitura(i3: dict) -> dict:
    lo, hi = i3["delta_rho_fixo_menos_fracao"]["ic95_bca"]
    if lo > 0:
        ordenacao = "SUSTENTADA: o IC da diferenca dos rho exclui zero, com rho(fixo) > rho(fracao)"
    elif hi < 0:
        ordenacao = "INVERTIDA: o IC da diferenca dos rho exclui zero, com rho(fixo) < rho(fracao)"
    else:
        ordenacao = "NAO SUSTENTADA: o IC da diferenca dos rho inclui zero"

    r = i3["fracao_0225_p95"]["rho_p95"]
    flo, fhi = r["ic95_fisher"]
    if flo <= 0 <= fhi:
        fracao = "SEM EVIDENCIA DE ASSOCIACAO: o IC do rho da fracao inclui zero"
    else:
        fracao = f"DEPENDENCIA RESIDUAL ({'positiva' if r['rho'] > 0 else 'negativa'}): o IC do rho da fracao exclui zero"

    pm = i3["pitman_morgan_fixo_x_fracao"]
    if pm["p"] < ALFA and pm["dp_y"] < pm["dp_x"]:
        dispersao = "SUSTENTADA: Pitman-Morgan p < 0,05 com DP(fracao) < DP(fixo)"
    elif pm["p"] < ALFA:
        dispersao = "INVERTIDA: Pitman-Morgan p < 0,05 com DP(fracao) > DP(fixo)"
    else:
        dispersao = "NAO SUSTENTADA: Pitman-Morgan p >= 0,05"
    return dict(ordenacao_pela_atenuacao=ordenacao, associacao_na_fracao=fracao, dispersao_menor_na_fracao=dispersao)


# ----------------------------------------------------------- RELATORIO ----
MENOS = chr(8722)      # sinal de menos tipografico


def br(x, casas=2, sinal=False):
    """Numero em notacao brasileira. Zero arredondado sai sem sinal (nunca -0,00)."""
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "n/d"
    if round(x, casas) == 0:
        return f"{0:.{casas}f}".replace(".", ",")
    s = f"{x:+.{casas}f}" if sinal else f"{x:.{casas}f}"
    return s.replace(".", ",").replace("-", MENOS)


def brp(p, casas=3):
    """Valor de p; abaixo da menor casa mostrada, '< 0,001'."""
    if p is None or not np.isfinite(p):
        return "n/d"
    piso = 10 ** (-casas)
    return ("< " + f"{piso:.{casas}f}").replace(".", ",") if p < piso else br(p, casas)


def linha_regra(nome, r):
    q = r["rho_p95"]
    return (f"| {nome} | {r['n']} | {br(r['vies'], 2, True)} | {br(r['dp'])} | {br(r['semi_loa'])} | "
            f"{br(r['pior'])} | {br(q['rho'], 2, True)} | {br(q['ic95_fisher'][0], 2, True)} a "
            f"{br(q['ic95_fisher'][1], 2, True)} | {brp(q['p'], 4)} |")


def relatorio_md(res: dict) -> str:
    i1, i2, i3, i5, rl = res["item1"], res["item2"], res["item3"], res["item5"], res["regra_de_leitura"]
    n = res["n"]
    L = []
    L.append(f"# VAE-001, Adendo P: analises pos-hoc -- {res['conjunto']} (n = {n})")
    L.append("")
    L.append(f"Entrada: `{res['csv']}` (SHA-256 `{res['csv_sha256']}`). Semente {SEMENTE}; {B} reamostras.")
    if res["conjunto"] != "LACRADO":
        L.append("")
        L.append("**Conjunto de DESENVOLVIMENTO: teste do codigo. Estes numeros ja eram conhecidos (Tabela 1 do artigo).**")
    L += ["", "## Item 1. Emulacao do dispositivo contra as saidas da execucao unica", ""]
    L.append(f"- Diametro identico (|dif| < 1e-6 mm): **{i1['diametro_identico']} de {n}**; maior diferenca {i1['maior_dif_mm']:.2e} mm.")
    L.append(f"- Maximo identico: {i1['maximo_identico']} de {n}. Numero de voxels identico: {i1['n_voxels_identico']} de {n}.")
    if i1["ids_diametro_difere"]:
        L.append(f"- Calculos em que o diametro difere: {i1['ids_diametro_difere']}.")
    L.append(f"- Calculos com mais de uma componente >= 200 UH: {i1['componentes_200UH_mais_de_uma'] or 'nenhum'}.")

    L += ["", "## Item 2. Erro do dispositivo e atenuacao", ""]
    a, m, ab = i2["rho_p95_erro"], i2["rho_maximo_erro"], i2["rho_p95_erro_abs"]
    L.append(f"- rho(p95, erro) = **{br(a['rho'], 2, True)}** (IC95 {br(a['ic95_fisher'][0], 2, True)} a {br(a['ic95_fisher'][1], 2, True)}; p = {brp(a['p'])}; n = {a['n']}). Estimador pre-especificado.")
    L.append(f"- rho(maximo, erro) = {br(m['rho'], 2, True)} (IC95 {br(m['ic95_fisher'][0], 2, True)} a {br(m['ic95_fisher'][1], 2, True)}).")
    L.append(f"- rho(p95, |erro|) = {br(ab['rho'], 2, True)} (IC95 {br(ab['ic95_fisher'][0], 2, True)} a {br(ab['ic95_fisher'][1], 2, True)}; p = {brp(ab['p'])}).")
    if "rho_p95_erro_so_onde_emulacao_confere" in i2:
        c = i2["rho_p95_erro_so_onde_emulacao_confere"]
        L.append(f"- So nos calculos em que a emulacao reproduz o dispositivo (n = {c['n']}): rho(p95, erro) = {br(c['rho'], 2, True)} (IC95 {br(c['ic95_fisher'][0], 2, True)} a {br(c['ic95_fisher'][1], 2, True)}).")
    L.append(f"- T = 0,225 x p95 abaixo de 200 UH: **{i2['n_T_abaixo_de_200']} de {n}**. Razao media p95/maximo: {br(i2['razao_p95_maximo_media'], 4)}.")
    L += ["", "| Regime | n | Vies (mm) | DP (mm) | Minimo | Maximo |", "|---|---|---|---|---|---|"]
    for k, r in i2["regime"].items():
        if r:
            L.append(f"| {k} | {r['n']} | {br(r['vies'], 2, True)} | {br(r['dp'])} | {br(r['minimo'], 2, True)} | {br(r['maximo'], 2, True)} |")
    if "regime_levene_mediana_p" in i2:
        L.append("")
        L.append(f"Levene (mediana) entre regimes: p = {brp(i2['regime_levene_mediana_p'])}.")
    L += ["", "| Tercil de p95 | p95 (UH) | n | Vies (mm) | DP (mm) |", "|---|---|---|---|---|"]
    for r in i2["tercis_p95"]:
        L.append(f"| {r['tercil']} | {br(r['p95_min'], 0)} a {br(r['p95_max'], 0)} | {r['n']} | {br(r['vies'], 2, True)} | {br(r['dp'])} |")
    L.append("")
    L.append(f"Levene (mediana) entre tercis: p = {brp(i2['tercis_levene_mediana_p'])}.")

    def bloco3(i3, titulo):
        out = ["", titulo, "",
               "| Regra | n | Vies (mm) | DP (mm) | Semi-LoA (mm) | Pior (mm) | rho(p95) | IC95 do rho | p |",
               "|---|---|---|---|---|---|---|---|---|",
               linha_regra("Reimplementacao, 200 UH fixos", i3["fixo_200UH"]),
               linha_regra("Reimplementacao, 0,225 x p95", i3["fracao_0225_p95"]),
               linha_regra("Dispositivo congelado", i3["dispositivo"]), ""]
        d, pm, rz = i3["delta_rho_fixo_menos_fracao"], i3["pitman_morgan_fixo_x_fracao"], i3["razao_dp_fracao_sobre_fixo"]
        out.append(f"- Diferenca dos rho (fixo menos fracao): **{br(d['estimativa'], 2, True)}** (IC95 BCa {br(d['ic95_bca'][0], 2, True)} a {br(d['ic95_bca'][1], 2, True)}; percentil {br(d['ic95_percentil'][0], 2, True)} a {br(d['ic95_percentil'][1], 2, True)}).")
        out.append(f"- Pitman-Morgan (DP fixo {br(pm['dp_x'], 3)} x DP fracao {br(pm['dp_y'], 3)}): r = {br(pm['r'], 3, True)}, t = {br(pm['t'], 2, True)}, **p = {brp(pm['p'], 4)}**.")
        out.append(f"- Razao DP(fracao)/DP(fixo): {br(rz['estimativa'], 3)} (IC95 BCa {br(rz['ic95_bca'][0], 3)} a {br(rz['ic95_bca'][1], 3)}).")
        return out

    L += bloco3(i3, "## Item 3. Limiar fixo contra fracao, na reimplementacao de referencia")
    dr = i3["dispositivo_menos_reimplementacao"]
    L.append(f"- Dispositivo e reimplementacao (mesma regra) identicos em {dr['identicos']} de {i3['n']}. "
             f"Com T < 200 UH (n = {dr['T_abaixo_de_200']['n']}): {dr['T_abaixo_de_200']['menores_no_dispositivo']} menores no dispositivo "
             f"({br(dr['T_abaixo_de_200']['minimo'], 2, True)} a {br(dr['T_abaixo_de_200']['maximo'], 2, True)} mm). "
             f"Com T >= 200 UH (n = {dr['T_de_200_ou_mais']['n']}): {dr['T_de_200_ou_mais']['maiores_no_dispositivo']} maiores no dispositivo "
             f"({br(dr['T_de_200_ou_mais']['minimo'], 2, True)} a {br(dr['T_de_200_ou_mais']['maximo'], 2, True)} mm).")
    if i3["n_excluidos_sem_valor"]:
        L.append(f"- Excluidos por medida sem valor: {i3['n_excluidos_sem_valor']}.")

    L += ["", "## Item 5. Sensibilidade sem os calculos com T abaixo do piso da mascara", ""]
    if i5["ids_excluidos"]:
        L.append(f"Excluidos: {i5['ids_excluidos']} (n = {i5['n']}).")
        a5 = i5["item2"]["rho_p95_erro"]
        L.append("")
        L.append(f"- rho(p95, erro do dispositivo) = {br(a5['rho'], 2, True)} (IC95 {br(a5['ic95_fisher'][0], 2, True)} a {br(a5['ic95_fisher'][1], 2, True)}).")
        L += bloco3(i5["item3"], "Limiar fixo contra fracao, sem os excluidos:")
        r5 = i5["regra_de_leitura"]
        L += ["", "Regra de leitura na sensibilidade:", ""]
        L.append(f"- Ordenacao pela atenuacao: {r5['ordenacao_pela_atenuacao']}.")
        L.append(f"- Associacao na fracao: {r5['associacao_na_fracao']}.")
        L.append(f"- Dispersao menor na fracao: {r5['dispersao_menor_na_fracao']}.")
    else:
        L.append("Nenhum calculo com T abaixo do piso da mascara: a sensibilidade coincide com a analise principal.")

    L += ["", "## Regra de leitura (fixada antes da execucao)", ""]
    L.append(f"- Ordenacao pela atenuacao: **{rl['ordenacao_pela_atenuacao']}**.")
    L.append(f"- Associacao na fracao: **{rl['associacao_na_fracao']}**.")
    L.append(f"- Dispersao menor na fracao: **{rl['dispersao_menor_na_fracao']}**.")
    L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------- MAIN ----
def sha256_bruto(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def este_script() -> dict:
    """SHA-256 deste script (fins de linha normalizados) e se e o que o Adendo P registra."""
    h = hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    confere = None
    if HASHES_P.exists():
        reg = {l.split()[1].replace("\\", "/"): l.split()[0].lower()
               for l in HASHES_P.read_text(encoding="utf-8").splitlines() if len(l.split()) == 2}
        confere = reg.get(Path(__file__).name) == h
    return dict(sha256_lf=h, confere_com_adendo_p=confere)


def analisa(df: pd.DataFrame) -> dict:
    i3 = item3(df)
    return dict(item1=item1(df), item2=item2(df), item3=i3, regra_de_leitura=regra_de_leitura(i3))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desenv", action="store_true",
                    help="analisa o CSV do pre-voo (25 de desenvolvimento): teste do codigo")
    ap.add_argument("--csv", default=None, help="CSV de entrada (padrao: o de results/)")
    ap.add_argument("--saida", default=None, help="pasta de saida (padrao: results/)")
    args = ap.parse_args()

    conjunto = "DESENVOLVIMENTO" if args.desenv else "LACRADO"
    nome = "poshoc_prevoo_desenv.csv" if args.desenv else "poshoc_lacrado.csv"
    csv = Path(args.csv).resolve() if args.csv else RESULTS / nome
    saida = Path(args.saida).resolve() if args.saida else RESULTS
    saida.mkdir(parents=True, exist_ok=True)
    h = sha256_bruto(csv)

    if not args.desenv and not args.csv:
        if not TRAVA.exists():
            raise SystemExit("ABORTADO: results/POSHOC_EXECUTADA.json nao existe. Rode antes o poshoc_lacrado.py.")
        reg = json.loads(TRAVA.read_text(encoding="utf-8"))
        if reg.get("csv_sha256") != h:
            raise SystemExit("ABORTADO: o CSV nao confere com o SHA-256 do registro de execucao.")

    df = pd.read_csv(csv)
    for c in ("confere_diam", "confere_hu_max", "confere_n_voxels", "T_abaixo_piso"):
        df[c] = df[c].astype(str).str.lower().isin(["true", "1"])

    eu = este_script()
    if eu["confere_com_adendo_p"] is False:
        print("AVISO: este script DIFERE do que o Adendo P registra. O resultado fica marcado no JSON.")
        print()
    res = dict(conjunto=conjunto, n=int(len(df)), csv=f"results/{csv.name}", csv_sha256=h,
               script=eu,
               ambiente=dict(python=platform.python_version(), numpy=np.__version__,
                             scipy=scipy.__version__, pandas=pd.__version__),
               parametros=dict(semente=SEMENTE, reamostras=B, alfa=ALFA, limiar_fixo_UH=T_FIXO, tolerancia_mm=TOL))
    res.update(analisa(df))

    excl = sorted(df.loc[df["T_abaixo_piso"], "id"].astype(int).tolist())
    i5 = dict(ids_excluidos=excl)
    if excl:
        s = df[~df["T_abaixo_piso"]]
        r5 = analisa(s)
        i5.update(n=int(len(s)), item2=r5["item2"], item3=r5["item3"], regra_de_leitura=r5["regra_de_leitura"])
    res["item5"] = i5

    sufixo = "_desenv" if args.desenv else ""
    arq_json = saida / f"poshoc_analise{sufixo}.json"
    arq_md = saida / f"poshoc_analise{sufixo}.md"
    arq_json.write_bytes((json.dumps(res, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    md = relatorio_md(res)
    arq_md.write_bytes((md + "\n").encode("utf-8"))
    print(md)
    print()
    print(f"Salvo: {arq_json.name} e {arq_md.name} em {saida}")


if __name__ == "__main__":
    main()

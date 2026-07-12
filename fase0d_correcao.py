#!/usr/bin/env python3
"""
VAE-001 - FASE 0d: CORRECAO DO DESALINHAMENTO + DIVISAO REFEITA

ACHADO 4 (Fase 0): o ct-uroliths_table.csv esta DESALINHADO em relacao ao
.mat em 53 dos 101 calculos. Ambos parecem ordenados por volume crescente,
mas dentro de blocos de volume identico a ordem difere. O volume nao denuncia
(bate em 101/101); o diametro sim.

Consequencias:
  - gt_vol / gt_diam do .MAT sao a fonte autoritativa (vem no mesmo struct
    que a imagem; nao podem estar desalinhados entre si).
  - A composicao (StoneType) existe SO no CSV. Este script tenta recuperar
    a atribuicao correta via join pelo par (Volume, Diameter), e REPORTA
    honestamente quantos calculos ficam ambiguos.
  - A divisao pre-registrada, feita com o Diameter do CSV, e REFEITA com o
    gt_diam correto. Nenhum desfecho foi computado; refazer nao queima nada.

Uso:  python fase0d_correcao.py data\\raw
"""
import sys, os, io, json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.io import loadmat

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SEMENTE = 20260712
N_DESENV = {"5-10": 11, "10-20": 10, ">20": 4}
TOL = 0.006          # tolerancia do join: CSV arredonda a 2 casas; gt_vol
                     # tem quantum de 0.003333 -> 0.006 cobre com folga

NORM = {
    "cacliumoxalate-monohydrate": "calciumoxalate-monohydrate",
    "Cystine": "cystine",
}

OUT = []
def w(s=""):
    print(s); OUT.append(s)


def main(raw):
    raw = Path(raw)
    mat = next(p for p in raw.iterdir() if p.suffix.lower() == ".mat")
    csv = next(p for p in raw.iterdir() if p.suffix.lower() == ".csv")

    st = loadmat(mat, squeeze_me=False, struct_as_record=True)["stones"].ravel()
    M = pd.DataFrame({
        "mat_id":   np.arange(1, len(st) + 1),
        "gt_vol":   [float(np.asarray(x["gt_vol"]).ravel()[0]) for x in st],
        "gt_diam":  [float(np.asarray(x["gt_diam"]).ravel()[0]) for x in st],
        "voxvol_mL":[float(np.asarray(x["voxvol_mL"]).ravel()[0]) for x in st],
    })
    C = pd.read_csv(csv, sep=";")
    C["StoneType"] = C["StoneType"].replace(NORM)

    w("# VAE-001 - Fase 0d: correcao do desalinhamento e divisao refeita")
    w()

    # ---------------------------------------------------------------
    # 1. Documentar o desalinhamento
    # ---------------------------------------------------------------
    w("## 1. ACHADO 4 - magnitude do desalinhamento")
    w()
    dv = (M["gt_vol"] - C["Volume"].values).abs()
    dd = (M["gt_diam"] - C["Diameter"].values).abs()
    w(f"- Junção POSICIONAL (.mat linha i <-> CSV linha i):")
    w(f"  - discrepância de VOLUME  > 0,004 mL: **{(dv > 0.004).sum()} de 101**")
    w(f"  - discrepância de DIÂMETRO > 0,01 mm: **{(dd > 0.01).sum()} de 101**")
    w(f"  - discrepância máxima de diâmetro: **{dd.max():.2f} mm**")
    w()
    w("O volume não denuncia o problema porque ambas as tabelas estão ordenadas")
    w("por volume crescente, com muitos empates (0,10 mL ocorre 13x; 0,20 mL, 8x).")
    w("Dentro de cada bloco de volume idêntico, a ordem difere entre os arquivos.")
    w()
    w("**Fonte autoritativa: `gt_vol` e `gt_diam` do `.mat`** — vêm no mesmo struct")
    w("que a imagem e, portanto, não podem estar desalinhados em relação a ela.")
    w()

    # ---------------------------------------------------------------
    # 2. Recuperar a composicao via join pelo par (Volume, Diameter)
    # ---------------------------------------------------------------
    w("## 2. Recuperação da composição (StoneType)")
    w()
    w("A composição existe apenas no CSV. Tentativa de rejunção pelo par")
    w("(Volume, Diameter), com tolerância de ±0,006 (volume) e ±0,01 (diâmetro).")
    w()

    tipo = [None] * len(M)
    n_cands = []
    for i, row in M.iterrows():
        hit = C[(np.abs(C["Volume"] - row["gt_vol"]) <= TOL) &
                (np.abs(C["Diameter"] - row["gt_diam"]) <= 0.01)]
        n_cands.append(len(hit))
        if len(hit) == 1:
            v = hit["StoneType"].iloc[0]
            tipo[i] = None if pd.isna(v) else v
        elif len(hit) > 1:
            vals = set(hit["StoneType"].dropna().unique())
            # se todos os candidatos concordam (ou todos sao NaN), nao ha ambiguidade real
            if len(vals) == 1:
                tipo[i] = vals.pop()
            elif len(vals) == 0:
                tipo[i] = None
            else:
                tipo[i] = "AMBIGUO"

    M["stone_type"] = tipo
    M["n_candidatos"] = n_cands

    unico   = int((M["n_candidatos"] == 1).sum())
    multi   = int((M["n_candidatos"] > 1).sum())
    zero    = int((M["n_candidatos"] == 0).sum())
    ambiguo = int((M["stone_type"] == "AMBIGUO").sum())
    resolv  = int(M["stone_type"].notna().sum() - ambiguo)

    w("| Situação | n |")
    w("|---|---|")
    w(f"| Casamento único (1 candidato) | {unico} |")
    w(f"| Múltiplos candidatos, todos com a mesma composição | {multi - ambiguo} |")
    w(f"| Múltiplos candidatos, composições CONFLITANTES (ambíguo) | {ambiguo} |")
    w(f"| Nenhum candidato (falha de junção) | {zero} |")
    w()
    w(f"- Composição atribuída com confiança: **{resolv} de 101**")
    w(f"- Ambíguos ou irrecuperáveis: **{ambiguo + zero} de 101**")
    w()

    if zero > 0:
        w("**ATENÇÃO — houve falha de junção.** Cálculos sem candidato:")
        w()
        w("```")
        w(M[M["n_candidatos"] == 0][["mat_id", "gt_vol", "gt_diam"]].to_string(index=False))
        w("```")
        w()

    if ambiguo + zero > 0:
        w("Cálculos sem composição confiável são tratados como `n.d.` e NÃO podem")
        w("sustentar estratificação por composição. Ver Seção 5.")
        w()

    # normaliza ambiguo -> None
    M.loc[M["stone_type"] == "AMBIGUO", "stone_type"] = None

    w("**Distribuição da composição recuperada:**")
    w()
    w("```")
    w(M["stone_type"].fillna("n.d.").value_counts().to_string())
    w("```")
    w()

    # ---------------------------------------------------------------
    # 3. Divisao refeita com gt_diam correto
    # ---------------------------------------------------------------
    w("## 3. Divisão pré-registrada, refeita com `gt_diam` do `.mat`")
    w()
    M["estrato"] = pd.cut(M["gt_diam"], [0, 5, 10, 20, np.inf],
                          labels=["<5", "5-10", "10-20", ">20"], right=False)

    rng = np.random.default_rng(SEMENTE)
    desenv = []
    for e, n in N_DESENV.items():
        ids = M.loc[M["estrato"] == e, "mat_id"].to_numpy()
        if len(ids) < n:
            raise SystemExit(f"Estrato {e}: só {len(ids)} cálculos, pedidos {n}.")
        desenv.extend(rng.choice(ids, size=n, replace=False).tolist())

    desenv = sorted(int(i) for i in desenv)
    lacrado = sorted(int(i) for i in M["mat_id"] if i not in set(desenv))
    assert len(desenv) + len(lacrado) == 101 and not (set(desenv) & set(lacrado))

    M["grupo"] = np.where(M["mat_id"].isin(desenv), "DESENV", "LACRADO")

    w(f"Semente: **{SEMENTE}** (mantida). Estratificação por `gt_diam`.")
    w()
    w("| Estrato | Desenvolvimento | Lacrado | Total |")
    w("|---|---|---|---|")
    for e in ["5-10", "10-20", ">20"]:
        d = int(((M["estrato"] == e) & (M["grupo"] == "DESENV")).sum())
        l = int(((M["estrato"] == e) & (M["grupo"] == "LACRADO")).sum())
        w(f"| {e} mm | {d} | {l} | {d+l} |")
    w(f"| **TOTAL** | **{len(desenv)}** | **{len(lacrado)}** | **101** |")
    w()
    nl_p = int(((M["gt_diam"] >= 10) & (M["grupo"] == "LACRADO")).sum())
    w(f"**Estrato primário (≥ 10 mm) no conjunto lacrado: {nl_p}**")
    w()

    w("**Balanço de composição entre os conjuntos:**")
    w()
    w("```")
    w(pd.crosstab(M["stone_type"].fillna("n.d."), M["grupo"], margins=True).to_string())
    w("```")
    w()

    w("**IDs (do `.mat`, 1-based):**")
    w()
    w(f"- DESENVOLVIMENTO ({len(desenv)}): {desenv}")
    w()
    w(f"- LACRADO ({len(lacrado)}): {lacrado}")
    w()

    # ---------------------------------------------------------------
    # 4. Persistir
    # ---------------------------------------------------------------
    os.makedirs("results", exist_ok=True)
    M.to_csv("results/referencia_autoritativa.csv", index=False)

    payload = {
        "fonte": "gt_vol/gt_diam do ct-uroliths_matlab.mat (CSV desalinhado — ver ACHADO 4)",
        "semente": SEMENTE,
        "n_desenvolvimento": len(desenv),
        "n_lacrado": len(lacrado),
        "estrato_primario_lacrado": nl_p,
        "composicao_recuperada": resolv,
        "composicao_irrecuperavel": ambiguo + zero,
        "desenvolvimento": desenv,
        "lacrado": lacrado,
    }
    blob = json.dumps(payload, indent=2, ensure_ascii=False)
    with open("results/divisao_v2.json", "w", encoding="utf-8") as f:
        f.write(blob + "\n")
    h = hashlib.sha256(blob.encode()).hexdigest()
    with open("results/divisao_v2_sha256.txt", "w") as f:
        f.write(h + "\n")

    w("## 4. Registro")
    w()
    w(f"- `results/referencia_autoritativa.csv` — a tabela de referência CORRETA.")
    w(f"  **Use este arquivo, nunca o CSV original.**")
    w(f"- `results/divisao_v2.json` — SHA-256: `{h}`")
    w()
    w("```")
    w("git add results/referencia_autoritativa.csv results/divisao_v2.json results/divisao_v2_sha256.txt fase0d_correcao.py")
    w('git commit -m "VAE-001 ACHADO 4: CSV desalinhado; referencia corrigida e divisao refeita"')
    w("git tag vae001-divisao-v2")
    w("```")
    w()
    w("O commit anterior (`vae001-divisao`) NÃO é reescrito. O histórico honesto")
    w("registra a divisão original, a descoberta do erro, e a correção.")
    w()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/raw")
    os.makedirs("results", exist_ok=True)
    with open("results/fase0d_correcao.md", "w", encoding="utf-8") as f:
        f.write("\n".join(OUT) + "\n")
    print("\n>>> Salvo em results/fase0d_correcao.md")

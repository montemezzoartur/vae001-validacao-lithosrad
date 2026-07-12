#!/usr/bin/env python3
"""
VAE-001 - FASE 0c: DIVISAO PRE-REGISTRADA

Separa os 101 urolitos em:
  - DESENVOLVIMENTO (25) : irrestrito. Itere, ajuste, inspecione a vontade.
  - LACRADO         (76) : NAO ABRIR ate o congelamento do LithosRad.

A divisao e estratificada por faixa de diametro DE REFERENCIA, com semente
fixa. Usa exclusivamente caracteristica basal da referencia - jamais qualquer
saida do LithosRad. Nenhum desfecho e computado ou revelado aqui.

Executar UMA VEZ. Commitar a saida antes de qualquer analise.

Uso:  python fase0c_divisao.py data\\raw
"""
import sys, os, io, json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SEMENTE = 20260712          # registrada no protocolo, Anexo C
N_DESENV = {"5-10": 11, "10-20": 10, ">20": 4}   # total 25


def main(raw):
    raw = Path(raw)
    csv = next(p for p in raw.iterdir() if p.suffix.lower() == ".csv")
    df = pd.read_csv(csv, sep=";")

    df["estrato"] = pd.cut(df["Diameter"], [0, 5, 10, 20, np.inf],
                           labels=["<5", "5-10", "10-20", ">20"], right=False)

    rng = np.random.default_rng(SEMENTE)
    desenv = []
    for estrato, n in N_DESENV.items():
        ids = df.loc[df["estrato"] == estrato, "ID"].to_numpy()
        if len(ids) < n:
            raise SystemExit(f"Estrato {estrato} tem so {len(ids)} calculos, "
                             f"pedidos {n}. Reveja N_DESENV.")
        desenv.extend(rng.choice(ids, size=n, replace=False).tolist())

    desenv = sorted(int(i) for i in desenv)
    lacrado = sorted(int(i) for i in df["ID"] if i not in set(desenv))

    assert len(desenv) + len(lacrado) == len(df)
    assert not (set(desenv) & set(lacrado))

    # ---- relatorio ----
    print("# VAE-001 - Divisao pre-registrada\n")
    print(f"Semente: **{SEMENTE}**   (registrada no protocolo, Anexo C)\n")
    print("## Balanco por estrato\n")
    print("| Estrato | Desenvolvimento | Lacrado | Total |")
    print("|---|---|---|---|")
    for e in ["5-10", "10-20", ">20"]:
        d = sum(1 for i in desenv if df.loc[df.ID == i, "estrato"].iloc[0] == e)
        l = sum(1 for i in lacrado if df.loc[df.ID == i, "estrato"].iloc[0] == e)
        print(f"| {e} mm | {d} | {l} | {d+l} |")
    nd_p = sum(1 for i in desenv if df.loc[df.ID == i, "Diameter"].iloc[0] >= 10)
    nl_p = sum(1 for i in lacrado if df.loc[df.ID == i, "Diameter"].iloc[0] >= 10)
    print(f"| **TOTAL** | **{len(desenv)}** | **{len(lacrado)}** | **{len(df)}** |")
    print()
    print(f"**Estrato primario (>= 10 mm): {nl_p} no conjunto lacrado** "
          f"(e {nd_p} no de desenvolvimento).")
    print()

    print("## Composicao (checagem de balanco)\n")
    df["grupo"] = np.where(df["ID"].isin(desenv), "DESENV", "LACRADO")
    print("```")
    print(pd.crosstab(df["StoneType"].fillna("n.d."), df["grupo"], margins=True).to_string())
    print("```\n")

    print("## IDs\n")
    print(f"**DESENVOLVIMENTO ({len(desenv)}):**  {desenv}\n")
    print(f"**LACRADO ({len(lacrado)}):**  {lacrado}\n")

    # ---- persistir ----
    os.makedirs("results", exist_ok=True)
    payload = {
        "semente": SEMENTE,
        "n_desenvolvimento": len(desenv),
        "n_lacrado": len(lacrado),
        "desenvolvimento": desenv,
        "lacrado": lacrado,
        "estrato_primario_lacrado": nl_p,
    }
    blob = json.dumps(payload, indent=2, ensure_ascii=False)
    with open("results/divisao.json", "w", encoding="utf-8") as f:
        f.write(blob + "\n")
    h = hashlib.sha256(blob.encode()).hexdigest()
    with open("results/divisao_sha256.txt", "w") as f:
        f.write(h + "\n")

    df[["ID", "Diameter", "Volume", "StoneType", "estrato", "grupo"]] \
        .to_csv("results/divisao.csv", index=False)

    print("## Registro\n")
    print(f"- `results/divisao.json`   SHA-256: `{h}`")
    print("- `results/divisao.csv`")
    print()
    print("**COMMITE ESTES ARQUIVOS AGORA**, antes de qualquer analise:")
    print()
    print("```")
    print("git add results/divisao.json results/divisao_sha256.txt results/divisao.csv")
    print('git commit -m "VAE-001: divisao pre-registrada (semente 20260712)"')
    print("git tag vae001-divisao")
    print("```")
    print()
    print("A partir daqui, os IDs em `lacrado` NAO PODEM ser tocados ate que o")
    print("LithosRad esteja congelado (Secao 3.2 do protocolo).")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/raw")

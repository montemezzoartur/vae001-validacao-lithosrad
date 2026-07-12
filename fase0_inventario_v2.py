#!/usr/bin/env python3
"""
VAE-001 - FASE 0: INVENTARIO  (v2)
Dataset: ct-uroliths-freiburg (figshare 21992264, Kellner & Neubauer 2023)

v2: corrige encoding no console do Windows (cp1252) e o separador do CSV (;)

REGRA DA FASE 0: inspeciona ESTRUTURA. Proibido computar volume a partir das
imagens ou comparar qualquer saida com a referencia. Permitido: descrever a
referencia sozinha (caracteristica basal, nao desfecho).

Uso:  python fase0_inventario.py data\\raw
"""
import sys, os, io, hashlib
from pathlib import Path
import numpy as np
import pandas as pd

# --- forca UTF-8 na saida, evita UnicodeEncodeError no Windows ---
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT = []
def w(s=""):
    print(s)
    OUT.append(s)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_csv(p):
    """Detecta separador e separador decimal."""
    best, meta = None, None
    for sep in [";", ",", "\t"]:
        for dec in [",", "."]:
            try:
                df = pd.read_csv(p, sep=sep, decimal=dec)
            except Exception:
                continue
            if df.shape[1] < 2:
                continue
            n_num = sum(pd.api.types.is_numeric_dtype(df[c]) for c in df.columns)
            score = (df.shape[1], n_num)
            if best is None or score > best:
                best, meta = score, (df, sep, dec)
    if meta is None:
        return pd.read_csv(p), "?", "?"
    return meta


def describe(name, obj, depth=0, maxdepth=6):
    pad = "  " * depth
    if depth > maxdepth:
        w(f"{pad}- `{name}`: (profundidade maxima)")
        return
    if isinstance(obj, np.ndarray):
        if obj.dtype.names:
            w(f"{pad}- `{name}`: STRUCT  shape={obj.shape}  campos={list(obj.dtype.names)}")
            if obj.size:
                first = obj.flat[0]
                for fld in obj.dtype.names:
                    try:
                        describe(fld, first[fld], depth + 1, maxdepth)
                    except Exception as e:
                        w(f"{pad}  - `{fld}`: <ilegivel: {e}>")
        elif obj.dtype == object:
            w(f"{pad}- `{name}`: CELL  shape={obj.shape}  ({obj.size} elementos)")
            if obj.size:
                describe(f"{name}[0]", obj.flat[0], depth + 1, maxdepth)
        elif obj.ndim == 3:
            w(f"{pad}- `{name}`: *** VOLUME 3D ***  shape={obj.shape}  dtype={obj.dtype}")
            w(f"{pad}    min={obj.min():.1f}  max={obj.max():.1f}  mean={obj.mean():.1f}")
        elif obj.ndim == 2 and min(obj.shape) > 4:
            w(f"{pad}- `{name}`: matriz 2D  shape={obj.shape}  dtype={obj.dtype}  "
              f"min={obj.min():.3g} max={obj.max():.3g}")
        elif obj.size <= 20:
            w(f"{pad}- `{name}`: array  shape={obj.shape}  dtype={obj.dtype}  "
              f"valores={obj.ravel().tolist()}")
        else:
            w(f"{pad}- `{name}`: array  shape={obj.shape}  dtype={obj.dtype}  "
              f"min={obj.min():.3g} max={obj.max():.3g}")
    elif isinstance(obj, (str, bytes)):
        w(f"{pad}- `{name}`: str = {obj!r}")
    elif isinstance(obj, dict):
        w(f"{pad}- `{name}`: dict  chaves={list(obj.keys())}")
        for k, v in obj.items():
            if not k.startswith("__"):
                describe(k, v, depth + 1, maxdepth)
    else:
        w(f"{pad}- `{name}`: {type(obj).__name__} = {repr(obj)[:100]}")


def main(raw_dir):
    raw = Path(raw_dir)
    files = sorted(p for p in raw.iterdir() if p.is_file() and not p.name.startswith("."))

    w("# VAE-001 - Fase 0: Inventario do dataset")
    w()
    w("Dataset: ct-uroliths-freiburg - DOI 10.6084/m9.figshare.21992264")
    w("Kellner E, Neubauer J. 2023-02-08. Licenca: CC BY 4.0.")
    w()

    w("## 1. Arquivos e integridade")
    w()
    w("| Arquivo | Tamanho | SHA-256 |")
    w("|---|---|---|")
    for p in files:
        w(f"| `{p.name}` | {p.stat().st_size:,} B | `{sha256(p)}` |")
    w()

    # ---------- CSV ----------
    w("## 2. Tabela de referencia (CSV)")
    w()
    for p in [f for f in files if f.suffix.lower() == ".csv"]:
        df, sep, dec = load_csv(p)
        w(f"### `{p.name}`")
        w()
        w(f"- Separador: `{sep}`   Separador decimal: `{dec}`")
        w(f"- Linhas: **{len(df)}**   Colunas: **{len(df.columns)}**")
        w()
        w("| Coluna | dtype | n nao-nulo | n unicos | min | max |")
        w("|---|---|---|---|---|---|")
        for c in df.columns:
            s = df[c]
            if pd.api.types.is_numeric_dtype(s):
                w(f"| `{c}` | {s.dtype} | {s.notna().sum()} | {s.nunique()} "
                  f"| {s.min():.4g} | {s.max():.4g} |")
            else:
                w(f"| `{c}` | {s.dtype} | {s.notna().sum()} | {s.nunique()} | - | - |")
        w()

        # categoricas: mostrar os niveis (necessario para saber se ha origem/composicao)
        for c in df.columns:
            s = df[c]
            if not pd.api.types.is_numeric_dtype(s) and s.nunique() <= 25:
                w(f"**Niveis de `{c}`:**")
                w()
                w("```")
                w(s.value_counts(dropna=False).to_string())
                w("```")
                w()

        num = df.select_dtypes(include=[np.number])
        if len(num.columns):
            w("**Distribuicao da referencia** (caracteristica basal, nao e desfecho):")
            w()
            w("```")
            w(num.describe().to_string())
            w("```")
            w()

        # estratos do protocolo
        dcol = next((c for c in df.columns if "diam" in c.lower()), None)
        if dcol and pd.api.types.is_numeric_dtype(df[dcol]):
            bins = [0, 5, 10, 20, np.inf]
            labs = ["< 5 mm", "5-10 mm", "10-20 mm", "> 20 mm"]
            cnt = pd.cut(df[dcol], bins=bins, labels=labs, right=False)\
                    .value_counts().reindex(labs)
            w(f"**Populacao dos estratos do protocolo** (via `{dcol}`):")
            w()
            w("| Estrato | n |")
            w("|---|---|")
            for k, v in cnt.items():
                w(f"| {k} | {int(v) if pd.notna(v) else 0} |")
            w()
            w("> O estrato >= 10 mm e o desfecho primario. Se estiver pouco povoado,")
            w("> o estudo perde poder - registrar como limitacao ANTES de rodar.")
            w()

        w("**ACHADOS CRITICOS DO CSV:**")
        w()
        cols = [c.lower() for c in df.columns]
        raters = any(k in c for c in cols for k in ("rater", "obs", "reader"))
        origem = any(k in c for c in cols for k in ("orig", "spec", "human", "dog", "canin", "anim"))
        w(f"- Medicoes individuais dos 3 avaliadores: **{'SIM' if raters else 'NAO'}**")
        w(f"- Coluna de origem (humano/canino): **{'SIM' if origem else 'NAO'}**")
        w("- Se ambas forem NAO aqui, verificar no `.mat` (secao 3). Se nao estiverem")
        w("  la tampouco, o protocolo precisa de emenda (Secoes 5 e 8) e provavelmente")
        w("  de contato com os autores.")
        w()

    # ---------- MAT ----------
    w("## 3. Dados de imagem (MATLAB)")
    w()
    for p in [f for f in files if f.suffix.lower() == ".mat"]:
        w(f"### `{p.name}`")
        w()
        ok = False
        try:
            from scipy.io import loadmat
            m = loadmat(p, squeeze_me=False, struct_as_record=True)
            w("- Formato: MAT v7 ou anterior (scipy.io.loadmat)")
            w()
            for k, v in m.items():
                if not k.startswith("__"):
                    describe(k, v)
            ok = True
        except NotImplementedError:
            pass
        except Exception as e:
            w(f"- scipy.io.loadmat falhou: {e}")

        if not ok:
            try:
                import h5py
                w("- Formato: MAT v7.3 (HDF5, h5py)")
                w()
                with h5py.File(p, "r") as f:
                    def visit(name, obj):
                        if isinstance(obj, h5py.Dataset):
                            w(f"- `{name}`: shape={obj.shape} dtype={obj.dtype}")
                    f.visititems(visit)
                ok = True
            except Exception as e:
                w(f"- FALHA ao ler como HDF5: {e}")
        w()

    # ---------- perguntas ----------
    w("## 4. Perguntas que viram emenda ao protocolo")
    w()
    for q in [
        "1. Espacamento do voxel esta no arquivo? Se nao, assumimos 0,7 x 0,7 x 0,7 mm "
        "do artigo - e isso vira premissa documentada, nao dado verificado.",
        "2. Os volumes 3D sao VOIs recortados ou exames inteiros? (ver shape) "
        "Se recortados, o criterio de exclusao por VAZAMENTO (Secao 11) e inaplicavel.",
        "3. Um calculo por volume, ou varios? Define se ha logica de semente.",
        "4. As medicoes individuais dos 3 avaliadores existem? Se nao, a Secao 5 cai.",
        "5. Ha informacao de origem (humano/canino)? Se nao, a Secao 8 e inexequivel.",
        "6. Unidades da referencia: Volume em mL ou mm3? Diameter em mm?",
        "7. Os dados ja vem em UH, ou ha escala a aplicar? (ver min/max dos volumes 3D)",
    ]:
        w(q)
        w()


if __name__ == "__main__":
    raw_dir = sys.argv[1] if len(sys.argv) > 1 else "data/raw"
    main(raw_dir)
    os.makedirs("results", exist_ok=True)
    with open("results/fase0_inventario.md", "w", encoding="utf-8") as f:
        f.write("\n".join(OUT) + "\n")
    print("\n>>> Salvo em results/fase0_inventario.md")

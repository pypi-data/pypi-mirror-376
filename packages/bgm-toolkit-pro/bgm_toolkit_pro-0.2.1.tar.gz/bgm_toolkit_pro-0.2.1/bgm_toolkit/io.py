import os, yaml, numpy as np, pandas as pd
def load_config(path):
    with open(path, 'r', encoding='utf-8') as f: return yaml.safe_load(f)
def ensure_output_dir(d):
    os.makedirs(d, exist_ok=True); return d
def validate_inputs(S_df,U_df,capitals=('E','C','S')):
    for c in capitals:
        if c not in S_df.columns: raise ValueError(f"students missing column: {c}")
        if c not in U_df.columns: raise ValueError(f"universities missing column: {c}")
    S_df=S_df.copy(); U_df=U_df.copy()
    S_df[list(capitals)]=S_df[list(capitals)].apply(pd.to_numeric, errors='coerce')
    U_df[list(capitals)]=U_df[list(capitals)].apply(pd.to_numeric, errors='coerce')
    if S_df[list(capitals)].isna().any().any(): raise ValueError("students has non-numeric values in capitals")
    if U_df[list(capitals)].isna().any().any(): raise ValueError("universities has non-numeric values in capitals")
    return S_df,U_df

import numpy as np
import pandas as pd


def normalize_capitals(df, cols=("E", "C", "S")):
    df = df.copy()
    for c in cols:
        mn, mx = df[c].min(), df[c].max()
        df[c] = 0.0 if mx == mn else (df[c] - mn) / (mx - mn)
    return df


def capital_volume(df_or_array, cols=("E", "C", "S")):
    if isinstance(df_or_array, pd.DataFrame):
        return df_or_array[list(cols)].sum(axis=1).to_numpy()
    arr = np.asarray(df_or_array)
    return arr.sum(axis=-1)


def to_composition(df, cols=("E", "C", "S"), eps=1e-9):
    df = df.copy()
    X = df[list(cols)].astype(float).to_numpy() + eps
    df[list(cols)] = X / X.sum(axis=1, keepdims=True)
    return df

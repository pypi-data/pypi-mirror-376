import numpy as np


def group_metrics_basic(S_df, shares, group_cols):
    out = {}
    if not group_cols:
        return out
    df = S_df.reset_index(dropna=False).copy()
    top_idx = shares.argmax(axis=1)
    df["top_uni_index"] = top_idx
    grp = df.groupby(group_cols, dropna=False)
    access = grp["top_uni_index"].value_counts(normalize=True).rename("rate").reset_index()
    access = access.rename(columns={"top_uni_index": "uni_index"})
    out["access_rate"] = access
    top_share = shares[np.arange(shares.shape[0]), top_idx]
    df["top_share"] = top_share
    out["top1_share_by_group"] = (
        df.groupby(group_cols, dropna=False)["top_share"].mean().reset_index()
    )
    return out

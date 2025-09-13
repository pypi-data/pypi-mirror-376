import numpy as np
import pandas as pd
import statsmodels.api as sm


def ols_elasticities(H, Ci, Cj, D):
    df = pd.DataFrame(
        {
            "logH": np.log(H.reshape(-1) + 1e-12),
            "logCi": np.log(np.repeat(Ci, H.shape[1], axis=1).reshape(-1) + 1e-12),
            "logCj": np.log(np.tile(Cj, (H.shape[0], 1)).reshape(-1) + 1e-12),
            "logD": np.log(D.reshape(-1) + 1e-12),
        }
    )
    X = sm.add_constant(df[["logCi", "logCj", "logD"]])
    y = df["logH"]
    return sm.OLS(y, X).fit(cov_type="HC1")


def poisson_gravity_fit(counts, logCj, logD, chooser_ids=None):
    df = pd.DataFrame({"y": counts, "logCj": logCj, "logD": logD})
    if chooser_ids is not None:
        df["chooser"] = chooser_ids
        X = pd.get_dummies(df["chooser"], prefix="i", drop_first=True)
        X = pd.concat(
            [pd.Series(1.0, index=df.index, name="const"), df[["logCj", "logD"]], X], axis=1
        )
    else:
        X = pd.concat([pd.Series(1.0, index=df.index, name="const"), df[["logCj", "logD"]]], axis=1)
    model = sm.GLM(df["y"], X, family=sm.families.Poisson())
    return model.fit(cov_type="HC1")

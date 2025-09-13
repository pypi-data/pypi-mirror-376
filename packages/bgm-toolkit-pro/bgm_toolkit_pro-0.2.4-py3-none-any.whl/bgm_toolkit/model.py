import numpy as np
import pandas as pd


def gravity_H(C_i, C_j, D_ij, beta1=1.0, beta2=1.0, beta3=1.0, delta=1.0, eps=1e-12):
    C_i = np.asarray(C_i, float)
    C_j = np.asarray(C_j, float)
    D_ij = np.asarray(D_ij, float) + eps
    return delta * (np.power(C_i, beta1) * np.power(C_j, beta2)) / np.power(D_ij, beta3)


def choice_shares(H_row):
    import numpy as np

    h = np.asarray(H_row, float)
    return h / (h.sum() if h.sum() > 0 else 1.0)


def log_form_design(H, C_i, C_j, D_ij, eps=1e-12):
    import numpy as np

    return pd.DataFrame(
        {
            "logH": np.log(np.asarray(H) + eps),
            "logCi": np.log(np.asarray(C_i) + eps),
            "logCj": np.log(np.asarray(C_j) + eps),
            "logD": np.log(np.asarray(D_ij) + eps),
        }
    )


def delta_from_intercept(alpha):
    import numpy as np

    return float(np.exp(alpha))

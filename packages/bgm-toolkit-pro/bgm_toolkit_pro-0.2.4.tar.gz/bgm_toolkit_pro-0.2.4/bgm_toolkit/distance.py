import numpy as np


def pairwise_euclidean(S, U, eps=1e-9):
    S = np.asarray(S, float)
    U = np.asarray(U, float)
    Sd = (S**2).sum(axis=1, keepdims=True)
    Ud = (U**2).sum(axis=1, keepdims=True).T
    D2 = Sd + Ud - 2 * (S @ U.T)
    return np.sqrt(np.maximum(D2, eps))


def pairwise_weighted(S, U, w, eps=1e-9):
    if w is None:
        raise ValueError("weights required for metric='weighted'")
    w = np.asarray(w, float)
    S = np.asarray(S, float) * np.sqrt(w)
    U = np.asarray(U, float) * np.sqrt(w)
    return pairwise_euclidean(S, U, eps=eps)


def pairwise_mahalanobis(S, U, eps=1e-9):
    S = np.asarray(S, float)
    U = np.asarray(U, float)
    X = np.vstack([S, U])
    C = np.cov(X, rowvar=False)
    C += np.eye(C.shape[0]) * eps
    Ci = np.linalg.inv(C)
    sCs = (S @ Ci * S).sum(axis=1, keepdims=True)
    uCu = (U @ Ci * U).sum(axis=1, keepdims=True).T
    cross = S @ Ci @ U.T
    D2 = sCs + uCu - 2 * cross
    return np.sqrt(np.maximum(D2, eps))


def _safe_norm(X, eps=1e-12):
    n = np.linalg.norm(X, axis=1, keepdims=True)
    return np.where(n < eps, eps, n)


def pairwise_cosine(S, U, eps=1e-12):
    S = np.asarray(S, float)
    U = np.asarray(U, float)
    Sn = S / _safe_norm(S, eps)
    Un = U / _safe_norm(U, eps)
    # cosine distance = 1 - cosine similarity
    return 1.0 - (Sn @ Un.T)


def pairwise_aitchison(S, U, eps=1e-9):
    S = np.asarray(S, float)
    U = np.asarray(U, float)
    S = np.clip(S, eps, None)
    U = np.clip(U, eps, None)
    S = S / S.sum(axis=1, keepdims=True)
    U = U / U.sum(axis=1, keepdims=True)
    lS = np.log(S)
    lU = np.log(U)
    cS = lS - lS.mean(axis=1, keepdims=True)
    cU = lU - lU.mean(axis=1, keepdims=True)
    Sd = (cS**2).sum(axis=1, keepdims=True)
    Ud = (cU**2).sum(axis=1, keepdims=True).T
    D2 = Sd + Ud - 2 * (cS @ cU.T)
    return np.sqrt(np.maximum(D2, eps))


def pairwise_distance(metric, S, U, weights=None, eps=1e-9):
    m = (metric or "euclidean").lower()
    if m == "euclidean":
        return pairwise_euclidean(S, U, eps=eps)
    elif m == "weighted":
        return pairwise_weighted(S, U, weights, eps=eps)
    elif m == "mahalanobis":
        return pairwise_mahalanobis(S, U, eps=eps)
    elif m == "cosine":
        return pairwise_cosine(S, U, eps=eps)
    elif m == "aitchison":
        return pairwise_aitchison(S, U, eps=eps)
    else:
        raise ValueError(
            f"unknown distance metric: {metric}; valid options = "
            f"euclidean, weighted, mahalanobis, cosine, aitchison"
        )

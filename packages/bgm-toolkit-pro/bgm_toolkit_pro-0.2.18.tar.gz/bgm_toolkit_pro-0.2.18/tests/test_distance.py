import numpy as np

from bgm_toolkit.distance import pairwise_distance

X = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
Y = np.array([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])


def test_shapes_and_nonneg():
    D = pairwise_distance("euclidean", X, Y)
    assert D.shape == (2, 2)
    assert (D >= 0).all()


def test_weighted_identity():
    D1 = pairwise_distance("euclidean", X, Y)
    D2 = pairwise_distance("weighted", X, Y, weights=[1, 1, 1])
    assert np.allclose(D1, D2)


def test_cosine_bounds():
    D = pairwise_distance("cosine", X + 1e-9, Y + 1e-9)
    assert ((D >= 0) & (D <= 2)).all()

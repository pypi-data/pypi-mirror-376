from wnet import Distribution, Distribution_1D, WassersteinNetwork
from wnetalign import WNetAligner
from wnet.distances import wrap_distance_function
import numpy as np


def test_1d():
    E = Distribution_1D([1], [1])
    T = Distribution_1D([2], [1])
    solver = WNetAligner(E, [T], lambda x, y: np.linalg.norm(x - y, axis=0), 10, 10, 100)
    #solver = WassersteinSolver(E, [T], [SimpleTrash(10)])
    solver.set_point([1])
    assert solver.total_cost() == 1


def test_2d():
    s1_pos = np.array([[0, 1, 0], [0, 0, 1]])
    s1_int = np.array([1, 1, 1])
    s1 = Distribution(s1_pos, s1_int)
    s2_pos = np.array([[1, 1, 0], [1, 0, 1]])
    s2_int = np.array([1, 1, 1])
    s2 = Distribution(s2_pos, s2_int)
    solver = WNetAligner(s1, [s2], lambda x, y: np.linalg.norm(x - y, axis=0), 1000000, 1000000, 1000)
    solver.set_point([1])
    # print(solver.run())
    assert solver.total_cost() == 1.414

    # new algo
    DG = WassersteinNetwork(
        s1, [s2], wrap_distance_function(lambda x, y: 1000 * np.linalg.norm(x - y, axis=0)), 5000
    )
    DG.add_simple_trash(1000000)
    DG.build()

    DG.solve()
    assert DG.total_cost() == 1414



if __name__ == "__main__":
    test_1d()
    test_2d()
    print("Everything passed")

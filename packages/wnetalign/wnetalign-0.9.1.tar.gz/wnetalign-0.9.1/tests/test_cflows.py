import numpy as np


from wnet.distribution import Distribution
from wnetalign.aligner import WNetAligner as Solver


def test_flows():
    S1 = Distribution(np.array([[1, 2, 30]]), np.array([1, 4, 3]))
    S2 = Distribution(np.array([[1, 4, 30, 31]]), np.array([5, 1, 1, 1]))

    dist_fun = lambda x, y: np.linalg.norm(x - y, axis=0)
    trash_cost = 10
    max_distance = 100
    solver = Solver(
        empirical_spectrum=S1,
        theoretical_spectra=[S2],
        distance_function=dist_fun,
        max_distance=max_distance,
        trash_cost=trash_cost,
        scale_factor=None,
    )

    solver.set_point([1])

    solver.print_diagnostics()

    print("Flows:")
    for flow in solver.flows():
        print(flow)

    #DGW = DecompositableGraphWrapper(solver.graph)
    #SG = list(DGW.get_subgraphs())[0]
    #print(SG.as_nx_graph())
    #SG.show()


if __name__ == "__main__":
    test_flows()
    print("Everything passed")

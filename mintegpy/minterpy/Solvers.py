# -*- coding:utf-8 -*-
import numpy as np

from mintegpy.minterpy.MultiIndicesTree import MultiIndicesTree

# TODO define slots for all classes


def dds_1d(grid_values, fct_values):
    # https://en.wikipedia.org/wiki/Divided_differences
    # https://stackoverflow.com/questions/14823891/newton-s-interpolating-polynomial-python
    n = len(grid_values)
    grid_values = np.copy(grid_values)
    c = np.copy(fct_values)  # newton coefficients
    for k in range(1, n):
        c[k:] = (c[k:] - c[k - 1]) / (grid_values[k:] - grid_values[k - 1])
    return c


class DDS:

    def __init__(self, *args, **kwargs):
        pass

    def run(self, m, N, tree, F, Points, gamma, I, J):
        # 1D DDS FIXME KeyError: (0, -1)
        if m == 1:
            n = tree[(I - 1, tree[(I, J)].parent[0])].split[0]
            for i in range(n):
                for j in range(i + 1, n):
                    F[j] = (F[j] - F[i]) / (Points[0, j] - Points[0, i])

            return F

        #if m == 1:
        #    dds_1d(Points[0,:N], F)

        # nD DDS
        N0 = tree[(I, J)].split[0]  # left subtree
        N1 = tree[(I, J)].split[1]  # right subtree
        F0 = F[0:N0]
        F1 = F[N0:N]

        # Project F0 onto F1 and compute(F1 - F0) / QH
        s0 = 1
        s1 = 0
        pn = 0

        # Traverse binary tree
        if N1 > 1:

            PF0 = F0
            # PF0 = np.arange(len(F0))

            pn = tree[(I, J)].pro_number
            for i in range(pn):
                PF0_index2 = np.ones(len(PF0), dtype=bool)
                Pro = tree[(I, J)].project[(1, i + 1)]
                k0 = Pro[0]
                s1 = s1 + Pro[2]

                if k0 > 0:
                    l = 0 # TODO
                    jj = np.arange(int(k0), dtype=np.int)
                    PF0_index2[Pro[3 + jj].astype('int') - 1] = False
                    # for j in range(int(k0)):
                    #    PF0 = np.delete(PF0, int(Pro[3 + j]) - l - 1)
                    #    l = l + 1
                QH = Points[m - 1, int(gamma[m - 1]) + i + 1] - Points[m - 1, int(gamma[m - 1])]
                PF0 = PF0[PF0_index2]

                F1[int(s0) - 1:int(s1)] = (F1[int(s0) - 1:int(s1)] - PF0[0:int(Pro[2])]) / QH
                s0 = s0 + Pro[2]

        # Substract the constant part if existing
        if s1 < N1 or N1 == 1:
            QH = Points[m - 1, int(gamma[m - 1]) + pn + 1] - Points[m - 1, int(gamma[m - 1])]
            F1[N1 - 1] = (F1[N1 - 1] - F0[0]) / QH

        # Recursion
        gamma[m - 1] = gamma[m - 1] + 1

        if m > 1 and pn >= 1:
            tree_child1 = tree[(I, J)].child[0]
            tree_child2 = tree[(I, J)].child[1]
            o1 = self.run(m - 1, N0, tree, F0.copy(), Points, gamma.copy(), I + 1, tree_child1)
            o2 = self.run(m, N1, tree, F1.copy(), Points, gamma.copy(), I + 1, tree_child2)
            out = np.concatenate([o1, o2], axis=-1)
        elif m > 1:
            tree_child1 = tree[(I, J)].child[0]
            o1 = self.run(m - 1, N0, tree, F0.copy(), Points, gamma.copy(), I + 1, tree_child1)
            out = np.concatenate([o1, F1], axis=-1)
        elif m == 1 and pn >= 1:
            tree_child2 = tree[(I, J)].child[1]
            o2 = self.run(m, N1, tree, F1.copy(), Points, gamma.copy(), I + 1, tree_child2)
            out = np.concatenate([F0, o2], axis=-1)
        else:
            out = np.concatenate([F0, F1], axis=-1)

        return out


# TODO rename: newton solver?!, pip solver?!
# TODO test
class interpol(DDS):
    def __init__(self, M=2, n=2, lp=2,point_kind='leja',optimal = False,split = None):
        DDS.__init__(self)
        self.M = M
        self.n = n
        self.lp = lp
        self.point_kind = point_kind
        self.optimal = optimal
        self.gamma = np.zeros([M])
        self.split  = split
        #print("split interpol",split)
        self.__build_tree()

    def __build_tree(self):
        self.tree = MultiIndicesTree(M=self.M, K=self.n, lpDegree=self.lp,point_kind = self.point_kind,optimal = self.optimal,split = self.split)
        self.nn, self.N = self.tree.PP.shape

    def __call__(self, func):
        F = np.zeros([self.N])
        for i in range(self.N):
            F[i] = func(self.tree.PP[:, i])
        self.D = self.run(self.M, self.N, self.tree.tree, F.copy(), self.tree.GP.copy(), self.gamma.copy(), 1, 1)
        return lambda x: self.tree.eval_lp(x, self.D.copy(), self.M, self.n, self.N, self.gamma.copy(),
                                           self.tree.GP.copy(), self.tree.lpDegree, 1, 1)

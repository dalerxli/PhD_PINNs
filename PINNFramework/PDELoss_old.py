import torch
from torch import Tensor as Tensor
from torch.nn import Module as Module
from torch.nn import MSELoss, L1Loss
from .LossTerm import LossTerm
import numpy as np


class PDELoss(LossTerm):
    def __init__(self, dataset, pde, quad_weights, norm='L2', weight=1.):
        """
        Constructor of the PDE Loss

        Args:
            dataset (torch.utils.Dataset): dataset that provides the residual points
            pde (function): function that represents residual of the PDE
            norm: Norm used for calculation PDE loss
            weight: Weighting for the loss term
        """
        super(PDELoss, self).__init__(dataset, norm, weight)
        self.dataset = dataset
        self.pde = pde
        self.quad_weights = quad_weights
    def __call__(self, x: Tensor, model: Module, quad_weights, norm='L2', **kwargs):
        """
        Call function of the PDE loss. Calculates the norm of the PDE residual

        x: residual points
        model: model that predicts the solution of the PDE
        """

        def FT(f_i, x):
            shift = 1
            C_b = torch.fft(f_i, 1)
            N_2 = int(len(f_i) / 2)
            zer = torch.Tensor([0])
            im_shift = torch.Tensor([2 * np.pi * shift * torch.sum(x)])
            F_y = torch.tensor([torch.complex(C_b[b][0], C_b[b][1]) *
                                torch.exp(torch.complex(zer, torch.Tensor([2 * np.pi * b * (torch.sum(x))])))
                                for b in range(-N_2, N_2)])
            f_star = (torch.exp(torch.complex(zer, im_shift)) * torch.sum(F_y))
            return torch.tensor([torch.real(f_star), torch.imag(f_star)])

        x.requires_grad = True  # setting requires grad to true in order to calculate
        u = model.forward(x)
        # ux = torch.stack([FT(u, x) for i in range(len(x))],0)
        pde_residual = self.pde(x, u, **kwargs)
        if norm == 'L2':
            zeros = torch.zeros(pde_residual.shape, device=pde_residual.device)
            self.loss = torch.nn.MSELoss()(pde_residual,zeros)
        elif norm == 'Quad':
            quad_loss = (np.sum([torch.sum(torch.square(pde_residual[i])) * abs(self.quad_weights[i]) for i in
                                                      range(len(pde_residual))]) ** (1 / 2))
            self.loss = quad_loss
        #quad_loss = (np.sum([torch.sum(torch.square(pde_residual[i])) * abs(self.quad_weights[i]) for i in
        #                     range(len(pde_residual))]) ** (1 / 2))
        #mse_loss = loss(pde_residual, zeros)
        return self.loss* 0 # quad_loss

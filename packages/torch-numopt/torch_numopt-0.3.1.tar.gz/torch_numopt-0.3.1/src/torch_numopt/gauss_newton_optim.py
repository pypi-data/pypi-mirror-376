from __future__ import annotations
from typing import Iterable
import torch
import torch.nn as nn
from torch.autograd.functional import hessian
from torch.func import functional_call
from .second_order_optimizer import SecondOrderOptimizer
from .utils import fix_stability, pinv_svd_trunc
from copy import copy


class GaussNewtonLS(SecondOrderOptimizer):
    """
    Heavily inspired by https://github.com/hahnec/torchimize/blob/master/torchimize/optimizer/gna_opt.py

    Parameters
    ----------

    model: nn.Module
        The model to be optimized
    lr_init: float
        Maximum learning rate in backtracking line search, if the learning rate is set as constant, this will be the value used.
    lr_method: str
        Method to use to initialize the learning rate before applying line search.
    c1: float
        Coefficient of the sufficient increase condition in backtracking line search.
    c2: float
        Coefficient used in the second condition for wolfe conditions.
    tau: float
        Factor used to reduce the step size in each step of the backtracking line search.
    line_search_method: str
        Method used for line search, options are "backtrack" and "constant".
    line_search_cond: str
        Condition to be used in backtracking line search, options are "armijo", "wolfe", "strong-wolfe" and "goldstein".
    solver: str
        Method to use to invert the hessian.
    batch_size: int
        Size of the amount of data to use at a time to calculate the hessian matrix.
    """

    def __init__(
        self,
        model: nn.Module,
        lr_init: float = 1,
        lr_method: str = None,
        c1: float = 1e-4,
        c2: float = 0.9,
        tau: float = 0.1,
        line_search_method: str = "backtrack",
        line_search_cond: str = "armijo",
        solver: str = "solve",
        batch_size: int = None,
        **kwargs,
    ):
        super().__init__(
            model,
            lr_init=lr_init,
            lr_method=lr_method,
            line_search_cond=line_search_cond,
            line_search_method=line_search_method,
            c1=c1,
            c2=c2,
            tau=tau,
            batch_size=batch_size,
        )

        self.solver = solver

    def get_step_direction(self, d_p_list, h_list):
        dir_list = [None] * len(d_p_list)
        for i, (d_p, h) in enumerate(zip(d_p_list, h_list)):
            if torch.linalg.cond(h) > 1e8:
                h = fix_stability(h)

            match self.solver:
                case "pinv":
                    h_i = h.pinverse()
                    d2_p = (h_i @ d_p.flatten()).reshape(d_p.shape)
                case "solve":
                    d2_p = torch.linalg.solve(h, d_p.flatten()).reshape(d_p.shape)

            dir_list[i] = d2_p

        return dir_list

    def get_scaling_matrix(self, 
        x: torch.Tensor,
        y: torch.Tensor,
        loss_fn: nn.Module
    ):
        return self.approx_hessian_gn(x, y, loss_fn, vectorize=True)
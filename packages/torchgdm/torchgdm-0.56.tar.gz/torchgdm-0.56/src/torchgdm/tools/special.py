# -*- coding: utf-8 -*-
"""autodiff enabled special functions

- first 4 orders spherical Bessel
- integer order Bessel (1st and 2nd kind)
- integer order modified Bessel (1st and 2nd kind)
- integer order Hankel (1st and 2nd kind)

The functions are implemented through upward recursion. Thus, only integer orders are implemented and the stability of the recursion is limited.
Derivatives are implemented through forward Bessel function relations, based on upward recursions as well, making them even more prone to recursion instability.
The first 5-6 orders (3-4 orders in backward) are typically stable.

Only pure real or pure imaginary arguments are supported so far (except for spherical Bessel which support all complex arguments).

"""
# %%
import warnings

import torch
from torch import vmap
from torchgdm.constants import DTYPE_FLOAT, DTYPE_COMPLEX
from torchgdm.tools.misc import get_default_device


# --- double factorial via recursion (used as fixed value below)
def _doublefactorial(n):
    if n <= 0:
        return 1
    else:
        return n * _doublefactorial(n - 2)


# --- first 4 spherical Bessel functions in pytorch
def sph_j0(x: torch.Tensor, asymptotic_threshold=0.001):
    """spherical Bessel function of zero order

    for numerical stability, use asymptotic solutions at small arguments.

    Args:
        x (torch.Tensor): argument of Bessel function
        asymptotic_threshold (float, optional): threshold below which to use small argument asymptotic approximation. Defaults to 0.001.

    Returns:
        float: bessel result
    """
    x = torch.as_tensor(x, dtype=DTYPE_COMPLEX)
    j0 = torch.where(torch.abs(x) > asymptotic_threshold, torch.sin(x) / x, 1)
    return j0


def sph_j1(x: torch.Tensor, asymptotic_threshold=0.01):
    """spherical Bessel function of first order

    for numerical stability, use asymptotic solutions at small arguments.

    Args:
        x (torch.Tensor): argument of Bessel function
        asymptotic_threshold (float, optional): threshold below which to use small argument asymptotic approximation. Defaults to 0.01.

    Returns:
        float: bessel result
    """
    x = torch.as_tensor(x, dtype=DTYPE_COMPLEX)
    _sin_term = torch.sin(x) / x**2
    _cos_term = torch.cos(x) / x
    j1 = torch.where(torch.abs(x) > asymptotic_threshold, _sin_term - _cos_term, x / 3)
    return j1


def sph_j2(x: torch.Tensor, asymptotic_threshold=0.1):
    """spherical Bessel function of second order

    for numerical stability, use asymptotic solutions at small arguments.

    Args:
        x (torch.Tensor): argument of Bessel function
        asymptotic_threshold (float, optional): threshold below which to use small argument asymptotic approximation. Defaults to 0.1.

    Returns:
        float: bessel result
    """
    x = torch.as_tensor(x, dtype=DTYPE_COMPLEX)
    _sin_term = (3 / x**2 - 1) * (torch.sin(x) / x)
    _cos_term = 3 * torch.cos(x) / x**2
    j2 = torch.where(
        torch.abs(x) > asymptotic_threshold, _sin_term - _cos_term, x**2 / 15
    )
    return j2


def sph_j3(x: torch.Tensor, asymptotic_threshold=0.5):
    """spherical Bessel function of third order

    for numerical stability, use asymptotic solutions at small arguments.

    Args:
        x (torch.Tensor): argument of Bessel function
        asymptotic_threshold (float, optional): threshold below which to use small argument asymptotic approximation. Defaults to 0.5.

    Returns:
        float: bessel result
    """
    x = torch.as_tensor(x, dtype=DTYPE_COMPLEX)
    _sin_term = (15 / x**3 - 6 / x) * (torch.sin(x) / x)
    _cos_term = (15 / x**2 - 1) * (torch.cos(x) / x)
    j3 = torch.where(
        torch.abs(x) > asymptotic_threshold, _sin_term - _cos_term, x**3 / 105
    )
    return j3


# Bessel functions of first kind
# takes and returns purely real values
def _Jn(n, z: torch.Tensor):
    """integer order Bessel functions (first kind) via recurrence formula

    Notes:
        - Currently only supports real arguments using up-recurrence: J_n+1 = (2n/z) J_n - J_n-1
        - the recurrence relation numerically breaks down for large n and small z due to numerical errors.
        - this function uses torch.special, which is not autodiff-capable (as of torch V2.8)

    Args:
        n (int): integer order
        z (torch.Tensor): complex argument

    Raises:
        Exception: mixed real, imag argument

    Returns:
        torch.Tensor: result
    """

    # z = torch.as_tensor(z.real, dtype=DTYPE_COMPLEX)
    z = torch.as_tensor(z, dtype=DTYPE_COMPLEX)
    n = torch.as_tensor(n, dtype=torch.int)

    def true_fn2(n, z):
        return torch.as_tensor(torch.special.bessel_j0(z.real), dtype=DTYPE_COMPLEX)

    def false_fn2(n, z):
        return torch.as_tensor(torch.special.bessel_j1(z.real), dtype=DTYPE_COMPLEX)

    def true_fn1(n, z):
        return torch.cond(n.item() == 0, true_fn2, false_fn2, (n, z))

    def false_fn1(n, z):
        J_nm1 = _Jn(n - 1, z)
        J_nm2 = _Jn(n - 2, z)
        return (2 * (n - 1) / z.real) * J_nm1 - J_nm2

    def true_fn0(n, z):
        return torch.cond(
            ((n.item() == 0) or (n.item() == 1)), true_fn1, false_fn1, (n, z)
        )

    def false_fn0(n, z):
        return ((-1) ** n) * _Jn(-n, z)

    result = torch.cond((n.item() >= 0), true_fn0, false_fn0, (n, z))

    return result


class _gradJn(torch.autograd.Function):
    """add autodiff capability"""

    generate_vmap_rule = True

    @staticmethod
    def forward(n, z):
        return _Jn(n, z)

    @staticmethod
    def setup_context(ctx, inputs, outputs):
        n, z = inputs
        ctx.save_for_backward(z)
        ctx._n = n

    @staticmethod
    def backward(ctx, grad_out):
        (z,) = ctx.saved_tensors
        n = ctx._n
        ddz = grad_out * 0.5 * (_gradJn.apply(n - 1, z) - _gradJn.apply(n + 1, z))
        # return gradient tensor for each input of "forward" (n, z)
        return None, ddz


def Jn(n, z: torch.tensor):
    """integer order Bessel functions (1st kind)

    via recurrence formula

    Notes:
        - Currently only supports real arguments usinf up-recurrence: J_n+1 = (2n/z) J_n - J_n-1
        - the recurrence relation numerically breaks down for large n and small z due to numerical errors.
        - gradients are calculated via d/dx Jn = 1/2 ( Jn-1 - Jn+1 )

    Args:
        n (int): integer order
        z (torch.Tensor): complex argument

    Raises:
        Exception: mixed real, imag argument

    Returns:
        torch.Tensor: result
    """
    z = torch.as_tensor(z.real, dtype=DTYPE_COMPLEX)
    n = torch.as_tensor(n, dtype=torch.int)

    return _gradJn.apply(n, z)


def _Yn(n, z: torch.Tensor):
    """integer order Bessel functions of second kind via recurrence formula

    Notes:
        - Currently only supports real arguments using up-recurrence: Y_n+1 = (2n/z) Y_n - Y_n-1
        - the recurrence relation numerically breaks down for large n and small z due to numerical errors.

    Args:
        n (int): integer order
        z (torch.Tensor): complex argument

    Raises:
        Exception: mixed real, imag argument

    Returns:
        torch.Tensor: result
    """

    z = torch.as_tensor(z, dtype=DTYPE_COMPLEX)
    n = torch.as_tensor(n, dtype=torch.int)

    def true_fn2(n, z):
        return torch.as_tensor(torch.special.bessel_y0(z.real), dtype=DTYPE_COMPLEX)

    def false_fn2(n, z):
        return torch.as_tensor(torch.special.bessel_y1(z.real), dtype=DTYPE_COMPLEX)

    def true_fn1(n, z):
        return torch.cond(n.item() == 0, true_fn2, false_fn2, (n, z))

    def false_fn1(n, z):
        Y_nm1 = _Yn(n - 1, z)
        Y_nm2 = _Yn(n - 2, z)
        return (2 * (n - 1) / z) * Y_nm1 - Y_nm2

    def true_fn0(n, z):
        return torch.cond(
            ((n.item() == 1) or (n.item() == 0)), true_fn1, false_fn1, (n, z)
        )

    def false_fn0(n, z):
        return ((-1) ** n) * _Yn(-n, z)

    return torch.cond(n.item() >= 0, true_fn0, false_fn0, (n, z))


class _gradYn(torch.autograd.Function):
    """add autodiff capability"""

    # @staticmethod
    # def forward(ctx, n, z):
    #     ctx.save_for_backward(z)
    #     ctx._n = n
    #     return _Yn(n, z)
    generate_vmap_rule = True

    @staticmethod
    def forward(n, z):
        return _Yn(n, z)

    @staticmethod
    def setup_context(ctx, inputs, outputs):
        n, z = inputs
        ctx.save_for_backward(z)
        ctx._n = n

    @staticmethod
    def backward(ctx, grad_out):
        (z,) = ctx.saved_tensors
        n = ctx._n
        ddz = grad_out * 0.5 * (_gradYn.apply(n - 1, z) - _gradYn.apply(n + 1, z))
        # return gradient tensor for each input of "forward" (n, z)
        return None, ddz


def Yn(n, z: torch.Tensor):
    """integer order Bessel functions (2nd kind)

    via recurrence formula

    Notes:
        - real arguments only!
        - use recurrence: Y_n+1 = (2n/z) Y_n - Y_n-1
        - the recurrence relation numerically breaks down for large n and small z due to numerical errors.
        - gradients are calculated via d/dx Yn = 1/2 ( Yn-1 - Yn+1 )

    Args:
        n (int): integer order
        z (torch.Tensor): complex argument

    Raises:
        Exception: mixed real, imag argument

    Returns:
        torch.Tensor: result
    """
    z = torch.as_tensor(z, dtype=DTYPE_COMPLEX)
    n = torch.as_tensor(n, dtype=torch.int)
    return _gradYn.apply(n, z)  # grad takes only real arguments now!


def _In(n, z: torch.Tensor):
    """integer order modified Bessel functions of first kind via recurrence formula

    Notes:
        - supports real arguments only
        - use recurrence: I_n+1 = -(2n/z) I_n + I_n-1
        - the recurrence relation numerically breaks down for large n and small z due to numerical errors.

    Args:
        n (int): integer order
        z (torch.Tensor): complex argument

    Returns:
        torch.Tensor: result
    """
    z = torch.as_tensor(z, dtype=DTYPE_COMPLEX)
    n = torch.as_tensor(n, dtype=torch.int)

    def true_fn2(n, z):
        return torch.as_tensor(
            torch.special.modified_bessel_i0(z.real), dtype=DTYPE_COMPLEX
        )

    def false_fn2(n, z):
        return torch.as_tensor(
            torch.special.modified_bessel_i1(z.real), dtype=DTYPE_COMPLEX
        )

    def true_fn1(n, z):
        return torch.cond(n.item() == 0, true_fn2, false_fn2, (n, z))

    def false_fn1(n, z):
        I_nm1 = _In(n - 1, z)
        I_nm2 = _In(n - 2, z)
        return (-2 * (n - 1) / z.real) * I_nm1 + I_nm2

    def true_fn0(n, z):
        return torch.cond(
            ((n.item() == 1) or (n.item() == 0)), true_fn1, false_fn1, (n, z)
        )

    def false_fn0(n, z):
        return _In(n=-n, z=z)

    return torch.cond(n.item() >= 0, true_fn0, false_fn0, (n, z))


class _gradIn(torch.autograd.Function):
    """add autodiff capability"""

    generate_vmap_rule = True

    @staticmethod
    def forward(n, z):
        return _In(n, z)

    @staticmethod
    def setup_context(ctx, inputs, outputs):
        n, z = inputs
        ctx.save_for_backward(z)
        ctx._n = n

    @staticmethod
    def backward(ctx, grad_out):
        (z,) = ctx.saved_tensors
        n = ctx._n
        ddz = grad_out * 0.5 * (_gradIn.apply(n - 1, z) + _gradIn.apply(n + 1, z))
        # return gradient tensor for each input of "forward" (n, z)
        return None, ddz


def In(n: torch.Tensor, z: torch.Tensor):
    """integer order modified Bessel functions of first kind

    via recurrence formula

    Notes:
        - supports real arguments only
        - use recurrence: I_n+1 = -(2n/z) I_n + I_n-1
        - the recurrence relation numerically breaks down for large n and small z due to numerical errors.
        - gradients are calculated via d/dx In = 1/2 ( In-1 + In+1 )

    Args:
        n (int): integer order
        z (torch.Tensor): complex argument

    Returns:
        torch.Tensor: result

    """
    n = torch.as_tensor(n, dtype=torch.int)
    z = torch.as_tensor(z.real, dtype=DTYPE_COMPLEX)

    return _gradIn.apply(n, z)


def _Kn(n, z: torch.tensor):
    """integer order modified Bessel functions of second kind via recurrence formula

    Notes:
        - supports real arguments only
        - use recurrence: K_n+1 = (2n/z) K_n + K_n-1
        - the recurrence relation numerically breaks down for large n and small z due to numerical errors.

    Args:
        n (int): integer order
        z (torch.Tensor): complex argument

    Returns:
        torch.Tensor: result
    """
    z = torch.as_tensor(z, dtype=DTYPE_COMPLEX)
    n = torch.as_tensor(n, dtype=torch.int)

    def true_fn2(n, z):
        return torch.as_tensor(torch.special.modified_bessel_k0(z.real), dtype=DTYPE_COMPLEX)

    def false_fn2(n, z):
        return torch.as_tensor(torch.special.modified_bessel_k1(z.real), dtype=DTYPE_COMPLEX)

    def true_fn1(n, z):
        return torch.cond(n.item() == 0, true_fn2, false_fn2, (n, z))

    def false_fn1(n, z):
        K_nm1 = _Kn(n - 1, z)
        K_nm2 = _Kn(n - 2, z)
        return ((2 * (n - 1)) / z) * K_nm1 + K_nm2

    def true_fn0(n, z):

        return torch.cond(
            ((n.item() == 1) or (n.item() == 0)), true_fn1, false_fn1, (n, z)
        )

    def false_fn0(n, z):
        return _Kn(n=-n, z=z)

    return torch.cond(n.item() >= 0, true_fn0, false_fn0, (n, z))


class _gradKn(torch.autograd.Function):
    """add autodiff capability"""

    generate_vmap_rule = True

    @staticmethod
    def forward(n, z):
        return _Kn(n, z)

    @staticmethod
    def setup_context(ctx, inputs, outputs):
        n, z = inputs
        ctx.save_for_backward(z)
        ctx._n = n

    @staticmethod
    def backward(ctx, grad_out):
        (z,) = ctx.saved_tensors
        n = ctx._n
        ddz = grad_out * -0.5 * (_gradKn.apply(n - 1, z) + _gradKn.apply(n + 1, z))
        # return gradient tensor for each input of "forward" (n, z)
        return None, ddz


def Kn(n: torch.Tensor, z: torch.Tensor):
    """integer order modified Bessel functions of second kind via recurrence formula

    Notes:
        - supports real arguments only
        - use recurrence: K_n+1 = (2n/z) K_n + K_n-1
        - the recurrence relation numerically breaks down for large n and small z due to numerical errors.
        - gradients are calculated via d/dx Kn = -1/2 ( Kn-1 + Kn+1 )

    Args:
        n (int): integer order
        z (torch.Tensor): complex argument

    Returns:
        torch.Tensor: result
    """
    n = torch.as_tensor(n, dtype=torch.int)
    z = torch.as_tensor(z.real, dtype=DTYPE_COMPLEX)

    return _gradKn.apply(n, z)


# Hankel functions (via Bessel)
def H1n(n: int, z: torch.BoolTensor):
    """integer order Hankel functions of first kind

    Notes:
        - supports real arguments only
        - use: H1_n = J_n + 1j * Y_n
        - the recurrence relations used in the Bessel functions numerically break down for large n and small z due to numerical errors.

    Args:
        n (int): integer order
        z (torch.Tensor): complex argument

    Returns:
        torch.Tensor: result
    """
    z = torch.as_tensor(z, dtype=DTYPE_COMPLEX)
    n = torch.as_tensor(n, dtype=torch.int)

    return Jn(n, z) + 1j * Yn(n, z)


def H2n(n, z: torch.Tensor):
    """integer order Hankel functions of second kind

    Notes:
        - supports real arguments only
        - use: H2_n = J_n - 1j * Y_n
        - the recurrence relations used in the Bessel functions numerically break down for large n and small z due to numerical errors.

    Args:
        n (int): integer order
        z (torch.Tensor): complex argument

    Returns:
        torch.Tensor: result
    """
    z = torch.as_tensor(z, dtype=DTYPE_COMPLEX)
    return Jn(n, z) - 1j * Yn(n, z)


# # %%
# if __name__ == "__main__":
#     from scipy.special import jv, yv, iv, kv, hankel1, hankel2
#     from scipy.special import jvp, yvp, ivp, kvp, h1vp, h2vp
#     import matplotlib.pyplot as plt
#     from torchgdm.tools.misc import to_np

#     n = 1
#     z = torch.linspace(0.1, 1, 500, dtype=torch.float32)# * 1j

#     def eval_special(n, z, f_scipy, deriv_scipy, f_torch):
#         z = z.clone()
#         z.requires_grad = True

#         j_scipy = f_scipy(n, to_np(z))
#         ddx_j_scipy = deriv_scipy(n, to_np(z).conj())
#         j_torch = f_torch(n, z)
#         ddx_j_torch = torch.autograd.grad(
#             outputs=j_torch,
#             inputs=[z],
#             grad_outputs=torch.ones_like(j_torch),
#         )[0]
#         return j_scipy, j_torch, ddx_j_scipy, ddx_j_torch

#     # compare with scipy
#     # bessel
#     j_scipy, j_torch, ddz_j_s, ddz_j_t = eval_special(n, z, jv, jvp, Jn)
#     y_scipy, y_torch, ddz_y_s, ddz_y_t = eval_special(n, z, yv, yvp, Yn)

#     # modified bessel
#     i_scipy, i_torch, ddz_i_s, ddz_i_t = eval_special(n, z, iv, ivp, In)
#     k_scipy, k_torch, ddz_k_s, ddz_k_t = eval_special(n, z, kv, kvp, Kn)

#     # hankel
#     h1_scipy, h1_torch, ddz_h1_s, ddz_h1_t = eval_special(n, z, hankel1, h1vp, H1n)
#     h2_scipy, h2_torch, ddz_h2_s, ddz_h2_t = eval_special(n, z, hankel2, h2vp, H2n)

#     # # plot imag part
#     # z=z.imag
#     # j_scipy, j_torch, ddz_j_s, ddz_j_t = j_scipy.imag, j_torch.imag, ddz_j_s.imag, ddz_j_t.imag
#     # y_scipy, y_torch, ddz_y_s, ddz_y_t = y_scipy.imag, y_torch.imag, ddz_y_s.imag, ddz_y_t.imag


#     # - plot
#     plt.figure(figsize=(10, 4))
#     plt.subplot(231)
#     plt.plot(z.numpy(), j_scipy, label="scipy")
#     plt.plot(z.numpy(), to_np(j_torch), dashes=[2, 2], label="J - torch")
#     plt.legend()

#     plt.subplot(232)
#     plt.plot(z.numpy(), y_scipy, label="scipy")
#     plt.plot(z.numpy(), to_np(y_torch), dashes=[2, 2], label="Y - torch")
#     plt.legend()

#     plt.subplot(234)
#     plt.plot(z.numpy(), i_scipy, label="scipy")
#     plt.plot(z.numpy(), to_np(i_torch), dashes=[2, 2], label="I - torch")
#     plt.legend()

#     plt.subplot(235)
#     plt.plot(z.numpy(), k_scipy, label="scipy")
#     plt.plot(z.numpy(), to_np(k_torch), dashes=[2, 2], label="K - torch")
#     plt.legend()

#     plt.subplot(233)
#     plt.plot(z.numpy(), h1_scipy, label="scipy")
#     plt.plot(z.numpy(), to_np(h1_torch), dashes=[2, 2], label="H1 - torch")
#     plt.legend()

#     plt.subplot(236)
#     plt.plot(z.numpy(), h2_scipy, label="scipy")
#     plt.plot(z.numpy(), to_np(h2_torch), dashes=[2, 2], label="H2 - torch")

#     plt.legend()

#     plt.show()

#     # - plot
#     plt.figure(figsize=(10, 4))
#     plt.subplot(231)
#     plt.plot(z.numpy(), ddz_j_s, label="scipy")
#     plt.plot(z.numpy(), to_np(ddz_j_t), dashes=[2, 2], label="ddz J - AD")
#     plt.legend()

#     plt.subplot(232)
#     plt.plot(z.numpy(), ddz_y_s, label="scipy")
#     plt.plot(z.numpy(), to_np(ddz_y_t), dashes=[2, 2], label="ddz Y - AD")
#     plt.legend()

#     plt.subplot(234)
#     plt.plot(z.numpy(), ddz_i_s, label="scipy")
#     plt.plot(z.numpy(), to_np(ddz_i_t), dashes=[2, 2], label="ddz I - AD")
#     plt.legend()

#     plt.subplot(235)
#     plt.plot(z.numpy(), ddz_k_s, label="scipy")
#     plt.plot(z.numpy(), to_np(ddz_k_t), dashes=[2, 2], label="ddz K - AD")
#     plt.legend()

#     plt.subplot(233)
#     plt.plot(z.numpy(), ddz_h1_s, label="scipy")
#     plt.plot(z.numpy(), to_np(ddz_h1_t), dashes=[2, 2], label="ddz H1 - AD")
#     plt.legend()

#     plt.subplot(236)
#     plt.plot(z.numpy(), ddz_h2_s, label="scipy")
#     plt.plot(z.numpy(), to_np(ddz_h2_t), dashes=[2, 2], label="ddz H2 - torch")

#     plt.legend()

#     plt.show()

#     # %%

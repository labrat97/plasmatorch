from .defaults import *



@ts
def pi(dtype:t.dtype=DEFAULT_DTYPE) -> t.Tensor:
    """Gets the value of Pi in the requested datatype.

    Args:
        dtype (t.dtype, optional): The datatype to return Pi in. Defaults to DEFAULT_DTYPE.

    Returns:
        t.Tensor: The value of Pi as a tensor of size (1).
    """
    return t.tensor((3.14159265358979323846264338327950288419716939937510), dtype=dtype).detach()



@ts
def tau(dtype:t.dtype=DEFAULT_DTYPE) -> t.Tensor:
    """Gets the value of Tau (2. * Pi) in the requested datatype.

    Args:
        dtype (t.dtype, optional): The datatype to return Tau in. Defaults to DEFAULT_DTYPE.

    Returns:
        t.Tensor: The value of Tau as a tensor of size (1).
    """
    return pi() * 2.



@ts
def egamma(dtype:t.dtype=DEFAULT_DTYPE) -> t.Tensor:
    """Gets the value of the Euler-Mascheroni constant in the requested datatype.

    Args:
        dtype (t.dtype, optional): The datatype to return the Euler-Mascheroni constant in. Defaults to DEFAULT_DTYPE.

    Returns:
        t.Tensor: The value of the Euler-Mascheroni constant as a tensor of size (1).
    """
    return t.tensor((0.57721566490153286060651209008240243104215933593992), dtype=dtype).detach()



@ts
def phi(dtype:t.dtype=DEFAULT_DTYPE) -> t.Tensor:
    """Calculates the value of Phi in/with the requested datatype.

    Args:
        dtype (t.dtype, optional): The datatype to perform the computation in. Defaults to DEFAULT_DTYPE.

    Returns:
        t.Tensor: The value of Phi as a tensor of size (1).
    """
    one = t.ones((1), dtype=dtype).detach()
    square = t.sqrt(one * 5)

    return ((one + square) / 2).detach()



@ts
def asigphi(dtype:t.dtype=DEFAULT_DTYPE) -> t.Tensor:
    """Computes the inverse of a simoid activation on Phi so that the output of a sigmoid activation
    can come out as the golden ratio.

    Args:
        dtype (t.dtype, optional): The datatype to perform the computation in. Defaults to DEFAULT_DTYPE.

    Returns:
        t.Tensor: The value of the inverse of a sigmoid of the golden ratio.
    """
    return -t.log(phi(dtype=dtype) - 1)

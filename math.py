from .defaults import *
from .conversions import toComplex, nantonum

@ts
def pi() -> t.Tensor:
    return (t.ones((1)) * 3.14159265358979323846264338327950288419716939937510).detach()

@ts
def emconst() -> t.Tensor:
    return (t.ones((1)) * 0.57721566490153286060651209008240243104215933593992).detach()

@ts
def phi() -> t.Tensor:
    one = t.ones((1)).detach()
    square = t.sqrt(one * 5)

    return ((one + square) / 2).detach()

@ts
def asigphi() -> t.Tensor:
    return -t.log(phi() - 1)

@ts
def xbias(n:int, bias:int=0):
    composer = t.zeros((n)).add(bias)
    for i in range(n):
        composer[i].add_(i)
    return composer

@ts
def latticeParams(dims:int, basisParam:t.Tensor=phi()) -> t.Tensor:
    powers = xbias(n=dims, bias=0)
    return basisParam ** (-powers)

@ts
def i() -> t.Tensor:
    return t.view_as_complex(t.stack(
        (t.zeros(1), t.ones(1)), \
        dim=-1)).detach()

@ts
def isoftmax(x:t.Tensor, dim:int) -> t.Tensor:
    # Normal softmax
    if not x.is_complex(): 
        return t.softmax(x, dim=dim)

    # Imaginary softmax
    angle:t.Tensor = x.angle()
    magnitude:t.Tensor = x.abs()
    softMagnitude:t.Tensor = t.softmax(magnitude, dim=dim)
    
    # Convert back to imaginary
    newReal:t.Tensor = softMagnitude * t.cos(angle)
    newImag:t.Tensor = softMagnitude * t.sin(angle)
    
    # Return in proper datatype
    return t.view_as_complex(t.stack((newReal, newImag), dim=-1))

@ts
def nsoftmax(x:t.Tensor, dims:List[int]) -> t.Tensor:
    # Because n^0 == 1, this should be an appropriate initializer
    result = t.ones_like(x)

    # Creates an n root
    exponent:float = 1. / len(dims)

    # Multiplies each value in the result by the n-root of each isoftmax
    for dim in dims:
        nroot = t.pow(isoftmax(x, dim=dim), exponent)
        result.mul_(nroot)

    return result

@ts
def primishvals(n:int, base:t.Tensor=t.zeros(0, dtype=t.int64), gaussApprox:bool=False) -> t.Tensor:
    # Not in the 6x -+ 1 domain, or starting domain
    if base.size()[-1] < 3:
        base = t.ones(3, dtype=base.dtype)
        base[1] += base[0]
        base[2] += base[1]
    if n <= base.size()[-1]:
        return base[:n]
    
    # Construct the output values
    result:t.Tensor = t.zeros((n), dtype=t.int64).detach()
    result[:base.size()[-1]] = base
    
    # Compute every needed 6x -+ 1 value
    itr:int = base.size()[-1]
    pitr:int = int((itr - 3) / 2) + 1
    while itr < n:
        if itr & 0x1 != 0:
            if gaussApprox:
                result[itr] = (4 * pitr) + 1
            else:
                result[itr] = (6 * pitr) - 1
        else:
            result[itr] = result[itr - 1] + 2
        itr += 1
        pitr  = int((itr - 3) / 2) + 1

    return result

@ts
def realprimishdist(x:t.Tensor, relative:bool=True, gaussApprox:bool=False) -> t.Tensor:
    assert not t.is_complex(x)

    # Collect inverse values
    if gaussApprox:
        iprimeGuessTop:t.Tensor = ((x - 3.) / 4.).type(t.int64)
        iprimeGuessBot:t.Tensor = ((x + 3.) / 4.).type(t.int64)
    else:
        iprimeGuessTop:t.Tensor = ((x - 1.) / 6.).type(t.int64)
        iprimeGuessBot:t.Tensor = ((x + 1.) / 6.).type(t.int64)
    iprimeGuessTop = t.stack((iprimeGuessTop, iprimeGuessTop+1), dim=-1)
    iprimeGuessBot = t.stack((iprimeGuessBot, iprimeGuessBot+1), dim=-1)

    # Compute nearest values
    if gaussApprox:
        primishTop:t.Tensor = (iprimeGuessTop * 4) + 3
        primishBot:t.Tensor = (iprimeGuessBot * 4) - 3
    else:
        primishTop:t.Tensor = (iprimeGuessTop * 6) + 1
        primishBot:t.Tensor = (iprimeGuessBot * 6) - 1

    # Collect the primes into one tensor, add the special primes to the tensor, sort
    primish:t.Tensor = t.cat((primishTop, primishBot), dim=-1)
    specialPrimes:t.Tensor = t.ones_like(primish)[...,:4] * t.tensor([-1, 1, 2, 3])
    primish = t.cat((primish, specialPrimes), dim=-1)
    primish = primish.sort(dim=-1, descending=False).values

    # Find the closest prime approximates
    xish:t.Tensor = t.ones_like(primish) * x.unsqueeze(-1)
    lowidx:t.Tensor = (xish >= primish).type(dtype=x.dtype)
    highidx:t.Tensor = (xish < primish).type(dtype=x.dtype)
    low:t.Tensor = ((primish * lowidx) + ((1 - lowidx) * primish[...,0].unsqueeze(-1))).max(dim=-1).values
    high:t.Tensor = ((primish * highidx) + ((1 - highidx) * primish[...,-1].unsqueeze(-1))).min(dim=-1).values
    
    # Calculate approach distance to nearest primes
    lowDist:t.Tensor = x - low
    highDist:t.Tensor = high - x
    highLower:t.Tensor = highDist < lowDist

    # Turn into one tensor
    result:t.Tensor = (highLower.type(t.int64) * highDist) + ((1 - highLower.type(t.int64)) * lowDist)
    # Can ignore gaussApprox due to the normalized range being equal to one
    if relative and not gaussApprox:
        # Only ever traversing half of the maximum space
        totalDistance:t.Tensor = (high - low) / 2
        result.div_(totalDistance) 
    
    return result

@ts
def gaussianprimishdist(x:t.Tensor, relative:bool=True) -> t.Tensor:
    # Force complex type
    if not t.is_complex(x):
        x = toComplex(x)

    # Extract values to compute against
    real = x.real
    imag = x.imag
    gauss = (x.real * x.real) + (x.imag * x.imag)

    # Simple first distance calculation for the magnitude
    gaussdist = t.sqrt(realprimishdist(gauss, relative=relative, gaussApprox=False))

    # Calculate the other distances
    rdgauss = realprimishdist(real, gaussApprox=True)
    idgauss = realprimishdist(imag, gaussApprox=True)
    # 4k +- 3 leaves only a space of 2 between normal values
    # To normalize, divide by the size of the space (which is 2)
    rdgaussi = imag.abs() / 2
    idgaussi = real.abs() / 2
    # Raw distance function
    rdcomposite = t.sqrt((rdgauss * rdgauss) + (rdgaussi * rdgaussi))
    idcomposite = t.sqrt((idgauss * idgauss) + (idgaussi * idgaussi))

    # Take the minimum distance
    magnitudePerc = rdcomposite.min(other=idcomposite)
    return magnitudePerc.min(other=gaussdist)
    
@ts
def iprimishdist(x:t.Tensor, relative:bool=True) -> t.Tensor:
    if not t.is_complex(x):
        return realprimishdist(x, relative=relative)
    return gaussianprimishdist(x, relative=relative)

@ts
def isigmoid(x:t.Tensor) -> t.Tensor:
    # Normal sigmoid
    if not x.is_complex():
        return t.sigmoid(x)

    # Extract/calculate required basic parameters
    PI2 = pi() / 2
    ang = x.angle()
    xabs = x.abs()
    
    # Do a sigmoid in the unanimous sign'd quadrants and find the connecting point
    # between the sigmoids if not in the unanimous quadrants.
    posQuad:t.Tensor = t.logical_and(x.real >= 0, x.imag >= 0).type(t.uint8)
    negQuad:t.Tensor = t.logical_and(x.real < 0, x.imag < 0).type(t.uint8)
    examineQuadRight:t.Tensor = t.logical_and(x.real >= 0, x.imag < 0)
    examineQuadLeft:t.Tensor = t.logical_and(x.imag >= 0, x.real < 0)
    examineQuad:t.Tensor = t.logical_and(examineQuadLeft, examineQuadRight).type(t.uint8)
    

    # The positive and negative quadrants are just the magnitude of the absolute value piped into
    # the evaluation of a normal sigmoid, then bound to the appropriate side of the sign
    posVal:t.Tensor = posQuad * t.sigmoid(posQuad * xabs)
    negVal:t.Tensor = negQuad * t.sigmoid(negQuad * -xabs)

    # The "examine" quadrants will use a cosine activation to toggle between the signs compounded in the
    # magnitude evaluation for the sigmoid.
    rotScalar:t.Tensor = (t.cos(
        (examineQuadLeft.type(t.uint8) * (ang - (PI2))*2) \
            + (examineQuadRight.type(t.uint8) * (ang + (PI2))*2)
    ))
    examVal:t.Tensor = examineQuad * t.sigmoid(examineQuad * rotScalar * xabs)

    # Add everything together according to the previously applied boolean based scalars
    finalSigmoidMag:t.Tensor = posVal + negVal + examVal

    # Create the complex value alignment to finally push the signal through. As a note,
    # I really don't like the fact that there are hard non-differentiable absolute
    # values in this evaluation, but I would not like to lose the current sigmoid properties
    xabs_e = t.view_as_complex(t.stack((x.real.abs(), x.imag.abs()), dim=-1))
    sigmoidComplexVal:t.Tensor = xabs_e / xabs

    # Calculate and return
    return finalSigmoidMag * sigmoidComplexVal

@ts
def icos(x:t.Tensor) -> t.Tensor:
    # Normal cos
    if not x.is_complex():
        return t.cos(x)

    # Main conversion
    return t.cos(x.abs()) * t.exp(i() * 2. * x.angle())

@ts
def isin(x:t.Tensor) -> t.Tensor:
    # Normal sin
    if not x.is_complex():
        return t.sin(x)

    # Main conversion
    return t.sin(x.abs()) * t.exp(i() * x.angle())

@ts
def hmean(x:t.Tensor, dim:int=-1) -> t.Tensor:
    """Calculates the harmonic mean according to the given dimension.

    Args:
        x (t.Tensor): The tensor value to use as the base of calculation.
        dim (int, optional): The dimension to perform the calculation on. Defaults to -1.

    Returns:
        t.Tensor: The harmonic mean of the input
    """
    # Turn all the values to their -1 power
    invx:t.Tensor = 1. / x
    # Find the amount of values for the mean
    vals = x.size()[dim]
    
    # Calculate the harmonic mean
    return vals / invx.sum(dim=dim)

@ts
def harmonicvals(n:int, nosum:bool=False, addzero:bool=False) -> t.Tensor:
    # Quick error checking
    assert n >= 1

    # Find all of the 1/n values to be summed
    zeroint = int(addzero)
    factors:t.Tensor = (1. / xbias(n=n+zeroint, bias=1-zeroint))
    if nosum:
        return factors
    else:
        factors.unsqueeze_(0)

    # Turn the values into a big triangle
    composition:t.Tensor = t.triu(t.ones((n, 1)) @ factors, diagonal=0)

    # Sum the triangle together so that the harmonic values come out
    return composition.transpose(-1, -2).sum(dim=-1)

@ts
def harmonicdist(x:t.Tensor) -> t.Tensor:
    # Gather constants for evaluation
    em:t.Tensor = emconst()

    # Take the inverse harmonic index of the input values and flatten them after for indexing
    inverse:t.Tensor = t.round(t.exp(x - em)) + t.exp(-em)
    finv = inverse.flatten(0, -1)

    # Find the needed harmonics for producing the final value
    maxn:t.Tensor = finv.max()[0]
    harmonics:t.Tensor = harmonicvals(n=maxn, addzero=True)
    
    # Find the closest harmonic value, refold the shape, then calculate the result
    closest = harmonics[finv].unflatten(0, inverse.size())
    return x - closest

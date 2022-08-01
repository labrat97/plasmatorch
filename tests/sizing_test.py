import unittest

import torch as t
from plasmatorch import *

from random import randint



class PaddimTest(unittest.TestCase):
    PADOPTIONS:List[str] = ['reflect', 'replicate', 'circular']


    def testSizingByDim(self):
        # Generate the starting tensors
        SIZELEN:int = randint(2, 5)
        SIZE:List[int] = [randint(SUPERSINGULAR_PRIMES_LH[5], SUPERSINGULAR_PRIMES_LH[-4]) for _ in range(SIZELEN)]
        TSIZE:t.Size = t.Size(SIZE)
        x:t.Tensor = t.randn(TSIZE, dtype=DEFAULT_DTYPE)
        xc:t.Tensor = t.randn(TSIZE, dtype=DEFAULT_COMPLEX_DTYPE)

        # Iterate through each possible dim in the testing tensors and test the padding
        #   capabilities
        for idx in range(SIZELEN):
            # Generate the random values for padding the tensor on either side
            lowpad:int = randint(0, SUPERSINGULAR_PRIMES_LH[5]-1)
            highpad:int = randint(0, SUPERSINGULAR_PRIMES_LH[5]-1)
            padmode:str = self.PADOPTIONS[randint(0, len(self.PADOPTIONS)-1)]

            # Run the testing tensors through the padding function
            px:t.Tensor = paddim(x, lowpad=lowpad, highpad=highpad, dim=idx, mode=padmode)
            pxc:t.Tensor = paddim(xc, lowpad=lowpad, highpad=highpad, dim=idx, mode=padmode)

            # Assert the sizing for the test
            sizeDummy:List[int] = SIZE.copy()
            sizeDummy[idx] += lowpad + highpad
            self.assertEqual(px.size(), t.Size(sizeDummy), msg=f'{px.size()} != {sizeDummy} with a low and high {padmode}-padding of {(lowpad, highpad)} on dim {idx}')
            self.assertEqual(pxc.size(), t.Size(sizeDummy), msg=f'{pxc.size()} != {sizeDummy} with a low and high {padmode}-padding of {(lowpad, highpad)} on dim {idx}')
    

    def testConsistency(self):
        # Generate the starting tensors
        SIZELEN:int = randint(2, 5)
        SIZE:List[int] = [randint(SUPERSINGULAR_PRIMES_LH[0], SUPERSINGULAR_PRIMES_LH[-4]) for _ in range(SIZELEN)]
        TSIZE:t.Size = t.Size(SIZE)
        x:t.Tensor = t.randn(TSIZE, dtype=DEFAULT_DTYPE)
        xc:t.Tensor = t.randn(TSIZE, dtype=DEFAULT_COMPLEX_DTYPE)
        
        # Test the values of each pad mode to make sure they are consistent with
        #   the return values of `nnf.pad()`
        for padmode in self.PADOPTIONS:
            # Generate the random values for padding the tensor on either side
            lowpad:int = randint(0, 11)
            highpad:int = randint(0, 11)

            # Run the testing tensors through the `paddim()` function
            px:t.Tensor = paddim(x, lowpad=lowpad, highpad=highpad, dim=-1, mode=padmode)
            pxc:t.Tensor = paddim(xc, lowpad=lowpad, highpad=highpad, dim=-1, mode=padmode)

            # Run the testing tensors through the control `nnf.pad()` function
            xcont:t.Tensor = nnf.pad(x, pad=[lowpad, highpad] + ([0] * (2 * (x.dim() - 2))), mode=padmode)
            xccont:t.Tensor = nnf.pad(xc, pad=[lowpad, highpad] + ([0] * (2 * (x.dim() - 2))), mode=padmode)

            # Check that the values of the control functions and the `paddim()` functions are within
            #   a reasonable epsilon value from each other
            self.assertTrue(t.all((px - xcont).abs() <= 1e-4))
            self.assertTrue(t.all((pxc - xccont).abs() <= 1e-4))

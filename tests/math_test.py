import unittest
import test
import math

import torch
from plasmatorch import *

class ComplexQualiaTest(unittest.TestCase):
    SIZE = (97, 23, 256)

    def testSizing(self):
        # Seeding tensors
        x = torch.randn(self.SIZE, dtype=DEFAULT_DTYPE)
        xc = torch.randn(self.SIZE, dtype=DEFAULT_COMPLEX_DTYPE)

        # Calculate results
        mag = imagnitude(x)
        magc = imagnitude(xc)
        pol = ipolarization(x)
        polc = ipolarization(xc)

        # Test that the values have the same size
        self.assertEqual(x.size(), mag.size(), msg=f'{x.size()} != {mag.size()}')
        self.assertEqual(xc.size(), magc.size(), msg=f'{xc.size()} != {magc.size()}')
        self.assertEqual(x.size(), pol.size(), msg=f'{x.size()} != {pol.size()}')
        self.assertEqual(xc.size(), polc.size(), msg=f'{x.size()} != {polc.size()}')
    
    def testMagnitude(self):
        # Seeding tensors
        zeros = torch.zeros(self.SIZE, dtype=DEFAULT_DTYPE)
        zerosc = torch.zeros(self.SIZE, dtype=DEFAULT_COMPLEX_DTYPE)
        ones = zeros + 1
        onesc = zerosc + 1
        imag = torch.view_as_complex(torch.stack((zeros, ones), dim=-1))
        root2 = torch.view_as_complex(torch.stack((ones, ones), dim=-1))

        # Run the calculations
        zmag = imagnitude(zeros)
        zmagc = imagnitude(zerosc)
        omag = imagnitude(ones)
        omagc = imagnitude(onesc)
        imagc = imagnitude(imag)
        rmag = imagnitude(root2)

        # Check the values
        self.assertTrue(torch.all(zmag == 0))
        self.assertTrue(torch.all(zmagc == 0))
        self.assertTrue(torch.all(omag == 1))
        self.assertTrue(torch.all(omagc == 1))
        self.assertTrue(torch.all(imagc == 1))
        self.assertTrue(torch.all(rmag == torch.sqrt(ones * 2)))

    def testPolarization(self):
        # Seeding tensors
        zeros = torch.zeros(self.SIZE, dtype=DEFAULT_DTYPE)
        zerosc = torch.zeros(self.SIZE, dtype=DEFAULT_COMPLEX_DTYPE)
        ones = zeros + 1
        onesc = zerosc + 1
        imag = torch.view_as_complex(torch.stack((zeros, ones), dim=-1))
        root2 = torch.view_as_complex(torch.stack((ones, ones), dim=-1))

        # Run the calculations
        zpol = ipolarization(zeros)
        zpolc = ipolarization(zerosc)
        opol = ipolarization(ones)
        opolc = ipolarization(onesc)
        ipol = ipolarization(imag)
        iroot2 = ipolarization(root2)

        # Check the values
        self.assertTrue(torch.all(zpol == zeros))
        self.assertTrue(torch.all(zpolc == zeros))
        self.assertTrue(torch.all(opol == zeros))
        self.assertTrue(torch.all(opolc == zeros))
        self.assertTrue(torch.all(ipol - math.pi/2 < 0.0001))
        self.assertTrue(torch.all(iroot2 - math.pi/4 < 0.0001))

class SoftmaxTest(unittest.TestCase):
    SIZE = (97, 11, 13, 128)

    def testSizing(self):
        # Seeding tensors
        x = torch.randn(self.SIZE, dtype=DEFAULT_DTYPE)
        xc = torch.randn(self.SIZE, dtype=DEFAULT_COMPLEX_DTYPE)

        # Calculate
        y = isoftmax(x, dim=-1)
        y0 = isoftmax(x, dim=0)
        yc = isoftmax(xc, dim=-1)
        yc0 = isoftmax(xc, dim=0)

        # Test the sizing through the function
        self.assertEqual(x.size(), y.size(), msg=f'{x.size()} != {y.size()}')
        self.assertEqual(x.size(), y0.size(), msg=f'{x.size()} != {y0.size()}')
        self.assertEqual(x.size(), yc.size(), msg=f'{x.size()} != {yc.size()}')
        self.assertEqual(x.size(), yc0.size(), msg=f'{x.size()} != {yc0.size()}')

    def testValues(self):
        # Seeding tensors
        x = torch.randn(self.SIZE, dtype=DEFAULT_DTYPE) * torch.randn(self.SIZE, dtype=DEFAULT_DTYPE)
        xc = torch.randn(self.SIZE, dtype=DEFAULT_COMPLEX_DTYPE) * torch.randn(self.SIZE, dtype=DEFAULT_COMPLEX_DTYPE)

        # Calculate
        y = isoftmax(x, dim=-1)
        y0 = isoftmax(x, dim=0)
        yc = isoftmax(xc, dim=-1)
        yc0 = isoftmax(xc, dim=0)

        # Test that the values are actually softmax'd at least normally
        self.assertTrue(torch.all(y == torch.softmax(x, dim=-1)))
        self.assertTrue(torch.all(y0 == torch.softmax(x, dim=0)))

        # Test to make sure that the magnitudes are softmax'd
        self.assertTrue(torch.all(ipolarization(xc) - ipolarization(yc) < 0.0001))
        self.assertTrue(torch.all(ipolarization(xc) - ipolarization(yc0) < 0.0001))
        self.assertTrue(torch.all(torch.softmax(imagnitude(xc), dim=-1) - imagnitude(yc) < 0.0001))
        self.assertTrue(torch.all(torch.softmax(imagnitude(xc), dim=0) - imagnitude(yc0) < 0.0001))

class TrigTest(unittest.TestCase):
    SIZE = (11, 23, 1024, 3)

    def testSizing(self):
        # Seeding tensors
        x = torch.randn(self.SIZE, dtype=DEFAULT_DTYPE)
        xc = torch.randn(self.SIZE, dtype=DEFAULT_COMPLEX_DTYPE)

        # Calculate
        cosx = icos(x)
        cosxc = icos(xc)
        sinx = isin(x)
        sinxc = isin(xc)

        # Test that the values go in and come out the same
        self.assertEqual(cosx.size(), x.size(), msg=f'{cosx.size()} != {x.size()}')
        self.assertEqual(cosxc.size(), xc.size(), msg=f'{cosxc.size()} != {xc.size()}')
        self.assertEqual(sinx.size(), x.size(), msg=f'{sinx.size()} != {x.size()}')
        self.assertEqual(sinxc.size(), xc.size(), msg=f'{sinxc.size()} != {xc.size()}')

    def testCos(self):
        # Seeding tensors
        x = torch.randn(self.SIZE, dtype=DEFAULT_DTYPE)
        xc = torch.randn(self.SIZE, dtype=DEFAULT_COMPLEX_DTYPE)
        I = i()

        # Calculate
        cosx = icos(x)
        cosxc = icos(xc)

        # Test the values and assert lack of runaway
        self.assertTrue(torch.all(cosx == torch.cos(x)))
        self.assertFalse(torch.all(cosxc == torch.cos(xc)))

        self.assertTrue(torch.all(
            cosxc == (torch.exp(i() * xc.real) + torch.exp(i() * xc.imag) - 1)
        ))
    
    def testSin(self):
        # Seeding tensors
        x = torch.randn(self.SIZE, dtype=DEFAULT_DTYPE)
        xc = torch.randn(self.SIZE, dtype=DEFAULT_COMPLEX_DTYPE)
        I = i()

        # Calculate
        sinx = isin(x)
        sinxc = isin(xc)

        # Test the values and assert lack of runaway
        self.assertTrue(torch.all(sinx == torch.sin(x)))
        self.assertFalse(torch.all(sinxc == torch.sin(xc)))

        # Should just be a complex phase shift of icos
        self.assertTrue(torch.all(sinxc == (i() * icos(xc))))

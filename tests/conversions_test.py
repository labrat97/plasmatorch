import unittest
import test

import torch
from plasmatorch import *

class SmearTest(unittest.TestCase):
    def testSizing(self):
        sx, _ = test.getsmear(DEFAULT_DTYPE)
        sxc, _ = test.getsmear(DEFAULT_COMPLEX_DTYPE)
        
        self.assertEqual(sx.size(), torch.Size((test.KYLABATCH, test.TEST_FFT_SAMPLES)), msg='Sizing test (real)')
        self.assertEqual(sxc.size(), torch.Size((test.KYLABATCH, test.TEST_FFT_SAMPLES)), msg='Sizing test (imag)')

    def testValues(self):
        sx, smear = test.getsmear(DEFAULT_DTYPE)
        sxc, smearc = test.getsmear(DEFAULT_COMPLEX_DTYPE)

        ZERO_TEST_REAL = torch.all(sx == torch.zeros_like(sx))
        ZERO_TEST_COMPL = torch.all(sxc == torch.zeros_like(sxc))
        self.assertTrue(ZERO_TEST_REAL, msg='Zero test (real)')
        self.assertTrue(ZERO_TEST_COMPL, msg='Zero test (imag)')

        # Test smear with ones to test the bounds scalars
        y = torch.ones((test.KYLABATCH, 1), dtype=DEFAULT_DTYPE)
        yc = torch.ones((test.KYLABATCH, 1), dtype=DEFAULT_COMPLEX_DTYPE)
        sy = smear.forward(y)
        syc = smearc.forward(yc)
        
        LOWER_TEST_REAL = torch.all(sy[:, 0] == torch.ones_like(sy[:, 0], dtype=DEFAULT_DTYPE) * (1-(1/16)))
        LOWER_TEST_COMPL = torch.all(syc[:, 0] == torch.ones_like(syc[:, 0], dtype=DEFAULT_COMPLEX_DTYPE) * (1-(1/16)))
        self.assertTrue(LOWER_TEST_REAL, msg=f'Lower bound test (real: {sy[0, 0]})')
        self.assertTrue(LOWER_TEST_COMPL, msg=f'Lower bounds test (imag: {syc[0, 0]})')
        
        UPPER_TEST_REAL = torch.all(sy[:, -1] == torch.ones_like(sy[:, -1], dtype=DEFAULT_DTYPE) * (1+(1/16)))
        UPPER_TEST_COMPL = torch.all(syc[:, -1] == torch.ones_like(syc[:, -1], dtype=DEFAULT_COMPLEX_DTYPE) * (1+(1/16)))
        self.assertTrue(UPPER_TEST_REAL, msg=f'Upper bounds test (real: {sy[0, -1]})')
        self.assertTrue(UPPER_TEST_COMPL, msg=f'Upper bounds test (imag: {syc[0, -1]})')

class SmearResampleTest(unittest.TestCase):
    def testEquivalence(self):
        EPSILON = 1e-4
        
        sx, _ = test.getsmear(DEFAULT_DTYPE)
        sxc, _ = test.getsmear(DEFAULT_COMPLEX_DTYPE)
        sxRand = torch.rand_like(sx)
        sxcRand = torch.rand_like(sxc)

        # Test smear sizing and basis vectors
        randResize = resignal(sxRand, samples=int(test.TEST_FFT_SAMPLES*2))
        randcResize = resignal(sxcRand, samples=int(test.TEST_FFT_SAMPLES*2))
        randReturnSize = resignal(randResize, samples=test.TEST_FFT_SAMPLES)
        randcReturnSize = resignal(randcResize, samples=test.TEST_FFT_SAMPLES)

        sxRandFFT = torch.fft.fft(sxRand, n=test.TEST_FFT_SAMPLES, dim=-1)
        randReturnSizeFFT = torch.fft.fft(randReturnSize, n=test.TEST_FFT_SAMPLES, dim=-1)
        sxcRandFFT = torch.fft.fft(sxcRand, n=test.TEST_FFT_SAMPLES, dim=-1)
        randcReturnSizeFFT = torch.fft.fft(randcReturnSize, n=test.TEST_FFT_SAMPLES, dim=-1)

        FORWARD_BACK_REAL = not torch.all(torch.view_as_real((sxRandFFT - randReturnSizeFFT)) >= EPSILON)
        FORWARD_BACK_COMPLEX = not torch.all(torch.view_as_real((sxcRandFFT - randcReturnSizeFFT)) >= EPSILON)
        self.assertTrue(FORWARD_BACK_REAL, msg='Forward back test (real)')
        self.assertTrue(FORWARD_BACK_COMPLEX, msg='Forward back test (imag)')

        # Test the expansion of the size of the smear
        randResizeReturn = resignal(randReturnSize, samples=int(test.TEST_FFT_SAMPLES*2))
        randcResizeReturn = resignal(randcReturnSize, samples=int(test.TEST_FFT_SAMPLES*2))

        randResizeFFT = torch.fft.fft(randResize, n=int(test.TEST_FFT_SAMPLES*2), dim=-1)
        randResizeReturnFFT = torch.fft.fft(randResizeReturn, n=int(test.TEST_FFT_SAMPLES*2), dim=-1)
        randcResizeFFT = torch.fft.fft(randcResize, n=int(test.TEST_FFT_SAMPLES*2), dim=-1)
        randcResizeReturnFFT = torch.fft.fft(randcResizeReturn, n=int(test.TEST_FFT_SAMPLES*2), dim=-1)

        FORWARD_BACK_FORWARD_REAL = not torch.all(torch.view_as_real(randResizeFFT - randResizeReturnFFT) >= EPSILON)
        FORWARD_BACK_FORWARD_COMPL = not torch.all(torch.view_as_real(randcResizeFFT - randcResizeReturnFFT) >= EPSILON)
        self.assertTrue(FORWARD_BACK_FORWARD_REAL, msg='Forward back forward test (real)')
        self.assertTrue(FORWARD_BACK_FORWARD_COMPL, msg='Forward back forward test (imag)')

class ToComplexTest(unittest.TestCase):
    def testSmallToComplex(self):
        x = torch.ones((1), dtype=DEFAULT_DTYPE)
        xc = torch.ones((1), dtype=DEFAULT_COMPLEX_DTYPE)

        convertX = toComplex(x)
        convertXC = toComplex(xc)

        self.assertTrue(torch.is_complex(convertX), msg='Convert \'x\' (real)')
        self.assertTrue(torch.is_complex(convertXC), msg='Convert \'xc\' (complex)')
        self.assertTrue(torch.all(convertX.imag == torch.zeros_like(convertX.real)), msg='Empty imaginary from conversion (\'x\')')
        self.assertTrue(torch.all(xc == convertXC), msg='Already complex (\'xc\')')
        self.assertEqual(x.size(), convertX.size())
        self.assertEqual(xc.size(), convertXC.size())

    def testLargeToComplex(self):
        x = torch.ones((8, 8, 8, 8, 8), dtype=DEFAULT_DTYPE)
        xc = torch.ones((8, 8, 8, 8, 8), dtype=DEFAULT_COMPLEX_DTYPE)

        convertX = toComplex(x)
        convertXC = toComplex(xc)

        self.assertTrue(torch.is_complex(convertX), msg='Convert \'x\' (real)')
        self.assertTrue(torch.is_complex(convertXC), msg='Convert \'xc\' (complex)')
        self.assertTrue(torch.all(convertX.imag == torch.zeros_like(convertX.real)), msg='Empty imaginary from conversion (\'x\')')
        self.assertTrue(torch.all(xc == convertXC), msg='Already complex (\'xc\')')
        self.assertEqual(x.size(), convertX.size())
        self.assertEqual(xc.size(), convertXC.size())

class RealObserverTest(unittest.TestCase):
    def testSmallExample(self):
        x = torch.ones((1), dtype=DEFAULT_COMPLEX_DTYPE)
        
        observer = RealObserver(units=1, dtype=DEFAULT_DTYPE)
        observeX = observer.forward(x)

        self.assertTrue(not torch.is_complex(observeX), msg='Observed value is real')
        self.assertTrue(torch.all(observeX == x.real), msg='Expected real initialization')
        self.assertTrue(torch.all(torch.zeros_like(observeX) == x.imag), msg='Expected imag initialization')

    def testLargeExample(self):
        x = torch.ones((8, 8, 8, 8, 8), dtype=DEFAULT_COMPLEX_DTYPE)
        
        observer = RealObserver(units=1, dtype=DEFAULT_DTYPE)
        observeX = observer.forward(x)

        self.assertTrue(not torch.is_complex(observeX), msg='Observed value is real')
        self.assertTrue(torch.all(observeX == x.real), msg='Expected real initialization')
        self.assertTrue(torch.all(torch.zeros_like(observeX) == x.imag), msg='Expected imag initialization')
class ComplexObserverTest(unittest.TestCase):
    def testSmallExample(self):
        x = torch.ones((1), dtype=DEFAULT_DTYPE)
        
        observer = ComplexObserver(units=1, dtype=DEFAULT_DTYPE)
        observeX = observer.forward(x)

        self.assertTrue(torch.is_complex(observeX), msg='Observed value is complex')
        self.assertTrue(torch.all(observeX.real == x), msg='Expected real initialization')
        self.assertTrue(torch.all(observeX.imag == torch.zeros_like(x)), msg='Expected imag initialization')

    def testLargeExample(self):
        x = torch.ones((8, 8, 8, 8, 8), dtype=DEFAULT_DTYPE)
        
        observer = ComplexObserver(units=1, dtype=DEFAULT_DTYPE)
        observeX = observer.forward(x)

        self.assertTrue(torch.is_complex(observeX), msg='Observed value is complex')
        self.assertTrue(torch.all(observeX.real == x), msg='Expected real initialization')
        self.assertTrue(torch.all(observeX.imag == torch.zeros_like(x)), msg='Expected imag initialization')

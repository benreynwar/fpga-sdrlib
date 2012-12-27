# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import os
import random
import unittest
import logging
import shutil

from fpga_sdrlib.message import msg_utils
from fpga_sdrlib.conversions import f_to_int
from fpga_sdrlib.generate import logceil
from fpga_sdrlib import config, b100, buildutils
from fpga_sdrlib.testbench import TestBenchB100, TestBenchIcarusInner, TestBenchIcarusOuter

logger = logging.getLogger(__name__)

class TestMultiply(unittest.TestCase):

    def test_one(self):
        """
        Test the multiply module.
        """
        sendnth = 2
        n_data = 1000
        in_samples = []
        expected = []
        # We send samples a + bj and expected returned 0 + abj.
        in_samples = [random.random()*2-1 + random.random()*2j-1j for i in range(n_data)]
        expected = [c.real*c.imag*1j for c in in_samples]
        steps_rqd = len(in_samples)*sendnth*2 + 100
        executable_inner = buildutils.generate_icarus_executable(
            'fpgamath', 'multiply_inner', '-test',)
        executable_outer = buildutils.generate_icarus_executable(
            'fpgamath', 'multiply', '-test',)
        fpgaimage = buildutils.generate_B100_image(
            'fpgamath', 'multiply', '-test')
        tb_icarus_inner = TestBenchIcarusInner(executable_inner, in_samples,
                                               sendnth=sendnth)
        tb_icarus_outer = TestBenchIcarusOuter(executable_outer, in_samples,
                                               sendnth=sendnth)
        tb_b100 = TestBenchB100(fpgaimage, in_samples)
        for tb, steps, check_ms in (
                (tb_icarus_inner, steps_rqd, True),
                (tb_icarus_outer, steps_rqd, False),
                (tb_b100, 100000, False), 
                ):
            tb.run(steps)
            # Confirm that our data is correct.
            self.assertEqual(len(tb.out_samples), len(expected))
            for r, e in zip(tb.out_samples, expected):
                self.assertAlmostEqual(e, r, 3)

class TestMultiplyComplex(unittest.TestCase):

    def test_one(self):
        """
        Test the multiply_complex module.
        """
        sendnth = 2
        n_data = 1000
        in_samples = []
        expected = []
        xs = [random.random()*2-1 + random.random()*2j-1j for i in range(n_data)]
        ys = [random.random()*2-1 + random.random()*2j-1j for i in range(n_data)]
        for x, y in zip(xs, ys):
            in_samples.append(x)
            in_samples.append(y)
            z = x*y/2
            # We divide by two since multiplying two complex numbers in range (-1,-1) to (1,1)
            # produces a result in range (-2, -2) to (2, 2).
            expected.append(z)
        steps_rqd = len(in_samples)*sendnth*2 + 100
        executable_inner = buildutils.generate_icarus_executable(
            'fpgamath', 'multiply_complex_inner', '-test',)
        executable_outer = buildutils.generate_icarus_executable(
            'fpgamath', 'multiply_complex', '-test',)
        fpgaimage = buildutils.generate_B100_image(
            'fpgamath', 'multiply_complex', '-test')
        tb_icarus_inner = TestBenchIcarusInner(executable_inner, in_samples,
                                               sendnth=sendnth)
        tb_icarus_outer = TestBenchIcarusOuter(executable_outer, in_samples,
                                               sendnth=sendnth)
        tb_b100 = TestBenchB100(fpgaimage, in_samples)
        for tb, steps, check_ms in (
                (tb_icarus_inner, steps_rqd, True),
                (tb_icarus_outer, steps_rqd, False),
                (tb_b100, 100000, False), 
                ):
            tb.run(steps)
            # Confirm that our data is correct.
            self.assertEqual(len(tb.out_samples), len(expected))
            for r, e in zip(tb.out_samples, expected):
                self.assertAlmostEqual(e, r, 3)
        
if __name__ == '__main__':
    config.setup_logging(logging.DEBUG)
    #suite = unittest.TestLoader().loadTestsFromTestCase(TestMultiply)
    #unittest.TextTestRunner(verbosity=2).run(suite)
    unittest.main()

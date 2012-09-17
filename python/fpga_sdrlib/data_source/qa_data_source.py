# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

"""
MyHDL Test Bench to check the vericode data_source.
"""

import os
import random
import unittest
import math
import logging

from myhdl import always

from fpga_sdrlib.data_source.build import generate
from fpga_sdrlib.testbench import TestBenchBase
from fpga_sdrlib import config

class DataSourceTestBench(TestBenchBase):
    """
    Helper class for doing testing.
    
    Args:
        name: A name to use for generated files.
        width: Bit width of a complex number.
        mwidth: Bit width of the meta data.
        sendnth: Send an input on every `sendnth` clock cycle.
        data: A list of complex points to send.
        ms: A list of the meta data to send.
        n_loops: Number of times to loop data.
    """

    def __init__(self, name, width, mwidth, sendnth, data, ms, n_loops):
        TestBenchBase.__init__(self, width)
        outputdir = os.path.join(config.builddir, 'data_source')
        self.executable, inputfiles = generate(name, data, ms, sendnth, n_loops, width, mwidth)

class TestDataSource(unittest.TestCase):
    """
    Test the verilog data_source.
    """

    def setUp(self):
        # Random number generator
        rg = random.Random(0)
        self.myrand = rg.random
        self.myrandint = rg.randint

    def tearDown(self):
        pass

    def test_random(self):
        """
        Test with some random input.
        """
        n_data = 10
        n_loops = 1
        # Generate some random input.
        data =  [self.myrand()*2-1 + self.myrand()*2j-1j
                 for x in range(n_data)]
        # sends random ms between 0 and 7
        mwidth = 3
        ms = [self.myrandint(0, 7) for d in data]
        width = 32
        sendnth = 2
        steps_rqd = sendnth * n_data + 1000
        # Create the test bench
        tb = DataSourceTestBench('random', width, mwidth, sendnth, data, ms, n_loops)
        tb.simulate(steps_rqd)
        # Compare to expected output
        expected = data * n_loops
        expected_ms = ms * n_loops
        self.assertEqual(len(tb.output), len(expected))
        for r, e in zip(tb.output, data):
            self.assertAlmostEqual(r, e, 3)
        # Compare ms
        self.assertEqual(len(tb.out_ms), len(expected_ms))
        for r, e in zip(tb.out_ms, expected_ms):
            self.assertEqual(r, e)

if __name__ == '__main__':
    config.setup_logging(logging.DEBUG)
    unittest.main()

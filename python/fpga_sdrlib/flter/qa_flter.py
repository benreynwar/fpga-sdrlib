# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import os
import random
import unittest
import logging
import shutil

from fpga_sdrlib.conversions import f_to_int
from fpga_sdrlib.generate import logceil
from fpga_sdrlib import config, b100, buildutils
from fpga_sdrlib.testbench import TestBenchB100, TestBenchIcarusInner

logger = logging.getLogger(__name__)

def convolve(data, taps):
    out = []
    data = [0]*(len(taps)-1) + data
    for i in range(len(taps)-1, len(data)):
        v = 0
        for j in range(len(taps)):
            v += data[i-j]*taps[j]
        out.append(v)
    return out

def taps_to_start_msgs(taps, width):
    # First block has header flag set.
    start_msgs = [pow(2, config.msg_width-1)]
    # Following blocks contain taps.
    for tap in taps:
        start_msgs.append(f_to_int(tap, width, clean1=True))
    return start_msgs

class TestFilter(unittest.TestCase):

    def test_one(self):
        """
        Test the filter module.
        """
        width = config.default_width
        sendnth = config.default_sendnth
        taps = [1, 0, 0, 0]
        filter_length = len(taps)
        # Arguments used for producing verilog from templates.
        extraargs = {'summult_length': filter_length,}
        # Amount of data to send.
        n_data = 10
        # Define the input
        in_samples = [float(i)/n_data for i in range(n_data)]
        steps_rqd = len(in_samples)*sendnth + 100
        # Define meta data
        mwidth = 1
        in_ms = [random.randint(0, pow(2,mwidth)-1) for d in in_samples]
        expected = convolve(in_samples, taps)
        steps_rqd = n_data * sendnth * 2 + 1000
        # Create, setup and simulate the test bench.
        defines = config.updated_defines(
            {'WIDTH': width,
             'FILTER_LENGTH': filter_length,
             'FILTER_ID': 123,
             })
        executable = buildutils.generate_icarus_executable(
            'flter', 'filter_inner', '-test', defines=defines, extraargs=extraargs)
        #fpgaimage = buildutils.generate_B100_image(
        #    'flter', 'filter', '-test', defines=defines,
        #extraargs=extraargs)
        start_msgs = taps_to_start_msgs(taps, defines['WIDTH']/2)
        tb_icarus = TestBenchIcarusInner(executable, in_samples, in_ms, start_msgs)
        #tb_b100 = TestBenchB100(fpgaimage, in_samples, in_ms, start_msgs)
        for tb, steps in (
                (tb_icarus, steps_rqd),
                #(tb_b100, 100000), 
                ):
            tb.run(steps)
            # Confirm that our data is correct.
            self.assertEqual(len(tb.out_samples), len(expected))
            for r, e in zip(tb.out_samples, expected):
                self.assertEqual(e, r)

if __name__ == '__main__':
    config.setup_logging(logging.DEBUG)
    unittest.main()
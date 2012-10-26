# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

"""
MyHDL Test Bench to check the vericode filterbank.
"""

import os
import random
import unittest
import math
import logging

from myhdl import always

from fpga_sdrlib.conversions import f_to_int
from fpga_sdrlib.filterbank.build import generate_filterbank_executable
from fpga_sdrlib.testbench import TestBenchIcarus
from fpga_sdrlib import config

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
    for flt in taps:
        for tap in flt:
            start_msgs.append(f_to_int(tap, width, clean1=True))
    return start_msgs

class FilterbankTestBenchIcarus(TestBenchIcarus):
    """
    Helper class for doing testing.
    
    Args:
        name: A name to use with for generated files.
        n_filters: The number of filters.
        filter_length: The length of the filters.
        taps: A list of list of taps to set the filters with.
        in_samples: A list of complex points to send.
        sendnth: Send an input on every `sendnth` clock cycle.
        in_ms: A list of the meta data to send.
        defines: Macro definitions (constants) to use in verilog code.
    """

    extra_signal_names = ['first_filter', 'in_msg', 'in_msg_nd']

    def __init__(self, name, n_filters, filter_length, taps, in_samples,
                 sendnth=config.default_sendnth,
                 in_ms=None, defines=config.default_defines):
        start_msgs = taps_to_start_msgs(taps, defines['WIDTH']/2)
        super(FilterbankTestBenchIcarus, self).__init__(name, in_samples, sendnth,
                                                 in_ms, start_msgs, defines)
        self.n_filters = n_filters
        self.filter_length = filter_length
        self.taps = taps
        # Check that there are the correct number of taps.
        assert(len(taps) == n_filters)
        for tt in taps:
            assert(len(tt) == filter_length)
        self.out_ff = []
        self.drivers.append(self.get_first_filter)
        
    def prepare(self):
        self.executable = generate_filterbank_executable(
            self.name, self.n_filters, self.filter_length, self.defines)

    def get_first_filter(self):
        @always(self.clk.posedge)
        def run():
            if self.out_nd:
                self.out_ff.append(int(self.first_filter))
        return run

def scale_taps(tapss):
    """
    Scales a list of lists of taps.
    """
    scaledtaps = []
    maxabsintegral = 0
    for taps in tapss:
        absintegral = sum([abs(x) for x in taps])
        if absintegral > maxabsintegral:
            maxabsintegral = absintegral
    scaledtaps = [[t/maxabsintegral for t in taps] for taps in tapss]
    return scaledtaps, maxabsintegral 
    

class TestFilterbank(unittest.TestCase):
    """
    Test the verilog filterbank.
    """

    def setUp(self):
        # Random number generator
        rg = random.Random(0)
        self.myrand = rg.random
        self.myrandint = rg.randint

    def tearDown(self):
        pass

    def test_simple(self):
        """
        Test with some simple input and taps.
        """
        taps = [
            [1, 0, 0, 0], 
            [0, 1, 0, 0], 
            [0.5, 0.5, 0, 0], 
            [0, 0, 0.5, 0.5], 
            ]
        n_filters = len(taps)
        filter_length = len(taps[0])
        # Amount of data to send to every filter.
        n_data = 10
        # Define the input
        data = []
        for i in range(n_data):
            data += [float(i)/n_data]*len(taps)
        width = 32
        sendnth = 2
        steps_rqd = len(data)*sendnth + 100
        # Define meta data
        mwidth = 1
        ms = [self.myrandint(0, pow(2,mwidth)-1) for d in data]
        # Expected first filter signals
        ffs = ([1] + [0]*(n_filters-1))*n_data
        # Create the test bench
        defines = {"DEBUG": False,
                   "WIDTH": width,
                   "MWIDTH": mwidth}
        tb = FilterbankTestBenchIcarus('simpletaps', n_filters, filter_length, taps, data, sendnth, ms, defines)
        tb.prepare()
        tb.run(steps_rqd)
        # Compare to expected output
        input_streams = [data[i::n_filters] for i in range(n_filters)]
        received = [tb.out_samples[i::n_filters] for i in range(n_filters)]
        expected = [convolve(d,t) for d,t in zip(input_streams, taps)]
        for rs, es in zip(received, expected):
            for r, e in zip(rs, es):
                self.assertAlmostEqual(r, e, 3)
        # Compare ms
        self.assertEqual(len(tb.out_ms), len(ms))
        for r, e in zip(tb.out_ms, ms):
            self.assertEqual(r, e)
        # Compare first_filter signals
        self.assertEqual(len(tb.out_ff), len(ffs))
        for r, e in zip(tb.out_ff, ffs):
            self.assertEqual(r, e)
        

    def test_medium(self):
        """
        Test with some simple input and taps.
        """
        # Generate some random input.
        data =  [self.myrand()*2-1 + self.myrand()*2j-1j
                 for x in range(20)]
        # sends random ms between 0 and 7
        mwidth = 3
        ms = [self.myrandint(0, 7) for d in data]
        # get expected first_filter signal
        ffs = [1, 0] * (len(data)/2)
        # Some slightly more complicated taps.
        taps = [
            [0.4, 0.4, 0.1], 
            [0, 0.7, 0.3], 
            ]
        n_filters = len(taps)
        filter_length = len(taps[0])
        width = 32
        sendnth = 2
        steps_rqd = 20 * sendnth + 1000
        # Create the test bench
        defines = {"DEBUG": False,
                   "WIDTH": width,
                   "MWIDTH": mwidth}
        tb = FilterbankTestBenchIcarus('simpletaps', n_filters, filter_length, taps, data, sendnth, ms, defines)
        tb.prepare()
        tb.run(steps_rqd)
        # Compare to expected output
        n_filters = len(taps)
        received = [tb.out_samples[i::n_filters] for i in range(n_filters)]
        input_streams = [data[i::n_filters] for i in range(n_filters)]
        expected = [convolve(d,t) for d,t in zip(input_streams, taps)]
        for rs, es in zip(received, expected):
            for r, e in zip(rs, es):
                self.assertAlmostEqual(r, e, 3)
        # Compare ms
        self.assertEqual(len(tb.out_ms), len(ms))
        for r, e in zip(tb.out_ms, ms):
            self.assertEqual(r, e)
        # Compare first_filter signals
        self.assertEqual(len(tb.out_ff), len(ffs))
        for r, e in zip(tb.out_ff, ffs):
            self.assertEqual(r, e)

    def test_randominput(self):
        """
        Test a filterbank with random data and taps.
        """
        n_filters = 2
        n_taps = 3
        # Amount of data to send to every filter.
        n_data = 4#50
        # Send a new input every sendnth clock cycles.
        sendnth = 2
        # Width of a complex number
        width = 32
        # get expected first_filter signal
        ffs = ([1] + [0]*(n_filters-1)) * n_data
        # Generate some random input.
        data =  [self.myrand()*2-1 + (self.myrand()*2j-1j)
                 for x in range(n_data*n_filters)]
        mwidth = 7
        ms = [self.myrandint(0, pow(2,mwidth)-1) for d in data]
        # Generate some random taps.
        taps = [[self.myrand()*2-1 for x in range(n_taps)] for i in range(n_filters)]
        # Scale taps to prevent overflow
        chantaps, tapsscalefactor = scale_taps(taps)
        steps_rqd = n_data * n_filters * sendnth + 1000
        # Create the test bench
        defines = {"DEBUG": False,
                   "WIDTH": width,
                   "MWIDTH": mwidth}
        tb = FilterbankTestBenchIcarus('simpletaps', n_filters, n_taps, chantaps, data, sendnth, ms, defines)
        tb.prepare()
        tb.run(steps_rqd)
        received = [tb.out_samples[i::n_filters] for i in range(n_filters)]
        input_streams = [data[i::n_filters] for i in range(n_filters)]
        expected = [convolve(d,t) for d,t in zip(input_streams, chantaps)]
        for rs, es in zip(received, expected):
            for r, e in zip(rs, es):
                self.assertAlmostEqual(r, e, 3)
        # Compare ms
        self.assertEqual(len(tb.out_ms), len(ms))
        for r, e in zip(tb.out_ms, ms):
            self.assertEqual(r, e)
        # Compare first_filter signals
        self.assertEqual(len(tb.out_ff), len(ffs))
        for r, e in zip(tb.out_ff, ffs):
            self.assertEqual(r, e)

if __name__ == '__main__':
    config.setup_logging(logging.DEBUG)
    unittest.main()

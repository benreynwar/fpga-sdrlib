# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

"""
QA to check the vericode filterbank on the FPGA.
"""

import os
import random
import unittest
import logging
import math
import itertools

from fpga_sdrlib.data_source.build import generate as data_source_generate
from fpga_sdrlib.filterbank.build import generate as filterbank_generate
from fpga_sdrlib import config
from fpga_sdrlib import b100
from fpga_sdrlib.filterbank.qa_filterbank import convolve, scale_taps
from fpga_sdrlib.testbench import compare_unaligned, get_usrp_output

class TestChannelizer(unittest.TestCase):
    """
    Test the verilog channelizer on B100.
    """

    def setUp(self):
        rg = random.Random(0)
        self.myrand = rg.random
        self.myrandint = rg.randint

    def tearDown(self):
        pass

    def generate_and_run(self, name, data, ms, sendnth, width, mwidth, chantaps, n_data, n_filters, tol):
        executable, ds_inputfiles = data_source_generate(
            name, data, ms, sendnth, width, mwidth)
        executable, fb_inputfiles = filterbank_generate(
            name, chantaps, width, mwidth, 
            {'sendnth': sendnth, 'n_data': n_data*n_filters})
        qa_filterbank_fn = os.path.join(config.builddir, 'filterbank', 'qa_filterbank.v')
        b100.make_make(name, ds_inputfiles + fb_inputfiles + [qa_filterbank_fn])
        b100.synthesise(name)
        b100.copy_image(name)
        out_data = get_usrp_output(len(data)*2)
        input_streams = [data[i::n_filters]*2 for i in range(n_filters)]
        expected = [convolve(d,t)[n_data:] for d,t in zip(input_streams, chantaps)]
        expected = list(itertools.chain(*zip(*expected)))
        N = len(expected)
        print(expected)
        print('***********************')
        print(out_data)
        max_streak = compare_unaligned(expected, out_data, tol)
        print("Maximum streak was {0} out of {1}".format(max_streak, N))
        self.assertEqual(max_streak, N)
        

    def atest_random(self):
        n_filters = 2
        n_taps = 4
        # Amount of data to send to every filter.
        n_data = 50
        # Generate some random input.
        data =  [self.myrand()*2-1 + (self.myrand()*2j-1j)
                 for x in range(n_data*n_filters)]
        mwidth = 7
        ms = [self.myrandint(0, pow(2,mwidth)-1) for d in data]
        # Generate some random taps.
        taps = [[self.myrand()*2-1 for x in range(n_taps)]
                for i in range(fn_filters)]
        taps, tapscalefactor = scale_taps(taps)
        name = 'qafilterbank1'
        self.generate_and_run(
            name='qafilterbank1', data=data, ms=ms, sendnth=2, width=32,
            mwidth=mwidth, chantaps=taps, n_data=n_data, n_filters=n_filters,
            tol=1e-3)

    def test_simple(self):
        taps = [
            [1, 0, 0, 0], 
            [0, 1, 0, 0], 
            [0.5, 0.5, 0, 0], 
            [0, 0, 0.5, 0.5], 
            ]
        # Amount of data to send to every filter.
        n_data = 10
        # Define the input
        data = []
        for i in range(n_data):
            data += [float(i)/n_data]*len(taps)
        # Define meta data
        mwidth = 1
        ms = [self.myrandint(0, pow(2,mwidth)-1) for d in data]
        self.generate_and_run(
            name='qafilterbank2', data=data, ms=ms, sendnth=2,
            width=32, mwidth=mwidth, chantaps=taps, n_data=n_data,
            n_filters=len(taps[0]), tol=1e-3)
                

if __name__ == '__main__':
    config.setup_logging(logging.DEBUG)
    unittest.main()

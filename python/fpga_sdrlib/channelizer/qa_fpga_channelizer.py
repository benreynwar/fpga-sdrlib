# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

"""
QA to check the vericode channelizer on the FPGA.
"""

import os
import random
import unittest
import logging
import math

from gnuradio import uhd, gr

from fpga_sdrlib.data_source.build import generate as data_source_generate
from fpga_sdrlib.channelizer.build import generate as channelizer_generate
from fpga_sdrlib import config
from fpga_sdrlib import b100
from fpga_sdrlib.channelizer import qa_channelizer as qach

class TestChannelizer(unittest.TestCase):
    """
    Test the verilog channelizer on B100.
    """

    def setUp(self):
        # Number of channels
        self.M = 4
        self.logM = int(math.log(self.M)/math.log(2))
        # The amount of data to send
        self.n_data = self.M * 8
        # Baseband sampling rate
        self.fs = 1000        
        # Input samp rate to channelizer
        self.ifs = self.M*self.fs       
        # Each channel contains a pure frequency with an offset and
        # amplitude.
        self.freqs = [0, 100, 200, -300]
        self.amplitudes = [1, 1, -0.2, 0.5]
        # Random number generator
        rg = random.Random(0)
        self.myrand = rg.random
        self.myrandint = rg.randint
        # Width of a complex number
        self.width = 32
        # Generate some taps
        self.taps, self.tapscale = qach.get_channelizer_taps(self.M, n_taps=8)
        # How often to send input.
        # For large FFTs this must be larger since the speed scales as MlogM.
        # Otherwise we get an overflow error.
        self.sendnth = 2
        # Get the input data
        self.data = qach.get_mixed_sinusoids(self.fs, self.n_data, self.freqs, self.amplitudes)
        # Scale the input data to remain in (-1 to 1)
        datamax = 0
        for d in self.data:
            datamax = max(datamax, abs(d.real), abs(d.imag))
        self.inputscale = datamax
        self.data = [d/datamax for d in self.data]
        # Send in some meta data
        self.mwidth = 1
        self.ms = [self.myrandint(0, 2) for d in self.data]
        name = 'qachannelizer1'
        
        executable, ds_inputfiles = data_source_generate(
            name, self.data, self.ms, self.sendnth, self.width, self.mwidth)
        executable, ch_inputfiles = channelizer_generate(
            name, self.M, self.taps, self.width, self.mwidth,
            {'sendnth': self.sendnth, 'n_data': self.n_data})
        qa_channelizer_fn = os.path.join(config.builddir, 'channelizer', 'qa_channelizer.v')
        b100.make_make('channelizer', ds_inputfiles + ch_inputfiles + [qa_channelizer_fn])
        b100.synthesise('channelizer')
        b100.copy_image('channelizer')
        

    def tearDown(self):
        pass

    def test_channelizer(self):
        """
        Test a channelizer.
        """
        steps_rqd = self.n_data * self.sendnth + 1000
        self.tb.simulate(steps_rqd)
        received = [x*self.M for x in self.tb.output]
        skip = int(math.ceil(float(len(self.taps))/self.M-1)*self.M)
        received = [received[i+skip::self.M] for i in range(self.M)]
        expected = qach.get_expected_channelized_data(
            self.n_data/self.M, self.freqs, self.amplitudes)
        p_convolved, p_final = pychannelizer(self.taps, self.data, self.M)
        for ed, dd, pd in zip(expected, received, p_final):
            pd = [p*self.tapscale*self.inputscale for p in pd]
            dd = [d*self.tapscale*self.inputscale for d in dd]
            epf = ed[-1]/pd[-1]
            rpd = [p*epf for p in pd]
            self.assertTrue(len(rpd) != 0)
            self.assertTrue(len(ed) != 0)
            self.assertTrue(len(pd) != 0)
            for e, p in zip(ed, rpd):
                self.assertAlmostEqual(e, p, 3)
            for d, p in zip(dd, pd):
                self.assertAlmostEqual(d, p, 3)
        # Compare ms
        self.assertEqual(len(self.tb.out_ms), len(self.ms))
        for r, e in zip(self.tb.out_ms, self.ms):
            self.assertEqual(r, e)
        # Compare first_channel signals
        fcs = ([1] + [0]*(self.M-1)) * (self.n_data/self.M)
        self.assertEqual(len(self.tb.out_fc), len(fcs))
        for r, e in zip(self.tb.out_fc, fcs):
            self.assertEqual(r, e)

                

if __name__ == '__main__':
    config.setup_logging(logging.DEBUG)
    unittest.main()

# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

"""
QA to check the vericode DIT-FFT on the FPGA.
"""

import os
import random
import unittest
import logging
import math
import itertools

from numpy import fft

from gnuradio import uhd, gr

from fpga_sdrlib.fft.build import generate, make_qa_dit
from fpga_sdrlib import config
from fpga_sdrlib import b100

class TestDit(unittest.TestCase):
    """
    Test the verilog DIT-FFT on B100.
    """

    def setUp(self):
        # Width of a complex number
        self.width = 32
        self.mwidth = 1
        self.n = 8
        if False:
            executable, dit_inputfiles = generate(
                'xilinx', self.n, self.width, self.mwidth)
            make_qa_dit(self.n, self.width, self.mwidth)
            qa_dit_fn = os.path.join(config.builddir, 'fft', 'qa_dit.v')
            b100.make_make('dit', dit_inputfiles + [qa_dit_fn])
            b100.synthesise('dit')
        b100.copy_image('dit')
        

    def tearDown(self):
        pass

    def test_dit(self):
        """
        Test a DIT_FFT.
        """
        # The amount of data to send
        self.n_data = 100
        # Random number generator
        rg = random.Random(0)
        self.myrand = rg.random
        # Get the input data
        self.data = [(self.myrand()*2-1) + 1j*(self.myrand()*2-1) for i in range(self.n_data)]
        self.data = [0]* 200 + [1] + [0]*200
        # Create the top signal processing flow graph
        tb = gr.top_block()
        # Create the path for data to the USRP
        stream_args = uhd.stream_args(cpu_format='fc32', channels=range(1))
        src = gr.vector_source_c(self.data)
        to_usrp = uhd.usrp_sink(device_addr='', stream_args=stream_args)
        tb.connect(src, to_usrp)
        # Create the path from the USRP
        from_usrp = uhd.usrp_source(device_addr='', stream_args=stream_args)
        n_receive = 100000
        head = gr.head(gr.sizeof_gr_complex, n_receive)
        snk = gr.vector_sink_c()
        tb.connect(from_usrp, head, snk)
        # Run the flow graph
        tb.run()
        # Work out the data offset
        r_data = snk.data()
        first_i = None
        for i, d in enumerate(r_data):
            if d:
                first_i = i
                break
        if first_i is None:
            raise StandardError("No data received.  Try increasing n_receive.")
        if first_i + self.n_data > n_receive:
            raise StandardError("Increase n_receive.")
        # Work out expected data
        x_data = self.data + [0] * self.n
        ffteds = [fft.fft(self.data[i:i+self.n]) for i in range(0, len(self.data), self.n)]
        e_data = []
        for ffted in ffteds:
            for d in ffted:
                e_data.append(d)
        r_data = r_data[first_i:first_i+len(e_data)]
        if False:
            z_data = [0]*8 + self.data
            print('********')
            for i in range(0, 16):
                d = fft.fft(z_data[i:i+8])
                d = [x/self.n for x in d]
                print(d[0:2])
                if abs(d[0] - r_data[0]) < 1e-3:
                    print('hello')
            print('********')
            print(r_data[0:2])
            print(r_data[8:10])
        print([d*self.n for d in r_data])
        for i in range(8):
            print(list(fft.fft([0]*i + [1] + [0]*(7-i))))
        # And finally compare the data
        for e, r in zip(e_data, r_data):
            self.assertAlmostEqual(e.real, r.real, 3)
            self.assertAlmostEqual(e.imag, r.imag, 3)

                

if __name__ == '__main__':
    config.setup_logging(logging.DEBUG)
    unittest.main()

# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

"""
QA to check the vericode data_source on an FPGA.
"""

import os
import random
import unittest
import logging

from gnuradio import uhd, gr

from fpga_sdrlib.data_source.build import generate
from fpga_sdrlib import config
from fpga_sdrlib import b100

class TestB100DataSource(unittest.TestCase):
    """
    Test the verilog data_source on the USRP B100.
    """
    def setUp(self):
        # Random number generator
        rg = random.Random(0)
        self.myrand = rg.random
        self.myrandint = rg.randint
        n_data = 10
        # Generate some random input.
        data =  [self.myrand()*2-1 + self.myrand()*2j-1j
                 for x in range(n_data)]
        self.data = data
        # sends random ms between 0 and 7
        mwidth = 3
        ms = [self.myrandint(0, 7) for d in data]
        width = 32
        sendnth = 32
        steps_rqd = sendnth * n_data + 1000
        executable, inputfiles = generate('random', data, ms, sendnth, width, mwidth)
        qa_data_source_fn = os.path.join(config.builddir, 'data_source', 'qa_data_source.v') 
        b100.make_make('data_source', inputfiles + [qa_data_source_fn])
        b100.synthesise('data_source')
        b100.copy_image('data_source')

    def test_it(self):
        stream_args = uhd.stream_args(cpu_format='fc32', channels=range(1))
        from_usrp = uhd.usrp_source(device_addr='', stream_args=stream_args)
        head = gr.head(gr.sizeof_gr_complex, len(self.data)*2)
        snk = gr.vector_sink_c()
        tb = gr.top_block()
        tb.connect(from_usrp, head, snk)
        tb.run()
        out_data = snk.data()
        tol = 1e-3
        matched = False
        max_streak = 0
        for offset in range(len(self.data)):
            worked = True
            streak = len(self.data)
            for i in range(len(self.data)):
                if abs(self.data[i] - out_data[offset+i]) > tol:
                    worked = False
                    streak = i
                    break
            max_streak = max(streak, max_streak)
            if worked:
                matched = True
                break
        print("Maximum streak was {0} out of {1}".format(max_streak, len(self.data)))
        self.assertEqual(matched, True)
                                

if __name__ == '__main__':
    config.setup_logging(logging.DEBUG)
    unittest.main()

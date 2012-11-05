# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

"""
MyHDL Test Bench to check the vericode nothing module (does nothing at all).
"""

import random
import unittest
import logging
from copy import copy
import shutil
import os

from fpga_sdrlib import config, b100
from fpga_sdrlib.null.build import generate_null_B100_image
from fpga_sdrlib.testbench import TestBenchB100
from fpga_sdrlib.message import msg_utils
from fpga_sdrlib.message.msg_codes import parse_packet
from fpga_sdrlib.conversions import int_to_c

class NullTestBenchB100(TestBenchB100):
    """
    Helper class for doing testing.
    
    Args:
        name: A name to use with for generated files.
        in_samples: A list of complex points to send.
        defines: Macro definitions (constants) to use in verilog code.
    """

    def prepare(self):
        builddir = os.path.join(config.builddir, 'null')
        output_dir = os.path.join(builddir, 'build-B100_{name}'.format(name=self.name))
        binary = os.path.join(output_dir, 'B100.bin')
        shutil.copyfile(binary, b100.fpgaimage_fn)

class TestNull(unittest.TestCase):
    """
    Test the verilog nothing module (does nothing to data stream).
    """

    def setUp(self):
        # The amount of data to send
        self.n_data = 200
        # Random number generator
        rg = random.Random(0)
        self.myrand = rg.random
        # Get the input data
        self.data = [(self.myrand()*2-1) + 1j*(self.myrand()*2-1) for i in range(self.n_data)]
        #generate_null_B100_image('default', defines)
        self.tbb = NullTestBenchB100('default', self.data, None, )
        self.tbb.prepare()

    def tearDown(self):
        pass

    def test_null(self):
        """
        Test qa_wrapper_null
        """
        tb = self.tbb
        tb.run()
        self.assertEqual(len(tb.out_samples), len(self.data))
        # Compare data
        for e, r in zip(self.data, tb.out_samples):
            self.assertAlmostEqual(e, r, 3)
        # Checked passed messages
        # It should pass back the input data in messages.=
        data_from_msgs = []
        for packet in tb.out_messages:
            # Expected format of message is "nothing: received 23423423"
            msg = parse_packet(packet)
            data_from_msgs.append(int(msg.split()[2]))
            

if __name__ == '__main__':
    config.setup_logging(logging.DEBUG)    
    unittest.main()

# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

"""
MyHDL Test Bench to check the vericode nothing module (does nothing at all).
"""

import random
import unittest
import logging

from fpga_sdrlib import config
from fpga_sdrlib.nothing.build import generate_nothing_executable
from fpga_sdrlib.testbench import TestBenchIcarus
from fpga_sdrlib.message import msg_utils
from fpga_sdrlib.message.msg_codes import parse_packet
from fpga_sdrlib.conversions import int_to_c

class NothingTestBenchIcarus(TestBenchIcarus):
    """
    Helper class for doing testing.
    
    Args:
        name: A name to use with for generated files.
        in_samples: A list of complex points to send.
        sendnth: Send an input on every `sendnth` clock cycle.
        in_ms: A list of the meta data to send.
        defines: Macro definitions (constants) to use in verilog code.
    """

    def prepare(self):
        self.executable = generate_nothing_executable(self.name, self.defines)

class TestNothing(unittest.TestCase):
    """
    Test the verilog nothing module (does nothing to data stream).
    """

    def setUp(self):
        # The amount of data to send
        self.n_data = 200
        # Random number generator
        rg = random.Random(0)
        self.myrand = rg.random
        self.myrandint = rg.randint
        # Width of a complex number
        self.width = 32
        # How often to send input.
        self.sendnth = 2
        # Get the input data
        self.data = [(self.myrand()*2-1) + 1j*(self.myrand()*2-1) for i in range(self.n_data)]
        # Send in some meta data
        self.mwidth = 3
        self.ms = [self.myrandint(0, 7) for d in self.data]
        # Create the test bench
        name = 'basic'
        debug = True
        self.defines = {"DEBUG": debug,
                        "WIDTH": self.width,
                        "MWIDTH": self.mwidth,
                        }
        self.tb = NothingTestBenchIcarus(name, self.data, self.sendnth, self.ms, defines=self.defines)
        self.tb.prepare()

    def tearDown(self):
        pass

    def test_nothing(self):
        """
        Test a nothing block.
        """
        steps_rqd = self.n_data * self.sendnth + 1000
        self.tb.run(steps_rqd)
        self.assertEqual(len(self.tb.out_samples), len(self.data))
        # Compare data
        for e, r in zip(self.data, self.tb.out_samples):
            self.assertAlmostEqual(e.real, r.real, 3)
            self.assertAlmostEqual(e.imag, r.imag, 3)
        # Compare ms
        self.assertEqual(len(self.tb.out_ms), len(self.ms))
        for r, e in zip(self.tb.out_ms, self.ms):
            self.assertEqual(r, e)
        # Checked passed messages
        # It should pass back the input data in messages.=
        packets = msg_utils.stream_to_packets(self.tb.out_msgs)
        data_from_msgs = []
        for packet in packets:
            # Expected format of message is "nothing: received 23423423"
            msg = parse_packet(packet)
            data_from_msgs.append(int(msg.split()[2]))
        for r, e in zip(data_from_msgs, self.data):
            # Convert integers in message into the complex numbers.
            c = int_to_c(r, self.width/2)
            self.assertAlmostEqual(c, e, 3)
            

if __name__ == '__main__':
    config.setup_logging(logging.DEBUG)    
    unittest.main()

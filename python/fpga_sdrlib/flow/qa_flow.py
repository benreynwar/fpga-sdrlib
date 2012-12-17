# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import os
import random
import unittest
import logging
import shutil

from fpga_sdrlib.generate import logceil
from fpga_sdrlib import config, b100, buildutils
from fpga_sdrlib.testbench import TestBenchB100, TestBenchIcarusOuter

logger = logging.getLogger(__name__)

class TestSplit(unittest.TestCase):

    def test_one(self):
        """
        Test the split module.
        """
        width = 32
        sendnth = 4
        maxint = pow(2, width)-1
        n_data = 100
        n_streams = 3
        data = [random.randint(0, maxint) for d in range(n_data)]
        # Work out what the expected result is.
        expected_data = []
        for ds in [data[n_streams*i:n_streams*(i+1)] for i in range(n_data/n_streams)]:
            e_d = 0
            f = 1
            for d in ds:
                e_d += d*f
                f *= pow(2, width)
            expected_data.append(e_d)
        # How many steps are required to simulate the data.
        steps_rqd = n_data * sendnth * 2 + 1000
        # Create, setup and simulate the test bench.
        defines = config.updated_defines(
            {'N_OUT_STREAMS': n_streams,
             'LOG_N_OUT_STREAMS': logceil(n_streams),
             'WIDTH': width,
             })
        executable = buildutils.generate_icarus_executable(
            'flow', 'split', '-test', defines)
        tb = TestBenchIcarusOuter(executable, in_raw=data, width=width)
        tb.run(steps_rqd)
        # Confirm that our data is correct.
        self.assertEqual(len(tb.out_raw), len(expected_data))
        for r, e in zip(tb.out_raw, expected_data):
            self.assertEqual(e, r)

    def test_return_one(self):
        """
        Test the split module.
        """
        width = config.default_width
        sendnth = 4
        maxint = pow(2, width)-1
        n_data = 100
        n_streams = 2
        data = [random.randint(0, maxint) for d in range(n_data)]
        # Work out what the expected result is.
        # We don't know which stream will be returned.
        expected_data = data[::2]
        alt_expected_data = data[1::2]
        # How many steps are required to simulate the data.
        steps_rqd = n_data * sendnth * 2 + 1000
        # Create, setup and simulate the test bench.
        defines = config.updated_defines(
            {'WIDTH': width,
             })
        executable = buildutils.generate_icarus_executable(
            'flow', 'split_return_one', '-test', defines=defines)
        fpgaimage = buildutils.generate_B100_image(
            'flow', 'split_return_one', '-test', defines=defines)
        tb_icarus = TestBenchIcarusOuter(executable, in_raw=data)
        tb_b100 = TestBenchB100(fpgaimage, in_raw=data, output_msgs=False)
        for tb, steps in (
                (tb_icarus, steps_rqd),
                (tb_b100, 100000), 
                ):
            tb.run(steps)
            # Confirm that our data is correct.
            stream = None
            self.assertEqual(len(tb.out_raw), len(expected_data))
            for r, e, a in zip(tb.out_raw, expected_data, alt_expected_data):
                if stream is None:
                    if (r != e):
                        stream = 2
                    else:
                        stream = 1
                if stream == 1:
                    self.assertEqual(e, r)
                else:
                    self.assertEqual(a, r)

class TestBufferAA(unittest.TestCase):

    def test_one(self):
        """
        Test the buffer_AA module.
        """
        width = config.default_width
        sendnth = 1
        maxint = pow(2, width)-1
        buffer_length = 32
        n_data = 100
        data = [random.randint(1, maxint) for d in range(n_data)]
        # How many steps are required to simulate the data.
        steps_rqd = n_data * sendnth * 2 + 1000
        # Create, setup and simulate the test bench.
        defines = config.updated_defines(
            {'WIDTH': width,
             'BUFFER_LENGTH': buffer_length,
             'LOG_BUFFER_LENGTH': logceil(buffer_length),
             'WRITEERRORCODE': 666,
             'READERRORCODE': 777,
             })
        executable = buildutils.generate_icarus_executable(
            'flow', 'buffer_AA', '-test', defines=defines)
        fpgaimage = buildutils.generate_B100_image(
            'flow', 'buffer_AA', '-test', defines=defines)
        #fpgaimage = "/home/ben/Code/fpga-sdrlib/build/flow/build-B100_buffer_AA-test/B100.bin"
        tb_icarus = TestBenchIcarusOuter(executable, in_raw=data)
        tb_b100 = TestBenchB100(fpgaimage, in_raw=data, output_msgs=False)
        for tb, steps in (
                (tb_icarus, steps_rqd),
                (tb_b100, 100000), 
                ):
            tb.run(steps)
            # Confirm that our data is correct.
            stream = None
            self.assertEqual(len(tb.out_raw), len(data))
            for r, e in zip(tb.out_raw, data):
                self.assertEqual(e, r)

    def test_bursts(self):
        """
        Test the buffer_AA module.
        """
        width = config.default_width
        sendnth = 1
        maxint = pow(2, width)-1
        buffer_length = 32
        burst_length = 4
        n_data = 100
        data = [random.randint(1, maxint) for d in range(n_data)]
        # How many steps are required to simulate the data.
        steps_rqd = n_data * sendnth * 2 + 1000
        # Create, setup and simulate the test bench.
        defines = config.updated_defines(
            {'WIDTH': width,
             'BUFFER_LENGTH': buffer_length,
             'LOG_BUFFER_LENGTH': logceil(buffer_length),
             'LOG_BURST_LENGTH': logceil(burst_length),
             'WRITEERRORCODE': 666,
             'READERRORCODE': 777,
             })
        executable = buildutils.generate_icarus_executable(
            'flow', 'buffer_AA_burst', '-test', defines=defines)
        fpgaimage = buildutils.generate_B100_image(
            'flow', 'buffer_AA_burst', '-test', defines=defines)
        tb_icarus = TestBenchIcarusOuter(executable, in_raw=data)
        tb_b100 = TestBenchB100(fpgaimage, in_raw=data, output_msgs=False)
        for tb, steps in (
                (tb_icarus, steps_rqd),
                (tb_b100, 100000), 
                ):
            tb.run(steps)
            # Confirm that our data is correct.
            stream = None
            self.assertEqual(len(tb.out_raw), len(data))
            for r, e in zip(tb.out_raw, data):
                self.assertEqual(e, r)

if __name__ == '__main__':
    config.setup_logging(logging.DEBUG)
    #suite = unittest.TestLoader().loadTestsFromTestCase(TestSplit)
    #suite = unittest.TestLoader().loadTestsFromTestCase(TestBufferAA)
    #unittest.TextTestRunner(verbosity=2).run(suite)
    unittest.main()

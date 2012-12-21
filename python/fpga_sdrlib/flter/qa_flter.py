# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import os
import random
import unittest
import logging
import shutil

from fpga_sdrlib.message import msg_utils
from fpga_sdrlib.conversions import f_to_int
from fpga_sdrlib.generate import logceil
from fpga_sdrlib import config, b100, buildutils
from fpga_sdrlib.testbench import TestBenchB100, TestBenchIcarusInner, TestBenchIcarusOuter

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

def taps_to_start_msgs(taps, width, target):
    contents = [f_to_int(tap, width, clean1=True) for tap in taps]
    packet = msg_utils.packet_from_content(contents, config.msg_length_width,
                                           config.msg_width, target)
    return packet

def prune_zeros(xs):
    start_index = None
    stop_index = None
    for i, x in enumerate(xs):
        if x != 0:
            if start_index is None:
                start_index = i
            stop_index = i
    if start_index is None:
        return []
    else:
        return xs[start_index:stop_index+1]

class TestFilter(unittest.TestCase):

    def test_one(self):
        """
        Test the filter module.
        """
        width = config.default_width
        sendnth = config.default_sendnth
        # Changing filter_length will require resynthesis.
        filter_length = 4
        taps = [random.random()*2-1 for i in range(filter_length)]
        total = sum([abs(t) for t in taps])
        taps = [t/total for t in taps]
        # Arguments used for producing verilog from templates.
        extraargs = {'summult_length': filter_length,}
        # Amount of data to send.
        n_data = 10
        # Define the input
        in_samples = [random.random()*2-1 + random.random()*2j-1j for i in range(n_data)]
        in_samples += [0]*(filter_length-1)
        steps_rqd = len(in_samples)*sendnth + 100
        # Define meta data
        mwidth = 1
        in_ms = [random.randint(0, pow(2,mwidth)-1) for d in in_samples]
        expected = convolve(in_samples, taps)
        steps_rqd = n_data * sendnth * 2 + 1000
        filter_id = 123
        # Create, setup and simulate the test bench.
        defines = config.updated_defines(
            {'WIDTH': width,
             'FILTER_LENGTH': filter_length,
             'FILTER_ID': filter_id,
             })
        executable_inner = buildutils.generate_icarus_executable(
            'flter', 'filter_inner', '-test', defines=defines, extraargs=extraargs)
        executable_outer = buildutils.generate_icarus_executable(
            'flter', 'filter', '-test', defines=defines, extraargs=extraargs)
        fpgaimage = buildutils.generate_B100_image(
            'flter', 'filter', '-test', defines=defines,
            extraargs=extraargs)
        start_msgs = taps_to_start_msgs(taps, defines['WIDTH']/2, filter_id)
        tb_icarus_inner = TestBenchIcarusInner(executable_inner, in_samples, in_ms, start_msgs)
        tb_icarus_outer = TestBenchIcarusOuter(executable_outer, in_samples, start_msgs)
        tb_b100 = TestBenchB100(fpgaimage, in_samples, start_msgs)
        for tb, steps in (
                (tb_icarus_inner, steps_rqd),
                (tb_icarus_outer, steps_rqd),
                (tb_b100, 100000), 
                ):
            tb.run(steps)
            # Confirm that our data is correct.
            self.assertEqual(len(tb.out_samples), len(expected))
            for r, e in zip(tb.out_samples, expected):
                self.assertAlmostEqual(e, r, 3)

class TestFilterBank(unittest.TestCase):

    def test_one(self):
        """
        Test the filterbank module.
        """
        width = config.default_width
        sendnth = config.default_sendnth
        # Changing filter_length will require resynthesis.
        n_filters = 3
        filter_length = 3
        all_taps = []
        combined_taps = []
        for n in range(n_filters):
            taps = [random.random()*2-1 for i in range(filter_length)]
            total = sum([abs(t) for t in taps])
            taps = [t/total for t in taps]
            all_taps.append(taps)
            combined_taps.extend(taps)
        # Arguments used for producing verilog from templates.
        extraargs = {'summult_length': filter_length,}
        # Amount of data to send.
        n_data = 30
        # Define the input
        in_samples = [0]*filter_length*n_filters*2
        in_samples += [random.random()*2-1 + random.random()*2j-1j for i in range(n_data)]
        in_samples += [0]*(filter_length-1)*n_filters
        steps_rqd = len(in_samples)*sendnth + 100
        # Define meta data
        mwidth = 1
        in_ms = [random.randint(0, pow(2,mwidth)-1) for d in in_samples]
        possible_expected = []
        for m in range(n_filters):
            shifted_taps = all_taps[m:] + all_taps[:m]
            expected_outputs = []
            for n in range(n_filters):
                filter_inputs = in_samples[n::n_filters]
                convolved = convolve(filter_inputs, shifted_taps[n])
                expected_outputs.append(convolved)
            expected = []
            for eo in zip(*expected_outputs):
                expected.extend(eo)
            possible_expected.append(expected)
        steps_rqd = n_data * sendnth * 2 + 1000
        # Create, setup and simulate the test bench.
        filter_id = 123
        defines = config.updated_defines(
            {'WIDTH': width,
             'FILTER_LENGTH': filter_length,
             'FILTERBANK_ID': filter_id,
             'N_FILTERS': n_filters,
             'FILTERBANK_MSG_BUFFER_LENGTH': 128,
             })
        executable_inner = buildutils.generate_icarus_executable(
            'flter', 'filterbank_inner', '-test', defines=defines, extraargs=extraargs)
        executable_outer = buildutils.generate_icarus_executable(
            'flter', 'filterbank', '-test', defines=defines, extraargs=extraargs)
        fpgaimage = buildutils.generate_B100_image(
            'flter', 'filterbank', '-test', defines=defines,
            extraargs=extraargs)
        start_msgs = taps_to_start_msgs(combined_taps, defines['WIDTH']/2, filter_id)
        tb_icarus_inner = TestBenchIcarusInner(executable_inner, in_samples, in_ms, start_msgs)
        tb_icarus_outer = TestBenchIcarusOuter(executable_outer, in_samples, start_msgs)
        tb_b100 = TestBenchB100(fpgaimage, in_samples, start_msgs)
        for tb, steps in (
                (tb_icarus_inner, steps_rqd),
                (tb_icarus_outer, steps_rqd),
                (tb_b100, 100000), 
                ):
            tb.run(steps)
            # Confirm that our data is correct.
            received = prune_zeros(tb.out_samples)
            tol = 0.001
            matched_once = False
            for expected in possible_expected:
                expected = prune_zeros(expected)
                matches = True
                if (len(received) != len(expected)):
                    matches = False
                else:
                    for r, e in zip(received, expected):
                        if (abs(r-e) > tol):
                            matches = False
                            break
                if matches:
                    matched_once = True
            self.assertTrue(matched_once)

if __name__ == '__main__':
    config.setup_logging(logging.DEBUG)
    #suite = unittest.TestLoader().loadTestsFromTestCase(TestFilterBank)
    #unittest.TextTestRunner(verbosity=2).run(suite)
    unittest.main()

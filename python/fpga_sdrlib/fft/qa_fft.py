# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import os
import random
import unittest
import logging
import shutil
from numpy import fft

from fpga_sdrlib.message import msg_utils
from fpga_sdrlib.conversions import int_to_c
from fpga_sdrlib.generate import logceil
from fpga_sdrlib import config, b100, buildutils
from fpga_sdrlib.testbench import TestBenchB100, TestBenchIcarusInner, TestBenchIcarusOuter
from fpga_sdrlib.fft.dit import pystage

logger = logging.getLogger(__name__)

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

class TestButterfly(unittest.TestCase):

    def test_one(self):
        """
        Test the butterfly module.
        """
        sendnth = 5
        n_data = 1
        width = 32
        in_samples = []
        expected = []
        xas = [random.random()*2-1 + random.random()*2j-1j for i in range(n_data)]
        xbs = [random.random()*2-1 + random.random()*2j-1j for i in range(n_data)]
        # Max val of w is 10000 (roughly 0.5)
        ws = [0.5*(random.random()*2-1) + 0.5*(random.random()*2j-1j) for i in range(n_data)]
        for xa, xb, w in zip(xas, xbs, ws):
            in_samples.append(xa)
            in_samples.append(xb)
            in_samples.append(w)
            ya = xa + xb*w
            yb = xa - xb*w
            expected.append(ya/2)
            expected.append(yb/2)
        steps_rqd = len(in_samples)*sendnth*2 + 100
        # Define meta data
        mwidth = 1
        raw_ms = [random.randint(0, pow(2,mwidth)-1) for i in range(n_data)]
        in_ms = []
        expected_ms = []
        for m in raw_ms:
            in_ms.extend((m, 0, 0))
            expected_ms.extend((m, 0))
        defines = config.updated_defines({
            'DEBUG': True,
            })
        executable_inner = buildutils.generate_icarus_executable(
            'fft', 'butterfly_inner', '-test', defines=defines)

        executable_outer = buildutils.generate_icarus_executable(
            'fft', 'butterfly', '-test', defines=defines)
        #fpgaimage = buildutils.generate_B100_image(
        #    'fft', 'butterfly', '-test', defines=defines)
        tb_icarus_inner = TestBenchIcarusInner(executable_inner, in_samples, in_ms, sendnth=sendnth)
        tb_icarus_outer = TestBenchIcarusOuter(executable_outer, in_samples, sendnth=sendnth)
        #tb_b100 = TestBenchB100(fpgaimage, in_samples)
        for tb, steps, check_ms in (
                (tb_icarus_inner, steps_rqd, True),
                (tb_icarus_outer, steps_rqd, False),
                #(tb_b100, 100000, False), 
                ):
            tb.run(steps)
            # Confirm that our data is correct.
            print(tb.out_raw)
            print(tb.out_samples)
            print(expected)
            self.assertEqual(len(tb.out_samples), len(expected))
            for msg in tb.out_messages:
                print("message is")
                print(msg)
                xa = int_to_c(msg[1], width/2-1)
                xbw = int_to_c(msg[2], width/2-1)
                ya = int_to_c(msg[3], width/2-1)
                yb = int_to_c(msg[4], width/2-1)
                print("e xa is {0} xbw is {1}".format(xas[0]/2, xbs[0]*ws[0]/2))
                print("r xa is {0} xbw is {1}".format(xa, xbw))
            for r, e in zip(tb.out_samples, expected):
                print(e, r)
                self.assertAlmostEqual(e, r, 3)
            if check_ms:
                self.assertEqual(len(tb.out_ms), len(expected_ms))
                for r, e in zip(tb.out_ms, expected_ms):
                    self.assertEqual(e, r)
        
        
class TestStage(unittest.TestCase):

    def test_one(self):
        """
        Test the stage module.
        """
        width = config.default_width
        sendnth = config.default_sendnth
        # Changing N will require resynthesis.
        N = 8
        # Arguments used for producing verilog from templates.
        extraargs = {}
        # Amount of data to send.
        n_data = 2*N
        # Define the input
        in_samples = [random.random()*2-1 + random.random()*2j-1j for i in range(n_data)]
        steps_rqd = len(in_samples)*sendnth + 100
        # Define meta data
        mwidth = 3
        in_ms = [random.randint(0, pow(2,mwidth)-1) for d in in_samples]
        expected = in_samples
        steps_rqd = n_data * sendnth * 2 + 1000
        # Create, setup and simulate the test bench.
        defines = config.updated_defines(
            {'WIDTH': width,
             'MWIDTH': mwidth,
             'N': N
             })
        executable_inner = buildutils.generate_icarus_executable(
            'fft', 'stage_inner', '-{0}'.format(N), defines=defines,
            extraargs=extraargs)
        executable_outer = buildutils.generate_icarus_executable(
            'fft', 'stage', '-{0}'.format(N), defines=defines,
            extraargs=extraargs)
        #fpgaimage = buildutils.generate_B100_image(
        #    'fft', 'stage', '-{0}'.format(N), defines=defines,
        #    extraargs=extraargs)
        tb_icarus_inner = TestBenchIcarusInner(executable_inner, in_samples, in_ms)
        tb_icarus_outer = TestBenchIcarusOuter(executable_outer, in_samples)
        #tb_b100 = TestBenchB100(fpgaimage, in_samples)
        for tb, steps, check_ms in (
                (tb_icarus_inner, steps_rqd, True),
                (tb_icarus_outer, steps_rqd, False),
                #(tb_b100, 100000, False), 
                ):
            tb.run(steps)
            # Confirm that our data is correct.
            self.assertEqual(len(tb.out_samples), len(expected))
            for r, e in zip(tb.out_samples, expected):
                self.assertAlmostEqual(e, r, 3)
            if check_ms:
                self.assertEqual(len(tb.out_ms), len(in_ms))
                for r, e in zip(tb.out_ms, in_ms):
                    self.assertEqual(e, r)

class TestStageToStage(unittest.TestCase):

    def test_one(self):
        """
        Test the stage_to_stage module.
        """
        width = config.default_width
        sendnth = config.default_sendnth
        # Changing N will require resynthesis.
        N = 16
        # Arguments used for producing verilog from templates.
        extraargs = {'N': N,
                     'width': width}
        # Amount of data to send.
        n_data = 10*N
        # Define the input.
        # I think must have abs mag 1 so divide by sqrt(2)
        in_samples = [random.random()*2-1 + random.random()*2j-1j for i in range(n_data)]
        factor = pow(2, -0.5)
        in_samples = [s*factor for s in in_samples]
        steps_rqd = len(in_samples)*sendnth + 100
        # Define meta data
        mwidth = 3
        in_ms = [random.randint(0, pow(2,mwidth)-1) for d in in_samples]
        steps_rqd = n_data * sendnth * 2 + 1000
        stage_index = 1
        # Calculate expected output
        e_samples = []
        for stage_samples in [in_samples[i*N:(i+1)*N] for i in range(n_data/N)]:
            e_samples.extend(pystage(N, stage_index, stage_samples))
        e_samples = [s/2 for s in e_samples]
        # Create, setup and simulate the test bench.
        defines = config.updated_defines(
            {'WIDTH': width,
             'MWIDTH': mwidth,
             'N': N,
             'STAGE_INDEX': stage_index,
             })
        executable_inner = buildutils.generate_icarus_executable(
            'fft', 'stage_to_stage_inner', '-{0}'.format(N), defines=defines,
            extraargs=extraargs)
        executable_outer = buildutils.generate_icarus_executable(
            'fft', 'stage_to_stage', '-{0}'.format(N), defines=defines,
            extraargs=extraargs)
        #fpgaimage = buildutils.generate_B100_image(
        #    'fft', 'stage_to_stage', '-{0}'.format(N), defines=defines,
        #    extraargs=extraargs)
        tb_icarus_inner = TestBenchIcarusInner(executable_inner, in_samples, in_ms)
        #tb_icarus_outer = TestBenchIcarusOuter(executable_outer, in_samples)
        #tb_b100 = TestBenchB100(fpgaimage, in_samples)
        for tb, steps, check_ms in (
                (tb_icarus_inner, steps_rqd, True),
                #(tb_icarus_outer, steps_rqd, False),
                #(tb_b100, 100000, False), 
                ):
            tb.run(steps)
            # Confirm that our data is correct.
            self.assertEqual(len(tb.out_samples), len(e_samples))
            for r, e in zip(tb.out_samples, e_samples):
                self.assertAlmostEqual(e, r, 3)
            if check_ms:
                self.assertEqual(len(tb.out_ms), len(in_ms))
                for r, e in zip(tb.out_ms, in_ms):
                    self.assertEqual(e, r)

class TestDITSeries(unittest.TestCase):

    def test_one(self):
        """
        Test the dit_series module.
        """
        width = config.default_width
        sendnth = config.default_sendnth
        # Changing N will require resynthesis.
        N = 16
        # Arguments used for producing verilog from templates.
        extraargs = {'N': N,
                     'width': width}
        # Amount of data to send.
        n_data = 1*N
        # Define the input.
        # I think must have abs mag 1 so divide by sqrt(2)
        in_samples = [random.random()*2-1 + random.random()*2j-1j for i in range(n_data)]
        factor = pow(2, -0.5)
        in_samples = [s*factor for s in in_samples]
        steps_rqd = len(in_samples)*sendnth + 100
        # Define meta data
        mwidth = 3
        in_ms = [random.randint(0, pow(2,mwidth)-1) for d in in_samples]
        steps_rqd = n_data * sendnth * 2 + 1000
        # Calculate expected output
        e_samples = []
        for stage_samples in [in_samples[i*N:(i+1)*N] for i in range(n_data/N)]:
            e_samples.extend(fft.fft(stage_samples))
        e_samples = [s/N for s in e_samples]
        # Create, setup and simulate the test bench.
        defines = config.updated_defines(
            {'WIDTH': width,
             'MWIDTH': mwidth,
             'N': N,
             })
        executable_inner = buildutils.generate_icarus_executable(
            'fft', 'dit_series_inner', '-{0}'.format(N), defines=defines,
            extraargs=extraargs)
        #executable_outer = buildutils.generate_icarus_executable(
        #    'fft', 'dit_series', '-{0}'.format(N), defines=defines,
        #    extraargs=extraargs)
        #fpgaimage = buildutils.generate_B100_image(
        #    'fft', 'stage_to_stage', '-{0}'.format(N), defines=defines,
        #    extraargs=extraargs)
        tb_icarus_inner = TestBenchIcarusInner(executable_inner, in_samples, in_ms)
        #tb_icarus_outer = TestBenchIcarusOuter(executable_outer, in_samples)
        #tb_b100 = TestBenchB100(fpgaimage, in_samples)
        for tb, steps, check_ms in (
                (tb_icarus_inner, steps_rqd, True),
                #(tb_icarus_outer, steps_rqd, False),
                #(tb_b100, 100000, False), 
                ):
            tb.run(steps)
            # Confirm that our data is correct.
            self.assertEqual(len(tb.out_samples), len(e_samples))
            for r, e in zip(tb.out_samples, e_samples):
                self.assertAlmostEqual(e, r, 3)
            if check_ms:
                self.assertEqual(len(tb.out_ms), len(in_ms))
                for r, e in zip(tb.out_ms, in_ms):
                    self.assertEqual(e, r)

if __name__ == '__main__':
    config.setup_logging(logging.DEBUG)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDITSeries)
    #suite = unittest.TestLoader().loadTestsFromTestCase(TestStageToStage)
    unittest.TextTestRunner(verbosity=2).run(suite)
    #unittest.main()

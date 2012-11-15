# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import os
import random
import unittest
import logging
import shutil

from fpga_sdrlib.buildutils import generate_icarus_executable, generate_B100_image, logceil
from fpga_sdrlib import config, b100, buildutils
from fpga_sdrlib.message.msg_utils import stream_to_packets, make_packet_dict, stream_to_samples_and_packets
from fpga_sdrlib.testbench import TestBenchB100, TestBenchIcarusOuter

from myhdl import Cosimulation, Signal, delay, always, Simulation

logger = logging.getLogger(__name__)

class TestBenchMessageStreamCombiner(TestBenchIcarusOuter):
    """
    The message stream combiner needs it's own test bench because in_nd
    is an array holding the values for multiple input streams.
    """

    def send_input(self):
        self.count = 0
        self.first = True
        self.datapos = 0
        @always(self.clk.posedge)
        def run():
            """
            Sends input to our DUT (design-under-test) and
            receives output.
            """
            if not self.doing_prerun:
                # Send input.
                if self.count >= self.sendnth and self.datapos < len(self.in_raw):
                    m = 1
                    nd = 0
                    nd_m = 1
                    summed = 0
                    for d in self.in_raw[self.datapos]:
                        if d is not None:
                            summed += d * m
                            nd += nd_m
                        m *= pow(2, self.width)
                        nd_m *= 2
                    self.in_data.next = summed
                    self.in_nd.next = nd
                    self.datapos += 1
                    self.count = 0
                else:
                    self.in_nd.next = 0
                    self.count += 1
        return run

class TestBenchMessageSlicer(TestBenchIcarusOuter):
    """
    Message slicer needs it's own test bench because it's not the
    value of in_nd that indicats new data but rather whether it has
    changed.

    This is to make generating messages in the module code more
    convenient.
    """

    def send_input(self):
        self.count = 0
        self.first = True
        self.datapos = 0
        @always(self.clk.posedge)
        def run():
            """
            Sends input to our DUT (design-under-test) and
            receives output.
            """
            if not self.doing_prerun:
                # Send input.
                if self.count >= self.sendnth and self.datapos < len(self.in_raw):
                    self.in_data.next = self.in_raw[self.datapos]
                    if 'in_m' in self.signal_names:
                        self.in_m.next = self.in_ms[self.datapos]
                    self.in_nd.next = not self.in_nd
                    self.datapos += 1
                    self.count = 0
                else:
                    self.count += 1
        return run

def generate_random_packets(max_length, n_packets, bits_for_length, width, prob_start=1, myrand=random.Random(), none_sample=True):
    """
    Generate a data stream containing a bunch of random packets.
    The lengths are distributed uniformly up to max_length-1.

    """
    data = []
    packets = []
    sample_max = int(pow(2, width-2))
    info_max = int(pow(2, width-1-bits_for_length)-1)
    block_max = int(pow(2, width-1)-1)
    assert(pow(2, bits_for_length) >= max_length)
    for i in range(n_packets):
        while (myrand.random() > prob_start):
            if none_sample:
                data.append(None)
            else:
                data.append(myrand.randint(0, sample_max))
        packet = []
        l = myrand.randint(0, max_length-1)
        info = myrand.randint(0, info_max)
        # Make header
        header = (1 << int(width-1)) + (l << int(width-1-bits_for_length)) + info
        data.append(header)
        packet.append(header)
        for j in range(l):
            d = myrand.randint(0, block_max)
            data.append(d)
            packet.append(d)
        packets.append(packet)
    return data, packets


class TestMessageStreamCombiner(unittest.TestCase):

    def setUp(self):
        self.rg = random.Random(0)

    def test_one_stream(self):
        """
        Test the stream combiner with a single stream of data.
        """
        width = 32
        sendnth = 4
        input_buffer_length = 64
        max_packet_length = 1024
        # First bit is 0 so data is from 0 to pow(2, 31)-1
        maxint = pow(2, width-1)-1
        n_data = 10
        data = [self.rg.randint(0, maxint) for d in range(n_data)]
        # How many steps are required to simulate the data.
        steps_rqd = n_data * sendnth * 2 + 1000
        # Create, setup and simulate the test bench.
        defines = config.updated_defines(
            {'N_STREAMS': 1,
             'LOG_N_STREAMS': 1,
             'WIDTH': width,
             'INPUT_BUFFER_LENGTH': 16,
             'LOG_INPUT_BUFFER_LENGTH': 4,
             'MAX_PACKET_LENGTH': 16,
             'LOG_MAX_PACKET_LENGTH': 4,
             })
        executable = buildutils.generate_icarus_executable(
            'message', 'message_stream_combiner', '-one_stream', defines)
        tb = TestBenchIcarusOuter(executable, in_raw=data, width=width)
        tb.run(steps_rqd)
        # Confirm that our data is correct.
        self.assertEqual(len(tb.out_raw), len(data))
        for r, e in zip(tb.out_raw, data):
            self.assertEqual(e, r)

    def test_streams(self):
        """
        Test the stream combiner a number of streams.
        """
        width = 32
        sendnth = 8
        n_streams = 3
        buffer_length = 128
        max_packet_length = pow(2, config.msg_length_width)
        defines = config.updated_defines(
            {'N_STREAMS': n_streams,
             'LOG_N_STREAMS': logceil(n_streams),
             'WIDTH': width,
             'INPUT_BUFFER_LENGTH': buffer_length,
             'LOG_INPUT_BUFFER_LENGTH': logceil(buffer_length),
             'MAX_PACKET_LENGTH': max_packet_length,
             'LOG_MAX_PACKET_LENGTH': config.msg_length_width,
             })
        top_packet_length = 64
        n_packets = 10
        data_streams = []
        packet_streams = []
        data_stream = []
        packet_stream = []
        max_stream_length = 0
        # Prob to start new packet.
        prob_start = 0.1
        for i in range(n_streams):
            # data and packets have same content but packets is just
            # broken into the packets
            data, packets = generate_random_packets(
                top_packet_length, n_packets, config.msg_length_width,
                width, prob_start, self.rg)
            max_stream_length = max(max_stream_length, len(data))
            data_streams.append(data)
            data_stream += data
            packet_streams.append(packets)
            packet_stream += packets
        for ds in data_streams:
            for i in range(max_stream_length - len(ds)):
                ds.append(None)
        expected_packet_dict = make_packet_dict(packet_stream)
        combined_data = zip(*data_streams)
        # How many steps are required to simulate the data.
        steps_rqd = len(combined_data) * sendnth * 2 - 1000 # + 1000
        # Create, setup and simulate the test bench.
        executable = buildutils.generate_icarus_executable(
            'message', 'message_stream_combiner', '-streams', defines)
        tb = TestBenchMessageStreamCombiner(
            executable, in_raw=combined_data, width=width)
        tb.run(steps_rqd)
        # Confirm that our method of converting a stream to packets is correct
        packets_again = stream_to_packets(data_stream, config.msg_length_width, width, allow_samples=False)
        packet_dict_again = make_packet_dict(packets_again)
        self.assertEqual(expected_packet_dict, packet_dict_again)
        # Now use it on the ouput rather than the input.
        received_packets = stream_to_packets(tb.out_raw, config.msg_length_width, width, allow_samples=False)
        received_packet_dict = make_packet_dict(received_packets)
        self.assertEqual(expected_packet_dict, received_packet_dict)

class TestMessageSlicer(unittest.TestCase):

    def setUp(self):
        self.rg = random.Random(0)

    def test_slicer(self):
        """
        Test the stream slicer.
        """
        width = 32
        n_slices = 3
        sendnth = 4
        buffer_length = 16
        n_data = 10
        data = []
        expected_data = []
        mfactor = pow(2, width)
        for i in range(n_data):
            m = pow(mfactor, n_slices-1)
            t = 0
            for s in range(n_slices):
                d = self.rg.randint(0, mfactor-1)
                t += d * m
                m = m / mfactor
                expected_data.append(d)
            data.append(t)
        # How many steps are required to simulate the data.
        steps_rqd = len(data) * sendnth * 2 #+ 1000
        # Create, setup and simulate the test bench.
        defines = config.updated_defines(
            {'N_SLICES': 3,
             'LOG_N_SLICES': logceil(n_slices),
             'WIDTH': width,
             'BUFFER_LENGTH': buffer_length,
             'LOG_BUFFER_LENGTH': logceil(buffer_length),
             })
        executable = buildutils.generate_icarus_executable(
            'message', 'message_slicer', '-test', defines)
        tb = TestBenchMessageSlicer(executable, in_raw=data, width=width)
        tb.run(steps_rqd)
        # Now check output
        self.assertEqual(len(expected_data), len(tb.out_raw))
        for e,r in zip(expected_data, tb.out_raw):
            self.assertAlmostEqual(e, r, 3)

class TestSampleMsgSplitter(unittest.TestCase):
    
    def setUp(self):
        self.rg = random.Random(0)

    def test_sample_msg_splitter(self):
        """
        Tests the sample msg splitter.

        Just checks that the samples are correct.
        Doesn't worry about what happened to the packets
        other than that they were removed.
        """
        top_packet_length = 64
        n_packets = 20
        width = 32
        prob_start = 0.1
        data, packets = generate_random_packets(
            top_packet_length, n_packets, config.msg_length_width,
            width, prob_start, self.rg, none_sample=False)
        executable = buildutils.generate_icarus_executable(
            'message', 'sample_msg_splitter', '-test')
        fpgaimage = buildutils.generate_B100_image(
            'message', 'sample_msg_splitter', '-test')
        tb_icarus = TestBenchIcarusOuter(executable, in_raw=data)
        tb_b100 = TestBenchB100(fpgaimage, in_raw=data)
        for tb in (tb_icarus, tb_b100, ):
            tb.run(5000)
            samples, packets = stream_to_samples_and_packets(
                data, config.msg_length_width, width)
            self.assertEqual(len(samples), len(tb.out_raw))
            for e, r in zip(samples, tb.out_raw):
                self.assertEqual(e, r)

class TestCombo(unittest.TestCase):
    
    def setUp(self):
        self.rg = random.Random(0)

    def test_combo(self):
        """
        Tests sample msg splitter and message stream combiner together.
        """
        top_packet_length = 64
        n_packets = 20
        width = 32
        prob_start = 0.1
        data, packets = generate_random_packets(
            top_packet_length, n_packets, config.msg_length_width,
            width, prob_start, self.rg, none_sample=False)
        executable = buildutils.generate_icarus_executable(
            'message', 'combo', '-test')
        fpgaimage = buildutils.generate_B100_image(
            'message', 'combo', '-test')
        tb_icarus = TestBenchIcarusOuter(executable, in_raw=data)
        tb_b100 = TestBenchB100(fpgaimage, in_raw=data)
        for tb in (tb_icarus,
                   tb_b100, ):
            tb.run(20000)
            print(data)
            print(tb.out_raw)
            self.assertEqual(len(data), len(tb.out_raw))
            for e, r in zip(data, tb.out_raw):
                self.assertEqual(e, r)

if __name__ == '__main__':
    config.setup_logging(logging.DEBUG)

    #suite = unittest.TestLoader().loadTestsFromTestCase(TestCombo)
    #unittest.TextTestRunner(verbosity=2).run(suite)

    unittest.main()

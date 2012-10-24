# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

"""
MyHDL Test Bench to check the vericode message stream code.
"""

import os
import random
import unittest
import logging

from fpga_sdrlib.message.build import generate_stream_combiner_executable, generate_slicer_executable, logceil
from fpga_sdrlib import config
from fpga_sdrlib.message.msg_utils import stream_to_packets, make_packet_dict

from myhdl import Cosimulation, Signal, delay, always, Simulation

logger = logging.getLogger(__name__)

class MessageTestBenchBase(object):
    """
    Base class for doing testing on message blocks.
    """

    base_signal_names = ['clk', 'rst_n', 'in_data', 'in_nd', 
                         'out_data', 'out_nd', 'error']

    def __init__(self):
        self.signal_names = self.base_signal_names
        for sn in self.signal_names:
            if sn.endswith('_n'):
                setattr(self, sn, Signal(1))
            else:
                setattr(self, sn, Signal(0))
        self.output = []
        self.drivers = [self.clk_driver, self.get_output, self.check_error]

    def clk_driver(self):
        @always(delay(1))
        def run():
            """ Drives the clock. """
            self.clk.next = not self.clk
        return run

    def get_output(self):
        self.output = []
        @always(self.clk.posedge)
        def run():
            """
            Receive output.
            """
            if self.out_nd:
                self.output.append(int(self.out_data))
        return run

    def check_error(self):
        self.error_count = 0
        @always(self.clk.posedge)
        def run():
            if self.error_count > 0:
                raise StandardError("The error wire is high.")
            if self.error:
                self.error_count += 1
        return run
        
    def simulate(self, clks):
        """
        Run a test bench simulation.
        """
        myhdlvpi = os.path.join(config.verilogdir, 'myhdl.vpi')
        command = "vvp -m {myhdlvpi} {executable}".format(myhdlvpi=myhdlvpi, executable=self.executable)
        cosimdict = dict([(sn, getattr(self, sn)) for sn in self.signal_names])
        dut = Cosimulation(command, **cosimdict)
        drivers = [df() for df in self.drivers]
        sim = Simulation(dut, *drivers)
        sim.run(2*clks)
        dut.__del__()
        del dut


class MessageStreamCombinerTestBench(MessageTestBenchBase):
    """
    Helper class for doing testing on message stream combiner.
    
    Args:
       width: The width of the message block (in bits).
       input_buffer_length: Number of data blocks in each input buffer.
       max_packet_length: Maximum number of data blocks in a packet.
       sendnth: Send a data block every sendnth clks.
       data: A list of lists.  Each list contains a datapoint from each
             stream or None of that stream is not transmitting.
    """

    def __init__(self, width, input_buffer_length, max_packet_length, sendnth, data):
        super(MessageStreamCombinerTestBench, self).__init__()
        self.n_streams = len(data[0])
        self.data = data
        self.width = width
        self.sendnth = sendnth
        self.input_buffer_length = input_buffer_length
        self.max_packet_length = max_packet_length
        self.drivers += [self.send_input]
        self.executable = generate_stream_combiner_executable(
            'icarus', self.n_streams, self.width, self.input_buffer_length,
            self.max_packet_length)

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
            if self.first:
                # Reset on first input.
                self.first = False
                self.rst_n.next = 0
            else:
                self.rst_n.next = 1
                # Send input.
                if self.count >= self.sendnth and self.datapos < len(self.data):
                    this_data = self.data[self.datapos]
                    combined_nd = 0
                    combined_data = 0
                    for i, d in enumerate(this_data):
                        if d is not None:
                            combined_nd += pow(2, i)
                            combined_data += d * pow(2, self.width*i)
                    self.in_data.next = combined_data
                    self.in_nd.next = combined_nd
                    self.datapos += 1
                    self.count = 0
                else:
                    self.in_nd.next = 0
                    self.count += 1
        return run

class MessageSlicerTestBench(MessageTestBenchBase):
    """
    Helper class for doing testing on message slicer
    
    Args:
       n_slices: The input is n_slices*width wide.
       width: The width of the message block (in bits).
       buffer_length: Number of data blocks in each input buffer.
       sendnth: Send input every sendnth clks.
       data: A list of integers for input.
    """

    def __init__(self, n_slices, width, buffer_length, sendnth, data):
        super(MessageSlicerTestBench, self).__init__()
        self.n_slices = n_slices
        self.data = data
        self.width = width
        self.sendnth = sendnth
        self.buffer_length = buffer_length
        self.drivers += [self.send_input]
        self.executable = generate_slicer_executable(
            'icarus', self.n_slices, self.width, self.buffer_length)

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
            if self.first:
                # Reset on first input.
                self.first = False
                self.rst_n.next = 0
            else:
                self.rst_n.next = 1
                # Send input.
                if self.count >= self.sendnth and self.datapos < len(self.data):
                    this_data = self.data[self.datapos]
                    self.in_data.next = this_data
                    self.in_nd.next = not self.in_nd.next
                    self.datapos += 1
                    self.count = 0
                else:
                    self.count += 1
        return run

class TestMessageStreamCombiner(unittest.TestCase):

    def setUp(self):
        rg = random.Random(0)
        self.myrand = rg.random
        self.myrandint = rg.randint

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
        data = [[self.myrandint(0, maxint)] for d in range(n_data)]
        # How many steps are required to simulate the data.
        steps_rqd = n_data * sendnth * 2 + 1000
        # Create, setup and simulate the test bench.
        tb = MessageStreamCombinerTestBench(
            width, input_buffer_length, max_packet_length,
            sendnth, data)
        tb.simulate(steps_rqd)
        # Confirm that our data is correct.
        self.assertEqual(len(tb.output), len(data))
        for r, el in zip(tb.output, data):
            e = el[0]
            self.assertEqual(e, r)

    def generate_random_packets(self, max_length, n_packets, bits_for_length, width, prob_start=1):
        """
        Generate a data stream containing a bunch of random packets.
        The lengths are distributed uniformly up to max_length-1.
        """
        data = []
        packets = []
        info_max = pow(2, width-1-bits_for_length)-1
        block_max = pow(2, width-1)-1
        assert(pow(2, bits_for_length) >= max_length)
        for i in range(n_packets):
            while (self.myrand() > prob_start):
                data.append(None)
            packet = []
            l = self.myrandint(0, max_length-1)
            info = self.myrandint(0, info_max)
            # Make header
            header = (1 << width-1) + (l << width-1-bits_for_length) + info
            data.append(header)
            packet.append(header)
            for j in range(l):
                d = self.myrandint(0, block_max)
                data.append(d)
                packet.append(d)
            packets.append(packet)
        return data, packets

    def test_streams(self):
        """
        Test the stream combiner a number of streams.
        """
        width = 32
        sendnth = 4
        input_buffer_length = 64
        max_packet_length = 1024
        log_max_packet_length = logceil(max_packet_length)
        n_packets = 10
        top_packet_length = 64
        data_streams = []
        packet_streams = []
        data_stream = []
        packet_stream = []
        max_stream_length = 0
        # Prob to start new packet.
        prob_start = 0.005
        n_streams = 8
        for i in range(n_streams):
            data, packets = self.generate_random_packets(top_packet_length, n_packets, log_max_packet_length, width, prob_start)
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
        steps_rqd = len(combined_data) * sendnth * 2 + 1000
        # Create, setup and simulate the test bench.
        tb = MessageStreamCombinerTestBench(
            width, input_buffer_length, max_packet_length,
            sendnth, combined_data)
        tb.simulate(steps_rqd)
        # Confirm that our method of converting a stream to packets is correct
        packets_again = stream_to_packets(data_stream, log_max_packet_length, width)
        packet_dict_again = make_packet_dict(packets_again)
        self.assertEqual(expected_packet_dict, packet_dict_again)
        # Now use it on the ouput rather than the input.
        received_packets = stream_to_packets(tb.output, log_max_packet_length, width)
        received_packet_dict = make_packet_dict(received_packets)
        self.assertEqual(expected_packet_dict, received_packet_dict)

    def test_slicer(self):
        """
        Test the stream slicer.
        """
        width = 32
        n_slices = 3
        sendnth = 4
        buffer_length = 64
        log_buffer_length = logceil(buffer_length)
        n_data = 20
        data = []
        expected_data = []
        mfactor = pow(2, width)
        for i in range(n_data):
            m = 1
            t = 0
            for s in range(n_slices):
                d = self.myrandint(0, mfactor-1)
                t += d * m
                m = m * mfactor
                expected_data.append(d)
            data.append(t)
        # How many steps are required to simulate the data.
        steps_rqd = len(data) * sendnth * 2 #+ 1000
        # Create, setup and simulate the test bench.
        tb = MessageSlicerTestBench(
            n_slices, width, buffer_length, sendnth, data)
        tb.simulate(steps_rqd)
        # Now check output
        self.assertEqual(len(expected_data), len(tb.output))
        for e,r in zip(expected_data, tb.output):
            self.assertAlmostEqual(e, r, 3)

if __name__ == '__main__':
    config.setup_logging(logging.DEBUG)
    unittest.main()

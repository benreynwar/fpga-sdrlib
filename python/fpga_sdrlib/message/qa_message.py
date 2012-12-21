# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import os
import random
import unittest
import logging
import shutil

from fpga_sdrlib.generate import logceil
from fpga_sdrlib import config, b100, buildutils
from fpga_sdrlib.message import msg_utils
from fpga_sdrlib.testbench import TestBenchB100, TestBenchIcarusOuter
from fpga_sdrlib.uhd.qa_uhd import bits_to_int

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
        tb = TestBenchIcarusOuter(executable, in_raw=data, width=width,
                                  output_msgs=False)
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
        top_packet_length = 16
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
            data, packets = msg_utils.generate_random_packets(
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
        expected_packet_dict = msg_utils.make_packet_dict(packet_stream)
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
        packets_again = msg_utils.stream_to_packets(
            data_stream, config.msg_length_width, width, allow_samples=False)
        packet_dict_again = msg_utils.make_packet_dict(packets_again)
        self.assertEqual(expected_packet_dict, packet_dict_again)
        # Now use it on the ouput rather than the input.
        received_packets = msg_utils.stream_to_packets(
            tb.out_raw, config.msg_length_width, width, allow_samples=False)
        received_packet_dict = msg_utils.make_packet_dict(received_packets)
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
        tb = TestBenchMessageSlicer(executable, in_raw=data, width=width,
                                    output_msgs=False)
        tb.run(steps_rqd)
        # Now check output
        self.assertEqual(len(expected_data), len(tb.out_raw))
        for e,r in zip(expected_data, tb.out_raw):
            self.assertAlmostEqual(e, r, 3)

class TestSampleMsgSplitter(unittest.TestCase):
    
    def setUp(self):
        self.rg = random.Random(0)
        top_packet_length = 64
        n_packets = 10
        self.width = 32
        prob_start = 0.1
        data, packets = msg_utils.generate_random_packets(
            top_packet_length, n_packets, config.msg_length_width,
            self.width, prob_start, self.rg, none_sample=False)
        self.dummypacket = msg_utils.generate_random_packet(0, config.msg_length_width, self.width)
        self.original_data = data
        self.data = data + self.dummypacket * 100000
        self.samples, self.packets = msg_utils.stream_to_samples_and_packets(
            data, config.msg_length_width, self.width)

    def test_sample_msg_splitter(self):
        """
        Tests the sample msg splitter.

        Just checks that the samples are correct.
        """
        # First test qa_wrapper modules that return the samples
        executable = buildutils.generate_icarus_executable(
            'message', 'sample_msg_splitter', '-test')
        fpgaimage = buildutils.generate_B100_image(
            'message', 'sample_msg_splitter', '-test')
        tb_icarus = TestBenchIcarusOuter(executable, in_raw=self.data)
        tb_b100 = TestBenchB100(fpgaimage, in_raw=self.data)
        for tb, steps in (
            (tb_icarus, 10000),
            (tb_b100, 10000),
            ):
            tb.run(steps)
            samples, packets = msg_utils.stream_to_samples_and_packets(
                self.original_data, config.msg_length_width, self.width)
            self.assertEqual(len(samples), len(tb.out_raw))
            for e, r in zip(samples, tb.out_raw):
                self.assertEqual(e, r)

    def test_sample_msg_splitter_returns_msgs(self):
        """
        Tests the sample msg splitter.

        Just checks that the messages are correct.
        """
        # Then test qa_wrapper modules returning the messages.
        executable = buildutils.generate_icarus_executable(
            'message', 'sample_msg_splitter_returns_msgs', '-test')
        fpgaimage = buildutils.generate_B100_image(
            'message', 'sample_msg_splitter_returns_msgs', '-test')
        tb_icarus = TestBenchIcarusOuter(executable, in_raw=self.data)
        tb_b100 = TestBenchB100(fpgaimage, in_raw=self.data)
        for tb, steps in (
            (tb_icarus, 10000),
            (tb_b100, 1000), 
            ):
            tb.run(steps)
            samples, packets = msg_utils.stream_to_samples_and_packets(
                tb.out_raw, config.msg_length_width, self.width)
            self.assertEqual(len(samples), 0)
            first_index = None
            for i, p in enumerate(packets):
                if p != self.dummypacket:
                    first_index = i
                    break
            last_index = None
            for i, p in reversed(list(enumerate(packets))):
                if p != self.dummypacket:
                    last_index = i+1
                    break
            if first_index is None:
                raise StandardError("No packets found")
            packets = packets[first_index: last_index]
            self.assertEqual(len(packets), len(self.packets))
            for e, r in zip(packets, self.packets):
                self.assertEqual(len(e), len(r))
                for ee, rr in zip(e, r):
                    self.assertEqual(ee, rr)
        

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
        data, packets = msg_utils.generate_random_packets(
            top_packet_length, n_packets, config.msg_length_width,
            width, prob_start, self.rg, none_sample=False)
        padded_data = data
        buffer_length = 128
        defines = config.updated_defines(
            {'COMBINER_BUFFER_LENGTH': buffer_length,
             'LOG_COMBINER_BUFFER_LENGTH': logceil(buffer_length),
             'MAX_PACKET_LENGTH': pow(2, config.msg_length_width),
             })
        executable = buildutils.generate_icarus_executable(
            'message', 'combo', '-test', defines=defines)
        fpgaimage = buildutils.generate_B100_image(
            'message', 'combo', '-test', defines=defines)
        tb_icarus = TestBenchIcarusOuter(executable, in_raw=data)
        tb_b100 = TestBenchB100(fpgaimage, in_raw=padded_data)
        for tb, steps in (
                (tb_icarus, 10000),
                (tb_b100, 100000), 
                ):
            tb.run(steps)
            e_samples, e_packets = msg_utils.stream_to_samples_and_packets(
                data, config.msg_length_width, width)
            r_samples, r_packets = msg_utils.stream_to_samples_and_packets(
                tb.out_raw, config.msg_length_width, width)
            # Confirm all the samples are equal.
            self.assertEqual(len(e_samples), len(r_samples))
            for e, r in zip(e_samples, r_samples):
                self.assertEqual(e, r)
            # Confirm all the packets are equal.
            self.assertEqual(len(e_packets), len(r_packets))
            for ep, rp in zip(e_packets, r_packets):
                self.assertEqual(len(ep), len(rp))
                for e, r in zip(ep, rp):
                    self.assertEqual(e, r)

class TestSplitCombiner(unittest.TestCase):
    
    def test_one(self):
        """
        Tests split module and message stream combiner together.
        """
        width = 32
        sendnth = 2
        max_packet_length = 10
        n_packets = 20
        data1 = []
        for i in range(n_packets):
            length = random.randint(0, max_packet_length)
            packet = msg_utils.generate_random_packet(length, config.msg_length_width,
                                            width)
            data1.extend(packet)
        max_val = pow(2, width-1)-1
        data2 = [random.randint(1, max_val) for i in range(len(data1))]
        i_data = []
        for d1, d2 in zip(data1, data2):
            i_data.append(d1)
            i_data.append(d2)
        a_data = data1 + data2
        padded_data = i_data + [0]*1000
        buffer_length = 128
        defines = config.updated_defines(
            {'COMBINER_BUFFER_LENGTH': buffer_length,
             'LOG_COMBINER_BUFFER_LENGTH': logceil(buffer_length),
             'MAX_PACKET_LENGTH': pow(2, config.msg_length_width),
             'ERRORCODE': 666,
             'WIDTH': width,
             })
        executable = buildutils.generate_icarus_executable(
            'message', 'splitcombiner', '-test', defines=defines)
        fpgaimage = buildutils.generate_B100_image(
            'message', 'splitcombiner', '-test', defines=defines)
        tb_icarus = TestBenchIcarusOuter(executable, in_raw=i_data,
                                         sendnth=sendnth)
        tb_b100 = TestBenchB100(fpgaimage, in_raw=padded_data)
        for tb, steps in (
                (tb_icarus, len(i_data)*sendnth*2+1000),
                (tb_b100, 100000), 
                ):
            tb.run(steps)
            e_samples, e_packets = msg_utils.stream_to_samples_and_packets(
                a_data, config.msg_length_width, width)
            r_samples, r_packets = msg_utils.stream_to_samples_and_packets(
                tb.out_raw, config.msg_length_width, width)
            # Remove 0's from samples.
            # The splitter can introduce 0's at beginning and end.
            r_samples = [r for r in r_samples if r != 0]
            self.assertEqual(len(e_samples), len(r_samples))
            for e, r in zip(e_samples, r_samples):
                self.assertEqual(e, r)
            # Confirm all the packets are equal.
            self.assertEqual(len(e_packets), len(r_packets))
            for ep, rp in zip(e_packets, r_packets):
                self.assertEqual(len(ep), len(rp))
                for e, r in zip(ep, rp):
                    self.assertEqual(e, r)

class TestMessageStreamCombinerOne(unittest.TestCase):
    """
    Tests a message_stream_combiner block.
    It is combining two streams.
    One we are sending and the other is always empty.
    """

    def setUp(self):
        self.rg = random.Random(0)

    def test_one(self):
        packet = [2159820100L,  878477756, pow(2, 23)+1, 2, 3, 4]
        packets = [packet]*10
        data = range(1, 100)
        for packet in packets:
            data.extend(packet)
            data.extend(range(100, 110))

        buffer_length = 128
        defines = config.updated_defines(
            {'COMBINER_BUFFER_LENGTH': buffer_length,
             'LOG_COMBINER_BUFFER_LENGTH': logceil(buffer_length),
             'MAX_PACKET_LENGTH': pow(2, config.msg_length_width),
             })
        executable = buildutils.generate_icarus_executable(
            'message', 'message_stream_combiner_one', '-72', defines=defines)
        fpgaimage = buildutils.generate_B100_image(
            'message', 'message_stream_combiner_one', '-72', defines=defines)
        tb_icarus = TestBenchIcarusOuter(executable, in_raw=data)
        tb_b100 = TestBenchB100(fpgaimage, in_raw=data)

        for tb, steps in (
                (tb_icarus, 10000),
                (tb_b100, 100000), 
                ):
            tb.run(steps)
            self.assertEqual(len(data), len(tb.out_raw))
            for e, r in zip(data, tb.out_raw):
                self.assertEqual(e, r)

    def test_bits(self):
        width = 32
        maxint = pow(2, width)-1
        n_data = 10
        data = [random.randint(1, maxint) for d in range(n_data)]
        buffer_length = 128
        defines = config.updated_defines(
            {'COMBINER_BUFFER_LENGTH': buffer_length,
             'LOG_COMBINER_BUFFER_LENGTH': logceil(buffer_length),
             'MAX_PACKET_LENGTH': pow(2, config.msg_length_width),
             'WIDTH': width,
             'LOG_SENDNTH': 14,
             'LOG_WIDTH': logceil(width),
             'ERRORCODE': 666,
             })
        executable = buildutils.generate_icarus_executable(
            'message', 'message_stream_combiner_bits', '-test', defines=defines)
        fpgaimage = buildutils.generate_B100_image(
            'message', 'message_stream_combiner_bits', '-test', defines=defines)
        tb_icarus = TestBenchIcarusOuter(executable, in_raw=data, sendnth=70)
        tb_b100 = TestBenchB100(fpgaimage, in_raw=data)

        for tb, steps in (
                (tb_icarus, 10000),
                (tb_b100, 100000), 
                ):
            tb.run(steps)
            start_pos = None
            for i, x in enumerate(tb.out_raw):
                if (x==width-1):
                    start_pos = i
                    break
            for i, x in reversed(zip(range(0, len(tb.out_raw)), tb.out_raw)):
                if (x==width-1):
                    stop_pos = i
                    break
            if start_pos is None:
                raise ValueError("{0} not found in output".format(width-1))
            out = tb.out_raw[start_pos: stop_pos + 2*width]
            bitted = [out[i*2*width+1:(i+1)*2*width+1:2] for i in range(len(out)/width/2)]
            poses = [out[i*2*width:(i+1)*2*width:2] for i in range(len(out)/width/2)]
            expected = [31-x for x in range(32)]
            for i, p in enumerate(poses):
                self.assertEqual(p, expected)
            r_ints = [bits_to_int(bits) for bits in bitted]
            r_ints = [x for x in r_ints if x != 0]
            self.assertEqual(len(data), len(r_ints))
            for e, r in zip(data, r_ints):
                self.assertEqual(e, r)



if __name__ == '__main__':
    config.setup_logging(logging.DEBUG)

    #suite = unittest.TestLoader().loadTestsFromTestCase(TestSampleMsgSplitter)
    #suite = unittest.TestLoader().loadTestsFromTestCase(TestCombo)
    #suite = unittest.TestLoader().loadTestsFromTestCase(TestSplitCombiner)
    #suite = unittest.TestLoader().loadTestsFromTestCase(TestMessageSlicer)
    #suite = unittest.TestLoader().loadTestsFromTestCase(TestMessageStreamCombiner)
    #suite = unittest.TestLoader().loadTestsFromTestCase(TestMessageStreamCombinerOne)
    #unittest.TextTestRunner(verbosity=2).run(suite)

    unittest.main()

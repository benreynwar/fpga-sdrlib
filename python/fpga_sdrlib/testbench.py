# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import os

from myhdl import Cosimulation, Signal, delay, always, Simulation, _simulator

from gnuradio import uhd, gr

from fpga_sdrlib import config
from fpga_sdrlib import b100
from fpga_sdrlib.conversions import c_to_int, int_to_c
from fpga_sdrlib.message.msg_utils import stream_to_packets

def flip_bits(seq, width):
    """
    Takes a sequence of integers.  For each integer the higher and lower
    bits are swapped round.  Necessary to work around a bug in
    gr-uhd.
    """
    out = []
    h = pow(2, width//2)
    for x in seq:
        high_bits = x//h
        low_bits = x % h
        out.append(high_bits + low_bits * h)
    return out

def unsigned_to_signed(seq, width):
    """
    Convert unsigned integer to signed.
    """
    out = []
    k = pow(2, width)
    for x in seq:
        if x >= k/2:
            x -= k
        out.append(x)
    return out
        
def compare_unaligned(xs, ys, tol):
    """
    Compare two unaligned sequences.
    
    Args:
       xs: the shorter sequence
       ys: the longer sequence (should contain xs somewhere within)
       tol: how close individual elements must be

    Returns:
       The maximum number of continuous matching elements starting from the
       beginning.
    """
    matched = False
    max_streak = 0
    N = len(xs)
    for offset in range(len(ys)-len(xs)):
        worked = True
        streak = N
        for i in range(N):
            if abs(xs[i] - ys[offset+i]) > tol:
                worked = False
                streak = i
                break
        max_streak = max(streak, max_streak)
        if worked:
            matched = True
            break
    return max_streak

"""
What testbenchs do I need:
  samples, msgs, ms (raw module)

  samples, msgs in -> into merged stream ->samples, msgs out
  raw 32 bit in and out
  
"""

class TestBenchIcarusBase(object):
    """
    A base class for TestBenchIcarusInner and TestBenchIcarusOuter.
    Holds common code.
    """

    def __init__(self):
        # The MyHDL Signals
        for sn in self.signal_names:
            if sn.endswith('_n'):
                setattr(self, sn, Signal(1))
            else:
                setattr(self, sn, Signal(0))

    def clk_driver(self):
        @always(delay(1))
        def run():
            """ Drives the clock."""
            self.clk.next = not self.clk
        return run

    def run(self, clks):
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

    def get_output(self):
        self.out_raw = []
        @always(self.clk.posedge)
        def run():
            """
            Receive output.
            """
            if self.out_nd:
                self.out_raw.append(int(self.out_data))
                if 'out_m' in self.signal_names:
                    self.out_ms.append(int(self.out_m))
        return run

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
                    self.in_nd.next = 1
                    self.datapos += 1
                    self.count = 0
                else:
                    self.in_nd.next = 0
                    self.count += 1
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
        

class TestBenchIcarusInner(TestBenchIcarusBase):
    """
    A testbench to test a module using Icarus verilog.
    Separate sample, message and meta data connections.
    Message can only be sent before sending samples.

    Args:
        executable: The Icarus executable
        in_samples: The input samples.
        in_ms: The input meta data (same length as in_samples).
        start_msgs: Messages to send before sending samples.
        sendnth: How often to send a new sample.
        width: The width in bits of input data
        mwidth: The width of meta data
    """

    signal_names = ['clk', 'rst_n',
                    'in_data', 'in_nd', 'in_m', 'in_msg', 'in_msg_nd',
                    'out_data', 'out_nd', 'out_m', 'out_msg', 'out_msg_nd',
                    'error']

    def __init__(self, executable, in_samples, in_ms=None, start_msgs=None,
                 sendnth=config.default_sendnth, width=config.default_width,
                 mwidth=config.default_mwidth):
        TestBenchIcarusBase.__init__(self)
        self.executable = executable
        self.in_samples = in_samples
        if in_ms is not None:
            assert(len(in_samples) == len(in_ms))
        else:
            in_ms = [0] * len(in_samples)
        self.start_msgs = start_msgs
        self.sendnth = sendnth
        self.width = width
        self.mwidth = mwidth
        # Output arrays
        self.out_samples = []
        self.out_ms = []
        self.out_msgs = []
        # Set the MyHDL drivers
        self.drivers = [self.clk_driver, self.get_output, self.check_error,
                        self.send_input, self.prerun, self.get_message_stream]
        # ???
        self.in_raw = [c_to_int(d, self.width/2) for d in self.in_samples]

    def get_message_stream(self):
        @always(self.clk.posedge)
        def run():
            """
            Receive messages.
            """
            if self.out_msg_nd:
                self.out_msgs.append(int(self.out_msg))
        return run

    def prerun(self):
        self.first = True
        self.done_header = False
        self.doing_prerun = True
        self.msg_pos = 0
        @always(self.clk.posedge)
        def run():
            """
            Sends a reset signal at start.
            The loads taps in.
            """
            if self.first:
                self.first = False
                self.rst_n.next = 0
            else:
                self.rst_n.next = 1
                if self.start_msgs and (self.msg_pos < len(self.start_msgs)):
                    self.in_msg.next = self.start_msgs[self.msg_pos]
                    self.in_msg_nd.next = 1
                    self.msg_pos += 1
                else:
                    self.doing_prerun = False
                    self.in_msg_nd.next = 0
        return run

class TestBenchIcarusOuter(TestBenchIcarusBase):
    """
    A testbench to test a module using Icarus verilog.
    Only a single data connection in and out.
    Shared by data and messages.
    No possibility to pass meta data currently.
    Message can only be sent before sending samples.

    Args:
        executable: The Icarus executable
        in_samples: The input samples.
        start_msgs: Messages to send before sending samples.
        in_raw: The raw input integers can be specified, instead of
                in_samples and start_msgs.
        sendnth: How often to send a new sample.
        width: The bit width of the input data
    """

    signal_names = ['clk', 'reset',
                    'in_data', 'in_nd',
                    'out_data', 'out_nd',
                    'error']

    def __init__(self, executable, in_samples=None, start_msgs=None, in_raw=None,
                 sendnth=config.default_sendnth, width=config.default_width):
        super(TestBenchIcarusOuter, self).__init__()
        self.executable = executable
        self.in_samples = in_samples
        self.start_msgs = start_msgs
        self.in_raw = in_raw
        if (in_raw is not None) and (in_samples is not None or start_msgs is not None):
            raise ValueError("Cannot specify both (in_samples and/or start_msgs) and in_raw")
        self.sendnth = sendnth
        self.width = width
        # Set the MyHDL drivers
        self.drivers = [self.clk_driver, self.get_output,
                        self.send_input, self.prerun, self.check_error]
        # Generate the raw data to send in.
        if self.in_raw is None:
            self.in_raw = []
            if self.start_msgs is not None:
                self.in_raw += self.start_msgs
            # Subtracting 1 from width since we use 1st bit as a header.
            self.in_raw += [c_to_int(d, self.width/2-1) for d in self.in_samples]

    def run(self, steps_rqd):
        super(TestBenchIcarusOuter, self).run(steps_rqd)
        header_shift = pow(2, self.width-1)
        #packets = stream_to_packets(self.out_raw)
        #self.out_samples = []
        #self.out_messages = []
        #for p in packets:
        #    if p[0] // header_shift:
        #        self.out_messages.append(p)
        #    else:
        #        # It is a sample
        #        assert(len(p) == 1)
        #        self.out_samples.append(int_to_c(p[0], self.width/2-1))
    
    def prerun(self):
        self.first = True
        self.done_header = False
        self.doing_prerun = True
        self.msg_pos = 0
        @always(self.clk.posedge)
        def run():
            """
            Sends a reset signal at start.
            """
            if self.first:
                self.first = False
                self.reset.next = 1
            else:
                self.reset.next = 0
                self.doing_prerun = False
        return run


class TestBenchB100(object):
    """
    A minimal TestBench to run the module on the B100 FPGA.

    Args:
        fpga_image: The filename of the fpga_image.
        in_samples: A list of complex points to send.
        start_msgs: A list of messages to send before sending samples.
        defines: Macro definitions (constants) used in verilog code
                 (just used for extracting width here).
        width: Width of input data.
        in_raw: Raw integers to send instead of in_samples and start_msgs.
    """
    
    def __init__(self, fpgaimage, in_samples=None, start_msgs=None, 
                 width=config.default_width, in_raw=None):
        self.fpgaimage = fpgaimage
        self.in_samples = in_samples
        self.start_msgs = start_msgs
        self.width = width
        self.in_raw = in_raw
        # Generate the raw data to send in.
        if in_raw is None:
            if self.start_msgs is not None:
                self.in_raw += self.start_msgs
            # Subtracting 1 from width since we use 1st bit as a header.
            self.in_raw += [c_to_int(d, self.width/2-1) for d in self.in_samples]
        self.out_samples = []
        self.out_ms = []
        self.out_msgs = []

    def run(self, n_receive=None):
        """
        Run the simulation.
        
        Args:
            n_receive: Stop after receiving this many samples.
        """
        b100.set_image(self.fpgaimage)
        # steps_rqd only in for compatibility
        from gnuradio import gr, uhd
        if n_receive is None:
            n_receive = 10000
        # Flip high and low bits of in_raw
        flipped_raw = flip_bits(self.in_raw, self.width)
        flipped_raw = unsigned_to_signed(flipped_raw, self.width)
        stream_args = uhd.stream_args(cpu_format='sc16', channels=range(1))
        from_usrp = uhd.usrp_source(device_addr='', stream_args=stream_args)
        head = gr.head(4, n_receive)
        snk = gr.vector_sink_i()
        to_usrp = uhd.usrp_sink(device_addr='', stream_args=stream_args)
        src = gr.vector_source_i(flipped_raw)
        tb = gr.top_block()
        tb.connect(from_usrp, head, snk)
        tb.connect(src, to_usrp)
        tb.run()
        self.out_raw = snk.data()
        # Remove 0's
        start_offset = None
        stop_offset = None
        enumerated_raw = list(enumerate(self.out_raw))
        for i, r in enumerated_raw:
            if r != 0:
                start_offset = i
                break
        for i, r in reversed(enumerated_raw):
            if r != 0:
                stop_offset = i
                break
        if start_offset is None or stop_offset is None:
            raise StandardError("Could not find any non-zero returned data.")
        self.out_raw = self.out_raw[start_offset: stop_offset+1]
        # Shift to positive integers
        positive = []
        for r in self.out_raw:
            if r < 0:
                r += pow(2, self.width)
            positive.append(r)
        self.out_raw = positive
        # Flip bits in out_raw
        self.out_raw = flip_bits(self.out_raw, self.width)
        header_shift = pow(2, self.width-1)
        packets = stream_to_packets(self.out_raw)
        self.out_samples = []
        self.out_messages = []
        for p in packets:
            if p[0] // header_shift:
                self.out_messages.append(p)
            else:
                # It is a sample
                assert(len(p) == 1)
                self.out_samples.append(int_to_c(p[0], self.width/2-1))
    

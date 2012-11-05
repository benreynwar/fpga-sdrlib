# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import os

from myhdl import Cosimulation, Signal, delay, always, Simulation, _simulator

from gnuradio import uhd, gr

from fpga_sdrlib import config
from fpga_sdrlib.conversions import c_to_int, int_to_c
from fpga_sdrlib.message.msg_utils import stream_to_packets
        
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

def get_usrp_output(n):
    """
    Grabs data from USRP

    Args:
        n: Number of datapoint to get
    """
    stream_args = uhd.stream_args(cpu_format='fc32', channels=range(1))
    from_usrp = uhd.usrp_source(device_addr='', stream_args=stream_args)
    head = gr.head(gr.sizeof_gr_complex, n)
    snk = gr.vector_sink_c()
    tb = gr.top_block()
    tb.connect(from_usrp, head, snk)
    tb.run()
    return snk.data()

class TestBenchBase(object):
    """
    Defines the interface for a test bench to test a module.

    Args:
        in_samples: The complex numbers to send.
        in_ms: Meta data to send.
        start_msgs: Messages to send before sending the samples.
        defines: Preprocessor macro definitions.
    """

    def __init__(self, in_samples, in_ms=None, start_msgs=None, defines=config.default_defines):
        self.in_samples = in_samples
        self.start_msgs = start_msgs
        if in_ms is not None:
            assert(len(in_samples) == len(in_ms))
        else:
            in_ms = [0] * len(in_samples)
        self.in_ms = in_ms
        self.defines = defines
        self.out_samples = []
        self.out_ms = []
        self.out_msgs = []

    def prepare(self):
        raise StandardError("Not implemented")

    def run(self):
        raise StandardError("Not implemented.")

class TestBenchIcarusBase(TestBenchBase):
    """
    A minimal TestBench to run the module using icarus verilog.

    Args:
        name: A name to use with for generated files.
        in_samples: A list of complex points to send.
        sendnth: Send an input on every `sendnth` clock cycle.
        in_ms: A list of the meta data to send.
        start_msgs: A list of messages to send before sending samples.
        defines: Macro definitions (constants) to use in verilog code.
    """

    extra_signal_names = []
    base_signal_names = ['clk', 'rst_n',
                         'in_data', 'in_nd', 'in_m', 'in_msg', 'in_msg_nd',
                         'out_data', 'out_nd', 'out_m', 'out_msg', 'out_msg_nd',
                         'error']

    def __init__(self, name, in_samples, sendnth=config.default_sendnth,
                 in_ms=None, start_msgs=None, defines=config.default_defines):
        TestBenchBase.__init__(self, in_samples, in_ms, defines)
        debug = ("DEBUG" in defines) and defines["DEBUG"]
        self.in_width = defines["WIDTH"]
        self.out_width = defines["WIDTH"]
        self.sendnth = sendnth
        self.name = name
        self.defines = defines
        self.start_msgs = start_msgs
        # The MyHDL Signals
        self.signal_names = self.extra_signal_names + self.base_signal_names
        for sn in self.signal_names:
            if sn.endswith('_n'):
                setattr(self, sn, Signal(1))
            else:
                setattr(self, sn, Signal(0))
        # Set the MyHDL drivers
        self.drivers = [self.clk_driver, self.get_output, self.check_error,
                        self.send_input, self.prerun]

    def clk_driver(self):
        @always(delay(1))
        def run():
            """ Drives the clock."""
            self.clk.next = not self.clk
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
                if 'out_m' in self.base_signal_names:
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
                if self.count >= self.sendnth and self.datapos < len(self.in_samples):
                    self.in_data.next = self.in_raw[self.datapos]
                    if 'in_m' in self.base_signal_names:
                        self.in_m.next = self.in_ms[self.datapos]
                    self.in_nd.next = 1
                    self.datapos += 1
                    self.count = 0
                else:
                    self.in_nd.next = 0
                    self.count += 1
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
            """
            if self.first:
                self.first = False
                self.rst_n.next = 0
            else:
                self.rst_n.next = 1
                self.doing_prerun = False
        return run

class TestBenchIcarus(TestBenchIcarusBase):
    """
    A minimal TestBench to run the module using icarus verilog.

    Args:
        name: A name to use with for generated files.
        in_samples: A list of complex points to send.
        sendnth: Send an input on every `sendnth` clock cycle.
        in_ms: A list of the meta data to send.
        start_msgs: A list of messages to send before sending samples.
        defines: Macro definitions (constants) to use in verilog code.
    """

    extra_signal_names = []
    base_signal_names = ['clk', 'rst_n',
                         'in_data', 'in_nd', 'in_m', 'in_msg', 'in_msg_nd',
                         'out_data', 'out_nd', 'out_m', 'out_msg', 'out_msg_nd',
                         'error']

    def __init__(self, *args, **kwargs):
        TestBenchIcarusBase.__init__(self, *args, **kwargs)
        self.drivers.append(self.get_message_stream)
        self.in_raw = [c_to_int(d, self.in_width/2) for d in self.in_samples]
                    
    def run(self, steps_rqd):
        TestBenchIcarusBase.run(self, steps_rqd)
        self.out_samples = [(int_to_c(d, self.out_width/2)) for d in self.out_raw]
        self.out_messages = stream_to_packets(self.out_msgs)

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
        
class TestBenchIcarusCombined(TestBenchIcarusBase):
    """
    A minimal TestBench to run the module using icarus verilog.

    Args:
        name: A name to use with for generated files.
        in_samples: A list of complex points to send.
        sendnth: Send an input on every `sendnth` clock cycle.
        in_ms: A list of the meta data to send.
        start_msgs: A list of messages to send before sending samples.
        defines: Macro definitions (constants) to use in verilog code.
    """

    extra_signal_names = []
    base_signal_names = ['clk', 'rst_n',
                         'in_data', 'in_nd',
                         'out_data', 'out_nd',
                         'error']

    def __init__(self, *args, **kwargs):
        TestBenchIcarusBase.__init__(self, *args, **kwargs)
        # Generate the raw data to send in.
        self.in_raw = []
        if self.start_msgs is not None:
            self.in_raw += self.start_msgs
        # Subtracting 1 from width since we use 1st bit as a header.
        self.in_raw += [c_to_int(d, self.in_width/2-1) for d in self.in_samples]

    def run(self, steps_rqd):
        TestBenchIcarusBase.run(self, steps_rqd)
        header_shift = pow(2, self.out_width-1)
        packets = stream_to_packets(self.out_raw)
        self.out_samples = []
        self.out_messages = []
        for p in packets:
            if p[0] // header_shift:
                self.out_messages.append(p)
            else:
                # It is a sample
                assert(len(p) == 1)
                self.out_samples.append(int_to_c(p[0], self.out_width/2-1))
    

class TestBenchB100(TestBenchBase):
    """
    A minimal TestBench to run the module on the B100 FPGA.

    Args:
        name: A name to use with for generate files.
        in_samples: A list of complex points to send.
        start_msgs: A list of messages to send before sending samples.
        defines: Macro definitions (constants) to use in verilog code.
    """
    
    def __init__(self, name, in_samples, start_msgs=None, defines=config.default_defines):
        in_ms = None
        TestBenchBase.__init__(self, in_samples, in_ms, start_msgs, defines)
        # Generate the raw data to send in.
        self.name = name
        self.in_raw = []
        self.in_width = defines['WIDTH']
        self.out_width = self.in_width
        if self.start_msgs is not None:
            self.in_raw += self.start_msgs
        # Subtracting 1 from width since we use 1st bit as a header.
        self.in_raw += [c_to_int(d, self.in_width/2-1) for d in self.in_samples]

    def run(self, steps_rqd=None):
        # steps_rqd only in for compatibility
        from gnuradio import gr, uhd
        n_receive = 10000

        stream_args = uhd.stream_args(cpu_format='sc16', channels=range(1))
        from_usrp = uhd.usrp_source(device_addr='', stream_args=stream_args)
        head = gr.head(4, n_receive)
        snk = gr.vector_sink_i()
        to_usrp = uhd.usrp_sink(device_addr='', stream_args=stream_args)
        src = gr.vector_source_i(self.in_raw)
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
                r += pow(2, self.out_width)
            positive.append(r)
        self.out_raw = positive
        header_shift = pow(2, self.out_width-1)
        packets = stream_to_packets(self.out_raw)
        self.out_samples = []
        self.out_messages = []
        for p in packets:
            if p[0] // header_shift:
                self.out_messages.append(p)
            else:
                # It is a sample
                assert(len(p) == 1)
                self.out_samples.append(int_to_c(p[0], self.out_width/2-1))
    

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
    """

    def __init__(self, in_samples, in_ms=None, defines=config.default_defines):
        self.in_samples = in_samples
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


class TestBenchIcarus(TestBenchBase):
    """
    A minimal TestBench to run the module using icarus verilog.

    Args:
        name: A name to use with for generated files.
        in_samples: A list of complex points to send.
        sendnth: Send an input on every `sendnth` clock cycle.
        in_ms: A list of the meta data to send.
        defines: Macro definitions (constants) to use in verilog code.
    """

    extra_signal_names = []
    debug_signal_names = ['msg', 'msg_nd']
    base_signal_names = ['clk', 'rst_n',
                         'in_data', 'in_nd', 'in_m',
                         'out_data', 'out_nd', 'out_m',
                         'error']

    def __init__(self, name, in_samples, sendnth=config.default_sendnth,
                 in_ms=None, defines=config.default_defines):
        super(TestBenchIcarus, self).__init__(in_samples, in_ms, defines)
        debug = ("DEBUG" in defines) and defines["DEBUG"]
        self.in_width = defines["WIDTH"]
        self.out_width = defines["WIDTH"]
        self.sendnth = sendnth
        self.name = name
        # The MyHDL Signals
        self.signal_names = self.extra_signal_names + self.base_signal_names
        if debug:
            self.signal_names += self.debug_signal_names
        for sn in self.signal_names:
            if sn.endswith('_n'):
                setattr(self, sn, Signal(1))
            else:
                setattr(self, sn, Signal(0))
        # Set the MyHDL drivers
        self.drivers = [self.clk_driver, self.get_output, self.check_error, self.send_input]
        if debug:
            self.drivers.append(self.get_message_stream)

    def clk_driver(self):
        @always(delay(1))
        def run():
            """ Drives the clock. """
            self.clk.next = not self.clk
        return run

    def get_message_stream(self):
        @always(self.clk.posedge)
        def run():
            """
            Receive messages.
            """
            if self.msg_nd:
                self.out_msgs.append(int(self.msg))
        return run

    def get_output(self):
        @always(self.clk.posedge)
        def run():
            """
            Receive output.
            """
            if self.out_nd:
                self.out_samples.append(int_to_c(self.out_data, self.out_width/2))
                self.out_ms.append(int(self.out_m))
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
        self.out_messages = stream_to_packets(self.out_msgs)
    

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
                if self.count >= self.sendnth and self.datapos < len(self.in_samples):
                    self.in_data.next = c_to_int(self.in_samples[self.datapos], self.in_width/2)
                    self.in_m.next = self.in_ms[self.datapos]
                    self.in_nd.next = 1
                    self.datapos += 1
                    self.count = 0
                else:
                    self.in_nd.next = 0
                    self.count += 1
        return run

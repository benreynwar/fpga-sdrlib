# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import os

from myhdl import Cosimulation, Signal, delay, always, Simulation, _simulator

from fpga_sdrlib import config
from fpga_sdrlib.conversions import c_to_int, int_to_c

class TestBenchBase(object):
    """
    A minimal TestBench.
    Inherit from here directly if no input data is used.
    """

    extra_signal_names = []
    base_signal_names = ['clk', 'rst_n',
                         'out_data', 'out_nd', 'out_m', 'error']
    driver_factories = []

    def __init__(self, out_width):
        self.out_width = out_width
        # The MyHDL Signals
        self.signal_names = self.extra_signal_names + self.base_signal_names
        for sn in self.signal_names:
            if sn.endswith('_n'):
                setattr(self, sn, Signal(1))
            else:
                setattr(self, sn, Signal(0))
        self.drivers = [self.clk_driver, self.get_output, self.check_error]

    def clk_driver(self):
        @always(delay(1))
        def run():
            """ Drives the clock. """
            self.clk.next = not self.clk
        return run


    def get_output(self):
        self.output = []
        self.out_ms = []
        @always(self.clk.posedge)
        def run():
            """
            Receive output.
            """
            if self.out_nd:
                self.output.append(int_to_c(self.out_data, self.out_width/2))
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

        
class TestBench(TestBenchBase):
    """
    Base Class to create testing helper classes.
    """

    extra_signal_names = []
    base_signal_names = ['clk', 'rst_n', 'in_data', 'in_nd', 'in_m', 
                         'out_data', 'out_nd', 'out_m', 'error']

    def __init__(self, sendnth, data, ms, in_width, out_width):
        TestBenchBase.__init__(self, out_width)
        self.sendnth = sendnth
        self.data = data
        self.ms = ms
        assert(len(data) == len(ms))
        self.in_width = in_width
        self.drivers += [self.send_input]

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
                    self.in_data.next = c_to_int(self.data[self.datapos], self.in_width/2)
                    self.in_m.next = self.ms[self.datapos]
                    self.in_nd.next = 1
                    self.datapos += 1
                    self.count = 0
                else:
                    self.in_nd.next = 0
                    self.count += 1
        return run

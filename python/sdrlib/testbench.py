import os

from myhdl import Cosimulation, Signal, delay, always, Simulation

from sdrlib import config
from sdrlib.conversions import c_to_int, int_to_c

class TestBench(object):
    """
    Base Class to create testing helper classes.
    """

    extra_signal_names = []
    base_signal_names = ['clk', 'rst_n', 'in_data', 'in_nd', 'out_data',
                         'out_nd', 'error']

    def __init__(self, sendnth, data, in_width, out_width):
        self.sendnth = sendnth
        self.data = data
        self.in_width = in_width
        self.out_width = out_width
        # The MyHDL Signals
        self.signal_names = self.extra_signal_names + self.base_signal_names
        for sn in self.signal_names:
            if sn.endswith('_n'):
                setattr(self, sn, Signal(1))
            else:
                setattr(self, sn, Signal(0))

    def simulate(self, clks):
        """
        Run a test bench simulation.
        """
        myhdlvpi = os.path.join(config.verilogdir, 'myhdl.vpi')
        command = "vvp -m {myhdlvpi} {executable}".format(myhdlvpi=myhdlvpi, executable=self.executable)
        cosimdict = dict([(sn, getattr(self, sn)) for sn in self.signal_names])
        self.dut = Cosimulation(command, **cosimdict)
        sim = Simulation(self.dut, self.clk_driver(), self.control())
        sim.run(2*clks)

    def clk_driver(self):
        @always(delay(1))
        def run():
            """ Drives the clock. """
            self.clk.next = not self.clk
        return run

    def control(self):
        """
        
        """
        self.count = 0
        self.first = True
        self.datapos = 0
        self.output = []
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
                    self.in_data.next = c_to_int(self.data[self.datapos], self.in_width)
                    self.in_nd.next = 1
                    self.datapos += 1
                    self.count = 0
                else:
                    self.in_nd.next = 0
                    self.count += 1
                if self.error:
                    raise StandardError("The error wire is high.")
            # Receive output.
            if self.out_nd:
                self.output.append(int_to_c(self.out_data, self.out_width))
        return run

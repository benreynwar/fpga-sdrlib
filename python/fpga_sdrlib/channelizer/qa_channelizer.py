# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

"""
MyHDL Test Bench to check the vericode channelizer.
"""

import random
import unittest
import math

from myhdl import always
from numpy import fft
from scipy import signal
from fpga_sdrlib.conversions import c_to_int, cs_to_int, int_to_c, int_to_cs
from fpga_sdrlib.channelizer.build import generate
from fpga_sdrlib.testbench import TestBench

def convolve(X, Y):
    """
    Convolves two series.
    """
    N = len(X)
    ss = []
    for n in range(0, len(Y)):
        s = 0
        for l in range(0, len(X)):
            s += X[l].conjugate()*Y[(n+l)%len(Y)]
        ss.append(s)
    return ss

def pychannelizer(flt, data, M):
    """
    Implements a pfb channelizer in python.
    """
    flt = list(flt)
    if len(data)%M != 0:
        data = data[:int(len(data)/M)*M]
    if len(flt)%M != 0:
        flt = flt + [0] * (M - len(flt)%M)
    flts = [flt[i::M] for i in range(M)]
    css = [data[i::M] for i in range(M)]
    convolved = [convolve(flts[i], css[i]) for i in range(M)]
    channels = []
    for k in range(M):
        filtered = [fft.fft(c)[k] for c in zip(*convolved)]
        channels.append([x for x in filtered])
    return convolved, channels

class ChannelizerTestBench(TestBench):
    """
    Helper class for doing testing.
    
    Args:
        name: A name to use with for generated files.
        width: Bit width of a complex number.
        mwidth: The bit width of sent meta data.
        sendnth: Send an input on every `sendnth` clock cycle.
        n_chans: The number of channels to split into.
        data: A list of complex points to send.
        ms: A list of the meta data to send.
        taps: The taps to use for channelizing.
    """

    extra_signal_names = ['first_channel']

    def __init__(self, name, width, mwidth, sendnth, n_chans, data, ms, taps):
        self.logn = math.log(n_chans)/math.log(2)
        if int(self.logn) != self.logn:
            raise ValueError("The number of channels must be a power of two.")
        self.n_chans = n_chans
        self.width = width
        self.mwidth = mwidth
        self.name = name
        self.ms = ms
        self.taps = taps
        TestBench.__init__(self, sendnth, data, ms, self.width, self.width)
        self.executable, inputfiles = generate(self.name, self.n_chans, self.taps, self.width, self.mwidth)
        self.drivers.append(self.get_first_channel)

    def get_first_channel(self):
        self.out_fc = []
        @always(self.clk.posedge)
        def run():
            if self.out_nd:
                self.out_fc.append(int(self.first_channel))
        return run
        
class TestChannelizer(unittest.TestCase):
    """
    Test the verilog channelizer.
    """

    def setUp(self):
        # Number of channels
        self.M = 4
        self.logM = int(math.log(self.M)/math.log(2))
        # The amount of data to send
        self.n_data = self.M * 200
        # Baseband sampling rate
        self.fs = 1000        
        # Input samp rate to channelizer
        self.ifs = self.M*self.fs       
        # Each channel contains a pure frequency with an offset and
        # amplitude.
        self.freqs = [0, 100, 200, -300]
        self.amplitudes = [1, 1, -0.2, 0.5]
        # Random number generator
        rg = random.Random(0)
        self.myrand = rg.random
        self.myrandint = rg.randint
        # Width of a complex number
        self.width = 32
        # Generate some taps
        self.taps, self.tapscale = self.get_taps(self.M)
        # How often to send input.
        # For large FFTs this must be larger since the speed scales as MlogM.
        # Otherwise we get an overflow error.
        self.sendnth = 2
        # Get the input data (uses self.freqs and self.amplitudes)
        self.data = self.get_input_data()
        # Scale the input data to remain in (-1 to 1)
        datamax = 0
        for d in self.data:
            datamax = max(datamax, abs(d.real), abs(d.imag))
        self.inputscale = datamax
        self.data = [d/datamax for d in self.data]
        # Send in some meta data
        self.mwidth = 3
        self.ms = [self.myrandint(0, 7) for d in self.data]
        # Create the test bench
        name = 'complex'
        self.tb = ChannelizerTestBench(name, self.width, self.mwidth, self.sendnth, self.M, self.data, self.ms, self.taps)

    def tearDown(self):
        pass

    def get_taps(self, M):
        taps = signal.firwin2(100, [0, 1.0/M, 1.0/M+0.05, 1], [1, 1, 0, 0])
        # Divide by integral of absolute values to prevent the possibility
        # of overflow.
        chantaps = [taps[i::M] for i in range(M)]
        maxsum = 0
        for ts in chantaps:
            summed = sum([abs(t) for t in ts])
            if summed > maxsum:
                maxsum = summed
        taps = [float(x)/maxsum for x in taps]
        return taps, maxsum
        

    def get_expected_data(self, L):
        """
        Get the expected data in each channel.
        """
        def make_data(f, a):
            t = [float(x)/self.fs for x in  xrange(L)]
            return [a*math.cos(2*math.pi*f*x) + a*1j*math.sin(2*math.pi*f*x)
                    for x in t]
        expected_data = [make_data(f, a) for f, a in zip(self.freqs, self.amplitudes)]
        return expected_data

    def get_input_data(self):
        """
        Get the input data containing the combined sinusoids from each
        channel.
        """
        data = []
        ts = [float(x)/self.ifs for x in range(self.n_data)]
        for t in ts:
            d = 0
            for i, fa in enumerate(zip(self.freqs, self.amplitudes)):
                f, a = fa
                sf = f + i*self.fs
                d += a*math.cos(2*math.pi*sf*t) + a*1j*math.sin(2*math.pi*sf*t)
            data.append(d)
        sf = 100
        return data

    def test_channelizer(self):
        """
        Test a channelizer.
        """
        steps_rqd = self.n_data * self.sendnth + 1000
        self.tb.simulate(steps_rqd)
        received = [x*self.M for x in self.tb.output]
        skip = int(math.ceil(float(len(self.taps))/self.M-1)*self.M)
        received = [received[i+skip::self.M] for i in range(self.M)]
        expected = self.get_expected_data(self.n_data/self.M)
        p_convolved, p_final = pychannelizer(self.taps, self.data, self.M)
        for ed, dd, pd in zip(expected, received, p_final):
            pd = [p*self.tapscale*self.inputscale for p in pd]
            dd = [d*self.tapscale*self.inputscale for d in dd]
            epf = ed[-1]/pd[-1]
            rpd = [p*epf for p in pd]
            self.assertTrue(len(rpd) != 0)
            self.assertTrue(len(ed) != 0)
            self.assertTrue(len(pd) != 0)
            for e, p in zip(ed, rpd):
                self.assertAlmostEqual(e, p, 3)
            for d, p in zip(dd, pd):
                self.assertAlmostEqual(d, p, 3)
        # Compare ms
        self.assertEqual(len(self.tb.out_ms), len(self.ms))
        for r, e in zip(self.tb.out_ms, self.ms):
            self.assertEqual(r, e)
        # Compare first_channel signals
        fcs = ([1] + [0]*(self.M-1)) * (self.n_data/self.M)
        self.assertEqual(len(self.tb.out_fc), len(fcs))
        for r, e in zip(self.tb.out_fc, fcs):
            self.assertEqual(r, e)

if __name__ == '__main__':
    unittest.main()

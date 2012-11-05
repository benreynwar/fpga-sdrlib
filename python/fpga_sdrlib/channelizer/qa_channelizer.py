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

from fpga_sdrlib import config
from fpga_sdrlib.channelizer.build import generate_channelizer_executable
from fpga_sdrlib.testbench import TestBenchIcarus
from fpga_sdrlib.filterbank.qa_filterbank import scale_taps, taps_to_start_msgs, FilterbankTestBenchIcarus

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

def pychannelizer(flts, data, M):
    """
    Implements a pfb channelizer in python.
    """
    css = [data[i::M] for i in range(M)]
    convolved = [convolve(flts[i], css[i]) for i in range(M)]
    channels = []
    for k in range(M):
        filtered = [fft.fft(c)[k] for c in zip(*convolved)]
        channels.append([x for x in filtered])
    return convolved, channels

class ChannelizerTestBenchIcarus(TestBenchIcarus):
    """
    Helper class for doing testing.
    
    Args:
        name: A name to use with for generated files.
        n_chans: The number of channels (must be a power of 2).
        taps: The taps to use for the channelizer.
        in_samples: A list of complex points to send.
        sendnth: Send an input on every `sendnth` clock cycle.
        in_ms: A list of the meta data to send.
        defines: Macro definitions (constants) to use in verilog code.
    """

    extra_signal_names = ['first_channel']

    def __init__(self, name, n_chans, taps, in_samples,
                 sendnth=config.default_sendnth, in_ms=None,
                 defines=config.default_defines):
        self.logn = math.log(n_chans)/math.log(2)
        if int(self.logn) != self.logn:
            raise ValueError("The number of channels must be a power of two.")
        self.n_chans = n_chans
        self.name = name
        self.in_ms = in_ms
        self.in_samples = in_samples
        self.taps = taps
        self.n_taps = len(taps[0])
        self.width = defines['WIDTH']
        start_msgs = taps_to_start_msgs(taps, self.width/2)
        TestBenchIcarus.__init__(self, name, in_samples, sendnth, in_ms, start_msgs, defines)
        self.drivers.append(self.get_first_channel)

    def prepare(self):
        self.executable = generate_channelizer_executable(
            self.name, self.n_chans, self.width, self.n_taps, self.defines)

    def get_first_channel(self):
        self.out_fc = []
        @always(self.clk.posedge)
        def run():
            if self.out_nd:
                self.out_fc.append(int(self.first_channel))
        return run

def get_mixed_sinusoids(fs, n_data, freqs, amplitudes):
    """
    Return a stream of mixed sinusoids.  One sinusoid in
    each channel.
    
    Args:
        fs: The sampling frequency for an individual channel.
        n_data: The number of datapoints to return.
        freqs: The relative frequency of the signal in each stream.
        amplitudes: The amplitudes in each stream.
    """
    M = len(freqs)
    assert(len(amplitudes) == M)
    ifs = M * fs
    data = []
    ts = [float(x)/ifs for x in range(n_data)]
    for t in ts:
        d = 0
        for i, fa in enumerate(zip(freqs, amplitudes)):
            f, a = fa
            sf = f + i*fs
            d += a*math.cos(2*math.pi*sf*t) + a*1j*math.sin(2*math.pi*sf*t)
        data.append(d)
    return data

def get_channelizer_taps(M, n_taps=100):
    taps = signal.firwin2(100, [0, 1.0/M, 1.0/M+0.05, 1], [1, 1, 0, 0])
    # Divide by integral of absolute values to prevent the possibility
    # of overflow.
    chantaps = [taps[i::M] for i in range(M)]
    scaledtaps, tapscalefactor = scale_taps(chantaps)
    return scaledtaps, tapscalefactor
        
def get_expected_channelized_data(fs, L, freqs, amplitudes):
    """
    Get the expected data in each channel.
    """
    def make_data(f, a):
        t = [float(x)/fs for x in  xrange(L)]
        return [a*math.cos(2*math.pi*f*x) + a*1j*math.sin(2*math.pi*f*x)
                for x in t]
    expected_data = [make_data(f, a) for f, a in zip(freqs, amplitudes)]
    return expected_data



        
class TestChannelizer(unittest.TestCase):
    """
    Test the verilog channelizer.
    """

    def setUp(self):
        # Number of channels
        self.M = 4
        self.logM = int(math.log(self.M)/math.log(2))
        # The amount of data to send
        self.n_data = self.M * 30#200
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
        self.taps, self.tapscale = get_channelizer_taps(self.M, n_taps=100)
        # How often to send input.
        # For large FFTs this must be larger since the speed scales as MlogM.
        # Otherwise we get an overflow error.
        self.sendnth = 8
        # Get the input data
        self.data = get_mixed_sinusoids(self.fs, self.n_data, self.freqs, self.amplitudes)
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
        defines = config.updated_defines({"DEBUG": False,
                                          "WIDTH": self.width,
                                          "MWIDTH": self.mwidth})
        rtaps = []
        for tt in self.taps:
            rtaps.append(list(reversed(tt)))
        self.tb = ChannelizerTestBenchIcarus(name, self.M, rtaps, self.data,
                                             self.sendnth, self.ms, defines)
        self.ftb = FilterbankTestBenchIcarus(name, self.M, len(self.taps[0]), self.taps, self.data,
                                             self.sendnth, self.ms, defines)
        self.ftb.prepare()
        self.tb.prepare()

    def tearDown(self):
        pass

    def test_channelizer(self):
        """
        Test a channelizer.
        """
        steps_rqd = self.n_data * self.sendnth + 1000
        self.tb.run(steps_rqd)
        p_convolved, p_final = pychannelizer(self.taps, self.data, self.M)
        received = [x*self.M for x in self.tb.out_samples]
        skip = (len(self.taps[0])-1)*self.M
        received = [received[i+skip::self.M] for i in range(self.M)]
        expected = get_expected_channelized_data(
            self.fs, self.n_data/self.M, self.freqs, self.amplitudes)
        for ed, dd, pd in zip(expected, received, p_final):
            pd = [p*self.tapscale*self.inputscale for p in pd]
            dd = [d*self.tapscale*self.inputscale for d in dd]
            epf = ed[-1]/pd[-1]
            rpd = [p*epf for p in pd]
            self.assertTrue(len(rpd) != 0)
            self.assertTrue(len(ed) != 0)
            self.assertTrue(len(pd) != 0)
            allowed_dev = 5e-4
            for e, p in zip(ed, rpd):
                dev = abs(e-p)
                self.assertTrue(dev < allowed_dev)
            allowed_dev = 5e-3
            for d, p in zip(dd, pd):
                dev = abs(d-p)
                self.assertTrue(dev < allowed_dev)
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

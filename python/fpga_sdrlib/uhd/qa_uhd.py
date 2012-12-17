import random
import logging
import unittest

from fpga_sdrlib import config, buildutils
from fpga_sdrlib.testbench import TestBenchIcarusOuter, TestBenchB100
from fpga_sdrlib.generate import logceil

def bits_to_int(bits):
    f = 1
    s = 0
    for b in reversed(bits):
        s += b*f
        f *= 2
    return s

class TestNull(unittest.TestCase):
    
    def setUp(self):
        self.rg = random.Random(0)

    def atest_null(self):
        """
        Tests the null qa_wrapper.
        """
        width=32
        max_sample = pow(2, width-2)-1
        n_samples = 10
        data = [self.rg.randint(0, max_sample) for i in range(n_samples)]
        executable = buildutils.generate_icarus_executable(
            'uhd', 'null', '-test')
        fpgaimage = buildutils.generate_B100_image(
            'uhd', 'null', '-test')
        tb_icarus = TestBenchIcarusOuter(executable, in_raw=data)
        tb_b100 = TestBenchB100(fpgaimage, in_raw=data)
        for tb, steps in (
            (tb_icarus, 5000),
            (tb_b100, 10000),
            ):
            tb.run(steps)
            self.assertEqual(len(data), len(tb.out_raw))
            for e, r in zip(data, tb.out_raw):
                self.assertEqual(e, r)

    def test_bits(self):
        """
        Tests the bits qa_wrapper.
        """
        width=32
        sendnth = 70
        max_sample = pow(2, width)-1
        n_samples = 2
        data = [self.rg.randint(1, max_sample) for i in range(n_samples)]
        defines = config.updated_defines(
            {
             'LOG_WIDTH': logceil(width),
             'ERRORCODE': 666,
             'WIDTH': width,
             'LOG_SENDNTH': 12,
             })
        executable = buildutils.generate_icarus_executable(
            'uhd', 'bits', '-test', defines=defines)
        fpgaimage = buildutils.generate_B100_image(
            'uhd', 'bits', '-test', defines=defines)
        tb_icarus = TestBenchIcarusOuter(executable, in_raw=data, sendnth=sendnth)
        tb_b100 = TestBenchB100(fpgaimage, in_raw=data)
        for tb, steps in (
            (tb_icarus, 5000),
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
                if (p != expected):
                    print(i)
                    print(p)
                self.assertEqual(p, expected)
            r_ints = [bits_to_int(bits) for bits in bitted]
            r_ints = [x for x in r_ints if x != 0]
            self.assertEqual(len(data), len(r_ints))
            for e, r in zip(data, r_ints):
                self.assertEqual(e, r)

if __name__ == '__main__':
    config.setup_logging(logging.DEBUG)
    unittest.main()

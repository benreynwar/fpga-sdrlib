import random
import logging
import unittest

from fpga_sdrlib import config, buildutils
from fpga_sdrlib.testbench import TestBenchIcarusOuter, TestBenchB100

class TestNull(unittest.TestCase):
    
    def setUp(self):
        self.rg = random.Random(0)

    def test_null(self):
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

if __name__ == '__main__':
    config.setup_logging(logging.DEBUG)
    unittest.main()

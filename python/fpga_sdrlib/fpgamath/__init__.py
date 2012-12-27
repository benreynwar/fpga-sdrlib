"""
Utility functions to help with generation and verification of
verilog math code.
"""

from fpga_sdrlib.generate import copyfile

blocks = {
    # The basic modules.
    'log.v': (None, copyfile, {}),
    'multiply.v': (None, copyfile, {}),
    'multiply_complex.v': (('multiply.v',), copyfile, {}),
    # qa_contents modules.
    'qa_multiply.v': (('multiply.v',), copyfile, {}),
    'qa_multiply_complex.v': (('multiply_complex.v',), copyfile, {}),
    }

# compatible with running on the B100
compatibles = {
    'multiply':
        ('qa_multiply.v', 'uhd/qa_wrapper.v'),
    'multiply_complex':
        ('qa_multiply_complex.v', 'uhd/qa_wrapper.v'),
}

# Not compatible with running on the B100
incompatibles = {
    'multiply_inner':
        ('qa_multiply.v', 'uhd/dut_qa_contents.v'),
    'multiply_complex_inner':
        ('qa_multiply_complex.v', 'uhd/dut_qa_contents.v'),
}

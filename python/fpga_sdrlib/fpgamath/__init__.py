"""
Utility functions to help with generation and verification of
verilog math code.
"""

from fpga_sdrlib.generate import copyfile

blocks = {
    # The basic modules.
    'log.v': (None, copyfile, {}),
    # A qa_contents module for a filter.
    'multiply.v': (None, copyfile, {}),
    }

# compatible with running on the B100
compatibles = {
}

# Not compatible with running on the B100
incompatibles = {
}

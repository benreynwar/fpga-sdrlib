"""
Utility functions to help with generation and verification of
verilog message stream code.
"""

def copyfile(pck, fn):
    # Put inside to avoid circular dependency
    from fpga_sdrlib.buildutils import copyfile as cf
    return cf(pck,fn)

blocks = {
    # The basic modules.
    'split.v': (None, copyfile, {}),
    # Test module.
    'dut_split.v': (None, copyfile, {}),
    # A qa_wrapper that returns the first output from the splitter.
    'qa_split.v': (None, copyfile, {}),
    }

# compatible with running on the B100
compatibles = {
    'split_return_one':
        ('qa_split.v', 'split.v'),
}

# Not compatible with running on the B100
incompatibles = {
    'split':
        ('split.v', 'dut_split.v'),
}

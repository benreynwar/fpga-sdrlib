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
    'message_stream_combiner.v': (None, copyfile, {}),
    'message_slicer.v': (None, copyfile, {}),
    'sample_msg_splitter.v': (None, copyfile, {}),
    # Some dut's for incompatible icarus simulations.
    'dut_message_stream_combiner.v': (None, copyfile, {}),
    'dut_message_slicer.v': (None, copyfile, {}),
    # A qa_wrapper module containing just a sample_msg_splitter.
    # Drops the split out messages.
    'qa_sample_msg_splitter.v': (None, copyfile, {}),
    # A qa_wrapper module combining a sample_msg_splitter
    # and a message_stream_combiner.
    'qa_combo.v': (None, copyfile, {}),
    }

# compatible with running on the B100
compatibles = {
    'sample_msg_splitter': 
        ('sample_msg_splitter.v', 'qa_sample_msg_splitter.v'),
    'combo':
        ('sample_msg_splitter.v', 'message_stream_combiner.v', 'qa_combo.v'),
}

# Not compatible with running on the B100
incompatibles = {
    'message_stream_combiner':
        ('message_stream_combiner.v', 'dut_message_stream_combiner.v'),
    'message_slicer':
        ('message_slicer.v', 'dut_message_slicer.v'),
}

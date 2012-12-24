"""
Utility functions to help with generation and verification of
verilog fft code.
"""

from fpga_sdrlib.generate import copyfile

blocks = {
    # The basic modules.
    'stage.v': (None, copyfile, {}),
    'mstore.v': (None, copyfile, {}),
    'buffer_BB_to_stage.v': (None, copyfile, {}),
    'stage_to_out.v': (None, copyfile, {}),
    'dit.v': (('stage.v', ), copyfile, {}),
    # qa_contents modules
    'qa_stage.v': (('stage.v', 'mstore.v', 'buffer_BB_to_stage.v',
                    'stage_to_out.v', 'flow/buffer_BB.v'), copyfile, {}),
    'qa_dit.v': (('dit.v',), copyfile, {}),
    }

# compatible with running on the B100
compatibles = {
    'dit': 
        ('qa_dit.v', 'uhd/qa_wrapper.v',),
    'stage':
        ('qa_stage.v', 'uhd/qa_wrapper.v',),
}

# Not compatible with running on the B100
incompatibles = {
    'dit_inner': 
        ('qa_dit.v', 'uhd/dut_qa_contents.v'),
    'stage_inner':
        ('qa_stage.v', 'uhd/dut_qa_contents.v',),
}

"""
Generates some wrapper QA files for use with testing on a USRP.
"""

from fpga_sdrlib.generate import copyfile

blocks = {
    'dut_qa_wrapper.v': (None, copyfile, {}),
    'dut_qa_contents.v': (None, copyfile, {}),
    'qa_wrapper_null.v': (None, copyfile, {}),
    'bits.v': (None, copyfile, {}),
    'qa_wrapper_bits.v': (('bits.v',), copyfile, {}),
    'qa_wrapper.v': (('message/sample_msg_splitter.v',
                      'message/message_stream_combiner.v',),
                     copyfile, {}),
    }

compatibles = {
    'null': ('qa_wrapper_null.v',),
    'bits': ('qa_wrapper_bits.v',),
    }
incompatibles = {}

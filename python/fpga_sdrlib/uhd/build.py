# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import os

from fpga_sdrlib import config
from fpga_sdrlib.buildutils import copyfile, format_template, make_define_string
from fpga_sdrlib.message.build import generate_sample_msg_splitter_files, generate_stream_combiner_files

def generate_qa_wrapper_files():
    """
    Generate the files to make the 'nothing' block.
    """
    uhd_builddir= os.path.join(config.builddir, 'uhd')
    if not os.path.exists(uhd_builddir):
        os.makedirs(uhd_builddir)
    inputfiles = [copyfile('uhd', 'qa_wrapper.v'),
                  copyfile('uhd', 'dut_qa_wrapper.v')
                  ]
    inputfiles += generate_sample_msg_splitter_files()
    inputfiles += generate_stream_combiner_files()
    return inputfiles

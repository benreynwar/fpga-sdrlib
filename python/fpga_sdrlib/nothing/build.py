# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import os
import math
import shutil
import logging

from jinja2 import Environment, FileSystemLoader

from fpga_sdrlib import config, b100
from fpga_sdrlib.buildutils import copyfile, format_template, make_define_string
from fpga_sdrlib.message.build import generate_slicer_files

logger = logging.getLogger(__name__)

env = Environment(loader=FileSystemLoader(
        os.path.join(config.verilogdir, 'nothing')))

def generate_nothing_files():
    """
    Generate the files to make the 'nothing' block.
    """
    nothing_builddir= os.path.join(config.builddir, 'nothing')
    if not os.path.exists(nothing_builddir):
        os.makedirs(nothing_builddir)
    nothing_fn = copyfile('nothing', 'nothing.v')
    inputfiles = [nothing_fn]
    inputfiles += generate_slicer_files()
    return inputfiles

def generate_nothing_executable(name, defines):
    nothing_builddir= os.path.join(config.builddir, 'nothing')
    inputfiles = generate_nothing_files()
    dut_nothing_fn = copyfile('nothing', 'dut_nothing.v')    
    inputfilestr = ' '.join(inputfiles + [dut_nothing_fn])
    executable = 'nothing_{name}'.format(name=name)
    executable = os.path.join(nothing_builddir, executable)
    definestr = make_define_string(defines)
    cmd = ("iverilog -o {executable} {definestr} {msg_options} {inputfiles}"
           ).format(executable=executable,
                    definestr=definestr,
                    msg_options=config.msg_options,
                    inputfiles=inputfilestr)
    logger.debug(cmd)
    os.system(cmd)
    return executable

def make_qa_nothing(width, mwidth):
    """
    Generates a verilog file to use for QA on FPGA.
    """
    template_fn = 'qa_nothing.v.t'
    output_fn = os.path.join(config.builddir, 'nothing',
                             'qa_nothing.v')
    template = env.get_template(template_fn)
    if not os.path.exists(os.path.dirname(output_fn)):
        os.makedirs(os.path.dirname(output_fn))
    f_out = open(output_fn, 'w')
    f_out.write(template.render(
            width=width, mwidth=mwidth, 
            ))
    f_out.close()
    return output_fn
    
    

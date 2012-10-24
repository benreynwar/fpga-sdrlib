# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import os
import math
import shutil
import logging

from jinja2 import Environment, FileSystemLoader

from fpga_sdrlib import config, b100
from fpga_sdrlib.buildutils import copyfile, format_template
from fpga_sdrlib.message.build import generate_slicer_files

logger = logging.getLogger(__name__)

env = Environment(loader=FileSystemLoader(
        os.path.join(config.verilogdir, 'nothing')))

def generate(name, width, mwidth, debug):
    """
    Generate the files to make the 'nothing' block.
    
    Args:
        width: Number of bits in a complex number.
        mwidth: Number of bits in meta data.
        debug: Whether to include debug info in verilog.
    """
    nothing_builddir= os.path.join(config.builddir, 'nothing')
    if not os.path.exists(nothing_builddir):
        os.makedirs(nothing_builddir)
    dut_nothing_fn = copyfile('nothing', 'dut_nothing.v')
    nothing_fn = copyfile('nothing', 'nothing.v')
    inputfiles = [nothing_fn]
    inputfiles += generate_slicer_files()
    print(inputfiles)
    inputfilestr = ' '.join(inputfiles + [dut_nothing_fn])
    executable = 'nothing_{name}'.format(name=name)
    executable = os.path.join(nothing_builddir, executable)
    if debug:
        debugstr = "-DDEBUG"
    else:
        debugstr = ""
    cmd = ("iverilog -o {executable} -DWIDTH={width} -DMWIDTH={mwidth} {debugstr} "
           "{msg_options} "
           "{inputfiles}"
           ).format(width=width, mwidth=mwidth,
                    executable=executable,
                    debugstr=debugstr,
                    msg_options=config.msg_options,
                    inputfiles=inputfilestr)
    logger.debug(cmd)
    os.system(cmd)
    return executable, inputfiles

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
    
    

# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import os
import math
import shutil
import logging

from fpga_sdrlib import config
from fpga_sdrlib import b100
from fpga_sdrlib.buildutils import copyfile, format_template, make_define_string
from fpga_sdrlib.message.build import generate_slicer_files
from fpga_sdrlib.uhd.build import generate_qa_wrapper_files

logger = logging.getLogger(__name__)

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
    cmd = ("iverilog -o {executable} {definestr} {inputfiles}"
           ).format(executable=executable,
                    definestr=definestr,
                    inputfiles=inputfilestr)
    logger.debug(cmd)
    os.system(cmd)
    return executable
    
def generate_nothing_combined_files():
    nothing_builddir= os.path.join(config.builddir, 'nothing')
    inputfiles = generate_nothing_files()
    inputfiles += generate_qa_wrapper_files()
    inputfiles.append(copyfile('nothing', 'qa_nothing.v'))
    return inputfiles

def generate_nothing_combined_executable(name, defines):
    nothing_builddir= os.path.join(config.builddir, 'nothing')
    inputfiles = generate_nothing_combined_files()
    inputfiles.append(copyfile('uhd', 'dut_qa_wrapper.v'))
    inputfilestr = ' '.join(inputfiles)
    executable = 'nothing_combined_{name}'.format(name=name)
    executable = os.path.join(nothing_builddir, executable)
    definestr = make_define_string(defines)
    cmd = ("iverilog -o {executable} {definestr} {inputfiles}"
           ).format(executable=executable,
                    definestr=definestr,
                    inputfiles=inputfilestr)
    logger.debug(cmd)
    os.system(cmd)
    return executable

def generate_nothing_B100_image(name, defines):
    nothing_builddir= os.path.join(config.builddir, 'nothing')
    inputfiles = generate_nothing_combined_files()
    b100.make_make(name, nothing_builddir, inputfiles, defines)
    b100.synthesise(name, nothing_builddir)
    

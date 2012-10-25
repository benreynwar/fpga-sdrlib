# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import cmath
import math
import os
import logging
import shutil

from jinja2 import Environment, FileSystemLoader

from fpga_sdrlib import config
from fpga_sdrlib.conversions import cs_to_dicts
from fpga_sdrlib.buildutils import copyfile, format_template, make_define_string
from fpga_sdrlib.math.build import generate_math_files

logger = logging.getLogger(__name__)

env = Environment(loader=FileSystemLoader(
        os.path.join(config.verilogdir, 'fft')))

def get_builddir():
    fftbuilddir = os.path.join(config.builddir, 'fft')
    if not os.path.exists(fftbuilddir):
        os.makedirs(fftbuilddir)
    return fftbuilddir

def generate_dit_files(fft_length, tf_width):
    """
    Generate the fft files to perform an fft.
    
    Args:
        fft_length: Length of the FFT.
        tf_width: Number of bits in each real number of each twiddle factor.
    """
    get_builddir()
    inputfiles = generate_math_files()
    inputfiles.append(copyfile('fft', 'butterfly.v'))
    log_fft_length = math.log(fft_length)/math.log(2)
    if log_fft_length != int(log_fft_length):
        raise ValueError("fft_length must be a power of two")
    log_fft_length = int(log_fft_length)
    # Generate the dit.v file
    dit_fn = 'dit_{0}'.format(fft_length)
    inputfiles.append(
        format_template('fft', 'dit.v.t', dit_fn, {'N': fft_length}))    
    # Generate twiddle factor file.
    tf_fn = 'twiddlefactors_{0}'.format(fft_length)
    vs = [cmath.exp(-i*2j*cmath.pi/fft_length) for i in range(0, fft_length/2)]
    tfs = cs_to_dicts(vs, tf_width*2, clean1=True)
    tf_dict = {
        'N': fft_length,
        'log_N': log_fft_length,
        'tf_width': tf_width, 
        'tfs': tfs,
        }
    inputfiles.append(
        format_template('fft', 'twiddlefactors.v.t', tf_fn, tf_dict))
    return inputfiles

def generate_dit_executable(name, fft_length, defines): 
    log_fft_length = math.log(fft_length)/math.log(2)
    if log_fft_length != int(log_fft_length):
        raise ValueError("fft_length must be a power of two")
    log_fft_length = int(log_fft_length)
    get_builddir()
    defines['N'] = fft_length
    defines['LOG_N'] = log_fft_length
    dut_dit_fn = copyfile('fft', 'dut_dit.v')
    inputfiles = generate_dit_files(fft_length, defines['WIDTH']/2)
    executable = "dit_{name}".format(name=name)
    executable = os.path.join(config.builddir, 'fft', executable)
    inputfilestr = ' '.join(inputfiles + [dut_dit_fn])
    definestr = make_define_string(defines)
    cmd = ("iverilog -o {executable} {definestr} {msg_options} {inputfiles}"
           ).format(executable=executable,
                    definestr=definestr,
                    msg_options=config.msg_options,
                    inputfiles=inputfilestr)
    logger.debug(cmd)
    os.system(cmd)
    return executable

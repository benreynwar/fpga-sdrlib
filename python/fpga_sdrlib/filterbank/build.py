# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import cmath
import math
import os
import shutil
import logging

from jinja2 import Environment, FileSystemLoader

from fpga_sdrlib.conversions import fs_to_dicts
from fpga_sdrlib import config
from fpga_sdrlib.buildutils import copyfile, format_template, make_define_string
from fpga_sdrlib.math.build import generate_math_files

logger = logging.getLogger(__name__)

env = Environment(loader=FileSystemLoader(
        os.path.join(config.verilogdir, 'filterbank')))

def get_builddir():
    fftbuilddir = os.path.join(config.builddir, 'filterbank')
    if not os.path.exists(fftbuilddir):
        os.makedirs(fftbuilddir)
    return fftbuilddir

def generate_filterbank_files(filter_length):
    """
    Generate the files for making a filterbank.
    
    Args:
        filter_length: The length of each filter.
    """
    get_builddir()
    log_filter_length = int(math.ceil(math.log(filter_length)/math.log(2)))
    inputfiles = []
    # Generate summult file
    summult_fn = 'summult_{0}.v'.format(filter_length)
    real_sum = ["x_re_y[{0}]".format(i) for i in range(filter_length)]
    real_sum = " + ".join(real_sum)
    imag_sum = ["x_im_y[{0}]".format(i) for i in range(filter_length)]
    imag_sum = " + ".join(imag_sum)
    inputfiles.append(
        format_template('filterbank', 'summult.v.t', summult_fn,
                        {'real_sum': real_sum,
                         'imag_sum': imag_sum}))
    inputfiles.append(copyfile('filterbank', 'filterbank.v'))
    inputfiles += generate_math_files()
    return inputfiles

def generate_filterbank_executable(name, n_filters, filter_length, defines):
    builddir = get_builddir()
    inputfiles = generate_filterbank_files(filter_length)                      
    dut_filterbank_fn = copyfile('filterbank', 'dut_filterbank.v')
    executable = "filterbank_{name}".format(name=name)
    executable = os.path.join(config.builddir, 'filterbank', executable)
    inputfilestr = ' '.join(inputfiles + [dut_filterbank_fn])
    defines.update({
            'N': n_filters,
            'LOG_N': int(math.ceil(math.log(n_filters)/math.log(2))),
            'FLTLEN': filter_length,
            'LOG_FLTLEN': int(math.ceil(math.log(filter_length)/math.log(2))),
            })
    definestr = make_define_string(defines)
    cmd = ("iverilog -o {executable} {definestr} {inputfiles}"
           ).format(executable=executable,
                    definestr=definestr,
                    inputfiles=inputfilestr)
    logger.debug(cmd)
    os.system(cmd)
    return executable


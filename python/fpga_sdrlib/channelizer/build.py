# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import os
import math
import shutil
import logging

from fpga_sdrlib.fft.build import generate_dit_files
from fpga_sdrlib.filterbank.build import generate_filterbank_files
from fpga_sdrlib import config
from fpga_sdrlib.buildutils import copyfile, format_template, make_define_string

logger = logging.getLogger(__name__)

def get_builddir():
    fftbuilddir = os.path.join(config.builddir, 'channelizer')
    if not os.path.exists(fftbuilddir):
        os.makedirs(fftbuilddir)
    return fftbuilddir

def generate_channelizer_files(n_chans, width, filter_length):
    """
    Generate the channelizer module files.
    
    Args:
        n_chans: Number of channels to split into.
        width: The width of a complex number
               (actually required so we can get the twiddle factor widths for fft).
        filter_length: The length of each filter in the filterbank.
    """
    builddir = get_builddir()
    logn = math.log(n_chans)/math.log(2)
    if int(logn) != logn:
        raise ValueError("Number of channels must be a power of two.")
    # Divide width by 2 since generate_dit_files takes real width not complex width.
    inputfiles = generate_dit_files(n_chans, width/2)
    inputfiles += generate_filterbank_files(filter_length)
    inputfiles.append(copyfile('channelizer', 'channelizer.v'))
    # Remove repeated dependencies
    inputfiles = list(set(inputfiles))
    return inputfiles
    
def generate_channelizer_executable(name, n_chans, width, filter_length, defines):
    """
    Generate an icarus verilog channelizer executable.
    
    Args:
        name: A name to identify the executable by.
        n_chans: Number of channels to split into.
        width: The width of a complex number
               (actually required so we can get the twiddle factor widths for fft).
        filter_length: The length of each filter in the filterbank.
        defines: Macro definitions for the verilog files.
    """
    builddir = get_builddir()
    inputfiles = generate_channelizer_files(n_chans, width, filter_length)                      
    dut_channelizer_fn = copyfile('channelizer', 'dut_channelizer.v')
    executable = "channelizer_{name}".format(name=name)
    executable = os.path.join(config.builddir, 'channelizer', executable)
    inputfilestr = ' '.join(inputfiles + [dut_channelizer_fn])
    defines['N'] = n_chans
    defines['LOG_N'] = int(math.ceil(math.log(n_chans)/math.log(2)))
    defines['FLTLEN'] = filter_length
    defines['LOG_FLTLEN'] = int(math.ceil(math.log(filter_length)/math.log(2)))
    definestr = make_define_string(defines)
    cmd = ("iverilog -o {executable} {definestr} {msg_options} {inputfiles}"
           ).format(executable=executable,
                    definestr=definestr,
                    msg_options=config.msg_options,
                    inputfiles=inputfilestr)
    logger.debug(cmd)
    os.system(cmd)
    return executable

def make_taps(taps, n_chans):
    extra_taps = int(math.ceil(1.0*len(taps)/n_chans)*n_chans - len(taps))
    taps = taps + [0] * extra_taps
    # Make taps for each channel
    chantaps = [list(reversed(taps[i: len(taps): n_chans])) for i in range(0, n_chans)]
    for taps in chantaps:
        summedtaps = sum(taps)
        if summedtaps < -1 or summedtaps > 1:
            raise ValueError("Summed taps for each channel must be between -1 and 1 (Value is {0}).".format(summedtaps))
    return chantaps


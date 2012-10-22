# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import os
import math
import shutil
import logging

from jinja2 import Environment, FileSystemLoader

from fpga_sdrlib.fft.build import generate as generate_fft
from fpga_sdrlib.filterbank.build import generate as generate_fb
from fpga_sdrlib import config, b100

logger = logging.getLogger(__name__)

env = Environment(loader=FileSystemLoader(
        os.path.join(config.verilogdir, 'channelizer')))

def generate(name, n_chans, taps, width, mwidth, qa_args={}):
    """
    Generate the fft files to perform an fft.
    
    Args:
        n_chans: Number of channels to split into.
        taps: The taps to use for the channelizer.
        width: Number of bits in a complex number.
        mwidth: Number of bits in meta data.
        qa_args: Arguments for data_source module if we're doing QA on FPGA.
    """
    logn = math.log(n_chans)/math.log(2)
    if int(logn) != logn:
        raise ValueError("Number of channels must be a power of two.")
    logn = int(logn)
    extra_taps = int(math.ceil(1.0*len(taps)/n_chans)*n_chans - len(taps))
    taps = taps + [0] * extra_taps
    # Make taps for each channel
    chantaps = [list(reversed(taps[i: len(taps): n_chans])) for i in range(0, n_chans)]
    for taps in chantaps:
        summedtaps = sum(taps)
        if summedtaps < -1 or summedtaps > 1:
            raise ValueError("Summed taps for each channel must be between -1 and 1 (Value is {0}).".format(summedtaps))
    flt_len = len(chantaps[0])
    chan_builddir= os.path.join(config.builddir, 'channelizer')
    if not os.path.exists(chan_builddir):
        os.makedirs(chan_builddir)
    if qa_args:
        qa_channelizer_fn = make_qa_channelizer(width, mwidth, n_chans, flt_len, qa_args)
    dut_channelizer_fn = os.path.join(chan_builddir, 'dut_channelizer.v')
    shutil.copyfile(os.path.join(config.verilogdir, 'channelizer', 'dut_channelizer.v'),
                    dut_channelizer_fn)
    channelizer_fn = os.path.join(chan_builddir, 'channelizer.v')
    shutil.copyfile(os.path.join(config.verilogdir, 'channelizer', 'channelizer.v'),
                    channelizer_fn)
    executable_fft, inputfiles_fft = generate_fft(n_chans, width/2, mwidth)
    executable_fb, inputfiles_fb = generate_fb(name, chantaps, width, mwidth)
    inputfiles = inputfiles_fft + inputfiles_fb + [channelizer_fn]
    inputfilestr = ' '.join(inputfiles) + ' ' + dut_channelizer_fn
    executable = 'channelizer_{name}'.format(name=name)
    executable = os.path.join(chan_builddir, executable)
    cmd = ("iverilog -o {executable} -DN={n} -DWDTH={width} -DMWDTH={mwidth} "
           "-DLOGN={logn} -DFLTLEN={flt_len} {inputfiles}"
           ).format(n=n_chans, width=width, mwidth=mwidth, logn=logn,
                    flt_len=flt_len, executable=executable,
                    inputfiles=inputfilestr)
    logger.debug(cmd)
    os.system(cmd)
    return executable, inputfiles

def make_qa_channelizer(width, mwidth, n, fltlen, qa_args):
    """
    Generates a verilog file to use for QA on FPGA.
    """
    sendnth = qa_args['sendnth']
    n_data = qa_args['n_data']
    logn = int(math.ceil(math.log(n)/math.log(2)))
    logsendnth = int(math.ceil(math.log(sendnth)/math.log(2)))
    logndata = int(math.ceil(math.log(n_data)/math.log(2)))
    template_fn = 'qa_channelizer.v.t'
    output_fn = os.path.join(config.builddir, 'channelizer',
                             'qa_channelizer.v')
    template = env.get_template(template_fn)
    if not os.path.exists(os.path.dirname(output_fn)):
        os.makedirs(os.path.dirname(output_fn))
    f_out = open(output_fn, 'w')
    f_out.write(template.render(
            width=width, mwidth=mwidth, n=n, fltlen=fltlen, logn=logn,
            sendnth=sendnth, logsendnth=logsendnth, n_data=n_data,
            logndata=logndata,
            ))
    f_out.close()
    return output_fn
    
    

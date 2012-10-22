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

logger = logging.getLogger(__name__)

env = Environment(loader=FileSystemLoader(
        os.path.join(config.verilogdir, 'filterbank')))

def generate(name, chantaps, width, mwidth, qa_args={}):
    """
    Generate the files for making a filterbank.
    
    Args:
        name: A name for the filterbank to use with generated files.
        chantaps: A list of lists of taps (taps are real not complex).
        width: Number of bits in a complex number.
    """
    flt_len = len(chantaps[0])
    n_filters = len(chantaps)
    print(flt_len, n_filters)
    addrlen = int(math.ceil(math.log(n_filters)/math.log(2)))
    for taps in chantaps:
        if len(taps) != flt_len:
            raise ValueError("All filters must be of the same length.")
    summult_fn = make_summult(flt_len)
    taps_fn = make_taps(name, chantaps, width/2)
    if qa_args:
        make_qa_filterbank(width, mwidth, n_filters, flt_len, qa_args)
    filterbank_fn = make_filterbank(n_filters, flt_len)
    dut_filterbank_fn = os.path.join(config.builddir, 'filterbank', 'dut_filterbank.v')
    shutil.copyfile(os.path.join(config.verilogdir, 'filterbank', 'dut_filterbank.v'),
                    dut_filterbank_fn)    
    inputfiles = [filterbank_fn, summult_fn, taps_fn]
    inputfilestr = ' '.join(inputfiles + [dut_filterbank_fn])
    executable = "filterbank_{name}".format(name=name)
    executable = os.path.join(config.builddir, 'filterbank', executable)
    cmd = ("iverilog -o {executable} -DN={n} -DWDTH={width} -DADDRLEN={addrlen} "
           "-DFLTLEN={flt_len} -DMWDTH={mwidth} {inputfiles}"
           ).format(executable=executable, n=n_filters, width=width,
                    addrlen=addrlen, flt_len=flt_len, mwidth=mwidth, inputfiles=inputfilestr)
    logger.debug(cmd)
    os.system(cmd)
    return executable, inputfiles

def make_summult(N, template_fn='summult.v.t', output_fn=None):
    """
    Generates a verilog file to do some multiplying and summing from
    at template.
    """
    if output_fn is None:
        output_fn = os.path.join(config.builddir, 'filterbank', 'summult_{0}.v'.format(N))
    # Generate a bunch of wires pointing at the individual numbers.
    t = "wire signed [WDTH-1:0] in_x{i}_re;\n"
    t += "wire signed [WDTH-1:0] in_x{i}_im;\n"
    t += "wire signed [WDTH-1:0] in_y{i};\n"
    t += "assign in_x{i}_re = in_xs[WDTH*(2*(N-{i}))-1 -:WDTH];\n"
    t += "assign in_x{i}_im = in_xs[WDTH*(2*(N-{i})-1)-1 -:WDTH];\n"
    t += "assign in_y{i} = in_ys[WDTH*(N-{i})-1 -:WDTH];"
    # Do the convolution on these numbers.
    real_sum_bits = []
    imag_sum_bits = []
    for i in range(N):
        real_sum_bits.append('(in_x{i}_re * in_y{i})'.format(i=i))
        imag_sum_bits.append('(in_x{i}_im * in_y{i})'.format(i=i))
    real_sum = '+'.join(real_sum_bits)
    imag_sum = '+'.join(imag_sum_bits)
    inputassigns = "\n".join([t.format(i=i) for i in range(N)])
    template = env.get_template(template_fn)
    if not os.path.exists(os.path.dirname(output_fn)):
        os.makedirs(os.path.dirname(output_fn))
    f_out = open(output_fn, 'w')
    f_out.write(template.render(real_sum=real_sum, imag_sum=imag_sum,
                                inputassigns=inputassigns))  
    f_out.close()
    return output_fn

def make_taps(name, chantaps, width, output_fn=None):
    """
    Generates a verilog file with all the taps.
    """
    template_fn = 'taps.v.t'
    if output_fn is None:
        output_fn = os.path.join(config.builddir, 'filterbank',
                                 'taps_{name}.v'.format(name=name))
    n_filters = len(chantaps)
    addrlen = int(math.ceil(math.log(n_filters)/math.log(2)))
    channels = []
    for i, taps in enumerate(chantaps):
        channels.append((i, reversed(fs_to_dicts(taps, width))))
    template = env.get_template(template_fn)
    if not os.path.exists(os.path.dirname(output_fn)):
        os.makedirs(os.path.dirname(output_fn))
    f_out = open(output_fn, 'w')
    f_out.write(template.render(channels=channels, tap_width=width,
                                addrlen=addrlen))
    f_out.close()
    return output_fn
    

def make_filterbank(n_chans, filter_length, template_fn='filterbank.v.t',
                    output_fn=None):
    """
    Generates the 'filterbank.v' verilog file.
    """
    if output_fn is None:
        output_fn = os.path.join(config.builddir, 'filterbank',
                                 'filterbank_{0}.v'.format(filter_length))
    t = "histories[{i}] <= {{WDTH*FLTLEN{{1'b0}} }};"
    zerohistories = '\n'.join([t.format(i=i) for i in range(n_chans)])
    #t = "histories[filter_n][WDTH*(FLTLEN-{i})-1:WDTH] <= histories[filter_n][WDTH*(FLTLEN-{ip})-1:0];"
    t = "shifted_history <= histories[filter_n][WDTH*(FLTLEN-{ip})-1:0];"
    shifthistories = [t.format(i=i, ip=i+1) for i in range(1, filter_length-1)]
    shifthistories = "\n".join(shifthistories)
    template = env.get_template(template_fn)
    if not os.path.exists(os.path.dirname(output_fn)):
        os.makedirs(os.path.dirname(output_fn))
    f_out = open(output_fn, 'w')
    f_out.write(template.render(zerohistories=zerohistories,
                                shifthistories=shifthistories))
    f_out.close()
    return output_fn
                               
def make_qa_filterbank(width, mwidth, n, fltlen, qa_args):
    """
    Generates a verilog file to use for QA on FPGA.
    """
    sendnth = qa_args['sendnth']
    n_data = qa_args['n_data']
    logn = int(math.ceil(math.log(n)/math.log(2)))
    logsendnth = int(math.ceil(math.log(sendnth)/math.log(2)))
    logndata = int(math.ceil(math.log(n_data)/math.log(2)))
    template_fn = 'qa_filterbank.v.t'
    output_fn = os.path.join(config.builddir, 'filterbank',
                             'qa_filterbank.v')
    template = env.get_template(template_fn)
    if not os.path.exists(os.path.dirname(output_fn)):
        os.makedirs(os.path.dirname(output_fn))
    f_out = open(output_fn, 'w')
    f_out.write(template.render(
            width=width, mwidth=mwidth, n=n, addrlen=logn, fltlen=fltlen,
            sendnth=sendnth, logsendnth=logsendnth, n_data=n_data,
            logndata=logndata,
            ))
    f_out.close()
    return output_fn
    
    

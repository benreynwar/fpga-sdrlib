# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import cmath
import math
import os
import shutil
import logging

from jinja2 import Environment, FileSystemLoader

from fpga_sdrlib.conversions import cs_to_dicts, is_to_dicts
from fpga_sdrlib import config

logger = logging.getLogger(__name__)

env = Environment(loader=FileSystemLoader(
        os.path.join(config.verilogdir, 'data_source')))

def generate(name, data, ms, sendnth, n_loops, width, mwidth):
    """
    Generate the files for making a data_source.
    
    Args:
        name: A name for the data_source to use with the generated files.
        data: A list of the complex data to send.
        ms: A list of the meta data to send (integers).
        width: Number of bits in a complex number.
        mwidth: Number of bits in meta data.
    """
    n_data = len(data)
    assert(len(ms) == n_data)
    log_n_data = int(math.ceil(math.log(n_data)/math.log(2)))
    log_n_loops = int(math.ceil(math.log(n_loops)/math.log(2)))
    if log_n_loops == 0:
        log_n_loops = 1
    log_sendnth = int(math.ceil(math.log(sendnth)/math.log(2)))
    data_source_fn = make_data_source(name, data, ms, width, mwidth);
    os.path.join(config.builddir, 'data_source', 'data_source.v')
    dut_data_source_fn = os.path.join(config.builddir, 'data_source', 'dut_data_source.v')
    shutil.copyfile(os.path.join(config.verilogdir, 'data_source', 'dut_data_source.v'),
                    dut_data_source_fn)    
    inputfiles = [data_source_fn]
    inputfilestr = ' '.join(inputfiles + [dut_data_source_fn])
    executable = "data_source_{name}".format(name=name)
    executable = os.path.join(config.builddir, 'data_source', executable)
    cmd = ("iverilog -o {executable} "
           "-DSENDNTH={sendnth} -DLOGSENDNTH={log_sendnth} "
           "-DN_LOOPS={n_loops} -DLOGNLOOPS={log_n_loops} "
           "-DWIDTH={width} -DMWIDTH={mwidth} "
           "-DN_DATA={n_data} -DLOGNDATA={log_n_data} {inputfiles}"
           ).format(executable=executable,
                    sendnth=sendnth, log_sendnth=log_sendnth,
                    n_loops=n_loops, log_n_loops=log_n_loops,
                    width=width, mwidth=mwidth,
                    n_data=n_data, log_n_data=log_n_data, 
                    inputfiles=inputfilestr)
    logger.debug(cmd)
    os.system(cmd)
    return executable, inputfiles

def make_data_source(name, data, ms, width, mwidth):
    """
    Generates a verilog file with the complex data and meta data.
    """
    template_fn = 'data_source.v.t'
    output_fn = os.path.join(config.builddir, 'data_source',
                             'data_source_{name}.v'.format(name=name))
    data = cs_to_dicts(data, width, clean1=False)
    ms = is_to_dicts(ms, mwidth)
    template = env.get_template(template_fn)
    if not os.path.exists(os.path.dirname(output_fn)):
        os.makedirs(os.path.dirname(output_fn))
    f_out = open(output_fn, 'w')
    f_out.write(template.render(data=data, ms=ms, width=width/2, mwidth=mwidth))
    f_out.close()
    return output_fn
    

"""
Utility functions to help with generation and verification of
verilog filter code.
"""

import os
import math

from fpga_sdrlib import config
from fpga_sdrlib.generate import copyfile, format_template

def make_filter(pck, fn, dependencies, extraargs={}):
    """
    Generate filter_X.v from filter.v
    
    This is done so that we can convert the 2D array tapvalues to
    a 1D array to pass to summult.
    """
    # dependencies is not used
    length = extraargs.get('summult_length', None)
    if length is None:
        raise ValueError("Length for filter.v is not known.")
    log_length = int(math.ceil(math.log(length)/math.log(2)))
    # Generate filter file
    assert(fn == 'filter.v.t')
    summult_fn = 'filter_{0}.v'.format(length)
    in_fn = os.path.join(config.verilogdir, pck, fn)
    out_fn = os.path.join(config.builddir, pck, summult_fn)
    out_dir = os.path.join(config.builddir, pck)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    tapvalues_1D = ["tapvalues[{0}]".format(i) for i in reversed(range(length))]
    tapvalues_1D = "{" + ", ".join(tapvalues_1D) + "}"
    format_template(in_fn, out_fn, {'tapvalues_1D': tapvalues_1D})
    return out_fn, {'summult.v.t': extraargs}
    

def make_summult(pck, fn, dependencies, extraargs={}):
    # dependencies is not used
    length = extraargs.get('summult_length', None)
    if length is None:
        raise ValueError("Length for summult.v is not known.")
    log_length = int(math.ceil(math.log(length)/math.log(2)))
    # Generate summult file
    assert(fn == 'summult.v.t')
    summult_fn = 'summult_{0}.v'.format(length)
    in_fn = os.path.join(config.verilogdir, pck, fn)
    out_fn = os.path.join(config.builddir, pck, summult_fn)
    out_dir = os.path.join(config.builddir, pck)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    real_sum = ["x_re_y[{0}]".format(i) for i in range(length)]
    real_sum = " + ".join(real_sum)
    imag_sum = ["x_im_y[{0}]".format(i) for i in range(length)]
    imag_sum = " + ".join(imag_sum)
    format_template(in_fn, out_fn, 
                    {'real_sum': real_sum,
                     'imag_sum': imag_sum})
    return out_fn, {}

blocks = {
    # The basic modules.
    'filter.v.t': (('summult.v.t',), make_filter, {}),
    # A qa_contents module for a filter.
    'qa_filter.v': (('filter.v.t',), copyfile, {}),
    'summult.v.t': (('fpgamath/multiply.v', ), make_summult, {})
    }

# compatible with running on the B100
compatibles = {
    'filter': 
        ('qa_filter.v', 'uhd/qa_wrapper.v',),
}

# Not compatible with running on the B100
incompatibles = {
    'filter_inner': 
        ('qa_filter.v', 'uhd/dut_qa_contents.v'),
}
